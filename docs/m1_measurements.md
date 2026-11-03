# M1 first pass: LoG1 against Buu's Fury's limits

Measured 2026-11-03 with `tools/measure_log1.py` on log1-decomp 9e1fc99.

| Check | Limit | Result |
|---|---|---|
| Area size | 256x256 tiles (BF masks) | All 42 fit; largest is area 29 at 240x240 |
| Unique tiles, as stored | 896 per map (BF BG VRAM, per mapkit) | 4 over: area 2 (1,050), 12 (1,027), 17 (1,388), 29 (1,084) |
| Character frames | 32x32 one piece, bosses larger | 77 of 84 records fit 32x32; 7 records have larger frames |
| Painted rooms | Tile swaps need repeating tiles | 19 one-screen areas use nearly all 600 cells as unique tiles |
| Corridor fit, median share of walkable tiles a 3x3 tile body can reach | BF's own floors: 1.00 | LoG1: 0.98; worst are area 27 (0.64) and 26 (0.84) |
| Flight-only tiles | | 27 of 42 areas have them |

Counts: 208 enemies, 75 NPCs, 95 warps; quests use 12 task types and 15 action types.
Largest task types: `after_quest` 24, `spawn_item` 21, `after_conversation` 15, `defeat` 12.
Largest action types: `set_entry` 35, `give_exp` 26, `conversation` 23, `scene` 19.

Not measured yet: flight inside BF areas, LoG2's sprites (log2-decomp needs the stand-alone ROM), art coverage (M2).

## Flight inside Buu's Fury areas (tested 2026-11-03)
Only the world map (0:50) has map `+0x40` = 1, and its layer 1 uses handler 0x08007B63. Setting `+0x40` = 1 on Snake Way
scrambled the screen in the emulator. So native flight needs the Mode 7 map. In-area flight would need a new hook: for example, a
button that swaps the collision check to the play-area mask and plays animation slot 15. That hook hasn't been written or tested.

## Converter (`tools/convert_log1.py`)
All 42 areas, 75 quests and 80 conversation sets load, and generated scene code passes Gero's parser and assembler.
It hasn't run in game: IDs for items, music, speakers and areas are placeholders until M2 and M3.
32 quests contain at least one manual item: `scene` 19, `set_walkable` 7, `spawn_character` 6, `escort` 6, `place_item` 6,
`speed_up` 4, `obstacle` 3, `end_game` 1. 59 dialogue lines exceed about 100 characters and are split automatically.
All warps point at valid areas, and every area can be reached from the start, a story warp or a warp chain.

## Painted rooms, Method B (decided 2026-11-03)
All 19 painted rooms convert within the 896-tile limit (341 to 519 unique tiles, about 47-59 KB each stored raw).
Only area 7 has been run in the emulator.

## In-area flight prototype (2026-11-03)
Live collision masks: floor pointer at IWRAM 0x03001A4C, air mask at 0x03001A50, working copy at 0x03001A54.
Writing the air pointer into 0x03001A4C from the harness let the player leave Snake Way's floor and cross the clouds and sky.
Control runs stayed on the path. Not built yet: the button, the flying animation (slot 15), landing rules, and a code hook;
the test wrote RAM directly.

## M2 first pass (`tools/audit_log1.py`)
Name search only, across each game's enemy tables, scouter tables and UI text. Matches need actor IDs confirmed.
Of 109 LoG1 sprite sets: 46 have a name match, 47 are generic NPCs or enemies, and 16 have no match:
burter, crab, ginyu, guru, jeice, nail, nappa, oldman, ptero1-3, raditz, recoome, snkqueen, squirrel, wolf.
Text matches can be mentions rather than sprites; Frieza's four forms match only by name so far.
LoG1's own sprites could fill gaps at build time: the checked unmatched characters use 16x32, 32x32 or 32x16 frames.

## In-area flight hook (`src/flight.c`, tested 2026-11-03)
R takes off and lands, through a veneer on the key reader 0x0803D4A0 and 240 bytes of code at ROM 0xBF0000.
On Snake Way: walking down stops at y 200; after R the player reaches y 407; R over open sky is refused; R at y 176 lands,
restores the pointers, and walking stops at y 200 again.
Not built or tested: flying animation (slot 15), ki and combat while flying, changing areas while flying, and LoG1's flyable masks.

## LoG1 sprite importer (`tools/log1_sprites.py`)
1,248 of 1,340 frames fit Buu's Fury's 32x32 character limit. 92 frames in 8 character records need boss handling or shrinking.
One test frame set ran in the emulator on an existing NPC actor. Row-to-animation mapping is a first guess and not confirmed per character.
