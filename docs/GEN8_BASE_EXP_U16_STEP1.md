# Gen 8 — experiência-base de 16 bits

## Problema

O `struct SpeciesInfo` de Emerald armazenava `expYield` em `u8`. No conjunto de 512 espécies novas (#387–898), 105 usam valores acima de 255; copiar esses valores para o campo anterior truncaria os dados.

## Alteração

O campo `expYield` agora é `u16`. Os offsets dos campos seguintes foram atualizados, e uma asserção exige que `sizeof(struct SpeciesInfo)` permaneça em 0x1E bytes com o sistema de três slots de habilidade já aplicado.

Não é uma alteração de armazenamento de Pokémon: `SpeciesInfo` é uma tabela constante do jogo. O tamanho de `BoxPokemon` e dos registros de party/PC/creche não é alterado por esta mudança.

## Limite do cálculo de batalha

A fórmula atual calcula a recompensa bruta como:

`expYield * level / 7`

O maior valor do conjunto Gen 4–8 é 390, na espécie #531 Audino. No nível 100, isso resulta em 5.571 pontos, dentro do acumulador `u16` usado pelo sistema de batalha.

O ledger calcula esse limite para cada espécie. Um valor de `expYield` que caiba em `u16`, mas produza uma recompensa de nível 100 maior que 65.535, recebe o bloqueio `max_level_exp_reward_exceeds_battle_u16`. Assim, ampliar o campo da espécie não esconde um possível overflow no cálculo seguinte.

## Testes

- Verifica o tipo `u16`, os offsets seguintes e o tamanho final de SpeciesInfo.
- Aceita o valor de 300, que antes era incompatível.
- Confere o limite superior de 65.535 para o campo.
- Rejeita valores acima de 65.535.
- Calcula a recompensa máxima de nível 100 e marca quando o acumulador de batalha não comporta o resultado.
- Atualiza a auditoria de compatibilidade para informar 0x1E bytes e três slots de habilidade.

## Limites

Esta mudança remove o bloqueio de largura de `expYield` para os dados atuais. Não ativa as espécies novas em `gSpeciesInfo`, não aloca IDs de produção e não conclui a integração dos tipos, habilidades, itens, movimentos, evoluções, cries ou gráficos.
