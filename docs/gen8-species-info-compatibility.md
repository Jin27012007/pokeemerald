# Gen 8 SpeciesInfo: source audit and Emerald compatibility

## Scope and safety boundary

This document describes the source-data conversion boundary for National Pokédex entries 1–898. It does not authorize changing `NUM_SPECIES`, assigning the 512 new internal species IDs, replacing Emerald's production `gSpeciesInfo`, or changing save data.

The Expansion source snapshot is vendored under `tools/vendor/pokeemerald-expansion` (upstream snapshot commit `c460a8661dfa0598ae25d42a968c690ecbf489c6`). The source declaration is `include/pokemon.h`; the target declaration is vanilla Emerald's `include/pokemon.h`.

## Struct layout: not binary-compatible

| Property | Vanilla Emerald | Expansion source |
|---|---:|---:|
| `struct SpeciesInfo` size | 0x1A (26 bytes) | 0xC4 (196 bytes) |
| Type storage | two `u8` values | two `enum Type` values |
| Experience yield | `u8` | `u16` |
| EV yields | six 2-bit fields | six 2-bit fields in a wider allocation |
| Held-item IDs | two `u16` values | two `enum Item` values |
| Egg groups | two `u8` values | `enum EggGroup[EGG_GROUPS_PER_MON]` |
| Ability slots | two `u8` values | `enum Ability[NUM_ABILITY_SLOTS]` (three slots) |
| Ability ID range | 8-bit storage | source catalog exceeds 255 |
| Additional source-only members | none in this struct | Pokédex text, cry, dimensions, graphics, flags, shadows, learnsets, evolutions, forms, overworld data |

The structures must never be copied, cast, or serialized as if they shared a layout. A future runtime implementation must use explicit field-by-field conversion or a new target-side data structure.

## Field-by-field compatibility

| Expansion source field | Emerald target / treatment | Compatibility |
|---|---|---|
| `baseHP`, `baseAttack`, `baseDefense`, `baseSpeed`, `baseSpAttack`, `baseSpDefense` | Same six `u8` stats | Direct |
| `types[2]` | Two `u8` type IDs; target battle type tables must contain every mapped type | Conditional; Fairy and Stellar are not supported by the current vanilla target |
| `catchRate` | `u8` | Direct |
| `expYield` | Target is `u8`, source is `u16` | Lossy for values above 255; never truncate silently |
| Six `evYield_*` fields | Six 2-bit yields | Width-compatible; omitted source yields mean zero only when confirmed by source initializer semantics |
| `itemCommon`, `itemRare` | Two `u16` IDs | Width-compatible, but item IDs, item effects, and battle behavior need explicit mappings |
| `genderRatio` | `u8` | Direct only after resolving source macros to Emerald's encoding |
| `eggCycles`, `friendship`, `growthRate` | `u8` | Direct after resolving source generation/configuration expressions |
| `eggGroups[2]` | Two `u8` values | Width-compatible after enum mapping |
| `abilities[3]` | Two `u8` values | Incompatible: third slot is absent and some source ability IDs exceed 255 |
| `safariZoneFleeRate` | `u8` | Direct when supplied; otherwise the source default must be recorded |
| `bodyColor`, `noFlip` | Same 7-bit/1-bit packing | Layout-compatible after enum mapping |

### Expansion-only data

The following source fields are not members of Emerald's 26-byte structure and must be audited and migrated into their appropriate runtime systems rather than discarded:

- Pokédex identity and text: `categoryName`, `speciesName`, `cryId`, `natDexNum`, `height`, `weight`, `description`.
- Battle graphics: front/back pictures, palettes, shiny palettes, icons, animation IDs/frames, female variants, dimensions and offsets.
- Species/form metadata: legendary/mythical/form flags, Tera and regional-form flags, perfect-IV settings, battle restrictions, shadow settings and egg IDs.
- Data references: level-up, teachable and egg-move learnsets; evolutions; form-species and form-change tables.
- Overworld data: object-event graphics, palettes and encounter behavior.

These fields may be represented in separate Emerald tables or asset systems. Their presence in a parsed initializer does not make them runtime-compatible.

## Parser and provenance requirements

