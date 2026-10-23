"""Coleta normal (Steam), sem dependências externas. Nunca grava a chave da API."""
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from trofeus import AWARDS, archive_weeks
from telemetria import collect_telemetry, build_report
from recuperar_partidas import collect_recent, archive_matches

BASE = Path(__file__).resolve().parent
MODES = ['squad-fpp', 'duo-fpp', 'squad', 'duo', 'solo-fpp', 'solo']
GROUPS = {'todos': MODES, 'fpp': MODES[:2], 'tpp': MODES[2:4], **{m: [m] for m in MODES}}
MEMBROS_CLA = ['gerskol', 'Burallosh', 'VoVoGOW', 'lauSL', 'ROGER__BR', 'crazyrock_com_br', 'Bicaleto', 'BoLHa___', 'CalanguinhoFPS', 'GEMINIAKI', 'JBMKTB', 'julianfps', 'LAUANNA7788', 'LuleLixxooXandTB', 'M43str0_FPS', 'manolobr07', 'PIGzinn_30fps', 'Pisanoslixo', 'PopMeeN', 'Padre0027', 'Rasdroc', 'Rickzzs', 'robo__GUERREIRO', 'ShigS-08', 'robo-_G', 'tematoo', 'zPaT0__', 'Zeus_god45']
MIN_PARTIDAS = 15
FIELDS = ['roundsPlayed', 'kills', 'losses', 'wins', 'top10s', 'damageDealt', 'dBNOs', 'headshotKills', 'longestKill', 'revives', 'assists', 'heals', 'boosts', 'timeSurvived', 'rideDistance', 'walkDistance', 'roadKills', 'teamKills', 'suicides']

def load_members():
    path = BASE / 'membros_cla.txt'
    if not path.exists():
        return MEMBROS_CLA  # Compatibilidade durante a instalação.
    members = []
    seen = set()
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        nick = line.strip()
        if not nick or nick.startswith('#'):
            continue
        if any(char.isspace() for char in nick) or len(nick) > 40:
            raise ValueError('Nick inválido em membros_cla.txt: use um nick por linha, sem espaços.')
        if nick.casefold() not in seen:
            members.append(nick)
            seen.add(nick.casefold())
    if not members:
        raise ValueError('A lista membros_cla.txt está vazia. Os dados anteriores foram preservados.')
    return members

def load_json(name, default):
    path = BASE / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))

def atomic_json(name, value):
    path = BASE / name
    temp = path.with_suffix(path.suffix + '.tmp')
    options = {'separators': (',', ':')} if name in ('historico_cla.json', 'partidas_cache.json') else {'indent': 2}
    temp.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, **options) + '\n', encoding='utf-8')
    temp.replace(path)

