# Gen 8 conversion — staging layer

Run `python3 tools/gen8_convert_emerald.py` from the repository root.

## Generated source files

- `include/gen8_species_map.h` and `src/data/gen8_species_map.c`: a compilable auxiliary lookup from National Dex 1–898 to Emerald internal species IDs. Existing Emerald identities keep their current numeric IDs; the 512 not-yet-imported base species map to `SPECIES_NONE`.
- `include/gen8_conversion_status.h`: generated count/readiness constants. `GEN8_NUM_SPECIES_EXPANSION_ALLOWED` remains 0.
- `data/pokemon/gen8_species_map.json`: full machine-readable identity table.
- `data/pokemon/gen8_move_dependencies.json`: moves beyond Emerald's MOVE_PSYCHO_BOOST / 354, with explicit outstanding BattleMove and ContestMove requirements.
- `data/pokemon/gen8_level_up_learnsets.json`: learnsets parsed from the Expansion's actual `struct LevelUpMove` / `LEVEL_UP_MOVE` syntax.
- `reports/gen8-conversion/`: counts, mapping, move dependencies, unresolved move symbols, and readiness report.

The GitHub Actions build uploads the report directory as `gen8-conversion-report`.

## Current scope

The pinned source has a complete base National Dex range through 898. The Emerald target currently has 386 matching base species and 512 species without assigned internal IDs. The map file does not assign IDs to those new species and does not change `NUM_SPECIES`.

Learnset extraction preserves source species symbols and move symbols. It does not pretend that missing moves are playable. Every new move still needs a semantically correct battle definition, a Contest effect/category/combo entry, and a stable Emerald move ID. Alternate forms are not made into extra base Dex records.

## Why NUM_SPECIES is still blocked

The current successful vanilla build reports EWRAM at 95.26%, IWRAM at 92.82%, SaveBlock1 at 99.24%, SaveBlock2 at 97.88%, and Pokémon Storage at 94.49%. Increasing the species bound without first planning save-layout and RAM usage is unsafe.

Before changing `NUM_SPECIES`, the next implementation milestones are: define a save-compatible species storage strategy; complete and test every Gen 8 SpeciesInfo record and field enum conversion; prepare graphics/palettes/icons/front/back assets and cry data; generate evolutions and Pokédex entries/text; allocate and implement battle and Contest move definitions; then audit all arrays, loops, tables, save serialization, links/trades, and species-indexed assets for the new bound.

No live production data table is replaced by this staging layer. A successful CI build proves that the existing Emerald ROM plus the auxiliary map compiles; it is not proof that Gen 8 species can already appear in-game.
