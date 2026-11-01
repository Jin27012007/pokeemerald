# Gen 8 conversion — stage 2

The conversion extractor is a data-normalization stage, not a runtime species expansion.

## Outputs

Run `python3 tools/gen8_convert_emerald.py`. The generated `reports/gen8-conversion/` directory contains:

- `conversion_report.json`: scope, counts, dependency gates, and readiness.
- `species_id_mapping.json`: complete canonical National Dex mapping, with existing Emerald internal IDs retained and new IDs left unset.
- `new_species_mapping.json`: new species only; no aliases or alternate forms counted as additional National Dex species.
- `species_info_compatible_candidates.json`: raw Gen 8 record blocks plus candidate values for fields whose names also exist in Emerald.
- `learnsets_raw.json`: level/move pairs extracted from source.
- `move_mapping_template.json` and `move_dependencies.csv`: the new source moves and unresolved Emerald definitions.
- `missing_learnset_moves.json`: every distinct learnset move symbol absent from Emerald.

## Safety

The script never writes C runtime source. It never edits species IDs, move IDs, `NUM_SPECIES`, save structures, evolution, Pokédex, or cry tables.

A field-name overlap is not automatically a semantic conversion. Ability IDs, type definitions, item IDs, growth curves, gender percentages, and egg group enums must be translated and validated separately. The Gen 8 source uses family feature flags and Expansion-only fields.

## Remaining gates

The vendored source does not include a Gen 8-to-Emerald evolution table, nor Gen 8 cry files/audio mapping in the Emerald sound format. Its Pokédex entry descriptions are embedded in Expansion SpeciesInfo, but the target uses a separate national-indexed table and localized string assets. All 487 new move constants need full battle records, and every new move used by the imported learnsets needs a Contest category, effect, and combo policy.

No new species should be activated in the runtime build until these dependencies and memory/save budgets are validated.
