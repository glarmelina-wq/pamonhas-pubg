/* Telemetria pós-partida compartilhada entre o perfil e a página de headshots. */
(() => {
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(n,d=0)=>Number(n||0).toLocaleString('pt-BR',{maximumFractionDigits:d});
const medals={sniper:['Cata-piolho','Snipers','sniper.svg'],dmr:['Dipirona ocular','DMRs','dmr.svg'],outras:['Apaga-luz','Demais armas','outras.svg']};
const group=(data,period,mode)=>data?.periodos?.[period]?.grupos?.[mode];
function advice(p){
 const tips=[];
 if(p.dano_azul>0)tips.push(['De olho na próxima safe',num(p.dano_azul,1)+' de dano azul em '+num(p.partidas)+' partidas analisadas ('+num(p.dano_azul/p.partidas,1)+'/jogo). '+num(p.mortes_azul)+' mortes finalizadas pelo gás.','Planeje a rotação antes de a zona fechar e combine veículo e rota com o squad. O dano pode vir de uma decisão tática; reveja as partidas antes de concluir.']);
 if(p.dano_queda>0)tips.push(['O chão também atira',num(p.dano_queda,1)+' de dano de queda observado.','Revise saltos de telhados e encostas. Procure uma descida com cobertura para preservar vida antes da troca.']);
 const labels={boost:['Boost em falta?','energético ou analgésico'],cura:['Revisar as curas','kit, primeiros socorros ou bandagem'],fumaca:['Cadê a cortina?','fumaça'],granada:['Pressão na mochila','granada ofensiva']};
 for(const [cat,[title,item]] of Object.entries(labels)){
  const count=p.mortes_saldo_zero?.[cat]||0, denominator=p.mortes_validas||0;
  if(denominator>=3 && count/denominator>=.5) tips.push([title,count+' de '+denominator+' mortes com saldo estimado zero de '+item+' nos eventos consistentes.','Teste conferir esse recurso após o loot e depois de cada luta. É uma estimativa anterior à morte, não prova de mochila vazia ou da causa da derrota.']);
 }
 if((p.coletados?.fumaca||0)>0 && (p.usados?.fumaca||0)===0)tips.push(['Fumaça também é para usar',num(p.coletados.fumaca)+' fumaças coletadas e nenhum uso observado.','Experimente usar para cruzar áreas abertas, reposicionar e ajudar um aliado. Ausência de uso registrado não garante que o item ficou guardado.']);
 if((p.coletados?.boost||0)>0 && (p.usados?.boost||0)===0)tips.push(['Boost ficou para depois?',num(p.coletados.boost)+' boosts coletados e nenhum uso observado.','Revise se houve uma janela segura para usar energético ou analgésico antes de uma rotação.']);
 if(!tips.length) tips.push(['Construindo seu diagnóstico',num(p.partidas)+' partidas analisadas; '+num(p.mortes_validas)+' mortes com eventos consistentes para estimar itens.','Ainda não há um padrão suficiente para uma dica específica. Observe curas, boosts e utilitários após cada combate.']);
 return tips.map(([title,evidence,tip])=>'<article class="card"><span class="eyebrow">Dica pós-partida</span><h3>'+esc(title)+'</h3><p class="small muted">'+esc(evidence)+'</p><p>'+esc(tip)+'</p></article>').join('');
}
function profile(nick,mode){
 const p=group(globalThis.PAMONHAS_TELEMETRIA,'semana',mode)?.jogadores?.find(p=>p.nick===nick);
 return '<section class="card" style="margin-top:20px"><span class="eyebrow">Partidas da semana</span><h3>Mochila, safe e recursos</h3>'+
 (p?'<div class="grid2" style="margin-top:16px">'+advice(p)+'</div>':'<p class="muted">Telemetria ainda não disponível para este jogador nesta modalidade. Sem dados não significa zero.</p>')+
 '<p class="small muted">Análise após o fim da partida, sem mochila ao vivo. Saldos estimados por coleta, uso e descarte; eventos inconsistentes são excluídos das dicas de saldo zero. Munição mostra coleta, sem saldo confiável.</p><a href="headshots.html">Abrir headshots e diagnóstico completo →</a></section>';
}
globalThis.PamonhasTelemetry={profile,advice};
document.addEventListener('DOMContentLoaded',async()=>{
 if(!document.getElementById('hs-content'))return;
 const content=document.getElementById('hs-content'),status=document.getElementById('hs-status');
 let data,period='semana',mode='todos',category='sniper',selected='';
 const render=()=>{
  const g=group(data,period,mode),periodData=data?.periodos?.[period];
  if(!g){content.innerHTML='<p class="notice">Ainda não há dados de telemetria para este período e modalidade.</p>';return;}
  const rows=g.jogadores||[],sorted=[...rows].sort((a,b)=>b.hs[category]-a.hs[category]||a.nick.localeCompare(b.nick));
  const date=s=>new Date(s).toLocaleDateString('pt-BR',{timeZone:'America/Sao_Paulo'});
  status.textContent=date(periodData.inicio)+' até '+date(periodData.ate)+' · '+g.partidas_analisadas+' de '+g.partidas_conhecidas+' partidas conhecidas com telemetria completa. A lista de partidas conhecidas também pode ser parcial.';
  document.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.period===period)));
  document.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.category===category)));
  const awards=Object.entries(medals).map(([key,[name,label,img]])=>{
   const winners=g.medalhas?.[key]||[],best=Math.max(0,...rows.map(p=>p.hs[key]));
   return '<article class="card medal"><img src="medalhas/'+img+'" alt="Medalha '+esc(name)+'" width="132" height="132"><span class="eyebrow">'+label+'</span><h2>'+name+'</h2><p class="winner">'+(winners.length?winners.map(esc).join(' · '):'Aguardando headshots')+'</p><p class="muted small">'+(best?num(best)+' abates de headshot · liderança provisória':'Ninguém com abate de headshot registrado')+'</p></article>';
  }).join('');
  const bestMatch=Math.max(0,...rows.map(p=>p.recorde_hs||0)),recordHolders=rows.filter(p=>bestMatch>0&&p.recorde_hs===bestMatch).map(p=>p.nick);
  content.innerHTML='<div class="grid3">'+awards+'</div><div class="section-head"><div><span class="eyebrow">Disputa aberta</span><h2>'+esc(medals[category][1])+'</h2><p class="muted">Abates creditados na cabeça. Empates compartilham posição e medalha.</p></div></div>'+
   (rows.length?'<div class="table-wrap"><table><thead><tr><th>Posição</th><th>Jogador</th><th>Headshots</th><th>HS/jogo</th><th>Jogos analisados</th></tr></thead><tbody>'+sorted.map((p,i)=>'<tr><td>'+(p.hs[category]>0?(sorted.findIndex(x=>x.hs[category]===p.hs[category])+1)+'º':'—')+'</td><td>'+esc(p.nick)+'</td><td>'+num(p.hs[category])+'</td><td>'+num(p.hs[category]/p.partidas,2)+'</td><td>'+num(p.partidas)+'</td></tr>').join('')+'</tbody></table></div>':'<p class="notice">A coleta está em andamento. Nenhum jogador com telemetria recuperada neste recorte.</p>')+
   '<div class="grid2" style="margin-top:22px"><article class="card"><span class="eyebrow">Capacete de papel</span><h3>Recorde numa partida</h3><p>'+(bestMatch?num(bestMatch)+' headshots · '+recordHolders.map(esc).join(' · '):'Aguardando partidas analisadas.')+'</p><p class="small muted">Soma das três categorias em uma única partida recuperada.</p></article><article class="card"><span class="eyebrow">Contagem transparente</span><h3>O que entra na disputa?</h3><p>Partidas normais oficiais de Steam, na modalidade selecionada. Sem treino, personalizado ou competitivo. Armas desconhecidas ficam fora das categorias: '+num(rows.reduce((n,p)=>n+p.hs_nao_classificados,0))+' abates de HS não classificados neste recorte.</p></article></div>'+
   '<div class="section-head"><div><span class="eyebrow">Preparar a próxima partida</span><h2>Mochila e sobrevivência</h2><p class="muted">Eventos do jogo antes da morte, analisados depois da partida.</p></div></div><label>Escolha um Pamonha <select id="hs-player"><option value="">Selecione um jogador</option>'+rows.map(p=>'<option value="'+esc(p.nick)+'">'+esc(p.nick)+'</option>').join('')+'</select></label><div id="hs-advice" style="margin-top:18px"></div>';
  const select=document.getElementById('hs-player');
  if(!rows.some(p=>p.nick===selected))selected=rows[0]?.nick||'';
  select.value=selected;
  const show=()=>{
   selected=select.value;const p=rows.find(p=>p.nick===selected);
   document.getElementById('hs-advice').innerHTML=p?'<div class="grid3">'+advice(p)+'</div><p class="small muted">Coleta observada: '+num(p.coletados.municao)+' unidades de munição; isso não é saldo nem indica falta. '+num(p.eventos_inconsistentes)+' partidas com inconsistências de inventário. '+num(p.mortes_validas)+' de '+num(p.mortes)+' mortes permitem avaliar saldo estimado.</p>':'';
  };select.addEventListener('change',show);show();
 };
 document.querySelectorAll('[data-period]').forEach(b=>b.addEventListener('click',()=>{period=b.dataset.period;render();}));
 document.querySelectorAll('[data-category]').forEach(b=>b.addEventListener('click',()=>{category=b.dataset.category;render();}));
 document.getElementById('hs-mode').addEventListener('change',e=>{mode=e.target.value;render();});
 try{
  const r=await fetch('telemetria_cla.json',{cache:'no-cache'});if(!r.ok)throw Error(r.status);data=await r.json();globalThis.PAMONHAS_TELEMETRIA=data;
  document.getElementById('hs-notice').textContent=data.aviso;render();
 }catch(e){status.textContent='Telemetria indisponível nesta consulta.';content.innerHTML='<div class="notice">A coleta ainda pode estar preparando os dados. <button onclick="location.reload()">Tentar novamente</button></div>';}
});
})();
