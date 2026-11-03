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

## M2 audit, ID pass (`tools/audit_log1.py`)
Actor IDs come from BF's scouter table, which links names to character IDs; text mentions no longer count, which removes Frieza and others.
These links haven't been checked in game for the right form or age, such as kid Gohan.

## M3 outdoor style test (`tools/map_convert.py`, 2026-11-03)
Areas 0, 4 and 24 convert with exact layouts: 568, 726 and 568 unique tiles, under the 896 limit. All three recoloured maps loaded in the emulator on Snake Way, and walking moved the player with collision active.
Automatic 8x8 matching doesn't work: it matched 1 of 756 tiles in area 4, using the one forest donor the loader could read.
The automatic ground swap replaced 7,913 tiles but chose a tree-canopy patch, so it needs a hand-picked ground patch.

## M3 style rule (user, 2026-11-03)
Match Buu's Fury only where feasible. If a result looks bad, recolour or ask.
Second test with hand-picked ground patches: area 0's sand swap damaged rocks and palm trunks, so that map stays recoloured.
Area 4's grass swap replaced 7,643 tiles and needs a decision: it lost flowers and shadows, and its olive ground doesn't match the trees.
`tools/bfmaps.py` reads Buu's Fury maps with animated tiles or empty chunks (static frames only). LoG1's animated tiles aren't ported yet.

## All areas recoloured (user decision, 2026-11-03)
Outdoor maps stay recoloured. 38 of 42 areas fit the 896-tile limit, using about 3.5 MB stored raw; areas 2, 12, 17 and 29 are over at 1,022, 946, 1,013 and 917.
17 areas have animated tiles, which aren't ported yet.

## Cutscene table (`tools/log1_scenes.py`)
22 table entries read, with 204 commands across 18 command functions. Two of them (0x0800CAC8, 0x0800CDF4) create actors through the area actor loader.
The other commands aren't named yet.

## Tile limit and animated tiles (2026-11-03)
`reduce_tiles` merges the least-used near-identical tiles, aiming for 860 so there's room to spare. Areas 2, 17 and 29 merged 57, 94 and 42 tiles (worst mean Lab distance per pixel 17.9, 13.7, 12.0); area 12 needed none once flipped tiles count as one.
All 42 areas now fit, at about 4.74 MB stored raw. Areas 2, 12, 17 and 29 loaded in the emulator without hanging.
`add_anim` writes LoG1's `tile_anim` as Buu's Fury animated tiles (16 areas use them). On area 0, 4 tiles change in VRAM with the port and none without it.
Each tile plays at LoG1's speed rounded to whole frames, and a base tile identical to another shares its animation.

## Cutscene commands and bosses (2026-11-03, read from reference C; names are provisional)
`0800CAC8`/`0800CDF4` create an actor through the area actor loader. `0800DC0C` changes an existing actor's sprite set. `0800DC8A` sets actor byte +0x13.
`0800CC60` plays a conversation, `0800CC74` plays music, `0800E078` starts a song from the track table. `0800CA74`, `0800CB24`, `0800CC02` and `0800D9C4` act on an existing actor.
Boss kill targets come from `defeat` tasks, and the actors are placed in area data with story flags. Raditz has no `defeat` task, and frieza2 and frieza3 aren't placed in any area.

## Boss fights in LoG1 (traced in reference C, 2026-11-03)
The `actor_leave` action sends message 2 to the matching character; its handler `sub_0800573A` builds an enemy on that character (`sub_08006D90`, row from byte table 0x0815A69C). So this action makes a character hostile.
Raditz: quest 22 turns him hostile after conversation 65, and quest 23 (`activate`, sprite 84) gives 4,000 EXP, plays scene 3 and warps to area 10.
Frieza: quests 64-67 do the same. `change_actor` sets actor byte +0x15 to the next sprite set (34 to 35 to 36), then quest 67 warps to area 41, where `frieza4` turns hostile; quest 68 (`defeat`) ends the game.
Reading `activate` as "this hostile character was beaten" fits the data, but it hasn't been observed running. The handler for that event is `sub_08005E12`.

## Live enemy spawn (`src/flight.c`, tested 2026-11-03)
The per-frame hook now has a table of up to 8 {flag, area entry, enemy record} rows. When a flag becomes set in that area, it calls the record's spawn function and adds the result to the object list, as the area loader does. Each row runs once per area visit.
Snake Way test, with the flag set by a direct RAM write: enemy count went from 0 to 1, object count from 5 to 6, and the game kept running for 240 more frames while walking. Objects later reached 11, which hasn't been explained.
Not tested: triggering from a real conversation, removing the NPC, fighting and defeating the enemy, its defeat script, or leaving and re-entering the area.

## Spawn, fight and defeat test (2026-11-03)
Snake Way, test enemy on an unused stats row (20 HP, 1,234 EXP) with a death script that sets flag 891. Flag 890 was set by RAM write.
Enemy count went 0, 1, 0 after A-button attacks, and flag 891 was set, so the fight and death script both ran. EXP gain wasn't read.
NPC removal failed: the object count only rose by the new enemy, so `find(8, 161)` found nothing or the NPC isn't in this list. The hook still contains this untested path.
The earlier rise to 11 objects didn't recur at this test's dump points and remains unexplained.

## Hostile-character chain (2026-11-03)
NPC removal fixed: the lookup is message type 5 with the value from `sub_08000158(index)`. Indexes 40, 135 and 161 each removed a different Snake Way NPC.
On Snake Way, talking to King Kai ran a real step list that set flag 890; the hook then spawned the enemy and removed him. A closed-loop bot (`tools/chain_test.py`) killed the enemy.
EXP rose by exactly 1,234 (2,200 to 3,434), and the player levelled up. The player's HP also fell during an earlier fixed-input run, so the enemy attacks.
