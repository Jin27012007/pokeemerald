# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald modification focused on Lilycove City and Pokémon Contests.

## Current status
- Source: the `pret/pokeemerald` decompilation.
- Stable baseline/build configuration is on `master`; active development and investigation documentation belong on `lilycove/development`.
- Codespaces setup: `.devcontainer/devcontainer.json`.
- Local build helper: `bash scripts/build-modern.sh`.
- GitHub Actions workflow: `.github/workflows/build.yml`; a successful run uploads `pokeemerald_modern.gba` as artifact `pokeemerald-modern-rom` for 90 days.
- Baseline build confirmed on 2026-10-23: workflow run [40037449537](https://github.com/Jin27012007/pokeemerald/actions/runs/40037449537), manually dispatched on `master` at commit `2110bd8c0c1b8b326b6f88ff9e3bd5e206c2c410`, concluded `success`. Artifact generation was verified; emulator/gameplay testing is still not confirmed.
- Current design proposal and phased technical plan: [`docs/PROJECT_PROPOSAL.md`](docs/PROJECT_PROPOSAL.md).
- First-scene investigation and exact scope: [`docs/FIRST_SCENE_PLAN.md`](docs/FIRST_SCENE_PLAN.md).
- The opening flow starts a new game at Lilycove harbor, moves the player into House4, and grants the birthday gift plus adoption card. The Safari Zone adoption choice and a custom 24×24 card icon are now implemented in source; build and emulator verification are tracked separately.

## Project direction confirmed by the user
The adventure starts with the protagonist arriving by boat at Lilycove, welcomed by their mother; they then go to their new home after moving from the father's home in another region. Pokémon Contests form the main progression and the project is planned in seasons, with new coordinator rivals arriving over time. Lilycove will gain more interactive homes, NPC routines, planting, multiple Pokéblock minigames, and a customizable player home with furniture, dolls, trophies, and other decorations. The game should remain contained within Lilycove. This is a long-term vision; development must begin with a small playable slice and grow incrementally.

## First-scene status
- `CB2_NewGame()` calls `NewGameInitData()`, but skips the original truck callback for a new game. `NewGameInitData()` uses `WarpToLilycoveOpening()` to send the player to the harbor while retaining normal save initialization.
- The harbor's on-frame map script plays the arrival dialogue once, hides the harbor-mother object and warps into `LilycoveCity_House4`.
- House4 contains a mother NPC and a floor gift object using existing object graphics. The gift grants five Poké Balls plus the key item `ITEM_ADOPTION_CARD`; both inventory checks occur before rewards are granted.
- The Safari Zone adoption interaction offers Skitty, Eevee, or Vulpix at level 5, requires and consumes `ITEM_ADOPTION_CARD` only after a successful transfer, sends the Pokémon to the party or PC when possible, and prevents repeat adoption. The custom 24×24 adoption-card icon and palette are present. The attendant uses an existing overworld sprite; custom character art and manual emulator testing remain pending.
- The adoption card has an item definition and description plus a custom 24×24 pixel-art icon. The Safari Zone attendant now offers Skitty, Eevee, or Vulpix at level 5, checks for party/PC space, consumes the card after adoption, and prevents repeat adoption. The attendant still uses an existing Camper sprite; no custom character sprite has been added.
- Existing ferry logic remains in the harbor scripts. Build success is tracked separately from manual emulator/gameplay verification.

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
