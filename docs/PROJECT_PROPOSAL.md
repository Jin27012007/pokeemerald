# Projeto — Pokémon Lilycove: foco em Contests

## Proposta confirmada pelo usuário

- A base técnica é Pokémon Emerald decompilado (`pret/pokeemerald`), não Quetzal.
- O foco principal da experiência serão os Pokémon Contests.
- O protagonista começa chegando de barco ao porto de Lilycove.
- A mãe do protagonista o recebe na chegada.
- Toda a aventura jogável deve acontecer em Lilycove; os interiores e subáreas conectados à cidade podem fazer parte desse espaço.
- A cidade deve parecer viva, detalhada e reativa, compensando a escala geográfica reduzida.
- Até esta proposta, não foram autorizadas mudanças de gameplay. Este documento é planejamento; não modifica a ROM.

## O que o código existente já oferece

- `data/maps/LilycoveCity/map.json`: mapa principal com 22 objetos, 14 warps, 13 eventos de fundo e 2 conexões de mapa (Route 121 e Route 124). O snapshot atual não tem eventos de coordenada nesse mapa.
- `data/maps/LilycoveCity/scripts.inc`: scripts da cidade, incluindo transição/entrada e interações com moradores. O script de transição atual altera estado relacionado ao Contest Hall, portanto precisa ser revisto cuidadosamente antes de qualquer mudança no fluxo de contests.
- `data/maps/LilycoveCity_Harbor/map.json` e `scripts.inc`: porto existente, com 5 objetos e 2 warps; já contém fluxo relacionado ao ferry/embarcações. É um ponto de partida natural para a cena de chegada, mas o fluxo de ferry existente não deve ser confundido com uma cena de prólogo.
- `data/maps/LilycoveCity_ContestHall/map.json` e `scripts.inc`: Contest Hall existente, com 32 objetos e 4 warps, incluindo NPCs e scripts relacionados a contests.
- O motor de contests existente está distribuído entre `src/contest.c`, `src/contest_util.c`, `src/contest_ai.c`, `src/contest_effect.c`, `src/contest_link.c`, `src/contest_painting.c` e headers associados. A primeira estratégia deve ser reutilizar e adaptar o sistema existente antes de pensar em reescrevê-lo.
- `src/overworld.c`: o fluxo de novo jogo chama `NewGameInitData()` e configura `gFieldCallback = ExecuteTruckSequence` em `CB2_NewGame`. Isso confirma que a abertura atual está integrada ao ciclo de inicialização do jogo. A cena de chegada deve ser planejada com cuidado para substituir ou redirecionar a abertura sem deixar flags, warp inicial ou estado do jogador inconsistentes.
- `include/constants/flags.h`, `include/constants/vars.h`, `data/scripts/new_game.inc`, os scripts de mapas e o sistema de warp/save precisam ser rastreados para mudanças de início e progressão.

## Direção de design inicial (sem decisões inventadas)

A estrutura proposta tem quatro pilares:

1. **Chegada e acolhimento:** nova abertura no porto, chegada de barco e encontro inicial com a mãe. A cena deve estabelecer por que o protagonista veio para Lilycove e encaminhar o jogador para a primeira atividade. A motivação e os detalhes do diálogo ainda não foram definidos.
2. **Cidade como espaço principal:** usar a cidade, o porto, o Contest Hall e os interiores conectados como uma rede de áreas exploráveis. As saídas para rotas ou regiões externas precisam ser removidas, bloqueadas ou redirecionadas de maneira consistente, sem deixar warps quebrados ou NPCs que prometem viagens indisponíveis.
3. **Contests como loop central:** preservar inicialmente as regras e o fluxo do motor existente; identificar quais partes já funcionam e quais precisam de progressão, variedade, recompensas ou apresentação específicas para sustentar a campanha. Não alterar regras de pontuação ou categorias até a proposta detalhada indicar o que deve mudar.
4. **Cidade viva:** interações de moradores, rotinas/posições de NPCs, pequenos eventos, serviços e mudanças por progresso podem tornar a cidade dinâmica. Quais sistemas concretos serão adicionados, com que frequência e com que impacto, ainda dependem das decisões do usuário.

## Plano técnico de implementação

### Fase 1 — Definição e rastreamento
- Definir o escopo exato de “toda a ROM se passa em Lilycove”: quais interiores e subáreas continuam acessíveis e quais saídas deixam de existir.
- Mapear todas as conexões e pontos de fuga para outras cidades/rotas, além de ferry, Fly, Teleport, Dig/Escape Rope, respawn após derrota e outros warps globais.
- Rastrear a inicialização de novo jogo, `ExecuteTruckSequence`, warp inicial, criação de personagem, escolha de nome/gênero, inicialização de flags/vars e script de abertura.
- Rastrear a jornada de um Contest do início ao fim: registro, seleção de categoria/rank, escolha de Pokémon, rodada de condição/apelo, IA dos rivais, resultados, prêmios, pinturas e retorno ao mapa.
- Auditar scripts atuais do Contest Hall e o uso de `VAR_CONTEST_HALL_STATE`/flags de estado de contest antes de mudar a progressão.
- Produzir uma lista precisa de arquivos/símbolos a alterar, riscos e testes. Nenhuma mudança de gameplay até esse plano ser revisto.

