# Vendored Gen 8 reference data

Source repository: https://github.com/rh-hideout/pokeemerald-expansion
Pinned upstream commit: c460a8661dfa0598ae25d42a968c690ecbf489c6
Source paths:
- `src/data/pokemon/species_info/gen_8_families.h`
- `src/data/pokemon/level_up_learnsets/gen_8.h`
- `include/constants/species.h`
- `include/constants/moves.h`

These files are retained as reference inputs for the Lilycove Emerald importer.
They are **not directly included by the Emerald build**. The Expansion source
uses additional macros, structures, feature flags, species forms, abilities,
items, types, and move definitions that do not exist in vanilla Emerald.
An importer must normalize the canonical National Dex 1-898 species, preserve
all existing Emerald IDs, translate every referenced identifier, and generate
all Emerald-indexed runtime tables before changing `NUM_SPECIES`.

The Gen 8 species file contains conditional family blocks and references
assets/fields from the Expansion project. Do not copy it into
`src/data/pokemon/species_info.h` as-is.

Respect the upstream repository's license and attribution requirements when
redistributing derived source. This vendor snapshot is source data, not game
graphics or a compiled ROM.
