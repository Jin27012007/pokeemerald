# Gen 8 Pokédex data import — status

Scope: 898 National Dex species (Gen 1–8), no CFRU battle engine.

## Changes made
- `tools/gen8_pokedex_manifest.py`: fetches official species names/IDs from PokeAPI and generates a deterministic National Dex manifest for IDs 1–898. It fails rather than emitting a partial list.
- `tools/validate_gen8_pokedex.py`: validates manifest numbering and checks that each species has the required Emerald graphics files. Missing assets are reported; no fake sprite aliases are generated.
- `.github/workflows/build.yml`: runs the manifest generator and validator before the existing Route 121 fix and modern ROM compilation.

## Current scope of the change
This is a data-ingestion and completeness gate only. It does not yet add the 487 missing species to C species IDs, species metadata, evolution tables, level-up learnsets, Pokédex text/order, cry mapping, graphics tables or save layout. Those source tables must be imported/generated from a coherent upstream dataset before raising `NUM_SPECIES`.

## Why the build is expected to stop at preflight
The existing Emerald graphics folder contains the original species assets, not complete Gen 4–8 resources. The validator is designed to fail and list missing files until those assets are imported. A failed preflight is intentional and safer than producing a ROM with invalid species references.

## Next integration steps
1. Pin a legally usable dataset and document its attribution/license.
2. Build importers for species stats/types/gender/egg groups/growth/abilities, evolutions, learnsets and national dex descriptions.
3. Convert front/back/animated sprites, icons, footprints and palettes into Emerald graphics conventions.
4. Extend cries and graphics lookup tables.
5. Reconcile contest moves/effects without importing the battle engine.
6. Expand species enum and save-backed dex flags only after all tables are generated.
7. Compile, audit ROM/RAM budget, and test new game, party, PC, Pokédex, evolution and contests.

## Build
The workflow is configured to run on this branch. The expected first action is a failing preflight if required assets are not yet imported. This is not a completed 898-species ROM.


## CI behavior correction
The asset checker now supports `--report-only` for the normal ROM build. This reports missing imported resources without marking the base Emerald build as a failed compile. Running it without that flag remains a strict readiness gate and returns a failing exit code until all graphics are present. This separates two different states: a valid base ROM build and a completed Gen 8 data migration.


## Source compatibility audit (CFRU)

Audited source: `Skeli789/Complete-Fire-Red-Upgrade` on its `master` branch.
The source defines 905 National Dex numbers (1-905), while the requested target
scope for this project remains the 898 species through Gen 8. The source species
constants also include regional forms and G-Max forms, with 1,268 species
constants in total. They are not a drop-in replacement for Emerald's 411
species-internal IDs. The importer must select canonical National Dex species
1-898, preserve Emerald's existing internal IDs where applicable, and generate
a deterministic mapping for missing species. Forms outside the canonical 898
must not be inserted accidentally.

The CFRU repository is a FireRed-based project and stores data in different
layouts. It is being used as a data reference only; its battle-engine hooks,
assembly patches, save code, and FireRed engine files are out of scope.

No species IDs, save fields, or C tables have been expanded in this audit.
