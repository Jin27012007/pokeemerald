# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald modification focused on Lilycove City.

## Current status
- Source: the `pret/pokeemerald` decompilation.
- Stable baseline/build configuration is on `master`; active development and investigation documentation belong on `lilycove/development`.
- Codespaces setup: `.devcontainer/devcontainer.json`.
- Local build helper: `bash scripts/build-modern.sh`.
- GitHub Actions workflow: `.github/workflows/build.yml`; a successful run uploads `pokeemerald_modern.gba` as artifact `pokeemerald-modern-rom` for seven days.
- Baseline build confirmed on 2026-10-23: workflow run [40037449537](https://github.com/Jin27012007/pokeemerald/actions/runs/40037449537), manually dispatched on `master` at commit `2110bd8c0c1b8b326b6f88ff9e3bd5e206c2c410`, concluded `success`. Artifact generation was verified; emulator/gameplay testing is still not confirmed.
- The main gameplay proposal has not yet been provided. Until it is provided, do not change gameplay behavior.

## First milestone: verified baseline build
1. Baseline compilation and artifact generation are now confirmed.
2. Test the artifact in a GBA emulator and verify that it reaches the title screen.
3. When the user supplies the proposal, trace the current behavior and dependencies before editing.
4. Implement in small, reviewable changes on `lilycove/development`; build after each logical slice.
5. Test the changed behavior and important adjacent states in an emulator before calling it done.

## Technical investigation map
- Architecture and per-task entry points: [`docs/CODE_NAVIGATION_GUIDE.md`](docs/CODE_NAVIGATION_GUIDE.md).
- Main city map/events: `data/maps/LilycoveCity/map.json`, `data/maps/LilycoveCity/scripts.inc`.
- Layout catalog: `data/layouts/layouts.json`; a map's layout references must be traced to the matching `data/layouts/<Layout>/` assets.
- State: `include/constants/flags.h`, `include/constants/vars.h`; check existing uses before reusing/adding state.
- Build/data generation: `Makefile`, `map_data_rules.mk`, `json_data_rules.mk`, `graphics_file_rules.mk`, `audio_rules.mk`.

## Development rules
1. Re-read the current branch contents before every code change; documentation/hashes are navigation aids, not a substitute for checking current source.
2. Keep changes small and reviewable; preserve unrelated behavior.
3. Do not overwrite original scripts without a clear reason.
4. Every map event must have a valid definition and a reachable script/target; inspect flags/vars, object IDs, warps and event triggers.
5. Change source files, not generated outputs, unless build rules prove that a generated file is intentionally the editable source.
6. Use GitHub Actions or `bash scripts/build-modern.sh` to compile.
7. A successful build proves compilation/artifact generation, not correct gameplay. Emulator testing is still required.
8. Do not invent major features or modify the ROM until the user specifies the desired changes.

## Design scope still to define
The user confirmed Pokémon Emerald as the base and asked for technical preparation focused on understanding how to implement systems, events, rules, and other changes. No gameplay feature list has been supplied yet.
