# Gen 8 runtime promotion gates

Status: **staging-only; production species IDs and save IO are unchanged.**

This document records the minimum gates before the National Dex 1-898 dataset may become visible to gameplay code.

## Current verified source state

- 898 canonical National Dex identities: complete and unique.
- 386 native Emerald records: retained under their current numeric IDs.
- 512 Expansion records: source fields parsed and audited.
- 512 Gen 8 level-up learnsets, 898 Pokédex catalog rows, 898 cry references, 898 graphics references, and referenced form-table inventory are staged.
- This does not mean every referenced runtime resource exists in Emerald.

## Confirmed runtime gaps from the conversion audit

- 311 canonical Gen 8 learnset moves lack target Emerald battle/contest move records.
- 165 abilities lack target Emerald constants.
- 57 held items lack target Emerald constants; 23 lack target item data records.
- Fairy type lacks an Emerald type definition.
- 2 canonical evolution methods require new handlers.
- 512 new species have no matching Emerald cry-table entry.
- 512 new species lack imported target graphics payloads.
- 128 form species tables and 83 form-change tables are referenced; existence checks alone do not prove form behavior is implemented.

## Species ID consumer inventory

The static audit scanned 714 C/header files and found 1,115 species-related references: 249 high-risk, 603 medium-risk, 263 low-risk, and 453 unclassified. High-risk examples include direct indexes into `gSpeciesInfo`, learnsets, evolution, front/back sprite, palette and other per-species arrays.

A source inventory is not a proof of runtime safety. Before ID allocation, all remaining unclassified references must be reviewed and all direct-index consumers either expanded or routed through a validated mapping API.

The approved CI artifact (`gen8-conversion-report`, run `41488150856`) measured 716 C/header files, 1,115 references, 249 high-risk findings, 603 medium-risk findings, 263 low-risk findings, and 453 unclassified findings. High-risk groups include 145 `gSpeciesInfo` accesses, 32 evolution-table accesses, 27 learnset accesses, 25 front-pic accesses, 11 back-pic accesses, and 7 palette accesses. This report is generated as a CI artifact, not a tracked runtime source file.

The native namespace currently has 413 numeric species constants, maximum explicit ordinary ID 411, Egg sentinel 412, `NUM_SPECIES == SPECIES_EGG`, and 27 calculated Unown auxiliary values. The canonical map covers 898 National Dex entries: 386 already have Emerald internal IDs and 512 still require IDs. National Dex numbers must not be substituted directly for internal IDs; for example, Treecko is National Dex 252 but Emerald internal ID 277.

The generated National Dex map now has a full host-C execution and parity gate. The test covers all 898 canonical entries, confirms zero mismatches for the 386 existing Emerald IDs, confirms all 512 new entries remain unassigned, and exercises forward/reverse lookup plus invalid IDs and sentinels. The legacy table also contains 22 auxiliary Unown pseudo-Dex entries at 899-920 (internal IDs 255-276); these are outside canonical Dex 1-898. `NationalPokedexNumToSpecies` and `SpeciesToNationalPokedexNum` now route canonical Dex/internal-ID conversion through this generated map. The forward lookup retains the legacy table fallback for Unown pseudo-Dex 899-920; the reverse lookup retains the old internal-ID table fallback for auxiliary Unown entries and rejects sentinels. The Makefile regenerates the header and C source when absent; CI deletes both outputs and verifies clean regeneration before compiling. This is the first runtime consumer migration only; the remaining direct-index consumers are still gated. The parity report is included in CI artifact run `41488150856`.

The compatibility audit confirms Expansion SpeciesInfo is not a drop-in replacement: Expansion has three ability slots while Emerald has two, source ability values are wider, and Fairy/Stellar types are absent from Emerald. The report records 414 runtime-gap records. Direct-index consumers must be migrated or routed through bounded translation wrappers before canonical IDs are promoted.

The SpeciesInfo read migration is now covered by a CI audit: 158 `GetSpeciesInfoSafe` call sites across 22 C files and zero remaining direct `gSpeciesInfo[...]` indexes outside the accessor. The evolution-table migration adds `GetEvolutionTableSafe`, which returns an empty zero-method row for species values at or beyond `NUM_SPECIES`. `GetEvolutionTargetSpecies`, the Shedinja creation path, and the daycare egg-species reverse traversal use the bounded accessor; the Shedinja target is also checked before indexing the species-name table. CI asserts that the only remaining direct `gEvolutionTable[...]` access is the guarded read inside the accessor. This is an index-safety migration only: it does not import Gen 8 evolution rows or add species IDs.

## Save and Pokédex storage

- The vanilla `struct Pokedex` uses 52-byte owned and seen arrays.
- National Dex 898 needs 113 bytes per array; the four legacy+extension copies need 244 bytes beyond the current arrays.
- The candidate SaveBlock1 reserved window is 384 bytes; the proposed isolated extension envelope is 256 bytes and leaves 128 bytes unused in that window.
- SaveBlock2 does not fit an inline Pokédex expansion: projected overflow is 38 bytes beyond its sector capacity.
- The 256-byte candidate envelope has a 12-byte header and 244 bytes of flag payload: four 61-byte copies for seen, owned, and backups.
- This capacity calculation is not a save migration approval.

The current implementation adds a typed, versioned envelope and independent checksum/flag helpers. It is not embedded in a live save block, is not referenced by save IO, and must not be used to mutate user saves.

## Required gates before save integration

1. C and host-side tests for header/version/size validation, bit boundaries, checksum corruption, generation rollover, and backup disagreement.
2. Round-trip write/read tests through the actual save-sector APIs.
3. Interrupted-write/power-loss tests proving one valid generation survives.
4. Corruption recovery policy that chooses a valid copy deterministically and does not silently combine conflicting data.
5. Old-save migration tests for saves with and without existing Pokédex data.
6. Sector offset tests proving Trainer Hill and Recorded Battle are untouched.
7. Full save size and checksum validation on hardware-compatible sector sizes.

## Required gates before species IDs / NUM_SPECIES

1. Resolve every species-index consumer, including the 453 unclassified references, special values, forms, Unown auxiliary values, and egg.
2. The canonical National Dex lookup now uses the tested generated API with a preserved Unown auxiliary fallback; migrate the remaining consumers with explicit domain and sentinel handling.
3. Migrate the 313 missing move records, ability/item/type domains, evolution handlers, cries, graphics, Pokédex text, and form behavior.
4. Test party, PC storage, daycare, battle, trade, link, save/load, summary, Pokédex, sprite/audio, evolution, and game-corner consumers.
5. Only then propose numeric IDs and update `NUM_SPECIES` in a separate, reviewable commit with a full migration plan.

## Safety invariant

Until every gate is green, `NUM_SPECIES` remains `SPECIES_EGG`, native species IDs remain unchanged, and the Gen 8 namespace is staging metadata only.
