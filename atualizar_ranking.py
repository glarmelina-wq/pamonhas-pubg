import os
import requests
import json
import time
from datetime import datetime

# Garante que o arquivo JSON será salvo na MESMA pasta deste script
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_JSON = os.path.join(PASTA_ATUAL, "ranking_cla.json")

# ==========================================
# CONFIGURAÇÕES DO CLÃ PAMONHAS & API
# ==========================================
# Agora ele puxa a chave de forma secreta e segura!
API_KEY = os.environ.get("PUBG_API_KEY")
PLATFORM = "steam"

MODOS_FPP = ["squad-fpp", "duo-fpp"]
MIN_PARTIDAS_MVP = 15

# ⚠️ IMPORTANTE: Troque abaixo pelos nicks REAIS do PUBG (exatamente como no jogo, com maiúsculas e minúsculas!)
MEMBROS_CLA = [
"gerskol",
    	"Burallosh",
	"VoVoGOW",
    	"lauSL",
	"ROGER__BR",
    	"crazyrock_com_br",
	"Bicaleto",
    	"BoLHa___",
	"CalanguinhoFPS",
    	"GEMINIAKI",
	"JBMKTB",
    	"julianfps",
	"LAUANNA7788",
    	"LuleLixxooXandTB",
	"M43str0_FPS",
    	"manolobr07",
	"PIGzinn_30fps",
    	"Pisanoslixo",
	"PopMeeN",
    	"Padre0027",
	"Rasdroc",
	"Rickzzs",
    	"robo__GUERREIRO",
	"ShigS-08",
	"robo-_G",
    	"tematoo",
	"zPaT0__",
    "Zeus_god45"
]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

DELAY_RPM = 6.2

def dividir_em_lotes(lista, tamanho=10):
    for i in range(0, len(lista), tamanho):
        yield lista[i:i + tamanho]

def requisicao_segura(url):
    while True:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 429:
            print("⏳ Limite de 10 RPM atingido! Aguardando 30 segundos...")
            time.sleep(30)
            continue
        return res

def buscar_ids_jogadores(nicks):
    mapa_jogadores = {}
    for lote in dividir_em_lotes(nicks, 10):
        nomes_str = ",".join(lote)
        url = f"https://api.pubg.com/shards/{PLATFORM}/players?filter[playerNames]={nomes_str}"
        res = requisicao_segura(url)
        
        if res.status_code == 200:
            for player in res.json().get("data", []):
                nome = player["attributes"]["name"]
                mapa_jogadores[nome] = player["id"]
                print(f" ✔️ Jogador localizado: {nome}")
        elif res.status_code == 404:
            print(f" ❌ Nenhum jogador encontrado neste lote: {lote}")
            print("    (Dica: Verifique letras MAIÚSCULAS e minúsculas exatas do nick no PUBG)")
        else:
            print(f" ⚠️ Aviso ao buscar lote {lote}: Status {res.status_code} - {res.text}")
        
        time.sleep(DELAY_RPM)
    return mapa_jogadores

def buscar_temporada_atual():
    url = f"https://api.pubg.com/shards/{PLATFORM}/seasons"
    res = requisicao_segura(url)
    time.sleep(DELAY_RPM)
    
    if res.status_code == 200:
        for season in res.json().get("data", []):
            if season["attributes"].get("isCurrentSeason"):
                return season["id"]
    return None

def somar_modos(game_mode_stats, modos):
    acumulado = {
        "roundsPlayed": 0, "kills": 0, "losses": 0, "wins": 0, "top10s": 0,
        "damageDealt": 0.0, "dBNOs": 0, "headshotKills": 0, "longestKill": 0.0,
        "revives": 0, "assists": 0, "heals": 0, "boosts": 0, "timeSurvived": 0.0,
        "rideDistance": 0.0, "walkDistance": 0.0, "roadKills": 0, "teamKills": 0, "suicides": 0
    }
    for modo in modos:
        s = game_mode_stats.get(modo, {})
        for chave in acumulado:
            if chave == "longestKill":
                acumulado[chave] = max(acumulado[chave], s.get(chave, 0.0))
            else:
                acumulado[chave] += s.get(chave, 0)
    return acumulado