1. Parse the complete initializer RHS, including family/form macros, before extracting designated fields. Macro-only records are valid source records, not missing species.
2. Preserve the unexpanded initializer and the expanded field map separately. Do not label expanded values as literal source text.
3. Record the source file, source generation/family, canonical National Dex number, and source symbol for every selected canonical record.
4. Record omitted optional fields and their documented source default separately from fields that were present with a value. A parser fallback is not evidence of a source default.
5. Keep source enum IDs distinct from Emerald enum IDs. A numeric source ID is never copied into Emerald merely because it fits the destination integer width.
6. Include all non-selected alternate forms in the source inventory, but select exactly one explicitly justified canonical record for each National Dex number 1–898.
7. Any unresolved macro, enum, conditional expression, alias, missing field, or source record must appear in the report and fail the corresponding readiness gate. No silent zero, `NONE`, or first-form fallback is permitted.

## Readiness gates

SpeciesInfo source coverage is complete only when all 898 canonical National Dex entries have exactly one selected source record, every required source field is resolved or explicitly documented as an intentional source default, and all source-field provenance is available.

Emerald runtime compatibility is a separate gate. It remains blocked until the 16-bit experience yield, Fairy/Stellar types, ability width/slot count, item definitions/effects, and every separate graphics, cry, evolution, learnset, Pokédex and form dependency have an explicit target implementation.

Passing source coverage does not authorize species-ID allocation or a `NUM_SPECIES` change. Save-block and Pokédex storage validation must also pass independently.

## ID-allocation preparation gate (not an allocation)

The current converter is an audit/staging tool. It must not assign the 512 new internal species IDs or edit `NUM_SPECIES`. Before a separate ID-allocation change is proposed, the following evidence must exist in the same pinned source snapshot and CI run:

1. Exactly 898 canonical National Dex rows, with unique Dex numbers 1–898 and exactly one selected canonical source initializer per number. Alternate forms must stay in a separate inventory and must not silently consume canonical IDs.
2. Every selected row must retain its source generation, exact source designator, raw initializer, expanded field map, and Dex-number provenance. Missing fields and present-but-unresolved fields must be separate lists; both must be empty for required fields.
3. The 386 existing Emerald species must retain their current internal IDs. A generated proposed mapping must prove that these IDs are unchanged and that the 512 remaining canonical identities are exactly the unassigned set. No ID can be inferred from source enum order.
4. The proposed 512-ID map must be deterministic, collision-free against existing species, `SPECIES_NONE`, egg placeholders, form constants and all other reserved IDs. The policy for regional, battle-only and cosmetic forms must be explicit and independently tested.
5. Every canonical SpeciesInfo field must have an explicit target policy. Width mismatches (notably 16-bit experience yields and source enum widths), the third ability slot, Fairy/Stellar, new ability/item identifiers and any source-only metadata must be represented as compatibility blockers or deliberate extension data. No truncation, arbitrary fallback ID or implicit zero is permitted.
6. Every indexed runtime family must have a matching ID policy and bounds audit: SpeciesInfo, cries, graphics/palettes/icons, evolutions, learnsets, Pokédex orders/flags/text, form tables, abilities, items, moves, scripts and UI consumers.
7. Save storage and migration must be independently approved with host-side serialization, round-trip, interrupted-write, corruption-recovery and old-save migration tests. The current SaveBlock2 in-place expansion exceeds its sector payload; the SaveBlock1 reserved bytes are only a candidate, not an approved design.
8. Only after all prior gates pass may a separate change allocate IDs and update `NUM_SPECIES`. That change must include compile-time count/bounds assertions, generated-table consistency tests, a full ROM build and save compatibility tests. It must not be combined with the source extraction or runtime-data conversion commits.

### Current decision

ID allocation is **blocked**. Canonical source-row coverage is not equivalent to complete source-field resolution, compact struct compatibility, or runtime readiness. The CI must report those dimensions independently. In particular, a source-complete result does not satisfy the target mapping gate, and a target mapping gate does not prove save migration safety.

### Provenance of the 898 canonical rows

The canonical audit now tags each row as either `existing_emerald_runtime_record` or `expansion_source_initializer`. CI expects exactly 386 preserved native Emerald rows and 512 Expansion-source rows, totaling 898. The preserved native rows prove that existing runtime records were found and retained; they do not claim that those rows were imported from Expansion. The 512 Expansion-source rows must independently pass the source-field and target-mapping audits above.

### Provenance-aware readiness

The 898-row canonical coverage count is intentionally split into 386 native Emerald rows and 512 Expansion-source rows. The `source_fields_resolved` counter applies only to the 512 Expansion rows; native rows are audited as preserved existing runtime records. Compact compatibility is evaluated in both groups using their respective provenance evidence. CI must verify the 386 + 512 split, 512 resolved Expansion records, and that the compact-stage readiness flag agrees with the combined compatible-row count. None of these checks alone makes runtime/save migration ready.