class PUBGClient:
    def __init__(self, key):
        if not key:
            raise RuntimeError('PUBG_API_KEY ausente. Configure o Secret do repositório.')
        self.key = key
        self.last_request = 0.0

    def get(self, path, params=None, missing_ok=False):
        url = 'https://api.pubg.com/shards/steam/' + path
        if params:
            url += '?' + urlencode(params)
        for attempt in range(4):
            time.sleep(max(0, 6.3 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            req = Request(url, headers={'Authorization': 'Bearer ' + self.key, 'Accept': 'application/vnd.api+json'})
            try:
                with urlopen(req, timeout=30) as response:
                    return json.load(response)
            except HTTPError as err:
                if err.code == 404 and missing_ok:
                    return None
                if err.code in (401, 403):
                    raise RuntimeError('A API recusou a credencial. Verifique o Secret PUBG_API_KEY.') from None
                if err.code not in (429, 500, 502, 503, 504):
                    raise RuntimeError('Falha da API: HTTP ' + str(err.code)) from None
                if attempt == 3:
                    raise RuntimeError('A API continuou indisponível após 4 tentativas.') from None
                if err.code == 429:
                    reset = err.headers.get('X-RateLimit-Reset', '')
                    delay = max(30, float(reset) - time.time() + 1) if reset.replace('.', '', 1).isdigit() else 60
                    time.sleep(min(delay, 90))
                else:
                    time.sleep(2 ** (attempt + 1))
            except (URLError, TimeoutError):
                if attempt == 3:
                    raise RuntimeError('Não foi possível conectar à API após 4 tentativas.') from None
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError('Coleta não concluída.')

def aggregate(stats, modes):
    result = {field: 0 for field in FIELDS}
    for mode in modes:
        item = stats.get(mode)
        if not isinstance(item, dict):
            raise ValueError('Resposta sem estatísticas do modo ' + mode)
        for field in FIELDS:
            value = item.get(field, 0)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Valor inválido na métrica ' + field)
            result[field] = max(result[field], value) if field == 'longestKill' else result[field] + value
    # Ausência da métrica não deve ser confundida com zero real.
    values = [stats[m].get('weaponsAcquired') for m in modes]
    result['weaponsAcquired'] = sum(values) if all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in values) else None
    return result

def metrics(nick, account_id, stats, modes):
    s = aggregate(stats, modes)
    rounds = s['roundsPlayed']
    def rate(value, factor=1):
        return value / rounds * factor if rounds else 0
    adr = rate(s['damageDealt'])
    winrate = rate(s['wins'], 100)
    top10rate = rate(s['top10s'], 100)
    kills_per_game = rate(s['kills'])
    revives_per_game = rate(s['revives'])
    return {
        'nick': nick, 'account_id': account_id, 'partidas': rounds,
        'elegivel_mvp': rounds >= MIN_PARTIDAS,
        'wins': s['wins'], 'win_rate': round(winrate, 1), 'top10s': s['top10s'],
        'top10_rate': round(top10rate, 1), 'kills': s['kills'],
        'kills_por_partida': round(kills_per_game, 2),
        'adr': round(adr, 1), 'damage_total': round(s['damageDealt'], 2),
        'dbnos': s['dBNOs'], 'headshots': s['headshotKills'],
        'hs_rate': round(s['headshotKills'] / s['kills'] * 100, 1) if s['kills'] else 0,
        'longest_kill': round(s['longestKill'], 1), 'revives': s['revives'],
        'assists': s['assists'], 'heals': s['heals'] + s['boosts'],
        'tempo_medio_min': round(rate(s['timeSurvived']) / 60, 1),
        'km_rodados': round(s['rideDistance'] / 1000, 1),
        'km_pe': round(rate(s['walkDistance']) / 1000, 2),
        'road_kills': s['roadKills'], 'team_kills': s['teamKills'], 'suicides': s['suicides'],
        'armas_loot': round(rate(s['weaponsAcquired']), 1) if s['weaponsAcquired'] is not None else None,
        'resenha': {key: s[key] for key in ('roundsPlayed', 'rideDistance', 'teamKills', 'suicides', 'revives', 'timeSurvived', 'heals', 'boosts', 'walkDistance', 'weaponsAcquired', 'longestKill')},
        'scores': {
            'mvp': round(adr * 1.5 + kills_per_game * 50 + winrate * 5 + top10rate * 1.5 + revives_per_game * 100, 1),
            'participacao': s['kills'] + s['wins'] * 20 + s['revives'] * 2 + s['assists'],
        }
    }

def build_snapshot(payload):
    return {'at': payload['updated_at'], 'season_id': payload['season_id'], 'score_version': 2, 'resenha_version': 1,
            'grupos': {group: [{key: player[key] for key in ('nick', 'account_id', 'partidas', 'kills', 'wins', 'damage_total', 'adr', 'revives', 'assists', 'scores', 'resenha')} for player in players]
                       for group, players in payload['grupos'].items()}}

def update_history(history, snapshot, now):
    snapshots = [s for s in history.get('snapshots', []) if s.get('season_id') == snapshot['season_id'] and s.get('score_version') == 2]
    # Evita duplicar a mesma hora; conserva primeira e última coleta de cada dia.
    # Isso mantém a referência da semana e limita o tamanho do arquivo público.
    snapshots = [s for s in snapshots if s['at'][:13] != snapshot['at'][:13] and datetime.fromisoformat(s['at']) >= now - timedelta(days=90)]
    snapshots.append(snapshot)
    snapshots.sort(key=lambda s: s['at'])
    days = {}
    for item in snapshots:
        day = datetime.fromisoformat(item['at']).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
        days.setdefault(day, []).append(item)
    retained = []
    for items in days.values():
        retained.append(items[0])
        if items[-1]['at'] != items[0]['at']:
            retained.append(items[-1])
    return {'schema_version': 2, 'snapshots': retained}

def main():
    members = load_members()
    client = PUBGClient(os.environ.get('PUBG_API_KEY'))
    seasons = client.get('seasons')['data']
    season = next((s['id'] for s in seasons if s['attributes'].get('isCurrentSeason')), None)
    if not season:
        raise RuntimeError('Não foi possível identificar a temporada atual.')
    # IDs previamente resolvidos evitam gastar consultas repetidas por nick.
    cache = load_json('jogadores_cache.json', {})
    resolved = {}
    missing = []
    for start in range(0, len(members), 10):
        batch = [nick for nick in members[start:start + 10] if nick not in cache]
        if batch:
            response = client.get('players', {'filter[playerNames]': ','.join(batch)}, missing_ok=True)
            for player in (response or {}).get('data', []):
                cache[player['attributes']['name']] = player['id']
    for nick in members:
        if nick not in cache:
            missing.append(nick)
        else:
            resolved[nick] = cache[nick]
    if not resolved:
        raise RuntimeError('Nenhum membro foi localizado; dados anteriores preservados.')
    groups = {group: [] for group in GROUPS}
    for nick, account_id in resolved.items():
        response = client.get(f'players/{account_id}/seasons/{season}')
        stats = response['data']['attributes']['gameModeStats']
        for group, modes in GROUPS.items():
            groups[group].append(metrics(nick, account_id, stats, modes))
        print('Coleta concluída: ' + nick)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    payload = {
        'schema_version': 2, 'score_version': 2, 'updated_at': now.isoformat(),
        'ultima_atualizacao': now.astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M'),
        'season_id': season, 'temporada': 'SEASON ' + season.split('-')[-1],
        'modo': 'SQUAD-FPP + DUO-FPP', 'min_partidas': MIN_PARTIDAS,
        'fonte': 'PUBG API • Steam • partidas normais',
        'membros_previstos': len(members), 'nao_encontrados': missing,
        'grupos': groups, 'jogadores': groups['fpp']
    }
    history = update_history(load_json('historico_cla.json', {}), build_snapshot(payload), now)
    trophies = archive_weeks(history, load_json('trofeus_cla.json', {}), now)
    old_matches = load_json('partidas_cache.json', {})
    try:
        match_cache, weekly = collect_recent(client, resolved, old_matches, now)
        trophies = archive_matches(match_cache, trophies, resolved, now, AWARDS)
        print(f"Partidas recentes: {weekly['partidas_semana']} na semana; {weekly['pendentes']} pendentes; cobertura pode ser parcial.")
    except Exception:
        # Estatísticas da temporada não devem desaparecer por uma falha no backfill.
        match_cache = old_matches
        weekly = load_json('resenha_semanal.json', {'schema_version': 1, 'fonte': 'partidas', 'grupos': {}})
        weekly['aviso'] = 'Falha temporária na recuperação de partidas. Exibindo os últimos dados disponíveis.'
        weekly['falha_recuperacao'] = True
        print('Aviso: recuperação de partidas incompleta; temporada preservada.')
    try:
        telemetry = collect_telemetry(match_cache, resolved, now)
    except Exception:
        telemetry = build_report(match_cache, resolved, now)
        telemetry['aviso'] += ' Coleta de telemetria com falha temporária.'
    # Valida tudo antes de substituir os arquivos. Qualquer falha de coleta aborta a execução.
    json.dumps([payload, history, cache, trophies, match_cache, weekly, telemetry], allow_nan=False)
    atomic_json('historico_cla.json', history)
    atomic_json('jogadores_cache.json', cache)
    atomic_json('trofeus_cla.json', trophies)
    atomic_json('partidas_cache.json', match_cache)
    atomic_json('resenha_semanal.json', weekly)
    atomic_json('telemetria_cla.json', telemetry)
    atomic_json('ranking_cla.json', payload)
    print(f'Atualizados {len(resolved)} membros; {len(missing)} não localizados.')
    if missing:
        print('Revise os nicks: ' + ', '.join(missing))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('ERRO: ' + str(error), file=sys.stderr)
        sys.exit(1)
