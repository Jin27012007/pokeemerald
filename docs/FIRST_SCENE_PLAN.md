# Primeira cena jogável — Lilycove

## Objetivo
Substituir a abertura inicial de Hoenn por uma chegada a Lilycove, a mudança para a casa nova e a preparação para adotar o primeiro Pokémon. Esta etapa não implementa ainda o sistema completo de adoção, as temporadas ou a progressão de Concursos.

## Implementação atualmente presente na branch
- `CB2_NewGame()` mantém a inicialização normal do save, mas não chama a animação do caminhão.
- `NewGameInitData()` chama `WarpToLilycoveOpening()`, que zera `VAR_LILYCOVE_OPENING_STATE` e inicia no interior do porto de Lilycove.
- O porto usa uma tabela `MAP_SCRIPT_ON_FRAME_TABLE` para disparar o diálogo da chegada apenas quando o estado é zero. A cena então esconde a mãe do porto e faz o warp para `LilycoveCity_House4`.
- House4 é a casa da família nesta versão. O script de primeira entrada apresenta a mudança, e a mãe usa o gráfico existente `OBJ_EVENT_GFX_MOM`.
- O presente está representado por um objeto de chão `OBJ_EVENT_GFX_ITEM_BALL`. Ao abri-lo, o jogador recebe cinco Poké Bolas e o item-chave `ITEM_ADOPTION_CARD`.
- `ITEM_ADOPTION_CARD` já tem definição, descrição e ícone reutilizado de um recurso existente (ícone do passe de Concurso). Não foi criado um sprite artístico novo para o cartão.
- O script do presente agora verifica espaço na bolsa para os dois itens antes de conceder qualquer recompensa; isso evita receber Poké Bolas repetidamente caso a bolsa esteja cheia e o cartão não caiba.
- O porto continua com seus eventos de ferry existentes; o novo diálogo foi adicionado sem substituir os scripts de atendimento do ferry.
- `VAR_LILYCOVE_OPENING_STATE` acompanha três etapas: 0 = primeira chegada, 1 = chegada à casa vista, 2 = presente/cartão recolhido.

## O que ainda não está completo
- O cartão ainda é um item-chave preparatório. A interação de adoção no Safari Zone, incluindo a lista de Pokémon disponível e a entrega do Pokémon escolhido, ainda precisa ser implementada.
- A mãe e o presente usam gráficos já existentes do jogo. Não há novos sprites personalizados nesta etapa.
- O fluxo de entrada, os warps e a interação do presente ainda precisam de teste manual no emulador; uma compilação bem-sucedida não comprova que a cena está correta durante o jogo.

## Verificação técnica antes de novas alterações
Preservar `NewGameInitData()` e seus passos de inicialização; não restaurar o callback do caminhão no início novo. Manter as rotinas de ferry de Lilycove Harbor. Ao ampliar o sistema, testar: jogo novo, diálogo do porto, chegada em House4, reentrada na casa, presente com espaço livre e bolsa cheia, salvamento e retorno após desmaio.

## Próxima etapa recomendada
Implementar a interação real de adoção usando `ITEM_ADOPTION_CARD`, com uma seleção pequena e curada de espécies oficiais, e somente então produzir sprites personalizados para personagens ou objetos que realmente precisem deles.