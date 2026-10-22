"""Recupera partidas oficiais recentes, com cache e limite de trabalho por execução.

Não baixa telemetria. Nunca persiste a chave nem estatísticas de quem não está no clã.
"""
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

MODES = ['squad-fpp', 'duo-fpp', 'squad', 'duo', 'solo-fpp', 'solo']
GROUPS = {'todos': MODES, 'fpp': MODES[:2], 'tpp': MODES[2:4], **{m: [m] for m in MODES}}
FIELDS = ['rideDistance', 'teamKills', 'revives', 'timeSurvived', 'heals', 'boosts', 'walkDistance', 'weaponsAcquired', 'longestKill', 'kills']

def moment(text):
    return datetime.fromisoformat(text.replace('Z', '+00:00'))

def week_start(now):
    local = now.astimezone(ZoneInfo('America/Sao_Paulo'))
    return (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else None

def normalize_match(payload, allowed):
    data = payload['data']
    attrs = data['attributes']
    at = moment(attrs['createdAt'])
    mode = attrs.get('gameMode')
    record = {'id': data['id'], 'at': at.isoformat(), 'mode': mode, 'players': {}}
    # Match types de treino, evento, personalizado e competitivo ficam de fora.
    if attrs.get('isCustomMatch') is not False or attrs.get('matchType') != 'official' or mode not in MODES:
        record['status'] = 'ignorada'
        return record
    record['status'] = 'normal'
    for item in payload.get('included', []):
        if item.get('type') != 'participant':
            continue
        stats = item.get('attributes', {}).get('stats', {})
        account_id = stats.get('playerId')
        if account_id not in allowed:
            continue
        raw = {key: number(stats.get(key)) for key in FIELDS}
        raw['roundsPlayed'] = 1
        death = stats.get('deathType')
        if number(stats.get('suicides')) is not None:
            raw['suicides'] = number(stats['suicides'])
        elif death == 'suicide':
            raw['suicides'] = 1
        elif death in ('alive', 'byplayer', 'byzone', 'logout'):
            raw['suicides'] = 0
        else:
            raw['suicides'] = None
        record['players'][account_id] = raw
    if not record['players']:
        raise ValueError('Partida oficial sem participantes do clã reconhecidos.')
    return record

def download_match(match_id):
    # /matches não consome a cota de 10 RPM e não precisa receber a chave secreta.
    url = 'https://api.pubg.com/shards/steam/matches/' + quote(match_id, safe='')
    for attempt in range(2):
        try:
            with urlopen(Request(url, headers={'Accept': 'application/vnd.api+json'}), timeout=15) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code == 404:
                return None
            if error.code not in (429, 500, 502, 503, 504) or attempt:
                raise RuntimeError('HTTP ' + str(error.code)) from None
        except (URLError, TimeoutError):
            if attempt:
                raise RuntimeError('Timeout ao recuperar partida') from None
        time.sleep(1)
    raise RuntimeError('Falha ao recuperar partida')

def add_raw(total, raw):
    for key, value in raw.items():
        if key == 'longestKill':
            total[key] = max(total.get(key, 0), value) if total.get(key, 0) is not None and value is not None else None
        else:
            total[key] = total.get(key, 0) + value if total.get(key, 0) is not None and value is not None else None

def aggregate_week(records, roster, start, end):
    by_mode = {mode: {} for mode in MODES}
    count = 0
    for match in records.values():
        if match.get('status') != 'normal' or match.get('mode') not in by_mode or not start <= moment(match['at']) < end:
            continue
        included = False
        for account_id, raw in match['players'].items():
            if account_id not in roster:
                continue
            total = by_mode[match['mode']].setdefault(account_id, {})
            add_raw(total, raw)
            included = True
        count += int(included)
    groups = {}
    for group, modes in GROUPS.items():
        combined = {}
        for mode in modes:
            for account_id, raw in by_mode[mode].items():
                add_raw(combined.setdefault(account_id, {}), raw)
        groups[group] = [{'nick': roster[aid], 'account_id': aid, 'partidas': raw['roundsPlayed'], 'raw': raw}
                         for aid, raw in combined.items() if raw['roundsPlayed'] > 0]
    return groups, count

def collect_recent(client, resolved, old_cache, now, fetch_match=None, max_matches=400, budget_seconds=180):
    fetch_match = fetch_match or download_match
    roster = {account_id: nick for nick, account_id in resolved.items()}
    cutoff = now - timedelta(days=90)
    records = {mid: item for mid, item in old_cache.get('partidas', {}).items()
               if moment(item['at']) >= cutoff}
    references = {}
    failures = []
    returned = set()
    ids = list(roster)
    for index in range(0, len(ids), 10):
        batch = ids[index:index + 10]
        try:
            response = client.get('players', {'filter[playerIds]': ','.join(batch)})
            for player in response['data']:
                account_id = player['id']
                if account_id not in roster:
                    continue
                relationships = player.get('relationships', {})
                if not isinstance(relationships.get('matches', {}).get('data'), list):
                    failures.append(roster[account_id])
                    continue
                returned.add(account_id)
                for item in relationships['matches']['data']:
                    if isinstance(item.get('id'), str):
                        references.setdefault(item['id'], set()).add(account_id)
        except Exception:
            failures.extend(roster[aid] for aid in batch)
    for aid in roster:
        if aid not in returned:
            failures.append(roster[aid])
    pending = {mid: set(aids) & set(roster) for mid, aids in old_cache.get('pendentes', {}).items() if set(aids) & set(roster)}
    for mid, aids in references.items():
        item = records.get(mid)
        if item and (item.get('status') == 'ignorada' or aids.issubset(item.get('players', {}))):
            continue
        pending.setdefault(mid, set()).update(aids)
    expired = dict(old_cache.get('indisponiveis', {}))
    # Uma referência que retorna 404 é tentada novamente nas duas coletas seguintes.
    for mid in list(pending):
        info = expired.get(mid)
        if info and (now - moment(info['primeira_tentativa']) > timedelta(days=14) or info['tentativas'] >= 3):
            del pending[mid]
    selected = list(pending)[:max_matches]
    started = time.monotonic()
    succeeded = 0
    download_errors = 0
    # Lotes pequenos permitem respeitar o orçamento sem deixar centenas de tarefas em espera.
    with ThreadPoolExecutor(max_workers=8) as executor:
        for index in range(0, len(selected), 8):
            if time.monotonic() - started >= budget_seconds:
                break
            futures = {executor.submit(fetch_match, mid): mid for mid in selected[index:index + 8]}
            for future in as_completed(futures):
                mid = futures[future]
                try:
                    payload = future.result()
                    if payload is None:
                        info = expired.setdefault(mid, {'primeira_tentativa': now.isoformat(), 'tentativas': 0})
                        info['tentativas'] += 1
                        if info['tentativas'] >= 3:
                            pending.pop(mid, None)
                        download_errors += 1
                        continue
                    item = normalize_match(payload, roster)
                    if item['id'] != mid:
                        raise ValueError('ID de partida divergente.')
                    records[mid] = item
                    expired.pop(mid, None)
                    if item['status'] == 'normal' and not pending[mid].issubset(item['players']):
                        download_errors += 1
                        continue
                    pending.pop(mid, None)
                    succeeded += 1
                except Exception:
                    download_errors += 1
    start = week_start(now)
    groups, week_count = aggregate_week(records, roster, start, now + timedelta(seconds=1))
    summary = {'schema_version': 1, 'fonte': 'partidas', 'updated_at': now.isoformat(),
               'inicio_semana': start.isoformat(), 'parcial': True, 'grupos': groups,
               'partidas_semana': week_count, 'partidas_em_cache': sum(m.get('status') == 'normal' for m in records.values()),
               'recuperadas_agora': succeeded, 'pendentes': len(pending), 'falhas_partidas': download_errors,
               'membros_sem_lista': sorted(set(failures)), 'indisponiveis': len(expired),
               'aviso': 'Somente partidas oficiais recuperadas. A API pode limitar as listas e omitir partidas; cobertura pode ser parcial.'}
    cache = {'schema_version': 1, 'updated_at': now.isoformat(), 'partidas': records,
             'pendentes': {mid: sorted(aids) for mid, aids in pending.items()}, 'indisponiveis': expired}
    return cache, summary

def archive_matches(cache, existing, resolved, now, award_definitions):
    roster = {aid: nick for nick, aid in resolved.items()}
    current_start = week_start(now)
    starts = {week_start(moment(m['at'])) for m in cache.get('partidas', {}).values()
              if m.get('status') == 'normal' and week_start(moment(m['at'])) < current_start}
    archived = list(existing.get('semanas', []))
    for start in sorted(starts):
        end = start + timedelta(days=7)
        groups, count = aggregate_week(cache['partidas'], roster, start, end)
        if not count:
            continue
        results = {}
        for mode, rows in groups.items():
            awards = {}
            for key, (field, minimum, per_game, ascending) in award_definitions.items():
                candidates = []
                for row in rows:
                    raw = row['raw']
                    value = (raw['heals'] + raw['boosts'] if raw.get('heals') is not None and raw.get('boosts') is not None else None) if field == 'heals_boosts' else raw.get(field)
                    if value is None or value <= 0 or row['partidas'] < minimum:
                        continue
                    candidates.append({'nick': row['nick'], 'valor': value / row['partidas'] if per_game else value, 'partidas': row['partidas']})
                if candidates:
                    best = (min if ascending else max)(p['valor'] for p in candidates)
                    awards[key] = [p for p in candidates if abs(p['valor'] - best) < 1e-9]
            results[mode] = awards
        same = [w for w in archived if w['inicio_semana'][:10] == start.isoformat()[:10]]
        # Semana já encerrada e arquivada por partidas fica estável: novos membros não alteram os vencedores.
        previous = next((w for w in same if w.get('fonte') == 'partidas'), None)
        if previous and now > start + timedelta(days=14):
            archived = [w for w in archived if w not in same or w is previous]
            continue
        archived = [w for w in archived if w not in same]
        archived.append({'id': 'semana:' + start.date().isoformat(), 'fonte': 'partidas', 'season_id': 'partidas-recuperadas',
                         'inicio_semana': start.isoformat(), 'de': start.isoformat(), 'ate': (end - timedelta(seconds=1)).isoformat(),
                         'atualizado_em': now.isoformat(), 'parcial': True, 'partidas_recuperadas': count, 'grupos': results})
    return {'schema_version': 1, 'semanas': sorted(archived, key=lambda w: w['inicio_semana'], reverse=True)[:52]}
