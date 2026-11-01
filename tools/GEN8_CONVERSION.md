# Gen 8 storage architecture and SpeciesInfo conversion

This phase quantifies the existing save/RAM limits and builds an auditable
National Dex 1-898 SpeciesInfo inventory from the pinned Expansion family
sources. It deliberately separates source coverage, fields resolved for the
Emerald compact record, and runtime compatibility. It does not allocate
species IDs, change NUM_SPECIES, or write SaveBlock1/SaveBlock2/PokemonStorage.

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
- The vendor snapshot includes Gen 4-9 family headers. Family headers contain
  multiple forms and may share a National Dex number; the audit selects the
  canonical symbol for each Dex entry and preserves sibling forms separately.
- Emerald's SpeciesInfo has two 8-bit ability slots; Expansion uses three
  16-bit ability slots. Modern ability IDs and the third slot cannot be copied
  into Emerald's struct without a runtime layout/API change.
- The source catalog has Fairy and later-generation type/ability/item values
  that are not necessarily represented by Emerald's enums. The audit records
  source identifiers symbolically and flags non-compatible target mappings.
- Source-only fields such as front/back sprites, animation, icons, cry,
  Pokédex text, form changes, height/weight and evolutions remain outside the
  compact Emerald battle-stat struct and require separate runtime tables.

## Generated outputs

Run:

```sh
python3 tools/audit_gen8_runtime.py
python3 tools/gen8_convert_emerald.py
```

The report directory contains:
- `storage_architecture_audit.json`: sector capacities, bitset requirements,
  identifier gaps and explicit readiness gates.
- `species_info_by_national_dex.json`: one canonical identity row per Dex
  number, including source symbol, generation, raw field presence, unresolved
  compact fields and alternate same-Dex forms.
- `species_info_field_coverage.json`: per-field source coverage counts.
- `emerald_species_info_compatibility.json`: explicit width/slot/type limits
  between Expansion and Emerald.
- `species_info_compact.json` and `species_info_unresolved.json`: per-source
  record parse results; unresolved expressions are never silently defaulted.
- `conversion_report.json`, species mapping, learnsets and move dependency
  inventories.

## SpeciesInfo mapping rule

Only values representable in `struct SpeciesInfo` are candidates:
base stats, catch rate, experience yield, EV yields, gender ratio, egg cycles,
friendship, growth rate, types, egg groups, abilities, held items and body
color. Expansion-only values (sprite pointers, animations, names, descriptions,
height/weight, cries, form changes, extra abilities, and flags) remain outside
the compact runtime record.

Numeric enum values are never copied by their numeric source value. Each
source catalog is parsed in its own enum domain, then target compatibility is
resolved by symbol. Missing identifiers and width/slot mismatches are reported,
never aliased to unrelated items/abilities/moves. The automated parser tests
cover enum numbering, nested initializer syntax, quoted strings and the
Expansion brace-on-next-line layout. The strict conversion check additionally
requires 898 canonical rows and zero unresolved compact records; it is expected
to fail while any source or runtime compatibility gap remains.

## NUM_SPECIES gate

The generated readiness report keeps `num_species_change_allowed=false`.
Before allocation: settle the extension sector layout and dual-copy recovery
tests; obtain complete 512-species SpeciesInfo; map or implement missing
abilities/items/Fairy type; finish evolution, move battle/Contest records,
Pokédex text, cry/audio assets, graphics/palettes/icons; audit all species-index
tables, Unown offsets, save serialization, link/trade and scripts; then build,
measure EWRAM/IWRAM and execute a new-game/save/reload emulator test.
