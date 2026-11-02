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
