"""Telemetria pós-partida: abates na cabeça, recursos estimados e dano ambiental.
Não salva eventos brutos de terceiros. Ausência de telemetria nunca vira zero.
"""
import gzip
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from recuperar_partidas import download_match, moment, week_start, GROUPS

VERSION = 2
SNIPERS = {'AWM', 'M24', 'Kar98k', 'Win94', 'Winchester', 'MosinNagant', 'L6', 'LynxAMR'}
DMRS = {'SKS', 'Mini14', 'Mk14', 'FNFal', 'QBU88', 'VSS', 'Mk12', 'Dragunov'}
CATEGORIES = ('sniper', 'dmr', 'outras')
ITEMS = {
    'Item_Boost_EnergyDrink_C': 'boost', 'Item_Boost_PainKiller_C': 'boost',
    'Item_Boost_AdrenalineSyringe_C': 'boost',
    'Item_Heal_FirstAid_C': 'cura', 'Item_Heal_MedKit_C': 'cura',
    'Item_Heal_Bandage_C': 'cura', 'Item_Weapon_SmokeBomb_C': 'fumaca',
    'Item_Weapon_Grenade_C': 'granada',
    'Item_Weapon_FlashBang_C': 'granada', 'Item_Weapon_Molotov_C': 'granada',
    'Item_Weapon_BluezoneGrenade_C': 'granada',
}

def weapon_category(name):
    if not isinstance(name, str) or not name.startswith('Weap') or not name.endswith('_C'):
        return None
    weapon = name[4:-2]
    if weapon in SNIPERS:
        return 'sniper'
    if weapon in DMRS:
        return 'dmr'
    # Unknown identifiers are explicitly separate rather than mislabeled as AR/SMG.
    others = {'AK47','M16A4','SCAR-L','M416','HK416','AUG','Groza','BerylM762',
              'Mk47Mutant','G36C','QBZ95','ACE32','FAMAS','P90','MP5K','UMP',
              'UMP9','Vector','UZI','Thompson','BizonPP19','JS9','MP9','MP7',
              'DP28','M249','MG3','Saiga12','S1897','DBS','OriginS12',
              'S686','M1911','M9','NagantM1895','DesertEagle','G18','vz61Skorpion',
              'Sawnoff','Crossbow','Pan','Machete','Cowbar','Sickle','Mortar','PanzerFaust100M'}
    return 'outras' if weapon in others else None

def empty_player():
    return {'hs': dict.fromkeys(CATEGORIES, 0), 'hs_nao_classificados': 0,
            'dano_azul': 0, 'dano_queda': 0, 'mortes_azul': 0,
            'coletados': dict.fromkeys(('boost','cura','fumaca','granada','municao'), 0),
            'usados': dict.fromkeys(('boost','cura','fumaca','granada'), 0),
            'mortes': [], 'vida_baixa_sem_cura_estimada': 0}

