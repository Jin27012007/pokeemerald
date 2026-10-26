# Route 121 fence/corridor regression notes

The latest Android test screenshots show that the map layout still renders pale tan crosshatched tiles where the blue vertical fence should continue, and the river/ground corner allows an apparently unintended grass-colored tile area.

The affected map is `data/layouts/Route121/map.bin`, not the Lilycove City map itself. The route's tileset references Lilycove metatiles, and the vertical fence labels already exist in `include/constants/metatile_labels.h`:
- `METATILE_Lilycove_Fence_Horizontal` = `0x341`
- `METATILE_Lilycove_Fence_Vertical` = `0x343`
- `METATILE_Lilycove_Fence_Vertical_Blue` = `0x346`

Recent commits modified the binary layout only. Build workflows passing only demonstrate that the binary assets compile; they do not validate in-game appearance or collision. Do not modify the map binary or metatile attributes by guessing raw bytes. Next edit should use a decoded layout/metatile inspection workflow or an available Porymap-compatible tooling environment, then rebuild and inspect a fresh in-game screenshot.

Known latest tested build source SHA: `b4bcd27d8c038be05b350e4f63935619b75e7a79`.
