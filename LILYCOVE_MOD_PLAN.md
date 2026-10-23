# Lilycove Mod — Development Notes

This fork is the working base for a Pokémon Emerald modification focused on Lilycove City.

## Current status
- Source: the `pret/pokeemerald` decompilation, branch `master`.
- Codespaces setup file added at `.devcontainer/devcontainer.json`.
- The build workflow was simplified to compile the modern build without relying on the upstream `symbols` branch, which is not present in this fork.
- One-command build script added: `bash scripts/build-modern.sh`.
- The assistant has not executed commands inside the user's live Codespace and has not verified an emulator boot. GitHub currently reports no Actions runs for this repository, so the workflow result is still unverified.

## Build milestone
1. Pull the latest commit in Codespaces with `git pull`.
2. If Codespaces asks for a container rebuild, rebuild it so the packages in `.devcontainer/devcontainer.json` are installed.
3. Run `bash scripts/build-modern.sh`.
4. Confirm that `pokeemerald_modern.gba` is created and test it in a GBA emulator.
5. Only then treat the base build as verified and begin gameplay changes.

Full steps: [docs/BUILD_AND_TEST.md](docs/BUILD_AND_TEST.md).

## Lilycove map entry points
- Map/event definitions: `data/maps/LilycoveCity/map.json`
- Event scripts: `data/maps/LilycoveCity/scripts.inc`
- Map layout source: verify the exact upstream path and generated layout format before editing it.

## Development rules
1. Keep upstream changes small and reviewable.
2. Do not overwrite original Lilycove scripts without a clear reason.
3. Each new event must be attached to a valid object, coordinate trigger, or background event before it can be considered playable.
4. Compile with the toolchain documented in upstream `INSTALL.md`.
5. Test every gameplay change in an emulator. A successful compile alone is not proof that the change works in-game.
