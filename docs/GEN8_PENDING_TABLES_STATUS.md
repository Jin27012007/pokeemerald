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
- `pending_species_tables_audit.json`: source coverage results and remaining runtime dependency blockers.

The CI regression test is `tools/test_gen8_pending_tables.py`. The workflow verifies the 898-row count, the table-generation readiness gates, the type/egg-group/growth-rate dependency counts and the safety gate that keeps `NUM_SPECIES` unchanged.

## What is closed at the source-data layer

The current comprehensive source-table generator passes its CI stage. The verified source gates include 898 canonical species identities, 898 Gen 8 learnset rows, parsed evolution expressions, Pokédex text rows, cry identifiers matched to the source table, graphics-reference rows, referenced form tables, the Gen 8 Pokédex order tables and the complete source MoveInfo inventory. The generated table files are included in the `gen8-conversion-report` workflow artifact.

A target symbol match is recorded as a mapping fact only. It is not treated as proof that the corresponding Emerald battle, item, ability or graphics behavior is implemented.

## Runtime blockers — intentionally not marked complete

These source tables are not yet safe to link into Emerald's production runtime:

1. Species IDs: the 512 new canonical internal IDs are still unallocated. Existing Emerald IDs remain unchanged, and `NUM_SPECIES` has not been modified.
2. Moves: many Gen 8 moves have no Emerald move ID, battle definition/effect or Contest definition/callback. The source catalog is available; target move execution and Contest semantics still need explicit implementations or reviewed compatibility mappings.
3. Abilities: Expansion uses three ability slots and IDs wider than Emerald's two `u8` slots. Missing target constants/handlers must not be replaced with arbitrary IDs or silently dropped.
4. Held items: a matching item constant does not prove that the item data record, hold effect, battle behavior or item-use effect is compatible. The dependency table keeps these checks separate.
5. Types: Fairy is used by canonical Gen 8 species but is absent from vanilla Emerald's type enum and type chart. This requires runtime type and effectiveness work.
6. Evolutions: parsing a source evolution expression does not implement its conditions, battle-only triggers, special form behavior, item requirements or target species IDs in Emerald.
7. Cries and graphics: identifiers and pointers are inventoried, but the corresponding new audio and graphical payloads have not been imported into Emerald's formats.
8. Pokédex and save: source text/order data is generated, but runtime list sizing, flag storage, save-sector placement and initialization remain separate implementation gates.

The current vanilla Emerald `struct SpeciesInfo` is 26 bytes; the Expansion source structure is 196 bytes. They are not binary-compatible. The conversion must remain field-by-field and must not truncate a source value or discard a source-only field without an explicit policy.

## Safety gate

Source-table extraction passing does not authorize internal species ID allocation, production C-table replacement, save-layout changes or a `NUM_SPECIES` change. Those steps remain blocked until the move/Contest, ability, item, Fairy type, audio, graphics and save/runtime implementations are validated independently.