The existing namespace audit currently finds unique explicit numeric IDs, ordinary species through 411, the Egg sentinel at 412, 25 numeric `SPECIES_OLD_UNOWN_*` constants, and 26 additional Unown constants expressed relative to `NUM_SPECIES`. This inventory is now covered by a parser-level regression test. It is not an approved allocation range: the Egg sentinel position and all consumers of the relative Unown constants still require a dedicated design and bounds audit.


## Sentinela, formas e contrato dos consumidores de IDs

Este documento estabelece uma política de identidade e indexação para a etapa pré-alocação. É uma decisão de arquitetura, não uma reserva de números. Nenhuma alteração de `NUM_SPECIES`, de constantes de produção, de tabelas indexadas ou de layout de save é autorizada por esta seção.

### 1. Identidade canônica versus forma

- O índice do National Dex identifica a espécie canônica (1–898). Ele não é, por si só, um ID interno de espécie.
- Uma forma que altera apenas aparência, paleta, sprite, ícone ou nome de apresentação deve permanecer como metadado/estado de forma da espécie-base. Não ganha ID independente apenas por existir em uma tabela de formas.
- Uma forma só poderá virar espécie interna separada quando houver uma justificativa de compatibilidade documentada: representação persistente necessária, comportamento incompatível com um estado de forma, ou consumidor legado que exija uma entrada de espécie. A exceção precisa declarar os dados independentes, as transições, a conversão de retorno e o comportamento do Pokédex.
- Formas temporárias de batalha (por exemplo, Mega, Primal, Ultra, Dynamax/Gigantamax ou mudanças de tipo dependentes de item) não podem ser gravadas como identidade permanente do Pokémon sem política explícita de serialização. O estado de batalha deve ser derivado/reconstruído.
- Formas regionais que constituem identidade biológica/jogável distinta podem ser linhas internas independentes se seus stats, tipos, habilidades, evolução, Pokédex e assets exigirem isso; a política não deve ser aplicada indiscriminadamente a todas as famílias. O vínculo com Dex pode continuar apontando ao número canônico correto conforme o modelo de Pokédex.
- Unown é exceção já implementada: suas 26 formas estendidas são códigos auxiliares de apresentação derivados do intervalo reservado, não 26 novas espécies canônicas. Devem ser tratadas no adaptador de forma/ícone, não confundidas com novas identidades do National Dex.

### 2. Sentinelas e valores especiais

- `SPECIES_NONE` permanece como valor nulo/slot vazio e nunca indexa tabelas de dados.
- Egg é um estado/valor sentinela, não uma espécie canônica e não entra na contagem 898. O código atual usa `SPECIES_EGG` como índice especial em tabelas de ícone e como retorno de `MON_DATA_SPECIES_OR_EGG`; por isso, sua futura posição precisa ser definida junto com os limites de arrays e as verificações de faixa. Não basta colocar Egg antes/depois da faixa sem adaptar os consumidores.
- O futuro contrato deve separar explicitamente `NUM_SPECIES` (quantidade/limite de IDs reais, conforme a convenção escolhida) de `SPECIES_EGG` (sentinela), em vez de manter a ambiguidade atual em que `NUM_SPECIES == SPECIES_EGG`. A convenção final de contagem e limite deve ser fechada com as declarações C e todos os loops antes de editar o header.
- Todos os sentinelas devem ser rejeitados antes de acessar `gSpeciesInfo`, tabelas de crescimento, learnsets, evoluções, gráficos, paletas, animações, cries, ícones e Pokédex. Acesso a tabelas especiais (como ícone de Egg) deve ocorrer por caminho dedicado e com dimensão validada.
- Os códigos auxiliares Unown devem ficar fora do intervalo normal indexável de espécies e ser convertidos para forma/ícone antes do acesso a tabelas comuns. Não devem ser usados como índices de `gSpeciesInfo`, evoluções, learnsets ou dados persistentes.

### 3. Contrato obrigatório de consumidores

