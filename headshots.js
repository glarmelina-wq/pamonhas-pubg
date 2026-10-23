/* Telemetria pós-partida compartilhada entre o perfil e a página de headshots. */
(() => {
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(n,d=0)=>Number(n||0).toLocaleString('pt-BR',{maximumFractionDigits:d});
const medals={sniper:['Cata-piolho','Snipers','sniper.svg'],dmr:['Dipirona ocular','DMRs','dmr.svg'],outras:['Apaga-luz','Demais armas','outras.svg']};
const group=(data,period,mode)=>data?.periodos?.[period]?.grupos?.[mode];
function advice(p){
 const tips=[];
 if(p.dano_azul>0)tips.push(['Entre na safe mais cedo',num(p.dano_azul,1)+' de dano azul em '+num(p.partidas)+' jogos: '+num(p.dano_azul/p.partidas,1)+' por jogo. '+num(p.mortes_azul)+' mortes na zona azul.','Olhe o tempo da safe e saia antes de o gás chegar. Combine o caminho e um veículo com o squad.']);
 if(p.dano_queda>0)tips.push(['Cuidado com as quedas',num(p.dano_queda,1)+' de dano por queda.','Evite pular de telhados altos e barrancos. Procure um caminho para descer sem perder vida.']);
 const labels={boost:['Reponha energético e analgésico','energético ou analgésico','Pegue energético ou analgésico ao repor a mochila depois das lutas.'],cura:['Reponha as curas','kits ou bandagens','Reponha os kits e as bandagens depois de cada luta. Se faltar, peça ao squad.'],fumaca:['Leve mais fumaça','fumaça','Reponha as fumaças. Use para atravessar lugares abertos ou proteger um aliado caído.'],granada:['Confira suas granadas','granadas','Confira se tem granadas antes da próxima luta. Elas ajudam a tirar o inimigo da cobertura.']};
 for(const [cat,[title,item,tip]] of Object.entries(labels)){
  const count=p.mortes_saldo_zero?.[cat]||0, total=p.mortes_validas||0;
  if(total>=3 && count/total>=.5)tips.push([title,'Em '+count+' de '+total+' mortes avaliadas, o saldo estimado de '+item+' era zero.',tip]);
 }
 if((p.coletados?.fumaca||0)>0 && (p.usados?.fumaca||0)===0)tips.push(['Lembre de usar a fumaça',num(p.coletados.fumaca)+' fumaças coletadas, sem uso registrado.','Use fumaça para cruzar áreas abertas, mudar de posição ou ajudar um aliado caído.']);
 if((p.coletados?.boost||0)>0 && (p.usados?.boost||0)===0)tips.push(['Use o energético e o analgésico',num(p.coletados.boost)+' energéticos ou analgésicos coletados, sem uso registrado.','Quando estiver em segurança, use um antes de uma caminhada longa ou da próxima luta.']);
 if(!tips.length)tips.push(['Ainda faltam jogos para dar uma dica',num(p.partidas)+' jogos analisados.','Por enquanto, confira curas, munição e fumaças depois de cada luta.']);
 return tips.map(([title,evidence,tip])=>'<article class="card"><span class="eyebrow">Depois da partida</span><h3>'+esc(title)+'</h3><p class="small muted">'+esc(evidence)+'</p><p>'+esc(tip)+'</p></article>').join('');
}
function profile(nick,mode){
 const p=group(globalThis.PAMONHAS_TELEMETRIA,'semana',mode)?.jogadores?.find(p=>p.nick===nick);
 return '<section class="card" style="margin-top:20px"><span class="eyebrow">Partidas da semana</span><h3>Mochila, safe e recursos</h3>'+
 (p?'<div class="grid2" style="margin-top:16px">'+advice(p)+'</div>':'<p class="muted">Telemetria ainda não disponível para este jogador nesta modalidade. Sem dados não significa zero.</p>')+
 '<p class="small muted">As dicas usam registros de partidas já encerradas. Os itens na mochila são uma estimativa e podem faltar registros. Não sabemos quanto de munição restou.</p><a href="headshots.html">Abrir headshots e diagnóstico completo →</a></section>';
}
globalThis.PamonhasTelemetry={profile,advice};
document.addEventListener('DOMContentLoaded',async()=>{
 if(!document.getElementById('hs-content'))return;
 const content=document.getElementById('hs-content'),status=document.getElementById('hs-status');
 let data,period='semana',mode='todos',category='sniper',selected='';
 const render=()=>{
  document.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.period===period)));
  document.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.category===category)));
  const g=group(data,period,mode),periodData=data?.periodos?.[period];
  if(!g){content.innerHTML='<p class="notice">Ainda não há dados de telemetria para este período e modalidade.</p>';return;}
  const periodName={semana:'Ranking da semana',mes:'Ranking do mês',temporada:'Ranking da temporada'}[period];
  document.getElementById('hs-period-title').textContent=periodName;
  const note=document.getElementById('hs-coverage');
  if(period==='temporada'){
   note.textContent='Atualização automática a cada hora. '+num(g.partidas_analisadas)+' de '+num(g.partidas_conhecidas)+' partidas conhecidas têm telemetria completa. A coleta segue tentando recuperar o restante, mas a API pode não fornecer todos os registros.';
  }else if(period==='mes'){
   const prior=g.partidas_anteriores_semana||0;
   note.textContent=prior
    ? 'O mês inclui '+num(prior)+' partidas analisadas de semanas anteriores, além das partidas desta semana. A cobertura ainda é parcial.'
    : 'Mês em formação: ainda não há partidas analisadas de semanas anteriores neste recorte. Por isso, os números podem coincidir com os da semana. A coleta está recuperando o histórico disponível.';
  }else{
   note.textContent='Semana de segunda a domingo. Os totais consideram somente as partidas com telemetria recuperada.';
  }
  const rows=g.jogadores||[],sorted=[...rows].sort((a,b)=>b.hs[category]-a.hs[category]||a.nick.localeCompare(b.nick));
  const date=s=>new Date(s).toLocaleDateString('pt-BR',{timeZone:'America/Sao_Paulo'});
  status.textContent=periodName+' · '+date(periodData.inicio)+' até '+date(periodData.ate)+' · '+g.partidas_analisadas+' de '+g.partidas_conhecidas+' partidas conhecidas com telemetria completa. A lista de partidas conhecidas também pode ser parcial.';
  document.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.period===period)));
  document.querySelectorAll('[data-category]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.category===category)));
  const awards=Object.entries(medals).map(([key,[name,label,img]])=>{
   const winners=g.medalhas?.[key]||[],best=Math.max(0,...rows.map(p=>p.hs[key]));
   return '<article class="card medal"><img src="medalhas/'+img+'" alt="Medalha '+esc(name)+'" width="132" height="132"><span class="eyebrow">'+label+'</span><h2>'+name+'</h2><p class="winner">'+(winners.length?winners.map(esc).join(' · '):'Aguardando headshots')+'</p><p class="muted small">'+(best?num(best)+' abates de headshot · liderança provisória':'Ninguém com abate de headshot registrado')+'</p></article>';
  }).join('');
  const bestMatch=Math.max(0,...rows.map(p=>p.recorde_hs||0)),recordHolders=rows.filter(p=>bestMatch>0&&p.recorde_hs===bestMatch).map(p=>p.nick);
  content.innerHTML='<div class="grid3" aria-label="'+periodName+'">'+awards+'</div><div class="section-head"><div><span class="eyebrow">Disputa aberta</span><h2>'+esc(medals[category][1])+'</h2><p class="muted">Abates creditados na cabeça. Empates compartilham posição e medalha.</p></div></div>'+
   (rows.length?'<div class="table-wrap"><table><thead><tr><th>Posição</th><th>Jogador</th><th>Headshots</th><th>HS/jogo</th><th>Jogos analisados</th></tr></thead><tbody>'+sorted.map((p,i)=>'<tr><td>'+(p.hs[category]>0?(sorted.findIndex(x=>x.hs[category]===p.hs[category])+1)+'º':'—')+'</td><td>'+esc(p.nick)+'</td><td>'+num(p.hs[category])+'</td><td>'+num(p.hs[category]/p.partidas,2)+'</td><td>'+num(p.partidas)+'</td></tr>').join('')+'</tbody></table></div>':'<p class="notice">A coleta está em andamento. Nenhum jogador com telemetria recuperada neste recorte.</p>')+
   '<div class="grid2" style="margin-top:22px"><article class="card"><span class="eyebrow">Capacete de papel</span><h3>Recorde numa partida</h3><p>'+(bestMatch?num(bestMatch)+' headshots · '+recordHolders.map(esc).join(' · '):'Aguardando partidas analisadas.')+'</p><p class="small muted">Soma das três categorias em uma única partida recuperada.</p></article><article class="card"><span class="eyebrow">Contagem transparente</span><h3>O que entra na disputa?</h3><p>Partidas normais oficiais de Steam, na modalidade selecionada. Sem treino, personalizado ou competitivo. Armas desconhecidas ficam fora das categorias: '+num(rows.reduce((n,p)=>n+p.hs_nao_classificados,0))+' abates de HS não classificados neste recorte.</p></article></div>'+
   '<div class="section-head"><div><span class="eyebrow">Preparar a próxima partida</span><h2>Mochila e sobrevivência</h2><p class="muted">Veja o que levar e o que mudar no próximo jogo.</p></div></div><label>Escolha um Pamonha <select id="hs-player"><option value="">Selecione um jogador</option>'+rows.map(p=>'<option value="'+esc(p.nick)+'">'+esc(p.nick)+'</option>').join('')+'</select></label><div id="hs-advice" style="margin-top:18px"></div>';
  const select=document.getElementById('hs-player');
  if(!rows.some(p=>p.nick===selected))selected=rows[0]?.nick||'';
  select.value=selected;
  const show=()=>{
   selected=select.value;const p=rows.find(p=>p.nick===selected);
   document.getElementById('hs-advice').innerHTML=p?'<div class="grid3">'+advice(p)+'</div><p class="small muted">Munição coletada: '+num(p.coletados.municao)+' unidades. Não sabemos quanto restou. '+num(p.eventos_inconsistentes)+' jogos com registros incompletos da mochila. '+num(p.mortes_validas)+' de '+num(p.mortes)+' mortes com dados para estimar os itens.</p>':'';
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
