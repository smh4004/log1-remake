# LoG1 Remake: copy-ready art prompts

Last updated 2026-11-16. One block per sprite sheet: Cooler's fourth form (the first Cooler fight), Dodoria, Lord Slug, giant Lord Slug, and
Bardock (one block per action). Cooler's final form is LoG2's own Cooler sprite and needs nothing. Written by `tools/art_prompts.py`; edit
that, not this file.

**How to use.** For each block: attach the images it lists at the top, in that order (they are in `log1remake/prompt_refs/` on your PC;
`python3 tools/prompt_refs.py <dir>` makes them from your ROMs), paste the whole block, send. Save what comes back unedited as
`log1remake/art_in/<the file name the block gives>` and tell Claude: it is snapped back to 1x, mapped to the game's colours and shown to you
as a preview in `log1remake/previews/` before anything goes into the game.

Every block carries the whole style spec, measured from the carts: LoG1's fighters are 16 px wide and 31-32 px tall, up to 15 colours each;
the outline is black only on hair, eyes and soles and elsewhere the darkest shade of the colour it borders (Frieza: 12 of his 79 edge pixels
black, Goku 55 of 88, mostly hair); the lit side is the left (7 of 9 fighters measured); every palette colour is one Buu's Fury's sprite
palette has, so shades don't merge when the art goes in. A giant (S2) is a 64x64 boss frame: it moves to the boss-class actor Cooler's final
form uses when its art comes in.

