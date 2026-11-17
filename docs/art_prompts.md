# LoG1 Remake: prompts for the new villain and Bardock sprites

Last updated 2026-11-16. Prompts for hand-made (AI-drawn) replacements of the sprites that are built from other characters today:
Cooler's fourth form (the first Cooler fight), Dodoria, Lord Slug, giant Lord Slug, and Bardock. Cooler's final form is LoG2's own
Cooler sprite and needs nothing. Each prompt is tied to reference images in the pack (section 1).

## 1. How to use

1. **Build the reference pack** from your own ROMs (it is never committed):
   `python3 tools/prompt_refs.py <out dir>`. On your PC it is already in `log1remake/prompt_refs/`, one folder per prompt ID
   (`C1`, `D1`, `S1`, `S2`, `B1`), files numbered in the order to attach them.
2. **Generate one sheet per prompt** (Bardock: one sheet per action). Paste the style block from section 2 for that prompt, then the
   character block from section 5, then the ACTION line. Attach that prompt's files in order.
3. **The template does the work.** File 01 (Bardock: the `a_` file of the action) is the same sheet you want back, drawn as another
   character from the original game: same cells, same poses, same size, same pixel style. The prompt asks the model to redraw it cell
   for cell as the new character, so the new art lines up with the game frame for frame.
4. **Deliver at exact 4x**: every game pixel a clean 4x4 block, flat `#00FFFF` background, nothing else on the sheet.
5. **Save the output unedited** as `log1remake/art_in/<ID>_<name>[_<action>].png` and tell Claude. Claude snaps it back to 1x,
   maps it to the game's colours, puts each cell into the game and makes a preview sheet in `log1remake/previews/` before anything
   is committed. Nothing is changed in the game until you've seen it.

## 2. Style blocks

Measured from the cart, not guessed: LoG1's fighters are 16 px wide and 31-32 px tall, up to 15 colours each; LoG1 outlines hair, eyes
and soles in black and everything else in the darkest shade of the colour it borders (Frieza: 12 of his 79 edge pixels are black, Goku:
55 of 88, most of them hair); the lit side is the left (left half brighter than the right on 7 of 9 fighters measured); most stand on a
1 px black sole row.

### A. LoG1 fighter style (C1, D1, S1)

```
STYLE: Game Boy Advance pixel-art sprite sheet in the exact style of "Dragon Ball Z: The Legacy of Goku" (2002). File 01 is a sheet from that game: copy its pixel style exactly - head-to-body ratio (the head is about 12-13 px of a 31-32 px figure), 1-2 px eyes (a black pupil and a white pixel), outline weight, number of shades, the way cloth folds and muscles are drawn with 2-3 flat shades. The new sheet must look like the same artist drew it for the same game.
TEMPLATE: redraw file 01 cell for cell as the character below. Keep every cell's pose, size, position, facing and the feet on the cell's bottom row. Change only who it is: head, body shape where the character is bigger, costume, colours.
VIEW: 3/4 top-down RPG view. Row 1 DOWN = facing the camera; row 2 UP = back view (no face; hair, head, cape or tail from behind); row 3 LEFT = profile facing left (the game mirrors it for right; never draw a right-facing row).
SIZE: exactly the height given in the character block, in game pixels, from the top of the head to the soles, in every standing and walking cell. Every pose stays inside its 32x32 cell, tail and arms included. Not bigger, not more detailed than file 01.
OUTLINE AND LIGHT: 1 px outline; black only on hair, eyes, soles and the darkest gaps; everywhere else the outline is the darkest shade of the colour it borders. Light from the top-left: left side lighter, right side and undersides darker. 2-3 shades per material plus its outline shade. No dithering, no gradients, no anti-aliasing, no soft shading, no highlights rimming the outline.
COLOUR: at most 15 colours on the whole sheet plus the background, and only those in the character block's palette.
CANVAS: same grid as file 01: one frame per 32x32 cell, 8 game pixels of background between cells, 6 columns x 3 rows. Columns: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT.
DELIVERY SCALE: draw at 1x, then upscale exactly 4x with nearest-neighbour. Every game pixel is one clean 4x4 block. No sub-pixel lines, no blur.
BACKGROUND: flat #00FFFF, nothing else. No text, no grid lines, no shadows on the ground, no effects or energy (the game draws its own).
```

### B. LoG1 giant style (S2)

