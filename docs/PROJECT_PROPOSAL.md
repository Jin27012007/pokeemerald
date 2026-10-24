# Projeto — Pokémon Lilycove: foco em Contests

## Proposta confirmada pelo usuário

- A base técnica é Pokémon Emerald decompilado (`pret/pokeemerald`), não Quetzal.
- O foco principal da experiência serão os Pokémon Contests; eles serão a progressão principal da aventura.
- O protagonista chega de barco ao porto de Lilycove e é recebido pela mãe. A família está se mudando da casa do pai, em outra região; esse contexto pode existir sem precisar dominar a história.
- Depois da chegada, protagonista e mãe vão para a nova casa em Lilycove.
- Toda a aventura jogável deve acontecer em Lilycove; interiores e subáreas conectados à cidade podem fazer parte desse espaço.
- A cidade terá algumas casas a mais, com pelo menos uma interação em cada uma.
- A casa do jogador será personalizável: móveis, bonecos, troféus e outros objetos decorativos.
- A cidade deve parecer viva, com rotinas de NPCs e interações.
- Haverá cultivo/plantio e vários minijogos diferentes para produzir Pokéblocks.
- A progressão será dividida em temporadas. Com o avanço do tempo/temporada, novos treinadores coordenadores chegam à cidade e passam a competir.
- O desenvolvimento deve começar pequeno e crescer em etapas verificáveis. A visão de longo prazo não significa implementar todos os sistemas de uma vez.
- Até esta proposta, não foram autorizadas mudanças de gameplay. Este documento é planejamento; não modifica a ROM.

## Princípios de design

### 1. Contests como progressão principal
Os Contests serão o eixo que dá estrutura à aventura. O jogador participa, melhora seu desempenho, recebe reconhecimento/recompensas e encontra novos rivais conforme as temporadas avançam. A mecânica existente de Emerald deve ser estudada e reaproveitada antes de se considerar uma reescrita. A forma exata de aprofundar categorias, condições, apelos, pontuação e recompensas ainda precisa ser desenhada.

### 2. Temporadas e coordenadores visitantes
Cada temporada representa uma nova etapa da vida competitiva de Lilycove. Novos coordenadores chegam à cidade, ampliando o elenco de rivais e as possibilidades de competição. Antes de implementar, será necessário definir o que inicia/finaliza uma temporada, como o tempo avança, quantos rivais aparecem e como o jogo registra resultados e desbloqueios. A primeira versão pode usar progressão por marcos claros, em vez de depender de um relógio complexo.

### 3. Casa do jogador
A casa será uma base pessoal e um espaço de expressão: móveis, bonecos, troféus e outros itens visuais. A personalização é uma meta importante, mas deve ser introduzida depois de existir uma estrutura mínima estável de progressão e inventário/estado. Primeiro pode haver uma interação simples com um expositor ou espaço de troféus; um sistema livre de posicionamento de móveis é um recurso mais complexo e deve ser avaliado separadamente.

### 4. Cidade habitada
As novas casas e os interiores devem ter uma razão para existir: personagens, diálogos, pequenos serviços, pistas, atividades ou mudanças entre temporadas. As rotinas dos NPCs podem começar com mudanças simples de posição/diálogo acionadas por eventos, sem exigir um simulador de vida completo.

### 5. Cultivo e Pokéblocks
Plantio e minijogos de Pokéblocks devem apoiar a preparação para os Contests, dando ao jogador formas diferentes de desenvolver seus Pokémon. O sistema deve ser planejado para não virar uma tarefa repetitiva obrigatória. Primeiro será preciso mapear berries, condição dos Pokémon e o sistema existente de Pokéblocks; depois, escolher um minijogo pequeno como protótipo antes de criar uma coleção inteira.

### 6. Escopo controlado
A visão final é ampla, mas a implementação começa com uma fatia vertical pequena e jogável. Cada etapa deve ter um objetivo concreto, build automatizada e teste manual no emulador quando possível. Não criar todos os sistemas em paralelo.

## O que o código existente já oferece