def parse_events(events, allowed):
    if not isinstance(events, list) or not any(e.get('_T') == 'LogMatchEnd' for e in events):
        raise ValueError('Telemetria incompleta: sem encerramento.')
    rows = {aid: empty_player() for aid in allowed}
    bags = {aid: {} for aid in allowed}
    seen_players = set()
    warnings = set()
    seen_kills = set()
    dead = set()
    started = set()
    thrown = set()
    def account(character):
        return (character or {}).get('accountId')
    for e in sorted(events, key=lambda x: x.get('_D', '')):
        kind = e.get('_T')
        if kind != 'LogMatchStart' and (e.get('common') or {}).get('isGame', 1) < 0.5:
            continue
        aid = account(e.get('character'))
        if kind == 'LogMatchStart':
            for wrapper in e.get('characters', []):
                who = account(wrapper.get('character', wrapper))
                if who in rows:
                    started.add(who)
                    seen_players.add(who)
        if kind == 'LogPlayerRedeploy' and aid in rows:
            bags[aid] = {}
            dead.discard(aid)
        if kind == 'LogPlayerUseThrowable':
            who = account(e.get('attacker'))
            item_id = (e.get('weapon') or {}).get('itemId', '')
            cat = ITEMS.get(item_id)
            key = (who, e.get('attackId'))
            if who in rows and cat in ('fumaca', 'granada') and key not in thrown:
                thrown.add(key)
                rows[who]['usados'][cat] += 1
                # Throwable consumption can also have LogItemUse: balance is uncertain.
                warnings.add(who)
        if aid in dead and kind.startswith('LogItem'):
            continue
        if aid in rows:
            seen_players.add(aid)
        if kind == 'LogPlayerTakeDamage':
            vid = account(e.get('victim'))
            if vid in rows:
                seen_players.add(vid)
                damage = e.get('damage')
                damage = max(0, damage) if isinstance(damage, (int,float)) else 0
                if e.get('damageTypeCategory') == 'Damage_BlueZone':
                    rows[vid]['dano_azul'] += damage
                elif e.get('damageTypeCategory') == 'Damage_Fall':
                    rows[vid]['dano_queda'] += damage
        if aid in rows and kind in ('LogItemPickup','LogItemPickupFromLootbox',
                'LogItemPickupFromCarepackage','LogItemPickupFromCustomPackage',
                'LogItemPickupFromVehicleTrunk','LogItemDrop','LogItemUse','LogItemPutToVehicleTrunk'):
            item = e.get('item') or {}
            item_id = item.get('itemId', '')
            category = ITEMS.get(item_id)
            ammo = item_id.startswith('Item_Ammo_')
            if category or ammo:
                count = item.get('stackCount')
                count = count if isinstance(count,int) and count > 0 else 1
                bag = bags[aid]
                pickup = kind.startswith('LogItemPickup')
                if pickup:
                    bag[item_id] = bag.get(item_id, 0) + count
                    rows[aid]['coletados'][category or 'municao'] += count
                else:
                    # A use consumes one item; stackCount is not necessarily consumed quantity.
                    count = 1 if kind == 'LogItemUse' else count
                    if bag.get(item_id, 0) < count:
                        warnings.add(aid)
                    bag[item_id] = max(0, bag.get(item_id, 0) - count)
                    if kind == 'LogItemUse' and category:
                        rows[aid]['usados'][category] += count
        if kind == 'LogPlayerPosition' and aid in rows:
            health = (e.get('character') or {}).get('health')
            if isinstance(health,(int,float)) and 0 < health <= 50:
                if sum(n for item,n in bags[aid].items() if ITEMS.get(item) == 'cura') == 0:
                    rows[aid]['vida_baixa_sem_cura_estimada'] += 1
        if kind in ('LogPlayerKillV2','LogPlayerKill'):
            victim = e.get('victim') or {}
            killer = e.get('killer') or {}
            vid, kid = account(victim), account(killer)
            # Different deaths after redeploy count separately; duplicate logs do not.
            identity = (vid, e.get('_D'), e.get('attackId'))
            if identity in seen_kills:
                continue
            seen_kills.add(identity)
            info = (e.get('killerDamageInfo') or {}) if kind == 'LogPlayerKillV2' else e
            if kid in rows and vid and kid != vid:
                seen_players.add(kid)
                team_kill = (killer.get('teamId') is not None and killer.get('teamId') == victim.get('teamId'))
                if not team_kill and kid not in e.get('teamKillers_AccountId', []) and not e.get('isSuicide') and info.get('damageReason') == 'HeadShot':
                    cat = weapon_category(info.get('damageCauserName'))
                    if cat:
                        rows[kid]['hs'][cat] += 1
                    else:
                        rows[kid]['hs_nao_classificados'] += 1
            if vid in rows:
                seen_players.add(vid)
                finish = (e.get('finishDamageInfo') or {}) if kind == 'LogPlayerKillV2' else e
                if finish.get('damageTypeCategory') == 'Damage_BlueZone':
                    rows[vid]['mortes_azul'] += 1
                balance = {cat: sum(n for item,n in bags[vid].items() if ITEMS.get(item) == cat)
                           for cat in ('boost','cura','fumaca','granada')}
                rows[vid]['mortes'].append({'at':e.get('_D'), 'saldo_estimado':balance,
                                           'eventos_inconsistentes': vid in warnings or vid not in started})
                dead.add(vid)
                bags[vid] = {}
    # Unobserved members must be retried, never counted as all-zero observations.
    return {aid: {**r, 'eventos_inconsistentes': aid in warnings or aid not in started} for aid,r in rows.items() if aid in seen_players}

