# Pinned Expansion table inventory

All files listed here are fetched from
`rh-hideout/pokeemerald-expansion` commit
`c460a8661dfa0598ae25d42a968c690ecbf489c6`.

| Source path | Purpose in the importer | Still required before runtime use |
|---|---|---|
| `src/data/abilities.h` | Ability names/descriptions/metadata | Ability execution callbacks and vanilla battle-engine compatibility |
| `src/data/items.h` | Item metadata and item definitions | Item IDs, use handlers, held-item effects, scripts, graphics and bag behavior |
| `src/data/pokemon/item_effects.h` | Pokémon item effects | Explicit target item behavior and ID mapping |
| `src/data/moves_info.h` | Battle move data (power, type, PP, accuracy, target and effects) | Reconcile move IDs/effects with Emerald battle scripts and struct semantics |
| `src/data/battle_move_effects.h` | Battle effect constants/definitions | Port required battle scripts, functions and effect handlers |
| `src/data/contest_moves.h` | Contest move effects and appeal/jam metadata | Map each move and Contest behavior into Emerald's Contest engine |
| `src/data/pokemon/egg_moves.h` | Egg-move learnsets | Species-ID and move-ID mapping; breeding-table integration |
| `src/data/pokemon/form_change_tables.h` | Form-change rules | Map methods/parameters, ability/item/move dependencies and runtime handlers |
| `src/data/pokemon/form_species_tables.h` | Form-to-species relationships | Assign target form IDs and preserve form-change invariants |
| `include/constants/form_change_types.h` | Form-change method IDs | Translate source enum values and implement every required handler |
| `src/data/pokemon/pokedex_orders.h` | Alternative Pokédex ordering tables | Adapt only the orderings selected by the project |
| `include/constants/pokedex.h` | National Dex constants | Canonical identity cross-check; does not replace target runtime dex flags |
| `sound/cry_tables.inc` | Species-to-cry assembly table | Cry IDs/audio assets and Emerald cry playback table mapping |

## Tables represented in SpeciesInfo family source

The Gen 1–8 `species_info/gen_N_families.h` files already contain designated
species initializers, including inline `evolutions`, `levelUpLearnset`,
`teachableLearnset`, `eggMoveLearnset`, `formSpeciesIdTable` and
`formChangeTable` references. Those references are source symbols/pointers,
not directly usable Emerald table indices. Their full initializer strings
must be retained in the audit output.

## Explicit exclusions

This import does not vendor or install Expansion Pokémon graphics, palettes,
icons, overworld sprites, footprints, or cry audio assets. The cry table only
maps source identifiers to cry symbols. Asset conversion and licensing review
remain separate tasks.

No vendored table is linked into the ROM. Source IDs must never be copied into
Emerald IDs merely because their integer widths happen to fit.
