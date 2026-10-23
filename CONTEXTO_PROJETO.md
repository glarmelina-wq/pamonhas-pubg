# Site dos Pamonhas — contexto de continuidade

Atualizado em 23/10/2026. Repositório: https://github.com/glarmelina-wq/pamonhas-pubg
Site: https://glarmelina-wq.github.io/pamonhas-pubg/

## Objetivo e base existente
Portal do clã PUBG Steam, com foco em amigos, resenha e homenagem ao Zé da Pamonha.
HTML/JavaScript estáticos, coleta em Python 3.12, JSON e GitHub Pages.
GitHub Actions executa no minuto 17 de cada hora e por mudanças nos arquivos relevantes.
A credencial PUBG_API_KEY permanece nos Secrets do GitHub.

Existiam: rankings técnicos, modalidades, jogadores/perfis, comparação, card para compartilhar,
histórico de desempenho, dicas editoriais, nove troféus de resenha e arquivo semanal.
Estatísticas da temporada e recuperação de partidas oficiais são fontes diferentes.

## Pedido retomado
Página separada com rankings semanal e mensal de abates de headshot por sniper, DMR e demais armas.
Medalhas Cata-piolho, Dipirona ocular e Apaga-luz, com imagens.
Dicas por inventário anterior à morte e dano da zona azul. Publicar quando concluído.

## Alterações implementadas em 23/10
- headshots.html e headshots.js: página Caça ao capacete, períodos e nove recortes de modalidade,
  contagem de abates de headshot, posições compartilhadas nos empates, líderes provisórios,
  recorde numa partida e diagnóstico individual.
- medalhas/*.svg: três imagens leves; o envio da arte grande em base64 travou a interface
  do ChatGPT com Invalid conversation body. Evitar repetir esse envio.
- telemetria.py: coleta limitada, incremental, com cache; análise de eventos concluídos,
  classificação de armas, exclusão de abates em aliados, danos azul/queda, coleta e uso de itens,
  saldos estimados anteriores à morte e tratamento de eventos inconsistentes.
- atualizar_ranking.py: integra a coleta e gera telemetria_cla.json.
- index.html: link para a página nova e dicas de telemetria nos perfis.
- .github/workflows/main.yml: valida os testes e publica página, script, medalhas e relatório.
- test_telemetria.py: nove testes de categorias, contagem, duplicação, aliados, loot inicial,
  morte/retorno, ausência de dados, períodos, empates e cache. Passaram localmente e no Actions.
  Verificação JavaScript de renderização, filtros, dicas e escape de nick também passou localmente.

## Cadastro e falha anterior
jogadores_cache.json estava inválido: uma linha tinha apenas o nick de Alien, sem valor.
Isso interrompia a atualização e impedia a publicação.
A linha inválida foi retirada. Adicionados a membros_cla.txt: Alien--__-- e TODDNH0.
O ID account.* é resolvido pela API e gravado no cache; não é preciso informá-lo manualmente.
A mensagem do usuário escreveu Alien--_--, mas o arquivo editado por ele escreveu Alien--__--.
A API confirmou Alien--__-- como account.3113f7d216874e83906ee9a1c4489c6c na coleta de 23/10.

## Regras e limites mantidos
- Somente partidas normais oficiais, sem treino, evento, personalizado ou competitivo.
- Semana começa segunda-feira; mês civil; ambos America/Sao_Paulo.
- Headshots representam abates creditados na cabeça, não todos os impactos.
- Empates compartilham medalha; nenhum prêmio para zero headshots.
- Telemetria é pós-partida. Não há mochila ao vivo.
- Cobertura é parcial, inclusive na lista de partidas conhecidas; dados ausentes não são zero.
- Saldos de recursos são estimativas por eventos; morte com eventos inconsistentes é excluída
  das dicas de saldo zero. Dica de saldo zero requer três mortes avaliáveis e recorrência >=50%.
- Munição exibe coleta observada, sem inferir saldo, falta ou compatibilidade com a arma.
- Dano azul pode ser tático: sugerir revisão, sem afirmar que foi erro.
- Loot inicial com isGame=0.5 precisa ser incluído; ignorá-lo perde parte do inventário.

A telemetria usa Damage_Instant_Fall (identificador oficial de queda), e conta o uso de utilitários em LogPlayerUseThrowable sem duplicar LogItemUse.

## Fontes de verdade para retomar
Conferir estado atual da branch main e execuções do GitHub Actions, não apenas esta nota.
Commit de implementação: 5a7d86644241b6d27ddd6176a17bd3c507801ebd.
Execução inicial: https://github.com/glarmelina-wq/pamonhas-pubg/actions/runs/40017391659
A primeira coleta recuperou telemetria de 100 partidas, com 311 partidas conhecidas na semana e 1237 no mês. Cobertura cresce nas próximas atualizações. Alien foi localizado. O envio inicial grande foi substituído com sucesso por SVGs leves. Publicação da correção final confirmada com sucesso na execução https://github.com/glarmelina-wq/pamonhas-pubg/actions/runs/40018218758 (nove testes aprovados). Dano de queda já foi observado nos dados reais. A página está em https://glarmelina-wq.github.io/pamonhas-pubg/headshots.html .
O histórico das conversas foi recuperado parcialmente; a transcrição integral não estava disponível.


## Correção do filtro de mês — 23/10/2026
O botão trocava o período, mas as primeiras 100 partidas com telemetria eram todas da semana atual;
por isso, mês e semana tinham totais idênticos. A coleta passou a intercalar partidas de semanas
anteriores do mês com as da semana corrente. A interface destaca Ranking do mês/Ranking da semana,
explica a cobertura disponível e atualiza a versão do script para evitar cache antigo.
Dez testes passaram, incluindo a distribuição do backfill e o limite por execução. O teste da
interface confirmou alternância de totais, título e aviso de cobertura.
Publicação confirmada: https://github.com/glarmelina-wq/pamonhas-pubg/actions/runs/40027682260
Na conferência após publicar: semana 150 partidas e 94 abates de HS;
mês 200 partidas e 129 abates de HS, incluindo 50 partidas anteriores à semana.
A cobertura mensal permanece parcial; não representa o mês completo.


## Troféu Caneta azul e dicas diretas — 23/10/2026
Adicionado Caneta azul, azul caneta ao Hall (dez troféus): maior soma de dano recebido da
zona azul na semana ou temporada, sem média ou mínimo de partidas, com empates compartilhados.
Inclui ranking, badges dos perfis, card PNG e arquivo semanal. O total usa apenas partidas
já analisadas e mostra que a cobertura é parcial.
A temporada é confirmada pelos IDs retornados em relationships.matches* da consulta de
estatísticas da temporada, reaproveitando as consultas existentes. tag_season_matches mantém
essa confirmação no cache; partidas de temporada desconhecida ficam fora do total sazonal.
telemetria_cla.json agora contém periodos.temporada e season_id. A mudança de temporada não
herda os números da anterior. archive_blue_awards acrescenta o troféu às semanas arquivadas.
As 72 dicas em dicas.js, os textos de headshots.js e as explicações de index.html foram
simplificados: frases curtas, item ou ação explícitos, aviso breve sobre estimativas de mochila.
Doze testes passaram, incluindo temporada, isolamento entre temporadas e empates no arquivo.
Teste de interface: dez troféus, contagem por soma e alternância entre semana e temporada.
Publicação confirmada: https://github.com/glarmelina-wq/pamonhas-pubg/actions/runs/40029236801