- `data/maps/LilycoveCity/map.json`: mapa principal com 22 objetos, 14 warps, 13 eventos de fundo e 2 conexões de mapa (Route 121 e Route 124). O snapshot atual não tem eventos de coordenada nesse mapa.
- `data/maps/LilycoveCity/scripts.inc`: scripts da cidade, incluindo transição/entrada e interações com moradores. O script de transição atual altera estado relacionado ao Contest Hall, portanto precisa ser revisto cuidadosamente antes de qualquer mudança no fluxo de contests.
- `data/maps/LilycoveCity_Harbor/map.json` e `scripts.inc`: porto existente, com 5 objetos e 2 warps; já contém fluxo relacionado ao ferry/embarcações. É um ponto de partida natural para a cena de chegada, mas o fluxo de ferry existente não deve ser confundido com uma cena de prólogo.
- `data/maps/LilycoveCity_ContestHall/map.json` e `scripts.inc`: Contest Hall existente, com 32 objetos e 4 warps, incluindo NPCs e scripts relacionados a contests.
- O motor de contests existente está distribuído entre `src/contest.c`, `src/contest_util.c`, `src/contest_ai.c`, `src/contest_effect.c`, `src/contest_link.c`, `src/contest_painting.c` e headers associados. A primeira estratégia deve ser reutilizar e adaptar o sistema existente antes de pensar em reescrevê-lo.
- `src/overworld.c`: o fluxo de novo jogo chama `NewGameInitData()` e configura `gFieldCallback = ExecuteTruckSequence` em `CB2_NewGame`. Isso confirma que a abertura atual está integrada ao ciclo de inicialização do jogo. A cena de chegada deve ser planejada com cuidado para substituir ou redirecionar a abertura sem deixar flags, warp inicial ou estado do jogador inconsistentes.
- `include/constants/flags.h`, `include/constants/vars.h`, `data/scripts/new_game.inc`, os scripts de mapas e o sistema de warp/save precisam ser rastreados para mudanças de início e progressão.
- Para cultivo e Pokéblocks, será necessário rastrear os sistemas de berries, condições de Contest, Pokéblocks e bag/inventário antes de propor uma integração.

## Plano técnico por etapas

### Etapa 0 — Especificação e auditoria (atual)
- Mapear o ciclo de um Contest, incluindo registro, rank/categoria, seleção do Pokémon, condição, rodada de apelos, IA, resultado, prêmios e retorno ao mapa.
- Identificar os dados persistentes já disponíveis para temporadas, rivais e progresso antes de adicionar flags/vars.
- Rastrear a inicialização de novo jogo, a sequência do caminhão, o warp inicial, a escolha de personagem, a inicialização de flags/vars e o save.
- Mapear todas as conexões e pontos de fuga para outras cidades/rotas, incluindo ferry, Fly, Teleport, Dig/Escape Rope e destinos de derrota/whiteout.
- Desenhar um primeiro ciclo jogável pequeno e validar seu escopo antes de alterar gameplay.

### Etapa 1 — Chegada e casa inicial
- Redirecionar o início para o porto, com chegada de barco e recepção pela mãe.
- Fazer a cena acontecer uma única vez e encaminhar o jogador para a nova casa.
- Confirmar como o jogador recebe o primeiro Pokémon/equipe; essa decisão ainda está em aberto.
- Verificar party, itens, dinheiro, Pokédex, relógio, warp de retorno, save/load e reentrada no porto.
- Manter a personalização da casa para uma etapa posterior, salvo uma interação simples que sirva ao protótipo.

### Etapa 2 — Primeiro ciclo de Contest
- Reutilizar o sistema existente para entregar uma primeira progressão completa e simples.
- Definir uma meta inicial, rivais limitados e recompensa clara.
- Registrar progresso sem criar um sistema de temporada complexo antes de demonstrar que o ciclo básico funciona.
- Compilar e testar a inscrição, a competição, o resultado e a persistência do progresso.

### Etapa 3 — Temporadas e elenco de coordenadores
- Definir gatilhos de passagem de temporada e a chegada de novos coordenadores.
- Introduzir novos rivais em pequenos grupos e testar o estado de cada um, seus diálogos e a disponibilidade de competições.
- Evitar depender de relógio real até que exista uma decisão explícita sobre como o tempo funciona.

