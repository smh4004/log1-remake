# M1 first pass: LoG1 against Buu's Fury's limits

Measured 2026-11-03 with `tools/measure_log1.py` on log1-decomp 9e1fc99.

| Check | Limit | Result |
|---|---|---|
| Area size | 256x256 tiles (BF masks) | All 42 fit; largest is area 29 at 240x240 |
| Unique tiles, as stored | 896 per map (BF BG VRAM, per mapkit) | 4 over: area 2 (1,050), 12 (1,027), 17 (1,388), 29 (1,084) |
| Character frames | 32x32 one piece, bosses larger | 73 of 84 records fit 32x32; 7 records have larger frames |
| Painted rooms | Tile swaps need repeating tiles | 19 one-screen areas use nearly all 600 cells as unique tiles |
| Corridor fit, median share of walkable tiles a 3x3 tile body can reach | BF's own floors: 1.00 | LoG1: 0.98; worst are area 27 (0.64) and 26 (0.84) |
| Flight-only tiles | | 27 of 42 areas have them |

Counts: 208 enemies, 75 NPCs, 95 warps; quests use 12 task types and 15 action types.
Largest task types: `after_quest` 24, `spawn_item` 21, `after_conversation` 15, `defeat` 12.
Largest action types: `set_entry` 35, `give_exp` 26, `conversation` 23, `scene` 19.

Not measured yet: flight inside BF areas, LoG2's sprites (log2-decomp needs the stand-alone ROM), art coverage (M2).
