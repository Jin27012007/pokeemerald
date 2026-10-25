# Primeira cena jogável — Lilycove

## Objetivo
Substituir a abertura inicial de Hoenn por uma chegada a Lilycove, a mudança para a casa nova e a preparação para adotar o primeiro Pokémon. Esta etapa não implementa ainda o sistema completo de adoção, as temporadas ou a progressão de Concursos.

## Implementação atualmente presente na branch
- `CB2_NewGame()` mantém a inicialização normal do save, mas não chama a animação do caminhão.
- `NewGameInitData()` chama `WarpToLilycoveOpening()`, que zera `VAR_LILYCOVE_OPENING_STATE` e inicia no interior do porto de Lilycove.
- O porto usa uma tabela `MAP_SCRIPT_ON_FRAME_TABLE` para disparar o diálogo da chegada apenas quando o estado é zero. A cena então esconde a mãe do porto e faz o warp para `LilycoveCity_House4`.
- House4 é a casa da família nesta versão. O script de primeira entrada apresenta a mudança, e a mãe usa o gráfico existente `OBJ_EVENT_GFX_MOM`.
- O presente está representado por um objeto de chão `OBJ_EVENT_GFX_ITEM_BALL`. Ao abri-lo, o jogador recebe cinco Poké Bolas e o item-chave `ITEM_ADOPTION_CARD`.
- `ITEM_ADOPTION_CARD` tem definição, descrição e ícone próprio de pixel art em 24×24 pixels (`graphics/items/icons/adoption_card.png`), com paleta dedicada.
- O script do presente agora verifica espaço na bolsa para os dois itens antes de conceder qualquer recompensa; isso evita receber Poké Bolas repetidamente caso a bolsa esteja cheia e o cartão não caiba.
- O porto continua com seus eventos de ferry existentes; o novo diálogo foi adicionado sem substituir os scripts de atendimento do ferry.
- `VAR_LILYCOVE_OPENING_STATE` acompanha três etapas: 0 = primeira chegada, 1 = chegada à casa vista, 2 = presente/cartão recolhido.

## O que ainda não está completo
- A interação de adoção no Safari Zone oferece Skitty, Eevee ou Vulpix no nível 5, entrega ao grupo ou ao PC se houver espaço, consome o cartão somente após a entrega e bloqueia uma segunda adoção.
- A mãe, o objeto do presente e o atendente usam gráficos existentes do jogo. O cartão tem um ícone personalizado; um sprite de personagem personalizado ainda não foi criado.
- O fluxo de entrada, os warps e a interação do presente ainda precisam de teste manual no emulador; uma compilação bem-sucedida não comprova que a cena está correta durante o jogo.

## Verificação técnica antes de novas alterações
Preservar `NewGameInitData()` e seus passos de inicialização; não restaurar o callback do caminhão no início novo. Manter as rotinas de ferry de Lilycove Harbor. Ao ampliar o sistema, testar: jogo novo, diálogo do porto, chegada em House4, reentrada na casa, presente com espaço livre e bolsa cheia, salvamento e retorno após desmaio.

## Próxima etapa recomendada
Testar manualmente a chegada, a retirada do presente e a adoção no emulador. Depois, criar um sprite personalizado para o atendente se isso melhorar a leitura visual da área.

## Ajuste da rota inicial — 2026-10-25
- A chegada inicial continua no porto e o script de abertura faz a transição para a cidade; a casa da família continua sendo acessada pelo warp normal `MAP_LILYCOVE_CITY_HOUSE4` no índice 11 do mapa da cidade.
- Foi adicionada uma nota de manutenção no script do porto para explicitar que a rota inicial deve permanecer a pé e que os scripts de ferry não devem ser substituídos por essa sequência.
- O script ainda usa o warp atual para `MAP_LILYCOVE_CITY` nas coordenadas `(12, 33)`. Não alterar esse destino para House4 diretamente sem validar a cena desejada: isso pularia a rua e a entrada pela porta.
- Validação automática parcial: `LilycoveCity/map.json` e `LilycoveCity_House4/map.json` declaram a ligação de saída de House4 para o warp 11 da cidade e o warp 11 aponta de volta para House4. A compilação e o teste real no My Boy! ainda são necessários.
