# Build and test the Lilycove mod

## Compile in GitHub Codespaces

After the repository has received the latest changes, open the integrated terminal in Codespaces and run:

```bash
git pull
bash scripts/build-modern.sh
```

The script checks for the required compiler tools, builds the modern version, and verifies that `pokeemerald_modern.gba` exists in the repository root.

If a required tool is missing, use **Codespaces: Rebuild Container** from the Command Palette after pulling the changes. The repository's `.devcontainer/devcontainer.json` installs the build packages when the container is created.

## Download to a phone

Once the build succeeds, locate `pokeemerald_modern.gba` in the Codespaces Explorer. Use the file's context menu to download it to your device. Keep the resulting ROM for your own testing; the GitHub Actions workflow checks compilation but does not publish the ROM as a public artifact.

## Testing checklist

- Confirm that the build command exits with status 0.
- Check that `pokeemerald_modern.gba` is non-empty.
- Open the ROM in a GBA emulator and confirm it reaches the title screen.
- Load a save or start a new game and enter Lilycove City.
- After any gameplay edit, repeat the build and test the affected event in-game.

A successful compilation is not proof that modified gameplay works. Test each event in an emulator before considering it finished.
