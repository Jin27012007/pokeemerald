# Gen 8 conversion — staging and runtime audit

Run `python3 tools/gen8_convert_emerald.py` and then `python3 tools/audit_gen8_runtime.py` from the repository root.

## Generated source files

- `include/gen8_species_map.h` and `src/data/gen8/species_map.c`: a compilable auxiliary lookup from National Dex 1–898 to Emerald internal species IDs. Existing Emerald identities keep their current numeric IDs; the 512 not-yet-imported base species map to `SPECIES_NONE`.
- `include/gen8_conversion_status.h`: generated readiness constants. `GEN8_NUM_SPECIES_EXPANSION_ALLOWED` remains 0.
- `data/pokemon/gen8_species_map.json`: machine-readable Dex identity table.
- `data/pokemon/gen8_move_dependencies.json`: source move dependencies beyond Emerald's existing move range.
- `data/pokemon/gen8_level_up_learnsets.json`: 1,104 learnset blocks parsed from the Expansion's actual `struct LevelUpMove` syntax.
- `reports/gen8-conversion/`: mapping files, move inventory, missing move symbols, runtime blocker report and summary.

GitHub Actions uploads both the compiled ROM and the report directory as separate artifacts.

## Validated staging counts

The current successful CI report found 898 canonical National Dex identities, with 386 matching existing Emerald species and 512 requiring future internal IDs. It parsed 1,104 learnset blocks, with 17,044 level/move entries and 732 distinct learnset move symbols. 419 of those symbols are not present in the vanilla Emerald move constants.

The pinned source header contains 186 SpeciesInfo records, not a complete 898-record table. The separate Gen 8 SpeciesInfo family file has conditional family data and Expansion-only field references. It is not safe to copy that file into Emerald's live `gSpeciesInfo`.

## Runtime blockers

`tools/audit_gen8_runtime.py` generates `integration_blockers.json` and `integration_blockers.md`. It inventories missing abilities, items, types, BattleMove and ContestMove records, extra species metadata fields, evolution method references, cry-name mismatches and known memory limits.

The vendored snapshot lacks the Expansion's battle move definitions and does not include the corresponding Gen 8 graphics or audio asset payloads. It is not enough to extract numeric learnsets; each referenced new move needs a correct battle implementation and Contest category/effect/combo data before it can be used in a Contest-focused game.

## Why NUM_SPECIES remains blocked

The latest successful vanilla compile reports EWRAM at 95.26%, IWRAM at 92.82%, SaveBlock1 at 99.24%, SaveBlock2 at 97.88%, and Pokémon Storage at 94.49%. SaveBlock1 has only 120 bytes remaining in that baseline. Expanding structures or adding new Pokémon without redesigning the save strategy is unsafe.

Before changing `NUM_SPECIES`, the next implementation milestones are: define a save-compatible species storage strategy; complete the missing SpeciesInfo records and translate every enum; supply Gen 8 battle definitions and Contest data; generate target-compatible evolutions and Pokédex strings; add graphics, palettes, icons and cries; then audit all species-indexed tables, loops, arrays, dex navigation, storage, trades, and save serialization.

No production species ID, move ID, live SpeciesInfo table or save structure is changed by the staging layer. A successful CI build proves the original Emerald runtime plus the auxiliary mapping compiles; it does not mean Gen 8 Pokémon are already playable.
