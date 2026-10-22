/* Catálogo editorial: dicas práticas, sem prometer uma análise de replay.
   Cada categoria tem seis dicas e três frases leves de resenha.
   As regras de seleção ficam no index.html; nenhuma dica é gerada por IA ao vivo. */
globalThis.PAMONHAS_DICAS = {
 amostra: {
  titulo: 'Primeiro, ganhar uma base de comparação',
  dicas: [
   'Jogue mais algumas partidas na mesma modalidade antes de tirar conclusões sobre suas médias. Uma partida muito boa ou ruim pesa bastante numa amostra pequena.',
   'Escolha uma combinação de armas para praticar por algumas sessões. Trocar tudo a cada queda dificulta perceber o que melhorou.',
   'Anote uma meta simples para a próxima sessão: causar dano antes de avançar ou combinar a rotação com o time.',
   'Compare o resultado depois de um conjunto de partidas, sem usar uma única vitória como prova de que uma mudança funcionou.',
   'Separe as modalidades nos filtros quando quiser estudar seu desempenho. Solo e Squad pedem decisões diferentes.',
   'Reserve alguns minutos de treino e depois teste uma única mudança por sessão. Isso torna a evolução mais fácil de observar.'
  ],
  zoeira: ['O currículo ainda está na fase do nome e do telefone.', 'Calma, fiscal do ranking: a pamonha ainda está cozinhando.', 'Ainda é trailer. O filme da temporada vem depois.']
 },
 combate: {
  titulo: 'Criar mais oportunidades de dano',
  dicas: [
   'Treine rajadas curtas numa distância que costuma aparecer nas suas partidas. Aumente a distância conforme conseguir manter os tiros no alvo.',
   'Antes de trocar tiros, escolha uma cobertura para voltar. Teste expor menos o corpo e evitar ficar parado fora dela.',
   'Em modos de equipe, combine dois jogadores atirando no mesmo alvo em vez de abrir quatro trocas separadas.',
   'Marque o inimigo e use uma referência clara antes de atirar. Comunicação curta ajuda o squad a aproveitar o dano que você causar.',
   'Ao abrir uma luta, veja se existe uma posição lateral segura. Um ângulo diferente pode ser mais útil que insistir no mesmo pico.',
   'Reveja uma troca perdida e procure o primeiro erro observável: exposição, mira, recarga ou avanço. Escolha só um para treinar.'
  ],
  zoeira: ['O inimigo agradeceu a massagem. Na próxima, manda o dano junto.', 'A mira está tirando foto do adversário; falta apertar o disparador.', 'O carregador foi inteiro, mas o boleto do dano ainda não chegou.']
 },
 precisao: {
  titulo: 'Treinar altura de mira e finalizações',
  dicas: [
   'No treino, mantenha a mira na altura provável do adversário antes de ele aparecer. Evite começar toda troca corrigindo a mira do chão.',
   'Pratique primeiro acertar o alvo e depois encurtar o tempo até o primeiro tiro. Velocidade sem controle pode só gastar munição.',
   'Faça um treino curto de alvos parados e outro de alvos móveis. Observe em qual dos dois sua mira mais passa do ponto.',
   'Teste uma sensibilidade por várias sessões antes de mudar novamente. Registre a configuração para conseguir comparar.',
   'Não force headshots se isso fizer você perder tiros fáceis no corpo. O objetivo é vencer a troca, não melhorar uma porcentagem isolada.',
   'Ao avaliar a taxa de headshot, lembre que ela conta abates finalizados na cabeça, não a precisão de todos os disparos.'
  ],
  zoeira: ['O capacete do inimigo saiu sem um arranhão, pronto para revenda.', 'A mira conhece o colete pelo primeiro nome.', 'O headshot está no catálogo, só falta colocar no carrinho.']
 },
 sobrevivencia: {
  titulo: 'Sobreviver mais sem abandonar as lutas',
  dicas: [
   'Depois de atirar, volte à cobertura e confira se apareceu outro ângulo contra você. Evite repetir o mesmo pico sem informação nova.',
   'Antes de atravessar um campo aberto, escolha o próximo abrigo e uma alternativa se houver tiro no caminho.',
   'Se perder a vantagem da troca, teste recuar, curar e mudar de posição antes de tentar de novo.',
   'No início da partida, priorize equipamento suficiente para se defender. Combater sem recurso e lotear para sempre são extremos diferentes.',
   'Em equipe, avise quando ficar isolado e combine um ponto de reencontro. Distância sem comunicação dificulta qualquer ajuda.',
   'Reveja as mortes mais cedo e identifique a causa real no replay. Tempo vivo baixo sozinho não prova erro de rotação ou morte no gás.'
  ],
  zoeira: ['A cadeira do lobby já está com seu nome bordado.', 'O ônibus ainda nem esfriou e já tem passageiro de volta.', 'Entrou para jogar ou só para testar a tela de carregamento?']
 },
 consistencia: {
  titulo: 'Chegar mais vezes à parte final',
  dicas: [
   'Quando a próxima zona aparecer, combine uma rota antes de continuar uma briga longa. Veja o tempo disponível para sair dela.',
   'Escolha posições com mais de uma saída. Um abrigo forte pode virar armadilha se a próxima zona não ajudar.',
   'Depois de vencer uma luta, reorganize cura, munição e transporte antes de iniciar outra.',
   'Em equipe, defina quem observa cada direção quando o squad parar. Quatro pessoas olhando o mesmo lugar deixam outros ângulos livres.',
   'Pratique reconhecer uma luta que você pode abandonar. Sair com o squad vivo também preserva a chance de vitória.',
   'Compare o Top 10 dentro da mesma modalidade. A métrica tem contexto diferente em Solo, Duo e Squad.'
  ],
  zoeira: ['O Top 10 mandou convite, mas parece que foi para a caixa de spam.', 'A safe mudou de endereço e esqueceram de avisar no grupo.', 'O final da partida está disponível; não precisa assistir só pelo amigo.']
 },
 conversao: {
  titulo: 'Transformar presença no final em vitória',
  dicas: [
   'No fim da partida, priorize informação antes de revelar sua posição. Atirar num alvo distante pode chamar uma luta que você não precisa.',
   'Guarde utilitários para atravessar ou tirar alguém de uma cobertura. Teste entrar no final com uma reserva em vez de gastar tudo cedo.',
   'Em equipe, combinem um alvo e um momento para avançar. Um avanço dividido facilita a defesa adversária.',
   'Ao ficar entre os últimos times, observe o espaço jogável e as coberturas antes de escolher a próxima luta.',
   'Reveja uma partida que terminou perto da vitória e identifique a última decisão que ainda permitia uma alternativa.',
   'Se já tem uma posição boa, teste manter a cobertura enquanto busca informação. A próxima eliminação nem sempre exige sair dela.'
  ],
  zoeira: ['Chegou ao restaurante, mas o frango foi para outra mesa.', 'O jantar está quase servido; falta parar de derrubar o prato.', 'Já tem presença VIP no final, agora falta retirar o troféu.']
 },
 suporte: {
  titulo: 'Aproximar o jogo do squad',
  dicas: [
   'Antes de tentar reanimar, confira cobertura, adversários e tempo disponível. Uma reanimação segura vale mais que cair junto.',
   'Combine uma distância que permita apoiar a troca de um aliado sem ficar todo mundo no mesmo ângulo.',
   'Avise quando recarregar, curar ou recuar. Essas três informações ajudam o parceiro a saber quando tem apoio.',
   'Use marcações e chamadas curtas para concentrar fogo. Assistência não exige que você abandone sua própria cobertura.',
   'Depois de um nocaute aliado, combine quem cobre e quem tenta recuperar. Evite todo mundo parar de observar para ajudar ao mesmo tempo.',
   'Teste carregar utilitários para proteger uma recuperação. Não force a reanimação quando a situação não oferece segurança.'
  ],
  zoeira: ['O amigo pediu cobertura e recebeu um orçamento.', 'O squad está junto no Discord; falta combinar o encontro no mapa.', 'Reanimação não gasta Pix. Pode ajudar o parceiro.']
 },
 mobilidade: {
  titulo: 'Planejar o próximo deslocamento',
  dicas: [
   'Antes de sair de uma posição, decida onde pretende chegar. Deslocamento com destino claro evita ficar procurando abrigo no aberto.',
   'Observe terreno e coberturas ao planejar a rota. A menor distância nem sempre oferece a travessia mais segura.',
   'Em equipe, avise o movimento antes de iniciá-lo. Quem ficou curando precisa saber para onde o grupo vai.',
   'Use o filtro de modalidade para comparar distâncias. Partidas curtas ou mapas diferentes podem alterar bastante essa média.',
   'Se houver veículo, pense também no lugar de desembarcar e na saída seguinte, não apenas no trajeto.',
   'Teste planejar a rotação logo após a mudança de zona. Assim você consegue decidir com mais tempo e informação.'
  ],
  zoeira: ['O endereço da safe mudou, mas o GPS continua em casa.', 'A barraca já está montada; só falta saber se a zona concorda.', 'O mapa tem outros bairros. Dá para visitar sem mudar de clã.']
 },
 controle: {
  titulo: 'Reduzir incidentes com aliados',
  dicas: [
   'Antes de lançar um explosivo, avise o local e confira se algum aliado está avançando para a mesma área.',
   'Ao trocar de ângulo, comunique se vai cruzar a linha de tiro do parceiro.',
   'Se o squad vai entrar numa construção, combine a ordem de entrada para evitar aliados atravessando sprays.',
   'Observe o trajeto de granadas em locais fechados. Um rebote pode levar o explosivo para uma posição diferente da planejada.',
   'Reveja o incidente no replay antes de tirar conclusões. A contagem de team kills não informa intenção ou circunstância.',
   'Perto de aliados, priorize identificar o alvo e a linha de tiro antes de disparar ou avançar com veículo.'
  ],
  zoeira: ['O fogo é amigo, mas o parceiro continua esperando a amizade.', 'O adversário agradece a terceirização do serviço.', 'Antes de atirar, confira se o nick também está no seu Discord.']
 },
 recursos: {
  titulo: 'Checar preparo entre as trocas',
  dicas: [
   'Depois de uma luta, confira vida, munição e recursos antes de avançar para a próxima.',
   'Combine trocas de itens com o squad durante momentos seguros. Evite perceber a falta de cura só quando alguém cair.',
   'Organize uma quantidade de recursos que faça sentido para seu estilo e duração de partida, sem transformar a mochila em depósito.',
   'Confira seus atalhos de cura no treino para não precisar procurar o item durante uma troca.',
   'Durante uma rotação longa, planeje onde pode parar com segurança caso precise se recuperar.',
   'Não use quantidade de curas como nota de habilidade. Quem toma pouco dano pode precisar de menos itens.'
  ],
  zoeira: ['A mochila abriu uma filial de conveniência.', 'Tem estoque para o churrasco, só falta sobrar espaço para utilitário.', 'O inventário está organizado por setor, corredor e prateleira.']
 },
 manter: {
  titulo: 'Manter o que já está funcionando',
  dicas: [
   'Escolha uma partida boa e reveja a decisão que criou sua vantagem. Procure repetir a decisão, não só perseguir o resultado.',
   'Compare sessões dentro da mesma modalidade para observar se suas médias continuam estáveis.',
   'Quando encontrar uma configuração confortável, mantenha uma referência salva antes de testar ajustes.',
   'Alterne treino de combate com revisão de decisões. Melhorar o spray não substitui escolher uma boa troca.',
   'Transforme um ponto forte em ajuda ao time: explique a chamada ou o posicionamento que deu certo para vocês.',
   'Estabeleça uma pequena meta nova por sessão sem abandonar as rotinas que já ajudaram a construir seus resultados.'
  ],
  zoeira: ['O frango está saindo com selo da casa.', 'O fiscal do ranking já pediu para conferir a receita da pamonha.', 'Está rendendo. Só não vale cobrar cachê do próprio squad.']
 },
 geral: {
  titulo: 'Um ajuste de cada vez',
  dicas: [
   'Antes da próxima sessão, escolha uma habilidade e uma meta observável para treinar. Evite tentar corrigir tudo na mesma noite.',
   'Ao rever uma morte, procure uma decisão que estava sob seu controle e teste uma alternativa na sessão seguinte.',
   'Em equipe, combinem chamadas curtas para localização, alvo e intenção. Informação útil vale mais que falar o tempo todo.',
   'Faça uma pausa quando perceber que começou a repetir decisões ruins por frustração. Depois retome com uma meta simples.',
   'Use médias para acompanhar tendências, mas consulte uma partida real antes de concluir por que um número mudou.',
   'Anote o que você treinou e compare após um conjunto de partidas. O objetivo é aprender algo que consiga repetir.'
  ],
  zoeira: ['A planilha ajuda, mas não segura o spray por você.', 'O segredo da pamonha ainda exige entrar na partida.', 'A resenha está em dia. Agora vamos atualizar o treino.']
 }
};