def download_events(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'telemetry-cdn.pubg.com':
        raise ValueError('URL de telemetria fora do CDN oficial.')
    req = Request(url, headers={'Accept-Encoding':'gzip','Accept':'application/json'})
    with urlopen(req, timeout=20) as response:
        data = response.read(40_000_001)
        if len(data) > 40_000_000:
            raise ValueError('Telemetria excede limite.')
        if data[:2] == b'\x1f\x8b':
            data = gzip.decompress(data)
        return json.loads(data)

def enrich_match(record, roster):
    payload = download_match(record['id'])
    if not payload:
        raise ValueError('Partida indisponível.')
    url = next((i.get('attributes',{}).get('URL') for i in payload.get('included',[])
                if i.get('type') == 'asset' and i.get('attributes',{}).get('name') == 'telemetry'), None)
    if not url:
        raise ValueError('Sem asset de telemetria.')
    allowed = set(record['players']) & set(roster)
    result = parse_events(download_events(url), allowed)
    if not allowed.issubset(result):
        raise ValueError('Telemetria sem todos os participantes esperados.')
    return {'version': VERSION, 'players':result}

def collect_telemetry(cache, resolved, now, max_matches=100, budget_seconds=160, fetch=None):
    roster = {aid:nick for nick,aid in resolved.items()}
    fetch = fetch or enrich_match
    candidates = [m for m in cache.get('partidas',{}).values()
                  if m.get('status') == 'normal'
                  and moment(m['at']) >= now - timedelta(days=14)
                  and (m.get('telemetria',{}).get('version') != VERSION
                       or not (set(m['players']) & set(roster)).issubset(m.get('telemetria',{}).get('players',{})))]
    candidates.sort(key=lambda m:m['at'], reverse=True)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i in range(0,min(max_matches,len(candidates)),4):
            if time.monotonic()-started >= budget_seconds:
                break
            futures = {pool.submit(fetch,m,roster):m for m in candidates[i:i+4]}
            for future in as_completed(futures):
                try:
                    futures[future]['telemetria'] = future.result()
                except Exception:
                    pass  # Not success: remains pending and is excluded from rankings.
    return build_report(cache, resolved, now)

def build_report(cache, resolved, now):
    roster = {aid:nick for nick,aid in resolved.items()}
    local = now.astimezone(week_start(now).tzinfo)
    current_week = week_start(now)
    month = local.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    periods = [('semana', current_week), ('mes', month)]
    result = {'schema_version':2,'updated_at':now.isoformat(),'periodos':{},
              'aviso':'Somente partidas oficiais com telemetria recuperada. Cobertura parcial; sem dados não significa zero. Semana de segunda a domingo e mês civil no horário de Brasília. Headshots são abates creditados na cabeça, não todos os tiros na cabeça. Saldos de itens são estimativas, sem certeza de mochila vazia. Munição: coleta observada, sem saldo confiável.'}
    for label,start in periods:
        groups = {}
        for group,modes in GROUPS.items():
            totals = {}
            known,covered = 0,0
            for m in cache.get('partidas',{}).values():
                if m.get('status') != 'normal' or m.get('mode') not in modes or not start <= moment(m['at']) <= now:
                    continue
                members = set(m['players']) & set(roster)
                if not members:
                    continue
                known += 1
                tele = m.get('telemetria', {})
                if tele.get('version') != VERSION:
                    continue
                data = tele.get('players', {})
                if members.issubset(data):
                    covered += 1
                for aid in members & set(data):
                    p = totals.setdefault(aid, {'nick':roster[aid], 'account_id':aid,'partidas':0,
                        'hs':dict.fromkeys(CATEGORIES,0), 'recorde_hs':0, 'recorde_partida':None,
                        'hs_nao_classificados':0,'dano_azul':0,'dano_queda':0,'mortes_azul':0,
                        'coletados':dict.fromkeys(('boost','cura','fumaca','granada','municao'),0),
                        'usados':dict.fromkeys(('boost','cura','fumaca','granada'),0),
                        'mortes':0,'mortes_validas':0,'mortes_saldo_zero':dict.fromkeys(('boost','cura','fumaca','granada'),0),
                        'eventos_inconsistentes':0, 'vida_baixa_sem_cura_estimada':0})
                    raw = data[aid]
                    p['partidas'] += 1
                    for cat in CATEGORIES:
                        p['hs'][cat] += raw['hs'][cat]
                    hs = sum(raw['hs'].values())
                    if hs > p['recorde_hs']:
                        p['recorde_hs'],p['recorde_partida'] = hs,m['id']
                    for key in ('hs_nao_classificados','dano_azul','dano_queda','mortes_azul','vida_baixa_sem_cura_estimada'):
                        p[key] += raw[key]
                    for key in ('coletados','usados'):
                        for cat,v in raw[key].items():
                            p[key][cat] += v
                    p['eventos_inconsistentes'] += int(raw.get('eventos_inconsistentes',False))
                    for death in raw['mortes']:
                        p['mortes'] += 1
                        if not death['eventos_inconsistentes']:
                            p['mortes_validas'] += 1
                            for cat,v in death['saldo_estimado'].items():
                                p['mortes_saldo_zero'][cat] += int(v == 0)
            rows = sorted(totals.values(),key=lambda p:p['nick'].casefold())
            medals = {}
            for cat in CATEGORIES:
                best = max((p['hs'][cat] for p in rows),default=0)
                medals[cat] = [p['nick'] for p in rows if best > 0 and p['hs'][cat] == best]
            groups[group] = {'partidas_conhecidas':known,'partidas_analisadas':covered,
                             'jogadores':rows,'medalhas':medals}
        result['periodos'][label] = {'inicio':start.isoformat(),'ate':now.isoformat(),'grupos':groups}
    return result