Cada consumidor deve ser classificado em um dos seguintes grupos e validado individualmente antes da alocação:
1. **Identidade/persistência:** `BoxPokemon`, `Pokemon`, `MON_DATA_SPECIES`, `MON_DATA_SPECIES_OR_EGG`, checksum, criptografia, troca, link, save e migração. Exige conversão explícita de IDs antigos e round-trip.
2. **Dados primários indexados:** `gSpeciesInfo`, experiência, crescimento, EV yield, habilidades, tipos, gênero, itens, evoluções e learnsets. Exige limites e entrada válida para cada espécie real; sentinelas nunca entram.
3. **Dex/identidade pública:** conversões National/Hoenn, seen/owned, ordem, nomes, descrições, formas e flags. Deve mapear espécie interna para Dex sem pressupor identidade 1:1.
4. **Recursos visuais e áudio:** front/back sprites, palettes, icons, footprints, escala/offset, animações e cries. Formas visuais devem resolver para asset e estado de forma sem ler além da tabela.
5. **Batalha/evolução/UI:** transformação, formas de batalha, party, PC/storage, resumo, enciclopédia, troca, evolução e scripts. Cada caminho deve tratar NONE/Egg/IDs inválidos antes de indexar.
6. **Dados auxiliares/formas:** tabelas `FormSpeciesIdTable`, `FormChangeTable`, mapeadores por personalidade, itens de forma e tabelas de forma. Devem declarar se armazenam espécie real, forma, ou sentinel de término; não misturar esses domínios.

Um consumidor só pode ser marcado como auditado quando houver: arquivo/função, domínio de entrada, limite da tabela, tratamento de NONE/Egg/Unown/forma inválida, conversão de forma, e teste que cubra o último ID válido e cada sentinela relevante.

### 4. Evidência do código atual e riscos conhecidos

O header atual define `SPECIES_EGG = 412`, `NUM_SPECIES = SPECIES_EGG` e 26 códigos Unown relativos a `NUM_SPECIES`. Foram observados, entre outros, os seguintes consumidores acoplados a esses limites:

- `src/pokemon.c`: arrays `[NUM_SPECIES - 1]` para ordem de Dex e animações; acessos diretos a `gSpeciesInfo[species]`, `gLevelUpLearnsets[species]`, `gEvolutionTable[species]`; funções de conversão National/Hoenn; condições `species > NUM_SPECIES`; `MON_DATA_SPECIES_OR_EGG`.
- `src/pokemon_icon.c`: tabela de ícones com entrada explícita de Egg e Unown, cálculo de forma Unown por `SPECIES_UNOWN_B`, e múltiplas verificações `species > NUM_SPECIES`.
- `src/battle_main.c`: cálculo de forma Unown com `NUM_SPECIES + unownForm` e validação de valores acima do limite.
- `src/pokemon_storage_system.c`: armazenamento/ícones de Box e caminhos que indexam `gMonFrontPicTable[species]`.
- `src/pokemon_summary_screen.c`: acessos a `gSpeciesInfo[summary->species]` e sprites por `summary->species2`.
- `src/evolution_scene.c`: acessos a tabelas de sprites e evoluções usando espécies atuais e destino.
- `src/pokedex.c`: iteração até `NUM_SPECIES - 1`, conversão Dex→espécie e acesso a `gSpeciesInfo`.
- `src/battle_script_commands.c` e `src/battle_util.c`: acessos a `gSpeciesInfo` com espécies oriundas de party/batalha e comparações com Egg/NONE.

Esta lista é evidência mínima, não um inventário exaustivo. Os demais arquivos e includes de dados precisam ser varridos automaticamente por referências a `NUM_SPECIES`, `SPECIES_EGG`, `SPECIES_UNOWN_*`, `gSpeciesInfo`, `gEvolutionTable`, learnsets, gráficos, paletas, cries e tabelas de forma. Os arquivos ausentes ou gerados por macros também precisam ser incluídos no inventário.

### 5. Condições para liberar a alocação

A fase de alocação só pode começar depois que:
- o inventário automatizado de consumidores estiver completo e sem ocorrências não classificadas;
- a convenção final de quantidade/limite e o valor do sentinela Egg estiverem aprovados por testes de limites;
- cada forma estiver classificada como metadado/estado ou exceção com ID próprio, com política de save explícita;
- os 386 IDs internos existentes forem preservados e todos os 512 novos IDs forem provados únicos;
- os arrays de runtime, assets e índices auxiliares tiverem dimensões e tabelas completas;
- testes cobrirem NONE, Egg, cada família Unown, primeira e última espécie, forma inválida, transformação temporária e migração de saves;
- o CI executar extração, auditorias, build completo e testes de save sem falha.

**Estado da decisão:** política arquitetural proposta e registrada; inventário ainda parcial; alocação de IDs bloqueada. `NUM_SPECIES`, `SPECIES_EGG`, Unown, formas, tabelas de produção e save permanecem inalterados.