```
STYLE: Game Boy Advance pixel art in the exact style of the Great Ape in "Dragon Ball Z: The Legacy of Goku" (file 02): a giant drawn with real 1 px detail at about 60 px tall (not a small sprite blown up), the same outline, 2-3 flat shades per material, light from the top-left.
TEMPLATE: file 01 is the giant made today by doubling every pixel of the small sprite. Keep each cell's pose, facing and footing, but redraw it with single pixels at full giant detail: muscles, cloth folds, face.
VIEW: rows DOWN, UP, LEFT as in file 01 (the game mirrors LEFT for right).
SIZE: 60 px tall from the top of the head (antennae included) to the soles; every pose inside its 64x64 cell.
OUTLINE AND LIGHT, COLOUR, DELIVERY SCALE, BACKGROUND: as in style block A (15 colours at most, exact 4x, flat #00FFFF, no text, no effects).
CANVAS: one frame per 64x64 cell, 8 game pixels between cells, same columns as file 01: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT.
```

### C. LoG2 player style (B1)

```
STYLE: Game Boy Advance pixel-art sprite sheet in the exact style of "Dragon Ball Z: The Legacy of Goku II" (2003). The attached template (the `a_` file) is Goku's sheet for this action from that game: copy its pixel style exactly - head size, eyes, hair spikes, outline, shading, how fists and feet are drawn. The new sheet must look like the same artist drew it for the same game.
TEMPLATE: redraw the template cell for cell as the character below: same pose, same timing, same size, same position and facing in every cell, feet on the same row. Only the costume, face details and colours change. Bardock has Goku's build, face and hair, so the outline of the head and body stays almost the same; the armour changes the torso's outline.
VIEW: row 1 DOWN, row 2 UP (back), row 3 LEFT (profile facing left; the game mirrors it). Same rows as the template.
SIZE: exactly as the template: 32 px tall standing (top of the hair to the soles), and every pose inside its 32x32 cell.
OUTLINE AND LIGHT: as the template: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing.
COLOUR: at most 15 colours plus the background, only those in the character block's palette.
CANVAS: same grid as the template: one frame per 32x32 cell, 8 game pixels of background between cells, frames left to right in play order.
DELIVERY SCALE: draw at 1x, upscale exactly 4x with nearest-neighbour; every game pixel one clean 4x4 block.
BACKGROUND: flat #00FFFF. No text, no grid, no ground shadows. Leave out energy, beams, streaks and swooshes the template shows: the game draws them.
```

## 3. Sizes

| ID | Character | Height (game px) | Cell | Size reference |
|---|---|---|---|---|
| C1 | Cooler, fourth form | 32 | 32x32 | "much taller than Frieza, being similar in height to Goku" (file 04: LoG1 Goku, 32) |
| D1 | Dodoria | 32, about 22 wide standing | 32x32 | large and round; taller than Frieza |
| S1 | Lord Slug | 31 | 32x32 | Piccolo's height (file 01) |
| S2 | Lord Slug, giant | 60 | 64x64 | the Great Ape's scale (file 02) |
| B1 | Bardock | 32 | 32x32 | LoG2 Goku (every template) |

Engine limits: a fighter's frame is one piece of at most 32x32, a boss's at most 64x64. Anything crossing the cell edge is cut off.

## 4. Action lists

**Fighters (C1, D1, S1) and the giant (S2):** one sheet, 6 columns x 3 rows (DOWN, UP, LEFT):

| Column | Action | Game use |
|---|---|---|
| 1 | STAND | standing still |
| 2 | WALK 1 | walking, one foot forward (the game alternates WALK 1 and 2) |
| 3 | WALK 2 | walking, the other foot forward |
| 4 | ATTACK 1 | wind-up (also played while casting a ki attack) |
| 5 | ATTACK 2 | the hit: punch or blast thrown |
| 6 | HURT | knocked back (new: today the attack frames stand in) |

**Bardock (B1):** one sheet per action. Each template `a_<number>_template_<action>.png` shows the frames and their count.

| File suffix | Template | Frames | Pose |
|---|---|---|---|
| idle | a_00 | 2 | standing, breathing |
| walk | a_01 | 4 | walking |
| run | a_02 | 4 | dashing |
| hurt_fall | a_03 | 4 | hit, sitting back, lying, lying |
| powerup | a_04 | 4 | powering up, fists raised and lowered |
| kiblast | a_05 | 3 | one-hand ki blast |
| combo1 | a_06 | 4 | punch combo |
| combo2 | a_07 | 4 | punch combo |
| combo3 | a_08 | 4 | finisher |
| guard_step | a_13 | 4 | guarded step |
| spirit_cannon | a_18 | 7 | his special: draw back, thrust one open hand forward (no energy ball: the game draws it) |
| teleport | a_16 | 7 | optional: appearing (not used in the vision; skip it) |

