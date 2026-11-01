# Gen 8 storage architecture — decision record

Status: investigation only. No production species IDs, save structs, storage structs, or `NUM_SPECIES` are changed by this document.

## Verified vanilla Emerald constraints

- `struct BoxPokemon` stores the species identifier as a 16-bit value in its encrypted secure data. `struct Pokemon` embeds that box record; the party record does not use an 8-bit species field. The identifier width itself therefore does not force a larger party/box record for 898 species.
- `struct PokemonStorage` contains 14 boxes × 30 records, followed by box names and wallpaper bytes. Its current declared size is 0x83C3 bytes. The save layout reserves nine 3968-byte data sectors for this structure (35,712 bytes), so the current serialized storage allocation has substantial sector-level headroom. This is capacity, not proof that every storage API or graphics/UI index is safe for a larger species table.
- SaveBlock1 is 0x3D88 bytes and has 120 bytes of sector payload headroom across its four sectors. It contains two existing National Dex mirror arrays, `seen1` and `seen2`, each sized by `NUM_DEX_FLAG_BYTES`.
- SaveBlock2 is 0xF2C bytes and has 84 bytes of sector payload headroom. Its `Pokedex` member is 0x78 bytes (the surrounding structure reserves 8 bytes after it).
- A National Dex of 898 entries needs 113 bytes per bitset, because ceil(898 / 8) = 113. Vanilla currently allocates 52 bytes per array for 412 entries. The 3 seen mirrors and 1 owned array represented by the current redundancy model require four 113-byte arrays (452 bytes total), an increase of 244 bytes over four 52-byte arrays.

## Storage architecture recommendation

1. Keep the existing `BoxPokemon` binary record and party record layouts. Preserve the 16-bit species field and the encrypted substructure format. Do not add species-specific data to each stored Pokémon.
2. Treat the National Dex bitsets separately from Pokémon storage. The 898-entry requirement is only 61 additional bytes per bitset. The existing SaveBlock1 internal reserved region (`unused_3598[0x180]`) is a candidate location for an extension payload, but it must not be consumed until all save offsets, checksum boundaries, sector packing, and mirror/recovery semantics are verified.
3. Do not enlarge SaveBlock1 or SaveBlock2 by simply extending arrays: their sector headroom is only 120 and 84 bytes respectively. A 244-byte increase across four mirrors cannot be accommodated by raw struct growth. Prefer an explicit versioned extension stored in currently unused payload space or a dedicated special sector, with duplicated/atomic writes and migration from vanilla saves. The final choice requires tracing `gRamSaveSectorLocations`, sector IDs 30/31 use, special-sector read/write, save checksum and load recovery paths.
4. Keep the existing 3-way seen redundancy and owned/seen consistency checks only if the implementation audit confirms the same four physical copies and recovery semantics. The current host-side model is not a flash read/write test and does not validate migration.
5. Add compile-time and host-side checks for record sizes, offsets, species field width, box counts, dex bounds, serialization, save/load round trips, interrupted writes, corrupted extension copies, and old-save migration before changing the production constants.

## SpeciesInfo conversion gate

The source file currently consumed by the extractor is only `tools/vendor/pokeemerald-expansion/src/data/pokemon/species_info/gen_8_families.h`. The latest extractor run reported 123 parsed records, and 0 fully resolved compact records. This is not a complete 512-species data source and cannot be treated as a finished SpeciesInfo migration.

Emerald's compact `struct SpeciesInfo` requires base stats, types, catch rate, experience yield, EV yields, held items, gender ratio, egg cycles, friendship, growth rate, egg groups, two ability slots, Safari Zone flee rate, body color and no-flip behavior. Expansion data also has a third (hidden) ability and extensive presentation/dex fields. These must be explicitly mapped or deliberately represented outside the legacy struct; truncating the hidden ability or copying source enum numbers is not acceptable.

The next SpeciesInfo phase must:
- inventory every Gen 8 family/source file and prove exactly one canonical record per National Dex species 1–898, while handling forms separately;
- obtain authoritative source data for all 512 currently missing species, not only the subset in the vendored Gen 8 family header;
- map types, abilities, egg groups, growth rates, held items and body colors by semantic name, with explicit unsupported-value reports;
- define a safe representation for hidden abilities and any required modern metadata without silently overloading vanilla fields;
- emit a full per-species field-coverage report and validate every required field before producing C initializers;
- keep all generated records staged until source coverage, enum mappings and runtime consumers pass.

## Current blockers

- Save extension placement, versioning, flash write ordering, migration and recovery are not validated.
- The storage capacity calculation does not audit all species-indexed consumers (graphics tables, cries, evolutions, learnsets, battle/contest tables, scripts, dex ordering and UI indices).
- The current SpeciesInfo input is incomplete; the latest extractor reported 123 parsed records and zero complete compact records.
- The latest CI run for head `3f227d8e981622b61d4f6d9597cd08060b0ed4ac` failed in the staging-source verification step after conversion generation. The failure must be diagnosed and fixed before treating the pipeline as green.

## Release gate

`NUM_SPECIES` and the 512 new internal IDs remain untouched until storage architecture, save migration/round-trip tests, complete SpeciesInfo, and all species-indexed runtime tables are independently validated.


## Save-sector trace findings

The live save writer maps fourteen sectors per rotating save slot: sector 0 is SaveBlock2, sectors 1–4 are SaveBlock1, and sectors 5–13 are Pokémon storage. Normal saves and link saves use these slot-backed locations; the special-sector API accepts only sector 30 (Trainer Hill) and 31 (Recorded Battle). The Hall of Fame occupies sectors 28–29. None of these special sectors can be considered free extension storage without breaking an existing feature.

The SaveBlock1 reserved region at offset 0x3598 has 0x180 bytes. This is a plausible in-struct payload candidate, but is not yet approved for use. SaveBlock1 is split into four 3968-byte chunks and the whole save alternates between two slots. An extension there would be duplicated in both slots on full saves. A correct implementation still needs version markers, initialization of old saves, and tests proving the extension is copied and loaded consistently without colliding with save checksum logic or encryption-key relocation.

The 898-entry dex bitsets require 113 bytes each. Three seen copies plus one owned copy require 452 bytes; the baseline four arrays occupy 208 bytes, so the incremental requirement is 244 bytes. The 0x180 reserved block can contain this payload with 140 bytes spare, but only after read/write and migration tests validate the design. This is not permission to alter SaveBlock1 or NUM_DEX_FLAG_BYTES.
