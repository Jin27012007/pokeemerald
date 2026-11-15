# Integração Gen 8 — fase 2: campos de espécie e slots de habilidade

## O que mudou

A ROM passa a ter estrutura suficiente para representar os três slots de habilidade da fonte e valores de experiência-base maiores que 255.

### SpeciesInfo

- `abilities[2]` foi ampliado para `abilities[3]`.
- `expYield` foi ampliado de `u8` para `u16`; os registros com valor acima de 255 deixam de sofrer truncamento.
- O tamanho esperado de `struct SpeciesInfo` passa de 26 para 30 bytes.
- Os IDs de habilidade no Emerald continuam sendo IDs locais de 8 bits.

### Pokémon armazenado e em batalha

- O seletor `abilityNum` passou de 1 para 2 bits em `PokemonSubstruct3`. O segundo bit reutiliza um bit reservado de ribbons; o substruct continua com 12 bytes, sem aumentar cada Pokémon armazenado.
- Em `BattlePokemon`, o seletor usa o byte anteriormente não utilizado em `0x23`, preservando os offsets seguintes.
- Um slot vazio ou um índice fora do intervalo retorna a primeira habilidade, em vez de ler uma posição inválida.
- `SetBoxMonAbilityNum` e `SetMonAbilityNum` permitem selecionar explicitamente os slots 0, 1 ou 2, desde que o slot exista para a espécie.
- A criação normal continua escolhendo entre os dois slots regulares; esta alteração não distribui habilidade oculta aleatoriamente. Sistemas de captura, criação e eventos poderão escolher o slot oculto explicitamente.

### Catálogo de habilidades

Foram adicionadas 165 constantes locais para as habilidades usadas pelas 512 espécies novas, com IDs Emerald de 78 a 242. Os IDs originais da Expansion não são copiados para o runtime. Nomes e descrições foram importados do snapshot fixado `rh-hideout/pokeemerald-expansion@c460a8661dfa0598ae25d42a968c690ecbf489c6`.

Os nomes foram limitados a 12 caracteres para respeitar `ABILITY_NAME_LENGTH` do Emerald. Descrições condicionais da fonte usam o primeiro texto da condição no snapshot. Isso é texto de interface; não significa que os efeitos de batalha tenham sido portados.

## O que ainda não está pronto

- Os 165 efeitos novos de habilidade ainda precisam de implementação e testes de batalha. Ter constante, nome e descrição não torna a habilidade funcional.
- A lógica de criação normal ainda não escolhe habilidade oculta. A API explícita de seleção já existe, mas precisa ser ligada aos métodos de captura, distribuição e criação que deverão oferecer esse slot.
- Fairy ainda não está implementado na tabela de tipos.
- Os 23 itens sem constante/registro, os movimentos ausentes, evoluções, gráficos e cries continuam pendentes.
- As espécies #387–898 continuam fora de `gSpeciesInfo`; esta fase prepara o layout e os IDs de habilidade, sem alocar IDs internos de espécies.

## Saves

O projeto será tratado como uma ROM nova. Não será desenvolvido um migrador para saves antigos. Os campos internos continuam dimensionados e testados para a nova estrutura; apenas a compatibilidade retroativa com saves de versões anteriores deixa de ser requisito.

## Validação

O CI testa:
- dois bits para o seletor de habilidade no Pokémon armazenado e no Pokémon de batalha;
- três slots na SpeciesInfo;
- `expYield` de 16 bits;
- seleção segura de slot e fallback;
- IDs de habilidade únicos e dentro de 8 bits;
- nomes e descrições para as 165 habilidades importadas.

A compilação moderna do jogo continua sendo a validação final desta fase. O ledger de compatibilidade segue como staging até que os efeitos de batalha e os demais sistemas estejam prontos.