### Fase 2 — Protótipo mínimo da abertura
- Redirecionar o novo jogo para o porto, de forma que o jogador apareça no local correto e a cena seja executada uma única vez.
- Adicionar a recepção pela mãe usando evento/NPC e flags apropriadas, evitando que a cena se repita ao reentrar no porto.
- Conferir inicialização de party, itens, dinheiro, Pokédex, relógio, warp de retorno e estado de save.
- Compilar e testar início de jogo novo, save/load e reentrada no porto.

### Fase 3 — Lilycove como mundo fechado
- Revisar as conexões do mapa principal e todas as saídas internas/externas.
- Adaptar serviços e NPCs para que nenhuma interação ofereça uma saída impossível ou dependa de progresso de regiões que não existem no jogo.
- Revisar destinos de derrota/whiteout, Fly/Teleport/Dig e quaisquer outros sistemas de deslocamento para evitar softlocks.
- Testar cada entrada e saída da cidade e dos interiores.

### Fase 4 — Progressão centrada em Contests
- Definir a progressão principal, metas e recompensas com o usuário.
- Reutilizar o motor de contests e alterar apenas o que a proposta pedir.
- Garantir que vitórias, derrotas, mudanças de rank e recompensas sejam persistentes e testáveis.
- Testar todas as categorias/ranks e estados de progresso que forem mantidos.

### Fase 5 — Cidade viva e detalhada
- Planejar atividades e interações por área, horário, progresso ou eventos, conforme decisões futuras.
- Priorizar eventos pequenos e reativos que reutilizem scripts, flags e vars existentes quando apropriado.
- Evitar encher a cidade de NPCs estáticos sem propósito; cada adição deve contribuir para atmosfera, serviços, história ou loop de contests.
- Validar colisões, caminhos, warps, objetos, falas e estados de reentrada.

## Riscos técnicos a controlar

- **Abertura:** o início atual usa um callback dedicado à sequência do caminhão. Redirecionar o mapa inicial sem rastrear toda a sequência pode deixar o jogador em posição incorreta ou executar scripts errados.
- **Flags e vars:** o jogo original pressupõe que eventos de história de várias regiões podem acontecer. Estados não usados precisam ser tratados com cuidado; reutilizar flags com significado original pode criar conflitos.
- **Contests:** o script de transição de Lilycove atualmente ajusta estado de Contest Hall. Alterações de calendário, disponibilidade ou repetição podem interferir no motor existente.
- **Mundo fechado:** bloquear somente as duas conexões do mapa principal é insuficiente. Portos, interiores, warp de cura/derrota, habilidades de deslocamento e scripts de NPC podem levar para fora da área pretendida.
- **Save compatibility:** mudanças em structs de save devem ser evitadas até que seja demonstrado que flags/vars existentes não bastam. Se forem inevitáveis, exigem análise separada de compatibilidade.
- **Validação:** GitHub Actions comprova compilação e geração de ROM, não funcionamento em jogo. A abertura e cada loop de contest precisam de teste manual no emulador.

## Decisões em aberto antes de codificar

1. A mãe acompanha o protagonista durante a aventura ou aparece só na chegada e em alguns eventos?
2. O jogador começa com um Pokémon e equipe como no jogo original, recebe um parceiro inicial em Lilycove ou escolhe entre opções? Ainda não definido.
3. A progressão será uma história com objetivos e personagens centrais, uma carreira de competidor livre, ou uma combinação?
4. Os contests mantêm exatamente categorias/ranks/regras de Emerald ou terão modificações específicas?
5. Haverá batalhas Pokémon tradicionais fora dos contests? Se sim, onde e com qual função?
6. O que deve acontecer com os edifícios/serviços originais de Lilycove (lojas, casas, museu/áreas secundárias, porto e demais interiores)? Quais são essenciais?
7. O tempo e a cidade mudam com relógio real, horários do jogo, progresso da história, ou não haverá sistema de rotina?
8. Quais sistemas de transporte/viagem devem desaparecer, permanecer como ambientação ou ser reaproveitados dentro da cidade?

## Critério para começar a implementação

Antes de tocar no código jogável, confirmar as decisões acima que afetam arquitetura, aprovar o fluxo inicial e a progressão de contests, e então dividir a implementação em mudanças pequenas. A cada etapa: conferir o diff, compilar e testar a ROM em emulador. A branch de trabalho continua sendo `lilycove/development`; `master` permanece como base estável.
