# Gen 8 pending-table inventory — status

Branch: `gen8/data-conversion`

Source snapshot: `rh-hideout/pokeemerald-expansion@c460a8661dfa0598ae25d42a968c690ecbf489c6`

Scope: canonical National Pokédex 1–898 (Generations 1–8). The Expansion source is used as a pinned, auditable data reference. Its runtime engine and binary assets are not copied into vanilla Emerald.

## Generated source tables

`tools/gen8_build_pending_tables.py` runs after the SpeciesInfo converter and emits deterministic JSON tables:

- `gen8_species_evolutions.json`: 898 source evolution rows and parsed evolution expressions.
- `gen8_species_level_up_learnsets.json`: one Gen 8 level-up learnset per canonical species, selected by the actual `levelUpLearnset` pointer in the SpeciesInfo initializer.
- `gen8_species_pokedex_entries.json`: species names, category strings, descriptions and size fields.
- `gen8_species_cry_map.json`: source cry identifiers matched to the Expansion cry assembly table.
- `gen8_species_graphics_references.json`: per-species pointers for front/back sprites, palettes, icons, animation metadata and related graphics.
- `gen8_species_form_references.json`: referenced form-species and form-change source tables, still represented symbolically.
- `gen8_pokedex_orders.json`: the source Pokédex order tables filtered to National Dex 1–898.
- `gen8_move_source_catalog.json` and `gen8_contest_effect_source_catalog.json`: source battle/Contest move metadata and source Contest callbacks.
- `gen8_ability_source_dependencies.json` and `gen8_item_source_dependencies.json`: source IDs and the target constants/data records required by the canonical species.
- `gen8_type_source_dependencies.json`, `gen8_egg_group_source_dependencies.json`, `gen8_growth_rate_source_dependencies.json` and `gen8_evolution_method_dependencies.json`: explicit source-to-Emerald symbol/ID comparisons.
- `gen8_evolution_condition_dependencies.json`: conditional evolution edges, source condition symbols and candidate Emerald method mappings. Candidates are not marked implemented.
- `pending_species_tables_audit.json`: source coverage results, target cry-table matches, per-species target graphics asset coverage and remaining runtime dependency blockers.

The CI regression test is `tools/test_gen8_pending_tables.py`. The workflow verifies the 898-row count, the table-generation readiness gates, the type/egg-group/growth-rate dependency counts and the safety gate that keeps `NUM_SPECIES` unchanged.

## What is closed at the source-data layer

The current comprehensive source-table generator passes its CI stage. The verified source gates include 898 canonical species identities, 898 Gen 8 learnset rows, parsed evolution expressions, Pokédex text rows, cry identifiers matched to the source table, graphics-reference rows, referenced form tables, the Gen 8 Pokédex order tables and the complete source MoveInfo inventory. The generated table files are included in the `gen8-conversion-report` workflow artifact.

A target symbol match is recorded as a mapping fact only. It is not treated as proof that the corresponding Emerald battle, item, ability or graphics behavior is implemented.

## Latest verified source-table measurements

The successful CI run for commit `e18f216b57519d77ed38063130a453fa9da70ea8` generated the following independent coverage figures:

| Table family | Verified source/target inventory |
|---|---:|
| Canonical species rows | 898 / 898 |
| Gen 8 level-up learnsets | 898 / 898; 0 missing |
| Evolution records | 480 parsed edges; 0 unresolved records |
| Conditional evolution edges | 130 edges across 21 condition symbols |
| Conditions with candidate Emerald methods | 8; candidate mappings still require semantic validation |
| Evolution methods needing new target handlers | 2: `EVO_SCRIPT_TRIGGER` and `EVO_SPIN` |
| Pokédex descriptions | 898 decoded; 0 unresolved |
| Source cry identifiers | 898 matched to Expansion cry table |
| Existing Emerald cry labels | 386 matched; 512 still absent |
| Graphics reference rows | 898 complete |
| Emerald graphics folders with all seven expected assets | 384 complete; 514 incomplete |
| Form-species / form-change tables | 228 / 143 referenced; 0 missing source-table definitions |
| National Pokédex orders | 3 / 3 complete |
| Source MoveInfo definitions | 839 / 839 found |
| Distinct Gen 8 level-up moves used | 639 |
| Gen 8 moves missing Emerald move, battle and Contest records | 322 |
| Source battle-effect symbols missing in Emerald | 162 |
| Source Contest effect definitions | 48; 0 missing target callbacks |
| Canonical abilities used | 249; 172 have no Emerald constant |
| Canonical held items used | 85; 85 have no Emerald constant; 30 have no target item-data record |
| Types used | 18; 1 missing target type (Fairy) |
| Egg groups / growth rates used | 15 / 6; none missing in the target catalogs |

The cry and graphics measurements are not proof of imported assets. They explicitly compare source references against the current Emerald assembly table and graphics folders. The 514 incomplete graphics rows and 512 missing cry labels remain outstanding work.

The evolution inventory also keeps source method numbers separate from Emerald method numbers. For example, Expansion `EVO_LEVEL` has source enum value 1 while Emerald's target method macro is 4. Never copy source numeric method IDs into Emerald's `struct Evolution`.

## Runtime blockers — intentionally not marked complete

These source tables are not yet safe to link into Emerald's production runtime:

1. Species IDs: the 512 new canonical internal IDs are still unallocated. Existing Emerald IDs remain unchanged, and `NUM_SPECIES` has not been modified.
2. Moves: many Gen 8 moves have no Emerald move ID, battle definition/effect or Contest definition/callback. The source catalog is available; target move execution and Contest semantics still need explicit implementations or reviewed compatibility mappings.
3. Abilities: Expansion uses three ability slots and IDs wider than Emerald's two `u8` slots. Missing target constants/handlers must not be replaced with arbitrary IDs or silently dropped.
4. Held items: a matching item constant does not prove that the item data record, hold effect, battle behavior or item-use effect is compatible. The dependency table keeps these checks separate.
5. Types: Fairy is used by canonical Gen 8 species but is absent from vanilla Emerald's type enum and type chart. This requires runtime type and effectiveness work.
6. Evolutions: parsing a source evolution expression does not implement its conditions, battle-only triggers, special form behavior, item requirements or target species IDs in Emerald. The 130 conditional edges include 21 distinct condition symbols; only eight have candidate Emerald method equivalents, and those still require semantic validation.
7. Cries and graphics: source labels and pointers are inventoried, but 512 source cry labels do not exist in the current Emerald cry table, and 514 canonical species folders still lack at least one of the seven required graphics assets.
8. Pokédex and save: source text/order data is generated, but runtime list sizing, flag storage, save-sector placement and initialization remain separate implementation gates.

The current vanilla Emerald `struct SpeciesInfo` is 26 bytes; the Expansion source structure is 196 bytes. They are not binary-compatible. The conversion must remain field-by-field and must not truncate a source value or discard a source-only field without an explicit policy.

## Safety gate

Source-table extraction passing does not authorize internal species ID allocation, production C-table replacement, save-layout changes or a `NUM_SPECIES` change. Those steps remain blocked until the move/Contest, ability, item, Fairy type, audio, graphics and save/runtime implementations are validated independently.
