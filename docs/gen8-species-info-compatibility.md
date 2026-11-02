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
