# Vendored Gen 8 reference data

Source repository: https://github.com/rh-hideout/pokeemerald-expansion
Pinned upstream commit: c460a8661dfa0598ae25d42a968c690ecbf489c6

This directory contains source references for the Lilycove Emerald importer.
The vendored files are **not directly included by the Emerald build**. They
are inputs for offline extraction and audits. The Expansion source uses
macros, structures, feature flags, species forms, abilities, items, types,
moves, cries and graphics that are not binary-compatible with vanilla Emerald.

The importer must normalize National Dex 1-898, preserve all 386 current
Emerald species IDs, translate identifiers and generate all Emerald-indexed
runtime tables before changing `NUM_SPECIES`.

Do not copy Expansion initializers into vanilla Emerald's `gSpeciesInfo`
without field-by-field conversion. The two `SpeciesInfo` layouts differ
substantially. No file in this vendor directory is compiled into the ROM.

See `UPSTREAM_TABLES.md` for the exact source-to-table inventory and limits.
Respect the upstream repository's license and attribution requirements.
This vendor snapshot is source data, not a redistribution of graphics or a
compiled ROM.
