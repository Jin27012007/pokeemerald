# Gen 8 — sistema de três slots de habilidade (fase estrutural)

## O que mudou

Emerald armazenava a escolha de habilidade como um bit: habilidade primária ou secundária. A Expansion fornece três entradas por espécie, sendo a terceira a habilidade oculta.

Esta fase adiciona suporte estrutural a três índices:

- `ABILITY_SLOT_PRIMARY = 0`
- `ABILITY_SLOT_SECONDARY = 1`
- `ABILITY_SLOT_HIDDEN = 2`

O vetor de `SpeciesInfo` agora tem `NUM_ABILITY_SLOTS == 3`. Os inicializadores existentes que informam apenas duas habilidades continuam preenchendo o terceiro slot com zero (`ABILITY_NONE`).

## Persistência do índice do Pokémon

O índice individual do Pokémon agora usa dois bits sem aumentar o tamanho de `BoxPokemon`:

- O bit baixo continua em `PokemonSubstruct3.abilityNum`.
- O bit alto usa um bit que antes fazia parte do campo público não utilizado de `BoxPokemon` (`abilityNumHigh`).

O acesso segue o caminho `MON_DATA_ABILITY_NUM`, portanto a escolha acompanha o registro do Pokémon quando ele passa por party, PC ou creche. Foram adicionadas asserções de compilação para impedir mudanças acidentais no tamanho de `BoxPokemon` (80 bytes), `PokemonSubstruct3` (12 bytes) e `BattlePokemon` (0x58 bytes).

## Batalha

`BattlePokemon` continua com o mesmo tamanho e formato de buffer. O bit baixo permanece em seu bitfield existente; o bit alto usa o bit 0 do byte reservado `unknown`. Os helpers `GetBattleMonAbilityNum` e `SetBattleMonAbilityNum` centralizam a conversão. Os quatro controladores (jogador, oponente e link) agora serializam os dois bits; a atualização de troca no núcleo de batalha recupera o índice completo. O script de IA também considera todos os slots não vazios ao estimar a habilidade de um adversário.

`GetAbilityBySpecies` agora indexa diretamente os três slots e rejeita índices fora de 0–2. `SetMonAbilitySlot` permite atribuir um slot existente a um Pokémon e rejeita slots vazios ou fora do intervalo. O Pickup agora consulta `GetMonAbility`, em vez de presumir que todo índice diferente de zero significa a segunda habilidade.

## O que ainda não está concluído

Esta mudança não importa as 150 habilidades novas ausentes do catálogo de constantes do Emerald, nem implementa seus efeitos de batalha. Também não introduz ainda uma probabilidade de habilidade oculta em encontros, criação por breeding ou outras rotas de aquisição. A API permite selecionar o terceiro slot quando a espécie já tiver esse dado; a distribuição e os comportamentos precisam de etapas próprias.

As espécies novas ainda não foram ativadas em `gSpeciesInfo`. O ledger de compatibilidade deixa de marcar o terceiro slot como estruturalmente impossível e passa a registrar a falta dos fluxos de aquisição como pendência semântica. Valores de habilidade sem constante-alvo continuam sem mapeamento; nenhum ID é adivinhado.

## Testes

O CI executa regressões que verificam os três slots, a leitura e escrita dos dois bits, a preservação do tamanho de `BattlePokemon`, a resolução do slot oculto e a correção do Pickup. A ROM moderna precisa continuar compilando com as tabelas de gameplay atuais.
