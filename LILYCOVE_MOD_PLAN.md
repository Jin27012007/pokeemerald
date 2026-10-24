# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald modification focused on Lilycove City and Pokémon Contests.

## Current status
- Source: the `pret/pokeemerald` decompilation.
- Stable baseline/build configuration is on `master`; active development and investigation documentation belong on `lilycove/development`.
- Codespaces setup: `.devcontainer/devcontainer.json`.
- Local build helper: `bash scripts/build-modern.sh`.
- GitHub Actions workflow: `.github/workflows/build.yml`; a successful run uploads `pokeemerald_modern.gba` as artifact `pokeemerald-modern-rom` for seven days.
- Baseline build confirmed on 2026-10-23: workflow run [40037449537](https://github.com/Jin27012007/pokeemerald/actions/runs/40037449537), manually dispatched on `master` at commit `2110bd8c0c1b8b326b6f88ff9e3bd5e206c2c410`, concluded `success`. Artifact generation was verified; emulator/gameplay testing is still not confirmed.
- Current design proposal and phased technical plan: [`docs/PROJECT_PROPOSAL.md`](docs/PROJECT_PROPOSAL.md).
- First-scene investigation and exact scope: [`docs/FIRST_SCENE_PLAN.md`](docs/FIRST_SCENE_PLAN.md).
- The latest development work is investigation/documentation only. No gameplay code or ROM mechanics have been changed yet.

## Project direction confirmed by the user
The adventure starts with the protagonist arriving by boat at Lilycove, welcomed by their mother; they then go to their new home after moving from the father's home in another region. Pokémon Contests form the main progression and the project is planned in seasons, with new coordinator rivals arriving over time. Lilycove will gain more interactive homes, NPC routines, planting, multiple Pokéblock minigames, and a customizable player home with furniture, dolls, trophies, and other decorations. The game should remain contained within Lilycove. This is a long-term vision; development must begin with a small playable slice and grow incrementally.

## First-scene status
- Confirmed technical entry path: `CB2_NewGame()` → `NewGameInitData()` → `WarpToTruck()`; `CB2_NewGame()` also sets `ExecuteTruckSequence` as the field callback.
- The truck scene's map scripts set the old Littleroot intro state, respawn and dynamic warp. It is unsafe to change only the map ID without replacing the linked old intro state logic.
- Lilycove harbor has existing ferry behavior and NPC scripts; preserve those while designing the opening.
- Next code step is to trace references to the intro state and confirm a dedicated persistent state/flag, then implement only the first opening segment. Still no code changes or gameplay verification at this point.

## Milestones
1. Successful baseline build and artifact generation are confirmed on `master`. A build on experimental code must be run separately.
2. Trace current behavior and dependencies before editing gameplay.
3. Implement in small, reviewable changes on `lilycove/development`; build after each logical slice.
4. Test changed behavior and adjacent states in an emulator before calling it done.
5. Implement the opening first; then award a starter Pokémon; only after that begin Contest systems and their progression.

## Technical investigation map
- Architecture and per-task entry points: [`docs/CODE_NAVIGATION_GUIDE.md`](docs/CODE_NAVIGATION_GUIDE.md).
- First scene, state dependencies and test criteria: [`docs/FIRST_SCENE_PLAN.md`](docs/FIRST_SCENE_PLAN.md).
- Main city map/events: `data/maps/LilycoveCity/map.json`, `data/maps/LilycoveCity/scripts.inc`.
- Harbor opening: `data/maps/LilycoveCity_Harbor/map.json`, `data/maps/LilycoveCity_Harbor/scripts.inc`, `src/overworld.c`, `src/new_game.c`, `data/maps/InsideOfTruck/scripts.inc`.
- Contest system: `src/contest.c`, `src/contest_util.c`, `src/contest_ai.c`, `src/contest_effect.c`, `src/contest_link.c`, `src/contest_painting.c`, plus Contest Hall scripts.
- Future preparation systems: berries, Pokéblocks, Pokémon condition, item/bag state, and map event scripts.
- State: `include/constants/flags.h`, `include/constants/vars.h`; check all existing uses before reusing/adding state.
- Build/data generation: `Makefile`, `map_data_rules.mk`, `json_data_rules.mk`, `graphics_file_rules.mk`, `audio_rules.mk`.

## Development rules
1. Re-read the current branch contents before every code change; documentation/hashes are navigation aids, not a substitute for checking current source.
2. Keep changes small and reviewable; preserve unrelated behavior.
3. Do not overwrite original scripts without a clear reason.
4. Every map event must have a valid definition and a reachable, tested exit/warp.
5. Build success and emulator gameplay verification are separate claims.
