import json
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import telemetria as t
import recuperar_partidas as rp

# Windows local sem tzdata: fixtures de outubro de 2026, UTC-3.
try:
    rp.ZoneInfo('America/Sao_Paulo')
except Exception:
    rp.ZoneInfo = lambda name: timezone(timedelta(hours=-3))

A='account.a'
B='account.b'
def char(a, team=1):
    return {'accountId':a, 'teamId':team}
def event(kind, sec=0, **kw):
    return {'_T':kind, '_D':f'2026-10-23T12:00:{sec:02d}Z', 'common':{'isGame':1}, **kw}
def frame(events):
    return [event('LogMatchStart',characters=[{'character':char(A)},{'character':char(B,2)}]), *events, event('LogMatchEnd',59)]
def kill(weapon='WeapKar98k_C',sec=20,reason='HeadShot',team=2):
    return event('LogPlayerKillV2',sec,killer=char(A),victim=char(B,team),
      killerDamageInfo={'damageReason':reason,'damageCauserName':weapon},
      finishDamageInfo={},attackId=sec)
class TelemetryTests(unittest.TestCase):
    def test_categories_and_kills(self):
        self.assertEqual(t.weapon_category('WeapWinchester_C'),'sniper')
        self.assertEqual(t.weapon_category('WeapFNFal_C'),'dmr')
        self.assertIsNone(t.weapon_category('WeapUnknown_C'))
        events=frame([kill(),kill('WeapMini14_C',21),kill('WeapM416_C',22),kill('WeapUnknown_C',23)])
        p=t.parse_events(events,{A,B})[A]
        self.assertEqual(p['hs'],{'sniper':1,'dmr':1,'outras':1})
        self.assertEqual(p['hs_nao_classificados'],1)
    def test_no_teamkill_bodyshot_or_duplicate(self):
        k=kill()
        p=t.parse_events(frame([k,k,kill(sec=21,team=1),kill(sec=22,reason='TorsoShot')]),{A})[A]
        self.assertEqual(p['hs']['sniper'],1)
    def test_early_loot_and_predeath_balance(self):
        pickup=event('LogItemPickup',1,character=char(B,2),item={'itemId':'Item_Heal_FirstAid_C','stackCount':2})
        pickup['common']['isGame']=0.5
        use=event('LogItemUse',2,character=char(B,2),item={'itemId':'Item_Heal_FirstAid_C','stackCount':2})
        after=event('LogItemDrop',30,character=char(B,2),item={'itemId':'Item_Heal_FirstAid_C','stackCount':1})
        p=t.parse_events(frame([pickup,use,kill(),after]),{B})[B]
        self.assertEqual(p['mortes'][0]['saldo_estimado']['cura'],1)
        self.assertFalse(p['mortes'][0]['eventos_inconsistentes'])
        self.assertEqual(p['coletados']['cura'],2)
    def test_inconsistent_and_missing_are_not_zero(self):
        use=event('LogItemUse',2,character=char(B,2),item={'itemId':'Item_Heal_FirstAid_C','stackCount':1})
        p=t.parse_events(frame([use,kill()]),{B,'absent'})
        self.assertTrue(p[B]['mortes'][0]['eventos_inconsistentes'])
        self.assertNotIn('absent',p)
        with self.assertRaises(ValueError):
            t.parse_events([kill()],{A})
    def test_damage_and_redeploy(self):
        dmg=event('LogPlayerTakeDamage',3,victim=char(B,2),damage=37.5,damageTypeCategory='Damage_BlueZone')
        fall=event('LogPlayerTakeDamage',4,victim=char(B,2),damage=12,damageTypeCategory='Damage_Instant_Fall')
        p=t.parse_events(frame([dmg,fall,kill(),event('LogPlayerRedeploy',25,character=char(B,2)),kill(sec=30)]),{B})[B]
        self.assertEqual(p['dano_azul'],37.5)
        self.assertEqual(p['dano_queda'],12)
        self.assertEqual(len(p['mortes']),2)
    def test_period_boundaries_ties_and_coverage(self):
        now=datetime(2026,10,23,16,tzinfo=timezone.utc)
        def m(mid,at,hs=1,covered=True):
            raw=t.empty_player();raw['hs']['sniper']=hs
            return {'id':mid,'at':at,'mode':'squad-fpp','status':'normal','players':{A:{},B:{}},
              **({'telemetria':{'version':t.VERSION,'players':{A:raw,B:raw}}} if covered else {})}
        cache={'partidas':{x['id']:x for x in [
          m('before','2026-10-19T02:59:59Z',9),
          m('start','2026-10-19T03:00:00Z'),
          m('monthbefore','2026-10-01T02:59:59Z',99),
          m('pending','2026-10-22T12:00:00Z',covered=False)]}}
        r=t.build_report(cache,{'Alpha':A,'Beta':B},now)
        g=r['periodos']['semana']['grupos']['todos']
        self.assertEqual(g['partidas_conhecidas'],2)
        self.assertEqual(g['partidas_analisadas'],1)
        self.assertEqual(g['medalhas']['sniper'],['Alpha','Beta'])
        self.assertEqual(g['jogadores'][0]['hs']['sniper'],1)
        self.assertEqual(r['periodos']['mes']['grupos']['todos']['jogadores'][0]['hs']['sniper'],10)
        self.assertEqual(r['periodos']['semana']['grupos']['solo']['jogadores'],[])
    def test_retry_and_cache_idempotency(self):
        now=datetime(2026,10,23,16,tzinfo=timezone.utc)
        cache={'partidas':{'m':{'id':'m','at':now.isoformat(),'mode':'squad-fpp','status':'normal','players':{A:{}}}}}
        fetch=lambda m,r: {'version':t.VERSION,'players':{A:t.empty_player()}}
        t.collect_telemetry(cache,{'Alpha':A},now,fetch=fetch)
        def fail(*a): raise AssertionError('cache should avoid fetch')
        report=t.collect_telemetry(cache,{'Alpha':A},now,fetch=fail)
        self.assertEqual(report['periodos']['semana']['grupos']['todos']['partidas_analisadas'],1)
    def test_throwable_use_not_counted_twice(self):
        pickup=event('LogItemPickup',1,character=char(A),item={'itemId':'Item_Weapon_Grenade_C','stackCount':2})
        use=event('LogItemUse',2,character=char(A),item={'itemId':'Item_Weapon_Grenade_C','stackCount':2})
        throw=event('LogPlayerUseThrowable',3,attacker=char(A),weapon={'itemId':'Item_Weapon_Grenade_C'},attackId=1)
        p=t.parse_events(frame([pickup,use,throw,throw]),{A})[A]
        self.assertEqual(p['usados']['granada'],1)
    def test_backfill_balances_month_and_week(self):
        now=datetime(2026,10,23,16,tzinfo=timezone.utc)
        def match(mid,at):
            return {'id':mid,'at':at,'mode':'squad-fpp','status':'normal','players':{A:{}}}
        records=[match('week1','2026-10-23T12:00:00Z'),
                 match('week2','2026-10-22T12:00:00Z'),
                 match('prior','2026-10-15T12:00:00Z')]
        cache={'partidas':{m['id']:m for m in records}}
        def fetch(m,roster):
            raw=t.empty_player()
            raw['hs']['sniper']=1 if m['id'].startswith('week') else 3
            return {'version':t.VERSION,'players':{A:raw}}
        report=t.collect_telemetry(cache,{'Alpha':A},now,max_matches=2,fetch=fetch)
        month=report['periodos']['mes']['grupos']['todos']
        week=report['periodos']['semana']['grupos']['todos']
        self.assertEqual(month['partidas_analisadas'],2)
        self.assertEqual(week['partidas_analisadas'],1)
        self.assertEqual(month['partidas_anteriores_semana'],1)
        self.assertEqual(month['jogadores'][0]['hs']['sniper'],4)
        self.assertEqual(week['jogadores'][0]['hs']['sniper'],1)
    def test_season_scope_and_reset(self):
        now=datetime(2026,10,23,16,tzinfo=timezone.utc)
        def match(mid,damage,season=None):
            raw=t.empty_player();raw['dano_azul']=damage
            return {'id':mid,'at':'2026-10-22T12:00:00Z','mode':'squad-fpp','status':'normal',
                'season_id':season,'players':{A:{}},'telemetria':{'version':t.VERSION,'players':{A:raw}}}
        cache={'partidas':{'current':match('current',25),'old':match('old',200,'s42'),'unknown':match('unknown',500)}}
        t.tag_season_matches(cache,'s43',['current'])
        report=t.build_report(cache,{'Alpha':A},now,season_id='s43')
        row=report['periodos']['temporada']['grupos']['todos']['jogadores'][0]
        self.assertEqual(row['dano_azul'],25)
        self.assertEqual(row['partidas'],1)
        self.assertEqual(cache['temporadas']['s43'],['current'])
        self.assertEqual(report['periodos']['semana']['grupos']['todos']['jogadores'][0]['dano_azul'],725)
        fresh=t.build_report(cache,{'Alpha':A},now,season_id='s44')
        self.assertEqual(fresh['periodos']['temporada']['grupos']['todos']['jogadores'],[])
    def test_blue_week_archive_ties(self):
        now=datetime(2026,10,23,16,tzinfo=timezone.utc)
        raw=t.empty_player();raw['dano_azul']=20
        record={'id':'m','at':'2026-10-15T12:00:00Z','mode':'squad-fpp','status':'normal','players':{A:{},B:{}},
                'telemetria':{'version':t.VERSION,'players':{A:raw,B:raw}}}
        archive={'semanas':[{'inicio_semana':'2026-10-12T00:00:00-03:00','grupos':{}}]}
        t.archive_blue_awards({'partidas':{'m':record}},archive,{'Alpha':A,'Beta':B},now)
        winners=archive['semanas'][0]['grupos']['todos']['caneta']
        self.assertEqual([p['nick'] for p in winners],['Alpha','Beta'])
        self.assertEqual(winners[0]['valor'],20)
        self.assertNotIn('tpp',archive['semanas'][0]['grupos'])
    def test_registration_json(self):
        cache=json.loads(Path('jogadores_cache.json').read_text(encoding='utf-8'))
        self.assertTrue(all(isinstance(v,str) and v.startswith('account.') for v in cache.values()))
        import atualizar_ranking as ar
        members=ar.load_members()
        self.assertIn('Alien--__--',members)
        self.assertIn('TODDNH0',members)
if __name__=='__main__': unittest.main()
