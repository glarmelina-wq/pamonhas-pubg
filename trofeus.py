"""Apuração de troféus de períodos encerrados a partir das coletas reais."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

AWARDS = {
    'kombi': ('rideDistance', 0, False, False),
    'amigo': ('teamKills', 0, False, False),
    'inimigo': ('suicides', 0, False, False),
    'samu': ('revives', 0, False, False),
    'lobby': ('timeSurvived', 5, True, True),
    'farmacia': ('heals_boosts', 5, True, False),
    'forrest': ('walkDistance', 5, True, False),
    'lutinho': ('weaponsAcquired', 5, True, False),
}

def raw_value(raw, key):
    if key == 'heals_boosts':
        return raw.get('heals', 0) + raw.get('boosts', 0)
    return raw.get(key)

def archive_weeks(history, existing, now):
    local = ZoneInfo('America/Sao_Paulo')
    groups = {}
    for item in history.get('snapshots', []):
        if item.get('resenha_version') != 1:
            continue
        at = datetime.fromisoformat(item['at']).astimezone(local)
        start = (at - timedelta(days=at.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        if start + timedelta(days=7) > now:
            continue
        key = (item['season_id'], start.isoformat())
        groups.setdefault(key, []).append(item)
    archive = {week['id']: week for week in existing.get('semanas', [])}
    for (season, start), snapshots in groups.items():
        snapshots.sort(key=lambda s: s['at'])
        if len(snapshots) < 2:
            continue
        first, last = snapshots[0], snapshots[-1]
        results = {}
        for mode, players in last['grupos'].items():
            baseline = {p.get('account_id', p['nick']): p for p in first['grupos'].get(mode, [])}
            rows = []
            for p in players:
                previous = baseline.get(p.get('account_id', p['nick']))
                if not previous or not p.get('resenha') or not previous.get('resenha'):
                    continue
                raw, old = p['resenha'], previous['resenha']
                count = raw['roundsPlayed'] - old['roundsPlayed']
                if count <= 0:
                    continue
                delta = {k: (v - old[k] if isinstance(v, (int, float)) and isinstance(old.get(k), (int, float)) else None)
                         for k, v in raw.items() if k != 'longestKill'}
                if any(v is not None and v < 0 for v in delta.values()):
                    continue
                rows.append({'nick': p['nick'], 'partidas': count, 'raw': delta})
            awards = {}
            for award, (field, minimum, per_game, ascending) in AWARDS.items():
                candidates = []
                for row in rows:
                    value = raw_value(row['raw'], field)
                    if value is None or value <= 0 or row['partidas'] < minimum:
                        continue
                    value = value / row['partidas'] if per_game else value
                    candidates.append({'nick': row['nick'], 'valor': value, 'partidas': row['partidas']})
                if candidates:
                    best = min(p['valor'] for p in candidates) if ascending else max(p['valor'] for p in candidates)
                    awards[award] = [p for p in candidates if abs(p['valor'] - best) < 1e-9]
            results[mode] = awards
        week_id = season + ':' + start[:10]
        archive[week_id] = {'id': week_id, 'season_id': season, 'inicio_semana': start,
                            'de': first['at'], 'ate': last['at'], 'parcial': True, 'grupos': results}
    return {'schema_version': 1, 'semanas': sorted(archive.values(), key=lambda w: w['inicio_semana'], reverse=True)[:52]}
