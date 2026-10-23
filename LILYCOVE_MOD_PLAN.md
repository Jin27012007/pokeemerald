# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald (pret/pokeemerald) modification focused on Lilycove City.

## Current status
- Source base: pret/pokeemerald decompilation, branch `master`.
- The fork has been checked and can be accessed by the linked GitHub connection.
- No ROM build has been run or verified by the assistant in the Codespaces terminal.
- No changes to map layout or gameplay are considered tested in an emulator yet.

## Development rules
1. Keep upstream changes small and reviewable.
2. Do not overwrite original Lilycove scripts without a clear reason.
3. Every new event must be attached to a valid object, coordinate trigger, or background event before it can be considered playable.
4. Compile with the toolchain documented in upstream `INSTALL.md`.
5. Test the resulting `pokeemerald.gba` in an emulator before declaring success.

## Lilycove map entry points
- Map data: `data/maps/LilycoveCity/map.json`
- Map event scripts and text: `data/maps/LilycoveCity/scripts.inc`
- Map layout: `data/layouts/LilycoveCity/layout.json` (verify exact path on this upstream revision if editing layouts)

## First milestone
Prepare a clean build in GitHub Codespaces, confirm `make` can produce `pokeemerald.gba`, then agree on a concrete set of Lilycove changes before adding playable events.
