# Auditoria técnica — Expansão da Pokédex até a Geração 8

Branch auditada: `lilycove/development`

## Escopo
O usuário aprovou todas as 898 espécies nacionais das Gerações 1–8. O motor de batalha CFRU não será importado; o sistema de Concursos Emerald será preservado.

## Achados confirmados no código

### 1. IDs internos atuais
Em `include/constants/species.h`, as espécies jogáveis terminam em `SPECIES_CHIMECHO 411`, seguidas de `SPECIES_EGG 412`. `NUM_SPECIES` é definido como `SPECIES_EGG`. Portanto, a tabela interna atual é essencialmente o conjunto de espécies de Gen 1–3 de Emerald, não uma faixa que comporte 898 espécies.

O mesmo arquivo reserva identificadores de Unown adicionais após `NUM_SPECIES`; essa convenção precisa ser preservada ou redesenhada com cuidado ao expandir a enumeração.

### 2. Save/Pokédex
Em `include/global.h`:
- `NUM_DEX_FLAG_BYTES` é calculado a partir de `NUM_SPECIES`.
- `struct Pokedex` armazena arrays `owned` e `seen` com esse tamanho.

A expansão de `NUM_SPECIES` aumenta o espaço reservado para flags na struct persistida. É obrigatório verificar tamanho/offsets do save, compatibilidade de saves existentes e checksums antes de mudar o valor.

### 3. Tabela de metadados
`src/data/pokemon/species_info.h` define `gSpeciesInfo[]` e atualmente contém entradas para as espécies do conjunto existente. Cada nova espécie exige metadados completos no formato da struct `SpeciesInfo`; esses campos também são usados pelo engine fora de batalhas.

### 4. Evoluções e learnsets
`src/data/pokemon/evolution.h` declara `gEvolutionTable[NUM_SPECIES][EVOS_PER_MON]`.
`src/data/pokemon/level_up_learnsets.h` contém learnsets específicos por espécie.
A adição de espécies requer entradas coerentes, mesmo que parte do conteúdo só seja usada em sistemas secundários.

### 5. Pokédex nacional e regional
`include/constants/pokedex.h` define IDs nacionais em enumeração e também a Pokédex de Hoenn.
`src/data/pokemon/pokedex_entries.h` contém entradas nacionais individuais.
`src/data/pokemon/pokedex_orders.h` contém tabelas de ordenação, incluindo alfabética e nacional.
`src/pokedex.c` dimensiona `pokedexList` com `NATIONAL_DEX_COUNT + 1` e percorre essa faixa. A interface e seus contadores/recursos gráficos precisam ser revisados para 898.

### 6. Conversões de espécie
`src/pokemon.c` contém tabelas de conversão entre IDs de espécie e números nacional/Hoenn, como arrays dimensionados por `NUM_SPECIES - 1`. Essas tabelas precisam cobrir a nova faixa sem deslocar índices antigos inadvertidamente.

### 7. Tela de resumo e concursos
`src/pokemon_summary_screen.c` implementa páginas separadas de movimentos de batalha e de concurso. O fluxo de concurso não é removido pela decisão de não portar CFRU. Cada espécie deve ter opções de movimentos compatíveis com a estrutura de golpes/efeitos de concurso disponível no Emerald.

## Conclusão de implementação
Não é seguro apenas alterar `NUM_SPECIES` ou acrescentar macros em `species.h`. A mudança exige sincronizar, no mínimo, enumeração de espécies, dados de espécie, evoluções, learnsets, Pokédex nacional, entradas, ordenações, conversões, gráficos e save data. Uma alteração parcial criaria arrays incompletos e referências sem dados.

## Estado desta etapa
- [x] Escopo 898 espécies registrado.
- [x] IDs atuais inspecionados.
- [x] Flags de Pokédex/save identificadas.
- [x] Tabelas nacionais e regionais identificadas.
- [x] Tabelas de metadados, evolução e conversão identificadas.
- [ ] Auditoria de todas as referências numéricas hardcoded e de todos os arrays gráficos.
- [ ] Definição de migração de save.
- [ ] Pipeline reprodutível de importação de dados e assets.
- [ ] Implementação, compilação e testes em emulador.

## Limitações
Esta auditoria foi feita por leitura dos arquivos da branch no GitHub. Não houve checkout local, compilação nem teste em emulador nesta etapa. A busca de código do conector não retornou resultados para consultas genéricas; os achados listados vêm de arquivos obtidos diretamente.
