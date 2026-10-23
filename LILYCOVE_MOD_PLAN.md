# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald modification focused on Lilycove City.

## Current status
- Source: the `pret/pokeemerald` decompilation.
- Stable base and build configuration are on `master`.
- Active mod work should happen on `lilycove/development`, so experiments do not go directly into the base branch.
- Codespaces setup: `.devcontainer/devcontainer.json`.
- Build script: `bash scripts/build-modern.sh`.
- GitHub Actions workflow: `.github/workflows/build.yml`; a successful run should upload `pokeemerald_modern.gba` as the artifact `pokeemerald-modern-rom` for seven days.
- No build has yet been verified. The GitHub API currently shows no Actions runs, so workflow execution is not confirmed.

## First milestone: verified build
1. Enable GitHub Actions for this fork if GitHub shows the disabled-workflows notice in the Actions tab.
2. Let the build workflow run on a push to `master` or `lilycove/**`.
3. Confirm the workflow passes and the ROM artifact is available.
4. Test the artifact in a GBA emulator and confirm it reaches the title screen.
5. Only after this, start adding gameplay changes and test each one in-game.

## Lilycove map entry points
- Map/event definitions: `data/maps/LilycoveCity/map.json`
- Event scripts and text: `data/maps/LilycoveCity/scripts.inc`
- Inspect the layout's exact source path and format before editing terrain or collision.

## Development rules
1. Keep changes small and reviewable.
2. Do not overwrite original scripts without a clear reason.
3. Attach each new event to a valid object, coordinate trigger, or background event.
4. Follow the upstream `INSTALL.md` toolchain instructions.
5. Do not call a feature finished until the ROM compiles and the affected event has been tested in an emulator.

## Design scope still to define
The current request established Pokémon Emerald as the base and Lilycove as the focus, but no specific gameplay feature list was recovered. Do not invent major features or change the city's existing events until the desired changes are specified.