## 5. Prompts

Every prompt is: the style block named in the heading + the character block + `ACTION: <the action>, rows DOWN, UP, LEFT.`

### C1. Cooler, fourth form (style A)

Pack `C1`: 01 template (LoG1 Frieza's final form), 02 today's Cooler (colours and parts to keep), 03 LoG2's own Cooler in his final form
(the official game's colours for him: copy how its white plates, magenta skin and blue gem are shaded), 04 LoG1 Goku (height).
```
CHARACTER: Cooler, Frieza's older brother, in his fourth form (his equivalent of Frieza's final form). Redraw file 01 (Frieza) as Cooler, who looks like a bigger, more masculine Frieza with the colours turned round: deep purple skin where Frieza is white, and white armour-like carapace where Frieza is purple.
- HEAD: smooth white carapace dome over the top and back of the head with a shiny blue oval spot on top; the face below it purple; narrow red eyes with black pupils; a short red stripe under each eye. No helmet ridges or horns.
- BODY: white carapace on the chest (one plate, no gem in the middle), shoulders, forearms and shins; everything else purple skin: neck, upper arms, belly, thighs, hands, feet. Long purple tail.
- BUILD: taller and broader than Frieza: 32 px, chest and shoulders 1 px wider each side; same poses as file 01.
HEIGHT: exactly 32 px, cell 32x32.
PALETTE (15 max): skin #E020E0 #A820A8 #782078, skin outline #202040; carapace #FFFFFF #D8D8D8 #A0A0A0, carapace outline #606060; blue spot #2080F8 #002088; eyes and stripes #D01028; black #000000.
MOVES: ATTACK 1 = a finger raised to fire a Death Beam; ATTACK 2 = a straight punch (file 01's own poses: keep them).
FILES: C1_cooler.png
```

### D1. Dodoria (style A)

Pack `D1`: 01 template (LoG1 Nappa: the closest build, bald head, armour with shoulder pads), 02 today's Dodoria, 03 a LoG1 Frieza
soldier (how this game draws Frieza's battle armour and scouter). Attach an official image of Dodoria as file 04 if you have one: it decides
the costume where this text is unsure.
```
CHARACTER: Dodoria, Frieza's general. Redraw file 01 (Nappa) as Dodoria: "a large and pink alien warrior with protruding spikes on his arms and head. He also wears a blue variant of the common Battle Armor that most of Frieza's men have, including the brown colored shoulder pads and a green scouter" (Dragon Ball Wiki).
- HEAD: big, round and bald, sitting low on the shoulders with almost no neck; short conical spikes all over the top and back of the head (4-5 visible from the front, more from behind); small eyes under a heavy brow; a wide mouth with thick lips; green scouter lens over his left eye (our right from the front) with a grey earpiece.
- BODY: barrel-shaped and fat, wider than file 01 at the belly (about 22 px wide standing, 3 px wider each side than Nappa at the belly, 1 px at the shoulders); pink skin; Frieza-army battle armour in blue on the chest and belly, brown shoulder pads; bare pink arms with a spike on each upper arm; dark bodysuit on the legs; white boots (likely: check file 04).
- BUILD: short thick legs under the round body; same poses as file 01.
HEIGHT: exactly 32 px including the head spikes, cell 32x32.
PALETTE (15 max): skin #F8B8D8 #F888B8 #B83878, skin outline #782040; armour #90C0F8 #2080F8 #2060A8; shoulder pads #C09050 #906030 #503000; bodysuit #202040; boots #FFFFFF #C0C0C0; scouter lens #70F870; black #000000.
MOVES: ATTACK 1 = leaning forward, mouth open (his mouth blast); ATTACK 2 = a heavy straight punch.
FILES: D1_dodoria.png
```

### S1. Lord Slug (style A)

Pack `S1`: 01 template (LoG1 Piccolo, a Namekian like him), 02 today's Slug. Attach an official image of young Lord Slug in battle,
helmet on, as file 03: it decides the costume where this text is unsure.
```
CHARACTER: Lord Slug, the Super Namekian warlord, young again by his wish. Redraw file 01 (Piccolo) as Slug: "tall stature, green skin, black eyes, and two antennae. He has a large cut on his left eye and two ear plates over his ears. He wears a black, hooded cloak, along with an orange and brown scarf around his neck. Black shoulder blades, brown medallion with straps on it and yellow undercoat under it" (Dragon Ball Wiki). In this film his skin is a yellow-green, not Piccolo's green and pink.
- HEAD: dark helmet over his scalp with his two antennae out of it (likely: check file 03), metal plates over his pointed ears, black eyes, a scar across his left eye (our right from the front), muscular jaw.
- BODY: black cloak hanging behind him (in place of Piccolo's cape, same length and shape), black shoulder pads, orange-and-brown scarf round the neck, brown medallion on the chest held by straps, yellow undercoat under it; yellow-green bare arms; dark trousers and boots (likely).
- BUILD: as Piccolo, a little more muscular; same poses as file 01.
HEIGHT: exactly 31 px, cell 32x32.
PALETTE (15 max): skin #C8E840 #88C838 #509800, skin outline #305800; helmet, cloak, pads #606060 #383838 #282828; scarf #F88000 #A86828; medallion #906030; undercoat #F8D000; ear plates #C0C0C0; eye whites #FFFFFF; black #000000.
MOVES: ATTACK 1 = one hand raised, palm out (a ki blast); ATTACK 2 = a stretching punch, arm thrown long.
FILES: S1_slug.png
```

### S2. Lord Slug, giant (style B)

Pack `S2`: 01 template (today's giant: S1's look with every pixel doubled), 02 LoG1's Great Ape (how this game draws a giant), and your
file 03 from S1. He has torn his helmet off.
```
CHARACTER: Lord Slug grown into a giant Namekian (Great Namek), helmet torn off: bare yellow-green head with his two long antennae and pointed ears, scar across his left eye, angry open mouth; the same costume as S1 (black shoulder pads, orange-and-brown scarf, brown medallion, yellow undercoat, dark trousers and boots) without the cloak; bulky, heavily muscled arms.
HEIGHT: exactly 60 px including the antennae, cell 64x64.
PALETTE (15 max): as S1, with the helmet's greys used only for the shoulder pads, trousers and boots.
MOVES: ATTACK 1 = arm raised, about to stamp or smash down; ATTACK 2 = punching down at the ground in front of him.
FILES: S2_slug_giant.png
```
Note: a 64x64 giant needs the boss-class actor Cooler's final form already uses (today's giant is a 32x64 figure drawn by hand in
src/flight.c). Claude moves him over when the art comes in.

### B1. Bardock (style C)

Pack `B1`: the `a_` templates (LoG2 Goku, one per action), `b_` today's Bardock (colours), `c_` LoG2 Vegeta's Androids Saga armour
(the cut of Bardock's armour: chest plate with shoulder straps, no shoulder pads). Attach the action's `a_` file first, then `b_`, then
`c_`.
```
CHARACTER: Bardock, Goku's father, as in "Dragon Ball Z: Bardock - The Father of Goku": Goku's face, build and spiky black hair, slightly darker skin, a long rough scar down his left cheek (our right from the front), a red headband (Tora's bloodied armband) tied round his forehead under his bangs, its two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- ARMOUR: green chest plate with green shoulder straps (no shoulder pads; file c_ shows the cut), a dark blue band at the waist and short green hip guards over the hips.
- ARMS: bare, muscular; long red wristbands from wrist to halfway up the forearm.
- LEGS: dark blue pants, a red band round each calf above the boots; dark blue-green boots.
- No scouter (likely: he has none by the final scene of the special).
HEIGHT: exactly as the template: 32 px standing, cell 32x32.
PALETTE (15 max): skin #E09880 #C88060 #A86828, skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040).
FILES: B1_bardock_<action>.png (one per row of section 4)
```

## 6. Sources

- Cooler: [Dragon Ball Wiki](https://dragonball.fandom.com/wiki/Cooler); his final form: LoG2's own sprite (the cart).
- Dodoria: [Dragon Ball Wiki](https://dragonball.fandom.com/wiki/Dodoria).
- Lord Slug: [Dragon Ball Wiki](https://dragonball.fandom.com/wiki/Lord_Slug).
- Bardock: [Dragon Ball Wiki](https://dragonball.fandom.com/wiki/Bardock).
- Every palette colour above is one Buu's Fury's sprite palette already has, so the art goes in without its shades merging.