def calcular_estatisticas():
    print("==========================================")
    print(" 🌽 PAMONHAS STATS TRACKER - INICIANDO")
    print("==========================================")
    print(f"📂 Pasta de destino: {PASTA_ATUAL}")
    
    print("\n1. Consultando temporada ativa na Krafton...")
    season_id = buscar_temporada_atual()
    if not season_id:
        print("❌ Erro: Não foi possível obter a temporada atual. Verifique sua conexão ou API Key.")
        return
    print(f" -> Temporada ativa: {season_id}")

    print("\n2. Buscando IDs dos membros na Steam...")
    jogadores = buscar_ids_jogadores(MEMBROS_CLA)
    if not jogadores:
        print("❌ Nenhum jogador válido encontrado. Edite a lista MEMBROS_CLA com nicks reais.")
        return

    lista_final = []
    total_membros = len(jogadores)

    print(f"\n3. Extraindo estatísticas de {total_membros} membros...")
    for idx, (nick, acc_id) in enumerate(jogadores.items(), 1):
        url = f"https://api.pubg.com/shards/{PLATFORM}/players/{acc_id}/seasons/{season_id}"
        res = requisicao_segura(url)

        if res.status_code != 200:
            print(f" [{idx}/{total_membros}] ❌ Erro ao puxar {nick}: Status {res.status_code}")
            time.sleep(DELAY_RPM)
            continue

        todos_modos = res.json()["data"]["attributes"]["gameModeStats"]
        s = somar_modos(todos_modos, MODOS_FPP)
        partidas = s["roundsPlayed"]

        if partidas == 0:
            print(f" [{idx}/{total_membros}] ⚪ {nick}: 0 partidas FPP na temporada atual.")
            # Mesmo com 0 partidas, se quiser que ele apareça zerado na tabela, podemos incluir ou pular
            time.sleep(DELAY_RPM)
            continue

        kills = s["kills"]
        losses = max(1, s["losses"])
        wins = s["wins"]
        top10s = s["top10s"]
        damage = s["damageDealt"]
        dbnos = s["dBNOs"]
        headshots = s["headshotKills"]
        longest_kill = s["longestKill"]
        revives = s["revives"]
        assists = s["assists"]
        heals = s["heals"]
        boosts = s["boosts"]
        time_survived = s["timeSurvived"]
        ride_dist = s["rideDistance"]
        walk_dist = s["walkDistance"]
        road_kills = s["roadKills"]
        team_kills = s["teamKills"]
        suicides = s["suicides"]
		weapons_acquired = s.get("weaponsAcquired", 0) # <--- NOVA LINHA

        adr = round(damage / partidas, 1)
        kd = round(kills / losses, 2)
        win_rate = round((wins / partidas) * 100, 1)
        top10_rate = round((top10s / partidas) * 100, 1)
        hs_rate = round((headshots / max(1, kills)) * 100, 1)
        tempo_medio_min = round((time_survived / partidas) / 60, 1)
        km_rodados = round(ride_dist / 1000, 1)
        km_a_pe_por_partida = round((walk_dist / 1000) / partidas, 2)
		armas_por_partida = round(weapons_acquired / partidas, 1) # <--- NOVA LINHA
		
        score_mvp = round((adr * 1.5) + (kd * 50) + (wins * 15) + (top10s * 3) + (revives * 2), 1)
        score_fragger = round(adr + (kills * 3) + (dbnos * 1.5), 1)
        score_sniper = round((headshots * 4) + (hs_rate * 2) + (longest_kill * 0.2), 1)
        score_suporte = round((revives * 10) + (assists * 5) + (heals * 0.2), 1)
        score_sobrevivente = round((tempo_medio_min * 5) + (top10_rate * 1.5) + (wins * 10), 1)
        score_vitorioso = round((wins * 20) + (win_rate * 5), 1)

        score_uber = round(km_rodados + (road_kills * 50), 1)
        score_inimigo = team_kills + suicides

        lista_final.append({
            "nick": nick,
            "partidas": partidas,
            "elegivel_mvp": partidas >= MIN_PARTIDAS_MVP,
            "wins": wins,
            "win_rate": win_rate,
            "top10_rate": top10_rate,
            "kills": kills,
            "kd": kd,
            "adr": adr,
            "dbnos": dbnos,
            "headshots": headshots,
            "hs_rate": hs_rate,
            "longest_kill": round(longest_kill, 1),
            "revives": revives,
            "assists": assists,
            "heals": heals + boosts,
            "tempo_medio_min": tempo_medio_min,
            "km_rodados": km_rodados,
            "road_kills": road_kills,
            "team_kills": team_kills,
            "suicides": suicides,
            "km_pe": km_a_pe_por_partida,
			"armas_loot": armas_por_partida, # <--- NOVA LINHA
            "scores": {
                "mvp": score_mvp,
                "fragger": score_fragger,
                "sniper": score_sniper,
                "suporte": score_suporte,
                "sobrevivente": score_sobrevivente,
                "vitorioso": score_vitorioso,
                "uber": score_uber,
                "inimigo": score_inimigo
            }
        })

        print(f" [{idx}/{total_membros}] 🔥 {nick}: {partidas} jogos | ADR: {adr} | K/D: {kd} | MVP: {score_mvp}")
        
        if idx < total_membros:
            time.sleep(DELAY_RPM)

    payload = {
        "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "temporada": "SEASON " + season_id.split("-")[-1],
        "modo": " + ".join([m.upper() for m in MODOS_FPP]),
        "min_partidas": MIN_PARTIDAS_MVP,
        "jogadores": lista_final
    }

    with open(CAMINHO_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)

    print("\n==========================================")
    print(f" ✅ ARQUIVO SALVO EM: {CAMINHO_JSON}")
    print("==========================================")

if __name__ == "__main__":
    try:
        calcular_estatisticas()
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
