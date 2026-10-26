/* Troféus calculados sobre dados reais. Não infere causas de morte ou direção de veículos. */
const PARTY_AWARDS = {
 caneta:{nome:'Caneta azul, azul caneta',emoji:'🖊️',campo:'dano_azul',unidade:'pontos de dano',telemetria:true,frase:'A safe chamou. Ele ficou para terminar a música.',descricao:'Quem mais recebeu dano da zona azul. Vale a soma do dano nas partidas analisadas.'},
 botkiller:{nome:'Caçador de Bots',emoji:'🤖',campo:'kills_bot',unidade:'abates',telemetria:true,frase:'O lobby veio com inteligência artificial. Ele também.',descricao:'Mais bots identificados pelo ID de IA eliminados pelo golpe final.'},
 playerkiller:{nome:'Matador de Players',emoji:'☠️',campo:'kills_player',unidade:'abates',telemetria:true,frase:'Encontrou player. O player não encontrou saída.',descricao:'Mais jogadores com ID de conta eliminados pelo golpe final. Bots e aliados não entram.'},
 kombi:{nome:'Kombi sem Freio',emoji:'🚐',campo:'rideDistance',unidade:'km',frase:'O hodômetro pediu férias.',descricao:'Maior distância em veículos. Inclui motorista e passageiros.'},
 amigo:{nome:'Amigo da Onça',emoji:'🤝',campo:'teamKills',unidade:'eventos',frase:'O inimigo agradeceu a ajuda.',descricao:'Mais eliminações de aliados registradas. Não indica intenção.'},
 inimigo:{nome:'Inimigo de Si Mesmo',emoji:'💥',campo:'suicides',unidade:'eventos',frase:'Resolveu o próprio problema antes do adversário.',descricao:'Mais mortes autoinfligidas. A estatística não identifica granada, queda ou outra causa.'},
 samu:{nome:'SAMU dos Pamonhas',emoji:'🚑',campo:'revives',unidade:'eventos',frase:'O plantão não acaba enquanto tiver pamonha no chão.',descricao:'Mais reanimações de companheiros.'},
 lobby:{nome:'Sócio do Lobby',emoji:'🛋️',campo:'timeSurvived',unidade:'min/jogo',media:true,menor:true,frase:'Já deixou a cadeira reservada para a próxima.',descricao:'Menor tempo médio vivo. Mínimo de 5 partidas na semana ou 15 na temporada.'},
 farmacia:{nome:'Farmácia Ambulante',emoji:'💊',campo:'heals_boosts',unidade:'itens/jogo',media:true,frase:'A receita veio com renovação automática.',descricao:'Mais curas e boosts consumidos por partida, não itens carregados na mochila.'},
 forrest:{nome:'Forrest Pamonha',emoji:'🏃',campo:'walkDistance',unidade:'km/jogo',media:true,frase:'A Kombi passou, mas preferiu ir a pé.',descricao:'Maior distância a pé por partida.'},
 sedex:{nome:'Entrega por Sedex',emoji:'🎯',campo:'longestKill',unidade:'m',soTemporada:true,frase:'Mandou a encomenda para outro CEP.',descricao:'Maior distância de um abate na temporada. Não é possível obter o máximo semanal subtraindo recordes.'},
 lutinho:{nome:'Zé Lutinho',emoji:'🧳',campo:'weaponsAcquired',unidade:'armas/jogo',media:true,frase:'Entrou para o combate, ficou pelo shopping.',descricao:'Mais armas coletadas por partida. Não conta todo tipo de loot e não significa tempo gasto looteando.'}
};
const partyState={period:'temporada',award:'kombi',archive:[],card:null,manual:false,autoFallback:false};
function partyRaw(p){
 if(p.resenha)return p.resenha;
 return {roundsPlayed:value(p,'partidas'),rideDistance:value(p,'km_rodados')*1000,teamKills:value(p,'team_kills'),suicides:value(p,'suicides'),revives:value(p,'revives'),timeSurvived:value(p,'tempo_medio_min')*60*value(p,'partidas'),heals:value(p,'heals'),boosts:0,walkDistance:value(p,'km_pe')*1000*value(p,'partidas'),longestKill:value(p,'longest_kill'),weaponsAcquired:null};
}
function partyField(raw,key){if(key==='heals_boosts')return typeof raw.heals==='number'&&typeof raw.boosts==='number'?raw.heals+raw.boosts:null;return raw[key];}
function partyContext(period=partyState.period){
 const updated=state.data.updated_at;
 if(period==='temporada')return {period,rows:players().map(p=>({nick:p.nick,account_id:p.account_id,partidas:p.partidas,raw:partyRaw(p)})),de:null,ate:updated};
 if(!updated)return {period,rows:[],reason:'O novo coletor ainda não registrou a referência da semana.'};
 const start=weekStart(updated),end=new Date(start.getTime()+7*86400000);
 const recovered=state.recovered;
 if(recovered?.fonte==='partidas'&&Date.parse(recovered.inicio_semana)===start.getTime()&&Array.isArray(recovered.grupos?.[state.mode])&&recovered.grupos[state.mode].length){
  const rows=recovered.grupos[state.mode].filter(p=>typeof p.nick==='string'&&p.partidas>0&&p.raw);
  return {period,rows,de:recovered.inicio_semana,ate:recovered.updated_at,start,partial:true,byMatch:true,recovered,reason:rows.length?'':'Nenhuma partida recuperada nesta modalidade.'};
 }
 const baseline=validHistory().find(s=>s.resenha_version===1&&new Date(s.at)>=start&&new Date(s.at)<end);
 if(!baseline)return {period,rows:[],reason:'A primeira coleta desta versão vai iniciar a contagem semanal. Os troféus da temporada já podem ser consultados.'};
 const before=new Map(baseline.grupos[state.mode].map(p=>[p.account_id||p.nick,p]));
 const rows=[];
 for(const p of players()){
  const old=before.get(p.account_id||p.nick);if(!p.resenha||!old?.resenha)continue;
  const delta={};for(const [key,current] of Object.entries(p.resenha)){if(key==='longestKill')continue;delta[key]=typeof current==='number'&&typeof old.resenha[key]==='number'?current-old.resenha[key]:null;}
  if(Object.values(delta).some(v=>typeof v==='number'&&v<0)||!delta.roundsPlayed)continue;
  rows.push({nick:p.nick,account_id:p.account_id,partidas:delta.roundsPlayed,raw:delta});
 }
 return {period,rows,de:baseline.at,ate:updated,start,partial:true,reason:rows.length?'':'Ainda não há partidas novas entre a referência e a última coleta.'};
}
function telemetryPartyContext(period){
 const data=globalThis.PAMONHAS_TELEMETRIA;
 const selected=data?.periodos?.[period];
 const g=selected?.grupos?.[state.mode];
 if(period==='temporada'&&data?.season_id!==state.data.season_id)return {period,rows:[],reason:'Aguardando os dados desta temporada.'};
 return {period,rows:(g?.jogadores||[]).map(p=>({nick:p.nick,account_id:p.account_id,partidas:p.partidas,raw:{dano_azul:p.dano_azul,kills_bot:p.kills_bot,kills_player:p.kills_player}})),de:selected?.inicio,ate:selected?.ate,partial:true,byMatch:true,telemetry:true,known:g?.partidas_conhecidas||0,analyzed:g?.partidas_analisadas||0,reason:'Ainda não há abates registrados neste período.'};
}
function bluePartyContext(period){return telemetryPartyContext(period);}
function partyResults(key,period=partyState.period){
 const award=PARTY_AWARDS[key],context=period==='mes'&&!award.telemetria?{period,rows:[],reason:'Este troféu não usa telemetria mensal.'}:award.telemetria?telemetryPartyContext(period):partyContext(period),minimum=award.media?(period==='semana'?5:minimumForParty()):0;
 if(award.soTemporada&&period==='semana'&&!context.byMatch)return {award,context,minimum,rows:[],winners:[],reason:'O recorde semanal será liberado quando houver partidas recuperadas.'};
 const rows=context.rows.map(p=>({...p,valor:partyField(p.raw,award.campo)})).filter(p=>Number.isFinite(p.valor)&&p.valor>0&&p.partidas>0&&p.partidas>=minimum).map(p=>({...p,valor:award.media?p.valor/p.partidas:p.valor})).sort((a,b)=>(award.menor?a.valor-b.valor:b.valor-a.valor)||a.nick.localeCompare(b.nick));
 const winners=rows.filter(p=>Math.abs(p.valor-rows[0].valor)<1e-9);
 let reason=context.reason||'Sem registro positivo neste período.';
 if(!rows.length&&award.media&&context.rows.length)reason=`Sem registros elegíveis. Mínimo de ${minimum} partidas e métrica disponível.`;
 if(key==='lutinho'&&!rows.length&&context.rows.length&&!context.rows.some(p=>Number.isFinite(p.raw.weaponsAcquired)))reason='A API não forneceu armas coletadas para este período. Sem vencedor inventado.';
 return {award,context,minimum,rows,winners,reason};
}
function minimumForParty(){return minimum();}
function partyFormat(key,v){const a=PARTY_AWARDS[key];if(a.unidade.startsWith('km'))return fmt(v/1000,2)+' '+a.unidade;if(a.unidade==='min/jogo')return fmt(v/60,1)+' min/jogo';if(a.unidade==='eventos')return fmt(v)+' '+({amigo:'eliminações de aliados',inimigo:'mortes autoinfligidas',samu:'reanimações'}[key]||'registros');if(key==='caneta')return fmt(v,1)+' de dano azul';if(a.unidade==='abates')return fmt(v)+(v===1?' abate':' abates');if(a.unidade==='m')return fmt(v,1)+' m';return fmt(v,2)+' '+a.unidade;}
function partyNames(winners){return winners.length>2?winners.slice(0,2).map(p=>p.nick).join(' + ')+` e mais ${winners.length-2}`:winners.map(p=>p.nick).join(' + ');}
function partyCards(period=partyState.period){return Object.entries(PARTY_AWARDS).filter(([,a])=>period!=='mes'||a.telemetria).map(([key,a])=>{
 const result=partyResults(key,period),win=result.winners[0];
 return `<button class="podium-card party-card ${win?'champion':''}" data-party-award="${key}"><span class="place">${a.emoji} ${esc(a.nome)}</span><h3>${win?esc(partyNames(result.winners)):'Sem vencedor'}</h3>${win?`<strong class="yellow" style="font-size:24px">${esc(partyFormat(key,win.valor))}</strong><p class="small muted">${esc(a.frase)}</p>${a.telemetria?'<p class="small muted">Dados parciais das partidas analisadas.</p>':''}${result.winners.length>1?'<span class="badge">Troféu compartilhado</span>':''}`:`<p class="small muted">${esc(result.reason)}</p>`}<span class="open">Ver ranking e regra →</span></button>`;
}).join('');}
function partyPeriodLabel(){
 const c=partyContext();
 if(partyState.period==='mes'){const t=telemetryPartyContext('mes');return `Mês civil · ${MODE_LABELS[state.mode]}. ${t.analyzed} de ${t.known} partidas conhecidas com telemetria completa; a cobertura pode ser parcial.`;}
 if(partyState.period==='temporada'){const t=telemetryPartyContext('temporada');return `${state.data.temporada} · ${MODE_LABELS[state.mode]}. Telemetria completa em ${t.analyzed} de ${t.known} partidas conhecidas; cobertura parcial. Métricas por média exigem ${minimum()} partidas.`;}
 if(!c.de)return c.reason;
 if(c.byMatch){const r=c.recovered;return `Semana desde ${dateLabel(c.de,true)} até a coleta de ${dateLabel(c.ate,true)} (Brasília). Partidas oficiais recuperadas, agrupadas pela data de início. ${r.partidas_semana} partidas distintas na semana, somando as modalidades. A cobertura pode ser parcial por limites das listas da API.${r.pendentes?' Há '+r.pendentes+' referências pendentes; a recuperação continua nas próximas execuções.':''}${r.membros_sem_lista?.length?' Alguns membros estão sem lista de partidas nesta consulta.':''}${r.falhas_partidas||r.falha_recuperacao?' Houve falhas temporárias na recuperação.':''} Médias exigem 5 partidas por jogador na seleção.`;}
 return `Semana: dados de ${dateLabel(c.de,true)} até ${dateLabel(c.ate,true)}, horário de Brasília. Contagem parcial entre coletas; não inclui o intervalo anterior à primeira referência. Médias exigem 5 partidas novas. Todos os modos normais selecionados contam, mesmo jogando sem o clã.`;
}
function partyAutoPeriod(){
 if(partyState.manual)return;
 const hasWeekly=Object.keys(PARTY_AWARDS).some(key=>partyResults(key,'semana').winners.length);
 partyState.period=hasWeekly?'semana':'temporada';partyState.autoFallback=!hasWeekly;
}
function renderResenha(){
 const period=partyState.period;
 for(const id of ['party-auto-home','party-auto-full'])if($(id)){$(id).hidden=!partyState.autoFallback;$(id).textContent='Mostrando a temporada enquanto a semana ainda não tem vencedores. Você já pode consultar os troféus; a semana será escolhida automaticamente na abertura da página quando houver resultados.'+(state.recovered?.pendentes?' Recuperação em andamento: '+state.recovered.pendentes+' referências pendentes para as próximas execuções.':'')+(state.recovered?.falha_recuperacao||state.recovered?.membros_sem_lista?.length?' A API não retornou todas as listas nesta consulta. A temporada continua disponível.':'');}
 for(const id of ['party-home','party-cards'])if($(id))$(id).innerHTML=partyCards(period);
 for(const id of ['party-home-context','party-context'])if($(id))$(id).textContent=partyPeriodLabel();
 document.querySelectorAll('[data-party-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.partyPeriod===period)));
 if($('party-award-select')){const available=Object.entries(PARTY_AWARDS).filter(([,a])=>period!=='mes'||a.telemetria);if(!available.some(([key])=>key===partyState.award))partyState.award='caneta';$('party-award-select').innerHTML=available.map(([key,a])=>`<option value="${key}">${esc(a.emoji+' '+a.nome)}</option>`).join('');$('party-award-select').value=partyState.award;}
 renderPartyTable();renderPartyArchive();
}
function renderPartyTable(){
 if(!$('party-ranking'))return;
 const key=partyState.award,{award,context,rows,winners,minimum,reason}=partyResults(key);
 let position=0,last=null;
 $('party-ranking').innerHTML=`<div class="section-head"><div><span class="eyebrow">${esc(award.emoji)} Ranking da brincadeira</span><h2>${esc(award.nome)}</h2><p class="muted small">${esc(award.soTemporada&&partyState.period==='semana'&&partyContext().byMatch?'Maior distância de um abate nas partidas recuperadas desta semana.':award.descricao)}${award.telemetria?' Dados parciais: só entram partidas já analisadas.':''}${minimum?` Mínimo aplicado: ${minimum} partidas.`:''}</p></div>${winners.length?`<button class="primary" data-party-share="${key}">Baixar troféu PNG ↓</button>`:''}</div>${rows.length?`<div class="table-wrap"><table><caption class="small muted" style="padding:12px;text-align:left">${partyState.period==='semana'?(partyContext().byMatch?'Semana · partidas recuperadas':'Semana entre coletas'):partyState.period==='mes'?'Mês':'Temporada'} · ${MODE_LABELS[state.mode]} · Empates dividem posição e troféu.</caption><thead><tr><th scope="col">Posição</th><th scope="col">Pamonha</th><th scope="col">${esc(award.nome)}</th><th scope="col">Partidas no período</th></tr></thead><tbody>${rows.map((p,i)=>{if(last===null||Math.abs(p.valor-last)>1e-9)position=i+1;last=p.valor;return `<tr><td>${position}º</td><td><button data-player="${esc(p.nick)}">${esc(p.nick)}</button></td><td class="yellow"><strong>${esc(partyFormat(key,p.valor))}</strong></td><td>${fmt(p.partidas)}</td></tr>`;}).join('')}</tbody></table></div>`:`<div class="empty">${esc(reason)}</div>`}`;
}
function renderPartyArchive(){
 if(!$('party-archive'))return;
 const weeks=partyState.archive.filter(w=>w.grupos?.[state.mode]&&Object.keys(w.grupos[state.mode]).length);
 $('party-archive').innerHTML=weeks.length?weeks.slice(0,8).map(w=>`<details class="card" style="margin-top:12px"><summary>🌽 Semana de ${dateLabel(w.inicio_semana)} · ${w.fonte==='partidas'?'partidas recuperadas':esc(w.season_id.split('-').at(-1))}</summary><p>Apuração parcial de ${dateLabel(w.de,true)} a ${dateLabel(w.ate,true)}${w.fonte==='partidas'?' · somente partidas recuperadas':''}. Modalidade: ${MODE_LABELS[state.mode]}.</p><div class="list">${Object.entries(w.grupos[state.mode]).filter(([key])=>PARTY_AWARDS[key]).map(([key,winners])=>`<div class="list-row"><span class="small">${PARTY_AWARDS[key].emoji} ${esc(PARTY_AWARDS[key].nome)}<br><strong>${esc(winners.map(p=>p.nick).join(' + '))}</strong></span><b class="small">${esc(partyFormat(key,winners[0].valor))}</b></div>`).join('')}</div></details>`).join(''):'<div class="empty">A galeria vai guardar os vencedores quando uma semana acompanhada terminar. Não há troféus históricos inventados.</div>';
}
function renderProfileTrophies(p){
 const target=$('profile-trophies');if(!target)return;
 const badges=[];
 for(const period of ['semana','mes','temporada'])for(const [key,a] of Object.entries(PARTY_AWARDS))if(partyResults(key,period).winners.some(w=>(w.account_id||w.nick)===(p.account_id||p.nick)))badges.push(`<span class="badge neutral">${a.emoji} ${esc(a.nome)} · ${period==='semana'?'Semana':period==='mes'?'Mês':'Temporada'}</span>`);
 target.innerHTML=`<span class="eyebrow">Coleção da resenha</span><h3 style="margin-top:8px">Seus troféus atuais</h3><div class="actions" style="margin-top:15px">${badges.join('')||'<p class="muted small">Ainda sem troféu nesta modalidade. A próxima resenha pode ser sua.</p>'}</div><p class="muted small" style="margin-top:12px">Troféus semanais são provisórios até o período encerrar. Empates compartilham a conquista.</p>`;
}
function downloadPartyCard(key){
 const {award,winners,context}=partyResults(key);if(!winners.length)return;
 const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1350;const c=canvas.getContext('2d');if(!c)return;
 const gradient=c.createLinearGradient(0,0,1080,1350);gradient.addColorStop(0,'#39402a');gradient.addColorStop(.6,'#142119');gradient.addColorStop(1,'#2e2514');c.fillStyle=gradient;c.fillRect(0,0,1080,1350);c.strokeStyle='#f2cc55';c.lineWidth=7;c.strokeRect(25,25,1030,1300);c.textAlign='center';
 const line=(text,y,size=40,color='#f1f5ed')=>{c.fillStyle=color;let fontSize=size;do{c.font=`800 ${fontSize}px system-ui`;if(c.measureText(text).width<930)break;fontSize-=2;}while(fontSize>18);c.fillText(text,540,y);};
 line('OS PAMONHAS',125,42,'#f2cc55');line('TROFÉU DA RESENHA',188,26,'#9bd3a5');line(award.emoji,355,110);line(award.nome.toUpperCase(),465,64,'#f2cc55');
 winners.slice(0,5).forEach((p,i)=>line(p.nick,590+i*62,56));if(winners.length>5)line(`+ ${winners.length-5} campeões empatados`,905,25,'#9bd3a5');
 line(partyFormat(key,winners[0].valor),1015,47,'#f2cc55');line(partyState.period==='semana'?(context.byMatch?'SEMANA • PARTIDAS RECUPERADAS':'SEMANA • ENTRE COLETAS'):partyState.period==='mes'?'MÊS • TELEMETRIA':state.data.temporada,1090,27,'#9bd3a5');line(MODE_LABELS[state.mode],1138,24);line(context.de?`${dateLabel(context.de,true)} a ${dateLabel(context.ate,true)} · Brasília`:`Coleta: ${state.data.ultima_atualizacao}`,1190,22,'#b8c9b9');line('O frango é raro. A resenha é garantida.',1255,26,'#f2cc55');
 try{canvas.toBlob(blob=>{if(!blob){$('party-download-status').textContent='Não foi possível gerar o card.';return;}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`Pamonhas_${key}_${partyState.period}.png`;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);$('party-download-status').textContent='Troféu gerado. Confira os downloads e envie no grupo.';},'image/png');}catch(e){$('party-download-status').textContent='Não foi possível baixar o troféu neste navegador.';}
}
document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 if(button.dataset.partyPeriod){partyState.manual=true;partyState.autoFallback=false;partyState.period=button.dataset.partyPeriod;renderResenha();}
 if(button.dataset.partyAward){partyState.award=button.dataset.partyAward;renderResenha();navigate('resenha');$('party-ranking').scrollIntoView({behavior:'auto',block:'start'});}
 if(button.dataset.partyShare)downloadPartyCard(button.dataset.partyShare);
});
document.addEventListener('change',event=>{if(event.target.id==='party-award-select'){partyState.award=event.target.value;renderPartyTable();}});
