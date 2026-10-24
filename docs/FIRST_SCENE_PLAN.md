# Primeira cena jogável — Lilycove

## Objetivo desta etapa
Substituir progressivamente a abertura original de Pokémon Emerald por uma chegada narrativa a Lilycove, sem ainda implementar concursos, temporada, cultivo ou catálogo de Pokémon.

## Direção escolhida
- O prólogo acontece em Lilycove.
- A cena deve começar com a chegada de barco ao porto.
- A mãe recebe o protagonista; os dois seguem para a nova casa.
- A primeira etapa termina quando o jogador chega à casa nova.
- O presente com o Pokémon inicial será tratado como uma etapa separada depois que o fluxo de chegada estiver estável.

## Escolha de mapa
Usar o porto existente de Lilycove como referência visual e de localização, e reservar uma das casas existentes para ser adaptada como a casa do jogador. A escolha final da casa depende de conferir layout, conexões/warps e possibilidade de adaptar o interior sem afetar outras rotas. Não sobrescrever um interior usado por NPC sem antes decidir como o conteúdo original será reaproveitado.

## Implementação técnica — ordem obrigatória
1. Rastrear a entrada de jogo novo: `CB2_NewGame` em `src/overworld.c`, `NewGameInitData()` e `WarpToTruck()` em `src/new_game.c`, além de `ExecuteTruckSequence()` em `src/field_special_scene.c`.
2. Identificar o estado de intro original, callbacks e flags/vars usados pela abertura, pelo quarto/casa de Littleroot e pelo primeiro save/respawn. Procurar todos os usos antes de reutilizar estados.
3. Definir um estado de introdução próprio para Lilycove e um ponto de entrada controlado, preservando inicialização geral do save e evitando que as etapas antigas disparem depois.
4. Implementar apenas o primeiro segmento observável: jogo novo → cena/entrada em Lilycove → diálogo de boas-vindas → transição para a casa.
5. Compilar no branch `lilycove/development`, revisar o diff e verificar o artefato da build.
6. Testar no emulador: novo jogo, chegada à cena, diálogo, transição para casa, saída/reentrada e salvamento. Build bem-sucedida não substitui o teste de gameplay.

## Restrições
- Não apagar o roteiro original do caminhão nem os mapas/recursos originais nesta fase.
- Não mudar a lógica de Pokémon iniciais/party antes da cena de chegada funcionar.
- Não implementar novas mecânicas de Contest nesta etapa.
- Não adicionar sprites novos ainda; reutilizar gráficos existentes como placeholders quando necessário.
- Não declarar a cena concluída até haver build verificada e teste manual no emulador.

## Estado atual
Planejamento e inspeção apenas. Nenhum arquivo de gameplay foi alterado por esta etapa.