Sources: [Cooler](https://dragonball.fandom.com/wiki/Cooler), [Dodoria](https://dragonball.fandom.com/wiki/Dodoria),
[Lord Slug](https://dragonball.fandom.com/wiki/Lord_Slug), [Bardock](https://dragonball.fandom.com/wiki/Bardock) (Dragon Ball Wiki).

## C1. Cooler, fourth form

Attach: `C1/01_template_log1_frieza_final_form.png`, `C1/02_colours_current_cooler.png`, `C1/03_style_log2_cooler_final_form.png`, `C1/04_height_log1_goku.png`

```text
I have attached 4 images, in this order:
1. C1/01_template_log1_frieza_final_form.png: the template, Frieza's final form from the original game. Redraw this sheet.
2. C1/02_colours_current_cooler.png: Cooler as the game shows him today (image 1 recoloured): keep which parts are white and which purple, and draw him properly.
3. C1/03_style_log2_cooler_final_form.png: Cooler's later, bigger form from Legacy of Goku II: copy how its white plates, purple skin and blue gem are shaded. Not its size, crown, spikes or mask.
4. C1/04_height_log1_goku.png: Goku from the same game. Cooler stands exactly his height.

Make a Game Boy Advance pixel-art sprite sheet of Cooler in his fourth form (his equivalent of Frieza's final form), for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from that game (2002): redraw it cell for cell as Cooler, in exactly the same pixel-art style and at exactly the same level of detail.

LAYOUT (exactly as image 1): 6 columns x 3 rows of 32x32-pixel cells, 8 pixels of background between cells. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Columns, left to right: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT. Keep each cell's pose, facing and position from image 1, feet on the cell's bottom row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Proportions as image 1: the head is about 12-13 px of a 31-32 px figure, short legs, big hands and feet.
- 1 px outline. Black only on hair, eyes, soles and the deepest gaps; everywhere else the outline is the darkest shade of the colour it borders.
- Light from the top-left: left side lighter, right side and undersides darker.
- 2-3 flat shades per material plus its outline shade. No dithering, no gradients, no anti-aliasing, no soft or airbrushed shading, no shine lines, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the blue spot 2x2 px, each red stripe 1 px under its eye, the eyes 1-2 px, the tail 2-3 px thick, the chest plate's lower edge one 1 px line. Leave out anything that would need more pixels than image 1 spends on it.

SIZE: 32 px tall from the top of the head to the soles in every standing and walking cell, about 16-17 px wide standing (the tail adds width).

CHARACTER: Cooler is Frieza's older brother: a taller, more muscular Frieza with the colours turned round, deep purple skin where Frieza is white and white armour-like carapace where Frieza is purple. "Cooler's skin is deep purple as opposed to the pure white of his brother. Cooler is also much taller than Frieza, being similar in height to Goku ... several armor-like carapaces on his chest, shoulders, shins, and head"; "red stripes under his eyes and does not have a middle-colored spot on his chest like Frieza. He also sports a shiny blue spot on his skull" (Dragon Ball Wiki).
- Head: a smooth white carapace dome over the top and back of the head with a shiny blue oval spot on top; the face below it purple; narrow red eyes; a short red stripe under each eye.
- Body: white carapace plates on the chest (one plate, no gem in the middle), the shoulders, the forearms and the shins. Everything else is purple skin: neck, upper arms, belly, thighs, hands and feet. A long purple tail.
- Build: 1 px broader each side than Frieza at the chest and shoulders.

COLOURS: use only these, at most 15 on the whole sheet: skin #E020E0 #A820A8 #782078; skin outline #202040; carapace #FFFFFF #D8D8D8 #A0A0A0; carapace outline #606060; blue spot #2080F8 #002088; eyes and stripes #D01028; soles and pupils #000000. Background flat #00FFFF.

POSES: ATTACK 1 = pointing one finger forward to fire a death beam. ATTACK 2 = a straight punch. The other cells keep image 1's poses.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file C1_cooler.png.
```

## D1. Dodoria

Attach: `D1/01_template_log1_nappa.png`, `D1/02_colours_current_dodoria.png`, `D1/03_armour_log1_frieza_soldier.png`, `(optional) an official picture of Dodoria`

```text
I have attached 4 images, in this order:
1. D1/01_template_log1_nappa.png: the template, Nappa from the original game (big, bald, in armour with shoulder pads). Redraw this sheet.
2. D1/02_colours_current_dodoria.png: Dodoria as the game shows him today (image 1 altered): his colours and parts, drawn properly now.
3. D1/03_armour_log1_frieza_soldier.png: a Frieza soldier from the same game: draw Dodoria's battle armour and scouter the way this game draws them.
4. (optional) an official picture of Dodoria: it decides his costume wherever this text says "likely".

Make a Game Boy Advance pixel-art sprite sheet of Dodoria, Frieza's general, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from that game (2002): redraw it cell for cell as Dodoria, in exactly the same pixel-art style and at exactly the same level of detail.

LAYOUT (exactly as image 1): 6 columns x 3 rows of 32x32-pixel cells, 8 pixels of background between cells. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Columns, left to right: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT. Keep each cell's pose, facing and position from image 1, feet on the cell's bottom row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Proportions as image 1: the head is about 12-13 px of a 31-32 px figure, short legs, big hands and feet.
- 1 px outline. Black only on hair, eyes, soles and the deepest gaps; everywhere else the outline is the darkest shade of the colour it borders.
- Light from the top-left: left side lighter, right side and undersides darker.
- 2-3 flat shades per material plus its outline shade. No dithering, no gradients, no anti-aliasing, no soft or airbrushed shading, no shine lines, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: head spikes 1 px wide and 2 px tall (4-5 along the top from the front, more from behind), one 2 px spike on each upper arm, the scouter lens 2x1 px with a 1 px earpiece, the mouth a 4-5 px line with a 1 px lip shade. Leave out anything that would need more pixels than image 1 spends on it.

SIZE: 32 px tall from the top of the head spikes to the soles in every standing and walking cell, about 22 px wide standing (his round belly).

CHARACTER: Dodoria is "a large and pink alien warrior with protruding spikes on his arms and head. He also wears a blue variant of the common Battle Armor that most of Frieza's men have, including the brown colored shoulder pads and a green scouter" (Dragon Ball Wiki).
- Head: big, round and bald, sitting low on the shoulders with almost no neck; short cone-shaped spikes over the top and back of the head; small eyes under a heavy brow; a wide mouth with thick lips; a green scouter over his left eye (our right from the front) with a grey earpiece.
- Body: barrel-shaped and fat, 3 px wider each side than Nappa at the belly and 1 px at the shoulders; pink skin; Frieza-army battle armour in blue over the chest and belly; brown shoulder pads; bare pink arms with a spike on each upper arm; a dark bodysuit on the legs; white boots (likely).
- Build: short thick legs under the round body.

COLOURS: use only these, at most 15 on the whole sheet: skin #F8B8D8 #F888B8 #B83878; skin outline #782040; armour #90C0F8 #2080F8 #2060A8; shoulder pads #C09050 #906030 #503000; bodysuit #202040; boots #FFFFFF #C0C0C0; scouter lens #70F870; soles and pupils #000000. Background flat #00FFFF.

POSES: ATTACK 1 = leaning forward, mouth wide open (his mouth blast). ATTACK 2 = a heavy straight punch. The other cells keep image 1's poses.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file D1_dodoria.png.
```

## S1. Lord Slug

Attach: `S1/01_template_log1_piccolo.png`, `S1/02_colours_current_slug.png`, `(optional) an official picture of young Lord Slug in battle with his helmet on`

```text
I have attached 3 images, in this order:
1. S1/01_template_log1_piccolo.png: the template, Piccolo from the original game (a Namekian like Slug). Redraw this sheet.
2. S1/02_colours_current_slug.png: Slug as the game shows him today (image 1 recoloured): his colours, drawn properly now.
3. (optional) an official picture of young Lord Slug in battle with his helmet on: it decides his costume wherever this text says "likely".

Make a Game Boy Advance pixel-art sprite sheet of Lord Slug, the Super Namekian warlord, young again by his wish, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from that game (2002): redraw it cell for cell as Lord Slug, in exactly the same pixel-art style and at exactly the same level of detail.

LAYOUT (exactly as image 1): 6 columns x 3 rows of 32x32-pixel cells, 8 pixels of background between cells. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Columns, left to right: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT. Keep each cell's pose, facing and position from image 1, feet on the cell's bottom row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Proportions as image 1: the head is about 12-13 px of a 31-32 px figure, short legs, big hands and feet.
- 1 px outline. Black only on hair, eyes, soles and the deepest gaps; everywhere else the outline is the darkest shade of the colour it borders.
- Light from the top-left: left side lighter, right side and undersides darker.
- 2-3 flat shades per material plus its outline shade. No dithering, no gradients, no anti-aliasing, no soft or airbrushed shading, no shine lines, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: antennae 1 px wide and 3-4 px long, the scar 2-3 px, ear plates 2x2 px, the medallion 2x2 px, the scarf 2 rows. Leave out anything that would need more pixels than image 1 spends on it.

SIZE: 31 px tall from the top of the head to the soles in every standing and walking cell, 16 px wide standing like image 1.

CHARACTER: Slug has a "tall stature, green skin, black eyes, and two antennae. He has a large cut on his left eye and two ear plates over his ears. He wears a black, hooded cloak, along with an orange and brown scarf around his neck. Black shoulder blades, brown medallion with straps on it and yellow undercoat under it" (Dragon Ball Wiki). In his film his skin is a yellow-green, not Piccolo's green and pink.
- Head: a dark helmet over his scalp with his two antennae coming out of it (likely), metal plates over his pointed ears, black eyes, a scar across his left eye (our right from the front), a hard square jaw.
- Body: a black cloak hanging behind him in place of Piccolo's cape (same length and shape as in image 1), black shoulder pads, an orange-and-brown scarf round the neck, a brown medallion on the chest held by straps, a yellow undercoat under it; bare yellow-green arms; dark trousers and boots (likely).
- Build: as Piccolo, a little more muscular.

COLOURS: use only these, at most 15 on the whole sheet: skin #C8E840 #88C838 #509800; skin outline #305800; helmet, cloak and pads #606060 #383838 #282828; scarf #F88000 #A86828; medallion #906030; undercoat #F8D000; ear plates #C0C0C0; eye whites #FFFFFF; soles and pupils #000000. Background flat #00FFFF.

POSES: ATTACK 1 = one hand raised, palm out (a ki blast). ATTACK 2 = a long stretching punch, arm thrown out. The other cells keep image 1's poses.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file S1_slug.png.
```

## S2. Lord Slug, giant

Attach: `S2/01_template_piccolo_at_giant_size.png`, `S2/02_scale_log1_great_ape.png`, `(optional) the official picture you used for Lord Slug, or one of him as a giant.`

```text
I have attached 3 images, in this order:
1. S2/01_template_piccolo_at_giant_size.png: the template, the giant as the game makes him today (Slug's small sprite with every pixel doubled). Keep its poses, not its chunky pixels.
2. S2/02_scale_log1_great_ape.png: the Great Ape from the original game: how this game draws a giant at full detail.
3. (optional) the official picture you used for Lord Slug, or one of him as a giant.

Make a Game Boy Advance pixel-art sprite sheet of Lord Slug grown into a giant Namekian, his helmet torn off, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from that game (2002): redraw it cell for cell as the giant Lord Slug, in exactly the same pixel-art style and at exactly the same level of detail.

LAYOUT (exactly as image 1): 6 columns x 3 rows of 64x64-pixel cells, 8 pixels of background between cells. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Columns, left to right: STAND, WALK 1, WALK 2, ATTACK 1, ATTACK 2, HURT. Keep each cell's pose, facing and position from image 1, feet on the cell's bottom row. Nothing may cross a cell's edge.

ART STYLE (copy image 2, the Great Ape, exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1's pixels are doubled (2x2 blocks): keep its poses, but draw the giant with single pixels at full giant detail, like image 2.
- 1 px outline. Black only on hair, eyes, soles and the deepest gaps; everywhere else the outline is the darkest shade of the colour it borders.
- Light from the top-left: left side lighter, right side and undersides darker.
- 2-3 flat shades per material plus its outline shade, muscles and cloth folds shaded the way image 2 shades the Great Ape's fur. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: as much detail as image 2 has at this size, no more. Every feature is whole pixels: antennae 2 px wide and 8-10 px long, the scar 4-5 px, the ears 3-4 px, the medallion 4x4 px, the eyes 3x2 px.

SIZE: 60 px tall from the tips of the antennae to the soles in every standing and walking cell, every pose inside its 64x64 cell.

CHARACTER: Slug as a giant Namekian (Great Namek), helmet torn off: a bare yellow-green head with his two long antennae and pointed ears, the scar across his left eye (our right from the front), an angry open mouth; bulky, heavily muscled bare arms; the same costume as before without the cloak: black shoulder pads, an orange-and-brown scarf round the neck, a brown medallion with straps on the chest, a yellow undercoat, dark trousers and boots (likely).

COLOURS: use only these, at most 15 on the whole sheet: skin #C8E840 #88C838 #509800; skin outline #305800; shoulder pads, trousers, boots #606060 #383838 #282828; scarf #F88000 #A86828; medallion #906030; undercoat #F8D000; eye whites #FFFFFF; outline and pupils #000000. Background flat #00FFFF.

POSES: ATTACK 1 = one arm raised high, about to smash down. ATTACK 2 = punching down at the ground in front of him. The other cells keep image 1's poses.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file S2_slug_giant.png.
```

## B1-idle. Bardock: idle

Attach: `B1/a_00_template_idle.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_00_template_idle.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: idle, 2 frames per row (standing, breathing), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 2 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_idle.png.
```

## B1-walk. Bardock: walk

Attach: `B1/a_01_template_walk.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_01_template_walk.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: walk, 4 frames per row (walking), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_walk.png.
```

## B1-run. Bardock: run

Attach: `B1/a_02_template_run.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_02_template_run.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: run, 4 frames per row (dashing), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_run.png.
```

## B1-hurt_fall. Bardock: hurt fall

Attach: `B1/a_03_template_hurt_fall.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_03_template_hurt_fall.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: hurt fall, 4 frames per row (hit, sitting back, lying, lying), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_hurt_fall.png.
```

## B1-powerup. Bardock: powerup

Attach: `B1/a_04_template_powerup.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_04_template_powerup.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: powerup, 4 frames per row (powering up, fists raised and lowered), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_powerup.png.
```

## B1-kiblast. Bardock: kiblast

Attach: `B1/a_05_template_kiblast.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_05_template_kiblast.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: kiblast, 3 frames per row (a one-hand ki blast), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 3 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_kiblast.png.
```

## B1-combo1. Bardock: combo1

Attach: `B1/a_06_template_combo1.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_06_template_combo1.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: combo1, 4 frames per row (a punch combo), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_combo1.png.
```

## B1-combo2. Bardock: combo2

Attach: `B1/a_07_template_combo2.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_07_template_combo2.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: combo2, 4 frames per row (a punch combo), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_combo2.png.
```

## B1-combo3. Bardock: combo3

Attach: `B1/a_08_template_combo3.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_08_template_combo3.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: combo3, 4 frames per row (a finisher), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_combo3.png.
```

## B1-guard_step. Bardock: guard step

Attach: `B1/a_13_template_guard_step.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_13_template_guard_step.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: guard step, 4 frames per row (a guarded step), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 4 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_guard_step.png.
```

## B1-spirit_cannon. Bardock: spirit cannon

Attach: `B1/a_18_template_spirit_cannon.png`, `B1/b_colours_current_bardock.png`, `B1/c_armour_cut_log2_vegeta.png`

```text
I have attached 3 images, in this order:
1. B1/a_18_template_spirit_cannon.png: the template, Goku doing this action in Legacy of Goku II. Redraw this sheet.
2. B1/b_colours_current_bardock.png: Bardock as the game shows him today (Goku recoloured): his colours.
3. B1/c_armour_cut_log2_vegeta.png: Vegeta's Androids Saga armour from the same game: the cut of Bardock's armour (chest plate with shoulder straps, no shoulder pads).

Make a Game Boy Advance pixel-art sprite sheet of Bardock, Goku's father, for a fan remake of "Dragon Ball Z: The Legacy of Goku" (GBA). Image 1 is a sprite sheet from its sequel, "Dragon Ball Z: The Legacy of Goku II" (GBA, 2003), whose sprites the remake uses for its playable figures: redraw it cell for cell as Bardock, in exactly the same pixel-art style and at exactly the same level of detail.

ACTION: spirit cannon, 7 frames per row (his special, the Final Spirit Cannon: drawing back, then thrusting one open hand forward (no energy ball: the game draws it)), timed and posed exactly as image 1.

LAYOUT (exactly as image 1): one 32x32-pixel cell per frame, 8 pixels of background between cells, 7 frames per row, left to right in play order. Row 1 = facing the camera (DOWN). Row 2 = back view, no face (UP). Row 3 = profile facing LEFT (never draw a right-facing row; the game mirrors it). Keep each cell's pose, timing, facing and position from image 1, feet on the same row. Nothing may cross a cell's edge.

ART STYLE (copy image 1 exactly; the new sheet must look like the same artist drew it for the same game):
- Image 1 is Goku. Bardock has Goku's build, face and hair, so keep the head and body outline almost pixel for pixel; only his armour changes the torso's outline.
- Outline, shading and proportions as image 1: black outline on hair and figure, light from the top-left, 2-3 flat shades per material. No dithering, no gradients, no anti-aliasing, no soft shading, no texture noise.
- DETAIL LEVEL: exactly as much detail as image 1 has, no more. Every feature is a few whole pixels: the headband one row across the forehead with 1-2 px ends at the back, the scar 2-3 px down his left cheek, wristbands 3 rows, legbands 1 row, shoulder straps 1 px wide, hip guards 2 rows, eyes exactly as image 1. Leave out the energy, streaks and swooshes image 1 shows.

SIZE: exactly as image 1: 32 px tall standing (top of the hair to the soles), every pose inside its 32x32 cell.

CHARACTER: Bardock, as in the TV special "Dragon Ball Z: Bardock - The Father of Goku", looks like Goku: the same face, build and spiky black hair, slightly darker skin, "the long, thick, rough scar running down his left cheek" (our right from the front), and a red headband (Tora's bloodied armband) tied round his forehead under his bangs, two short ends hanging at the back. "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands ... and dark blue and green boots" (Dragon Ball Wiki).
- Armour: a green chest plate with green shoulder straps (no shoulder pads; image 3 shows the cut), a dark blue band at the waist, short green hip guards.
- Arms: bare and muscular; long red wristbands from the wrist halfway up the forearm.
- Legs: dark blue pants, a red band round each calf above the boots, dark blue-green boots.
- No scouter (likely: by the special's last scene he has none).

COLOURS: use only these, at most 15 on the whole sheet: skin #E09880 #C88060 #A86828; skin outline and scar #683010; hair and outline #000000; eye whites #FFFFFF; armour #78D078 #20A040 #107800; pants and waist #2060A8 #002088 #202040; headband and bands #F83030 #900000; boots #206078 (shaded with the pants' #202040). Background flat #00FFFF.

OUTPUT: one PNG. Draw at 1x, then scale it up exactly 4x with nearest-neighbour, so every game pixel is one clean 4x4 block: no blur, no smoothing, no half-pixels, no pixels of other sizes. Nothing but the sprites on a flat #00FFFF background: no text, labels, numbers, grid lines, ground shadows, energy, sparks or speed lines (the game draws its own effects).

Name the file B1_bardock_spirit_cannon.png.
```
