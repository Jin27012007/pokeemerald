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


## Migration blockers confirmed from actual source tables

A deeper comparison against CFRU's `include/constants/species.h`,
`include/constants/pokedex.h`, `include/constants/moves.h`, and
`src/Tables/level_up_learnsets.c` found:

- The canonical target list is 898 National Dex numbers. CFRU's Pokédex header
  contains repeated alternate-form aliases and post-Gen-8 entries 899-905;
  the importer must filter these, not copy its header wholesale.
- CFRU internal species IDs are not Emerald internal IDs. Existing Emerald
  species IDs must remain stable; new species IDs must be allocated after the
  existing internal range and before the final Egg/special-form boundary.
- 510 canonical National Dex slots are new relative to the Emerald species
  constants, but four canonical entries do not have the same direct base-form
  name in CFRU's constants (Basculin, Minior, Alcremie and Urshifu), requiring
  explicit base-form alias resolution.
- CFRU Gen 4-8 level-up learnsets reference roughly 500 move constants that
  do not exist in this Emerald move table (which currently ends at 354).
  Importing the learnsets without the matching move definitions and compatible
  contest/battle data would create invalid references. The contest-focused
  project needs a separate move-compatibility pass; no numeric substitutions
  are allowed.

This confirms the migration order: canonical species mapping -> full move
identifier reconciliation -> species metadata/evolutions/learnsets -> Pokédex
strings/order/cries -> graphics -> species count/save expansion. Do not raise
`NUM_SPECIES` until each stage passes the generator's validation.


## Reproducible compatibility audit added

`tools/audit_gen8_import.py` now compares the checked-in 898-species manifest,
CFRU species/dex/move definitions and CFRU level-up learnset blocks against
Emerald's current IDs and move constants. It writes
`reports/gen8_import_compatibility.json` in CI. The audit does not rewrite C
tables and does not renumber moves. This prevents invalid partial imports while
the full movement/contest compatibility layer is unresolved.


## Pinned source snapshot

The four text source files used by the compatibility audit are now vendored
under `tools/vendor/cfru/`, pinned to upstream CFRU commit
`b637a27898b14e25dd24d0f69a3e302f0069deb8`. This makes the data audit
reproducible and independent of a moving upstream branch at build time. The
snapshot is limited to species constants, National Dex constants, move
constants, and level-up learnsets; no engine hooks or binary assets are copied.

## Important source-format correction

CFRU's `level_up_learnsets.c` keeps Gen 4-8 additions in a large commented
block before the closing comment marker. The source audit intentionally scans
those declarations as source data, but a production importer must extract
only those blocks and validate every referenced move symbol. It must not
uncomment or compile this upstream file as-is.
