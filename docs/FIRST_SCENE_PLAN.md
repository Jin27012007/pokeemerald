# Primeira cena jogável — Lilycove

## Objetivo desta etapa
Substituir progressivamente a abertura original de Pokémon Emerald por uma chegada narrativa a Lilycove, sem ainda implementar concursos, temporadas, cultivo ou o catálogo de Pokémon.

## Direção escolhida
- O prólogo começa com a chegada de barco ao porto de Lilycove.
- A mãe recebe o protagonista e os dois seguem para a nova casa.
- Esta primeira etapa termina na casa nova; o presente de Pokémon inicial fica para a próxima etapa.
- A implementação deve começar com scripts e mapas existentes, usando recursos temporários quando necessário.

## Descobertas confirmadas no código
- `CB2_NewGame()` em `src/overworld.c` chama `NewGameInitData()` e define `gFieldCallback = ExecuteTruckSequence`.
- `NewGameInitData()` em `src/new_game.c` inicializa o save, chama `WarpToTruck()` e executa `EventScript_ResetAllMapFlags`. A inicialização geral do save precisa ser preservada.
- `WarpToTruck()` manda para `MAP_INSIDE_OF_TRUCK`; `ExecuteTruckSequence()` em `src/field_special_scene.c` anima a cena do caminhão e libera o jogador.
- `data/maps/InsideOfTruck/scripts.inc` define `VAR_LITTLEROOT_INTRO_STATE`, o respawn e o warp dinâmico de Littleroot por gênero. A introdução antiga depende também dos scripts e objetos das casas de Littleroot.
- `data/maps/LilycoveCity_Harbor/map.json` é um interior usado pelo sistema de ferry; seus NPCs e scripts existentes não devem ser substituídos indiscriminadamente.
- Os interiores `LilycoveCity_House1` a `House4` já existem e usam entradas de warp ligadas ao mapa principal, mas House1, House2 e outras contêm habitantes/atividades originais que precisariam ser removidos ou reaproveitados deliberadamente antes de transformar um deles na casa da família.
- `VAR_LILYCOVE_CITY_STATE` está comentada como “Unused Var”, mas isso por si só não prova que é seguro reutilizá-la. Antes de adotá-la, é necessário localizar todas as referências e conferir o inventário completo de variáveis/flags.

## Escolha de mapa
Não reaproveitar o porto existente como mapa de cutscene separado nem substituir os scripts de ferry. Na implementação, preferir um ponto de chegada de roteiro que possa usar o porto sem destruir os serviços existentes, seguido por uma casa escolhida após validar layout, warps, personagens e coordenadas. O interior da casa ainda não foi definitivamente selecionado.

## Implementação técnica — ordem obrigatória
1. Encontrar as referências reais de `VAR_LITTLEROOT_INTRO_STATE`, os estados das duas casas, os callbacks do caminhão e o destino/respawn inicial. Fazer busca completa antes de alterar qualquer estado.
2. Definir um estado de introdução dedicado e confirmar que ele não conflita com variáveis ou flags já utilizadas. Se nenhum estado seguro puder ser confirmado, acrescentar uma definição própria com a contagem/limites de save revisados, em vez de reutilizar às cegas um ID marcado como não utilizado.
3. Alterar o destino do início do jogo de forma controlada, preservando todos os passos de `NewGameInitData()` que inicializam o save.
4. Implementar o primeiro segmento: jogo novo → chegada/diálogo em Lilycove → mãe conduz o jogador → warp para casa.
5. Garantir um respawn válido e testar reentrada, salvamento e retorno após desmaio/blackout antes de avançar para a cena do Pokémon inicial.
6. Compilar no branch `lilycove/development`, revisar o diff e inspecionar os logs e artefato da build.
7. Testar no emulador: jogo novo, cena de chegada, diálogo, transição à casa, saída/reentrada e salvamento. Build bem-sucedida não substitui teste de gameplay.

## Restrições
- Não apagar o roteiro original do caminhão nem os mapas/recursos de Littleroot nesta etapa.
- Não mudar a lógica de party ou Pokémon inicial antes que a chegada funcione.
- Não implementar mecânicas de Contest nesta etapa.
- Não criar sprites novos ainda; usar gráficos já existentes como placeholders se necessário.
- Não declarar a cena concluída sem build e teste manual.

## Estado atual
Apenas investigação e documentação. Nenhum arquivo de gameplay foi alterado ainda.