### Etapa 4 — Preparação para Contests
- Auditar berries, Pokéblocks e condições dos Pokémon.
- Implementar primeiro uma atividade de plantio ou um minijogo de Pokéblocks como protótipo, não os dois sistemas completos de uma vez.
- Medir se a recompensa da atividade afeta os Contests de maneira compreensível e equilibrada.

### Etapa 5 — Cidade viva e expansão
- Adicionar casas/interiores com interações específicas.
- Introduzir rotinas simples de NPCs e alterações de falas/eventos por progresso ou temporada.
- Expandir atividades, serviços e o elenco conforme o ciclo principal se mostrar estável.

### Etapa 6 — Personalização da casa
- Começar por exibição de troféus e alguns objetos pré-definidos.
- Avaliar depois a colocação livre de móveis, bonecos e outros itens, incluindo como salvar posição, impedir sobreposição e lidar com limites de tiles/objetos.
- Não prometer posicionamento totalmente livre antes de testar as limitações técnicas do engine de mapas.

## Riscos técnicos a controlar

- **Abertura:** o início atual usa um callback dedicado à sequência do caminhão. Redirecionar o mapa inicial sem rastrear toda a sequência pode deixar o jogador em posição incorreta ou executar scripts errados.
- **Flags e vars:** o jogo original pressupõe que eventos de história de várias regiões podem acontecer. Estados não usados precisam ser tratados com cuidado; reutilizar flags com significado original pode criar conflitos.
- **Contests:** o script de transição de Lilycove atualmente ajusta estado de Contest Hall. Alterações de calendário, disponibilidade ou repetição podem interferir no motor existente.
- **Temporadas:** a chegada de rivais e a disponibilidade de eventos precisam ser persistentes e previsíveis, inclusive depois de salvar/carregar.
- **Mundo fechado:** bloquear somente as duas conexões do mapa principal é insuficiente. Portos, interiores, warp de cura/derrota, habilidades de deslocamento e scripts de NPC podem levar para fora da área pretendida.
- **Save compatibility:** mudanças em structs de save devem ser evitadas até que seja demonstrado que flags/vars existentes não bastam. Se forem inevitáveis, exigem análise separada de compatibilidade.
- **Casa personalizável:** posicionamento de móveis pode exigir um sistema próprio de estado e renderização, dependendo das limitações dos mapas; começar com exibição de objetos pré-definidos reduz risco.
- **Validação:** GitHub Actions comprova compilação e geração de ROM, não funcionamento em jogo. A abertura e cada loop de Contest precisam de teste manual no emulador.

## Decisões ainda em aberto

1. Como o jogador recebe o primeiro Pokémon: já chega com um, escolhe entre opções em Lilycove ou recebe um parceiro específico?
2. O jogo terá batalhas Pokémon tradicionais fora dos Contests? Se sim, elas servem para treino, história ou outro propósito?
3. A passagem de temporada acontece depois de um número de competições, ao atingir uma meta ou por outro gatilho? A proposta inicial é usar marcos de progresso para manter o sistema controlável.
4. As regras originais de Contest serão mantidas no primeiro protótipo ou já há alguma alteração prioritária desejada?
5. Quais interiores/serviços originais de Lilycove devem permanecer? Quais saídas e transportes serão removidos ou reaproveitados como ambientação?
6. O relógio do jogo deve afetar as rotinas dos NPCs e o cultivo, ou as mudanças serão guiadas principalmente por progresso/temporada?
7. Para a primeira versão da casa, basta expor troféus e alguns objetos escolhidos, ou personalização com colocação livre é indispensável desde o começo?
8. Para plantio e Pokéblocks, existe alguma atividade que você imagina primeiro, ou devemos pesquisar as opções técnicas e propor um protótipo pequeno?

## Critério para começar a implementação

Antes de tocar no código jogável, fechar as decisões que afetam arquitetura e aprovar uma primeira fatia vertical: chegada → casa → preparação simples → primeiro Contest → resultado/recompensa. Implementar em mudanças pequenas na branch `lilycove/development`, revisar cada diff, compilar e testar a ROM no emulador. A branch `master` permanece como base estável.
