# Gen 8 storage architecture and SpeciesInfo conversion

This phase has two goals: quantify the existing save/RAM limits and extract the
small subset of Gen 8 SpeciesInfo that maps to Emerald's battle-stat record.
It intentionally does not allocate species IDs, change NUM_SPECIES, or write
SaveBlock1/SaveBlock2/PokemonStorage.

## Architecture findings

- Emerald stores seen/owned National Dex flags in SaveBlock2's Pokedex record
  and mirrors other flag bytes into SaveBlock1. The flag array size is derived
  from NUM_SPECIES, not NATIONAL_DEX_COUNT.
- SaveBlock1 is a fixed 0x3D88-byte structure assigned four 3968-byte data
  sectors. SaveBlock2 is assigned one sector; PokemonStorage is assigned nine.
  Increasing those structs in place can overflow the allocated sectors.
- The current internal species bound includes Egg and legacy Unown handling.
  Unown form IDs are defined after NUM_SPECIES; changing the bound moves those
  aliases. The custom species reservation is not itself a complete Gen 8
  integration.
- 898 National Dex entries need 113 bytes per seen/owned bitset (226 bytes
  total). That is small enough for a single 3968-byte sector, but a robust
  extension needs a version, magic, checksum, monotonic save counter and
  double-buffer/recovery policy. Sectors 30/31 are already used by Trainer Hill
  and Recorded Battle and must not be reused without a deliberate redesign.
- The Gen 8 vendor snapshot includes 186 Gen 8 SpeciesInfo blocks among its
  family data; it is not a complete 512-record dataset. Fields for front/back
  sprites, animation, icons, cry, Pokédex text, forms and evolutions do not
  belong to vanilla's compact struct SpeciesInfo.

## Generated outputs

Run:

```sh
python3 tools/audit_gen8_runtime.py
python3 tools/gen8_convert_emerald.py
```

The report directory contains:
- `storage_architecture_audit.json`: sector capacities, bitset requirements,
  identifier gaps and explicit readiness gates.
- `species_info_compact.json`: raw, reviewable compact-stat candidates for
  source records whose type/ability/egg-group/item identifiers can be mapped.
- `species_info_unresolved.json`: records that need an explicit identifier
  mapping or more complete source data.
- `conversion_report.json`, species mapping, learnsets and move dependency
  inventories.

## SpeciesInfo mapping rule

Only values representable in `struct SpeciesInfo` are candidates:
base stats, catch rate, experience yield, EV yields, gender ratio, egg cycles,
friendship, growth rate, types, egg groups, abilities, held items and body
color. Expansion-only values (sprite pointers, animations, names, descriptions,
height/weight, cries, form changes, extra abilities, and flags) remain outside
the compact runtime record.

Numeric enum values are never copied by their numeric source value. They must
be looked up by symbolic name in vanilla Emerald. Missing identifiers are
reported, never aliased to unrelated items/abilities/moves.

## NUM_SPECIES gate

The generated readiness report keeps `num_species_change_allowed=false`.
Before allocation: settle the extension sector layout and dual-copy recovery
tests; obtain complete 512-species SpeciesInfo; map or implement missing
abilities/items/Fairy type; finish evolution, move battle/Contest records,
Pokédex text, cry/audio assets, graphics/palettes/icons; audit all species-index
tables, Unown offsets, save serialization, link/trade and scripts; then build,
measure EWRAM/IWRAM and execute a new-game/save/reload emulator test.
