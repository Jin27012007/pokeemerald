# Gen 8 species ID migration contract

Status: **design stage; no production species ID changes.**

## Identifier domains

The conversion data uses National Dex numbers (1-898) as canonical external identities. Emerald gameplay currently uses internal species IDs. These domains are not interchangeable: the current source mapping contains 386 existing species but many IDs differ from their National Dex numbers (for example, Treecko is National Dex 252 and internal species ID 277).

The generator emits `gGen8SpeciesMap`, indexed by National Dex number, with `SPECIES_NONE` for the 512 unallocated species. `Gen8SpeciesMap_GetEmeraldId` accepts a National Dex number, rejects zero and values greater than 898, and returns `SPECIES_NONE` for unallocated rows. This API is a metadata lookup only; it is not a general conversion from stored party/box IDs to canonical Dex values.

## Runtime invariants

- Stored `MON_DATA_SPECIES`, battle species, evolution targets, and per-species table indices remain Emerald internal IDs until a separate allocation/migration commit.
- `SPECIES_NONE` and `SPECIES_EGG` are sentinels, not usable species data records.
- Unown auxiliary IDs are not canonical species rows and must not be included in a contiguous 512-ID allocation.
- Any API that accepts an internal ID must reject sentinels and IDs outside the corresponding table's actual bounds before indexing.
- Any API that accepts National Dex must translate through the explicit map; it must never index `gSpeciesInfo`, `gEvolutionTable`, `gLevelUpLearnsets`, sprite, palette, icon, or name arrays directly with the National Dex number.

## SpeciesInfo compatibility blockers

The current Emerald `struct SpeciesInfo` is 26 bytes and stores six stats, two types, two held items, growth/egg metadata and exactly two 8-bit ability slots. The Expansion source representation contains three ability slots and wider source ability IDs. Fairy and Stellar type definitions are also absent from the current Emerald target. Therefore raw Expansion SpeciesInfo rows cannot be copied into the current struct without explicit, tested adaptation or a runtime structure change.

## Consumer migration sequence

1. Keep the native species namespace unchanged and establish tested validators for each accepted ID domain.
2. Migrate the SpeciesInfo data access boundary first, preserving existing internal IDs and handling Egg/NONE/Unown explicitly.
3. Migrate evolution, learnset, graphics, palette, icon, cry, names and Pokédex consumers separately; tests must prove every lookup is bounded and uses the correct identifier domain.
4. Only after the 249 high-risk and 453 unclassified static findings are resolved should species IDs be allocated and `NUM_SPECIES` reconsidered.
5. Test save/load, party, PC, daycare, battle, trade/link, evolution, summary, Pokédex, graphics and audio before enabling the expanded namespace.

## Current audit evidence

The successful CI run 41468255573 scanned 716 C/header files and recorded 1,115 findings: 249 high-risk, 603 medium-risk, 263 low-risk, and 453 unclassified. The highest-risk direct-index groups are SpeciesInfo (145), evolution (32), learnsets (27), front pictures (25), back pictures (11), and palettes (7). Static findings require manual source review and are not proof of a runtime defect in every case.
