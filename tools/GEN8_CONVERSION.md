# Gen 8 conversion package — stage 1

This stage extracts source data into reviewable JSON/CSV. It deliberately does not emit C runtime tables, edit existing species IDs, change move IDs, or alter NUM_SPECIES.

## Run

```sh
python3 tools/gen8_convert_emerald.py
python3 tools/gen8_convert_emerald.py --check
```

Generated artifacts under `reports/gen8-conversion/`:
- `conversion_report.json`: coverage and blockers.
- `species_records_raw.json`: balanced raw SpeciesInfo initializer bodies for Gen 8 family entries.
- `learnsets_raw.json`: extracted learnset rows.
- `species_id_mapping_template.json`: National Dex to future internal-ID mapping skeleton.
- `move_mapping_template.json` and `move_dependencies.csv`: all new source moves after the Gen 3 range, with no invented Emerald IDs.

## Important limitations

The vendored Emerald Expansion snapshot supplies Gen 8 species info and learnsets, but it does not supply a compatible vanilla Emerald evolution table, complete Pokédex descriptions, or cry assets/mappings. The source species info contains conditional family macros and expansion-only fields. Those are retained as raw data, never compiled into vanilla Emerald.

New Gen 8 learnsets reference moves not present in vanilla Emerald. Each new move needs a full Emerald move definition and a Contest classification/effect compatible with this project. The current package labels these dependencies; it does not silently map them to unrelated moves.

Runtime C tables, graphics tables, cry tables, species IDs, and NUM_SPECIES stay unchanged until each data dependency is resolved and validated.
