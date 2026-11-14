"""Bardock's vision (post-game): his figure and Planet Vegeta. The story is a film in tools/log1_movies.py (FILMS 'bardock').

Bardock's figure: Legacy of Goku II's armoured Vegeta (the party's Vegeta, tools/log1_party.py) with LoG2 Goku's
head, in Bardock's colours. Made at build time from rom/log12.gba (the LoG I & II cart); nothing here holds art.

Bardock is Goku's father and looks like him, darker-skinned, with a scar on his left cheek and a red headband. The Dragon Ball Wiki, of the TV
special: "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps akin to what Vegeta wears from the
Androids Saga onwards, with the addition of hip guards. In addition, he wears dark blue pants, long red wristbands with matching legbands, a
green scouter on his left eye, and dark blue and green boots", and later "Tora's blood-soaked armband as a headband". The owner (Nov 13), of
the first try (green from shoulders to boots, a two-row band over the top of the hair): "neither is Bardock" accurate.

Every frame of LoG2 Vegeta's animations (r134: the Androids Saga armour, shoulder straps and all) gets the head of LoG2 Goku's frame with the
same animation, direction and number (r57; the two are built alike), placed on Vegeta's shoulders. Vegeta's greys (chest plate, gloves,
boots share them) are told apart by where they sit: everything in the bottom six rows is boot (its top row his red legband, the rest dark
blue-green); the patch round his shoulder straps is the chest plate, only as wide as it is under the straps (green); every other grey is a
hand (a long red wristband, the last two rows his bare hand). Vegeta's blue bodysuit is bare skin on his arms (beside the chest plate) and
Bardock's dark blue pants below it; the yellow straps are dark green. The band crosses his forehead (one row, at the top of his face), the
scar runs down his left cheek. Where Vegeta's body can't take the head (an arm over it, a spin), Goku's own frame is used in Bardock's
colours. tools/log1_party.py makes the figure a form of Goku's record;
src/skills.c puts it on him while he is on Planet Vegeta.

Planet Vegeta (area 70): LoG1's Namek landing site (area 24, Saiyan pods in their craters) in Planet Vegeta's rust reds, written into the
converted data like Yardrat (tools/log1_yardrat.py). No doors: the vision's lists take Goku there and back.

    COLOURS                                       LoG2 colour slot -> RGB for the new colours, for log1_party.colour_map
    bardock(v, g, d)                              one frame: Vegeta's v with Goku's g's head, in Bardock's colours (LoG2 indices)
    bardock_anim(ins, l2, src, k, cmap, cache, want, sl)    one BF animation from LoG2 animation k (as sprites.log2_anim)
    add_area(L)                                   before the areas are built: writes area 70 into the converted LoG1 data
"""
import struct
import numpy as np

VEGETA, GOKU = 'r134', 'r57'
# LoG2 colour indices (one OBJ palette for every LoG2 sprite)
OUTLINE, EYE = 1, 2
GREYS = (9, 10, 11, 12, 13, 15)                       # Vegeta's white armour, gloves and boots, light to dark
PADS = (40, 41, 42)                                   # his yellow shoulder straps
SUIT = (79, 80, 81)                                   # his blue bodysuit
VEG_SKIN = (17, 18, 19, 20, 23)
GOKU_SKIN = {114: 18, 115: 19, 116: 20, 20: 20, 21: 23, 22: 23, 23: 23}     # Goku's face in Vegeta's (darker) skin
GOKU_BODY = set(range(32, 36)) | {79, 80, 81, 215}    # his gi, undershirt and belt: below his head
GOKU_GI = set(range(32, 36))                          # his gi alone: his wristbands (and hands) can be above his head
# new colours in LoG2 slots no source frame uses
GREEN = (240, 241, 242, 243)                          # chest plate (and shoulder straps), light to dark
NAVY = (244, 245, 246)                                # his dark blue pants
BOOTS = (247, 248, 249)                               # dark blue-green boots
RED = (250, 251)                                      # headband
BAND = (252, 253)                                     # wristbands and legbands
SCAR = 254
BLACK = BOOTS                                         # (the old name)
COLOURS = {240: (124, 200, 104), 241: (80, 156, 70), 242: (50, 112, 50), 243: (28, 70, 32),
           244: (58, 64, 124), 245: (38, 42, 90), 246: (22, 24, 58),
           247: (54, 86, 98), 248: (34, 58, 68), 249: (18, 34, 40),
           250: (230, 36, 36), 251: (150, 18, 24),
           252: (214, 40, 40), 253: (140, 20, 24),
           254: (96, 40, 30)}
ARM_SKIN = {79: 18, 80: 20, 81: 23}                   # Vegeta's sleeves, light to dark, as bare arm (his own skin's shades)


def shoulder_line(img, body):
    """The first row with two or more body pixels, and the torso's middle (median body column over the next 8 rows), or None."""
    for y in range(img.shape[0]):
        if sum(int(v) in body for v in img[y]) >= 2:
            xs = [x for yy in range(y, min(img.shape[0], y + 8)) for x in range(img.shape[1]) if int(img[yy, x]) in body]
            return y, float(np.median(xs))
    return None


def components(mask):
    """4-connected patches of a boolean mask: [(list of (y, x))]."""
    seen = np.zeros_like(mask); out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]: continue
        stack = [(y0, x0)]; seen[y0, x0] = 1; pts = []
        while stack:
            y, x = stack.pop(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not seen[yy, xx]: seen[yy, xx] = 1; stack.append((yy, xx))
        out.append(pts)
    return out


def body(v, sv):
    """Vegeta's body in Bardock's colours (LoG2 indices), from his shoulders down (sv: the shoulder row)."""
    out = v.copy(); h, w = v.shape
    ys = np.nonzero(v)[0]; bottom = ys.max() if len(ys) else h - 1
    boot_top = bottom - 5
    # his armour's greys and whites, leaving out his hair's grey highlights (above his shoulders, inside his head's columns)
    shade = {EYE: 0, 9: 0, 10: 0, 11: 1, 12: 1, 13: 2, 15: 3}
    grey = np.isin(v, tuple(shade))
    vh = [x for y in range(max(1, sv - 2)) for x in range(w) if v[y, x] == OUTLINE]
    if vh: grey[:sv, max(0, min(vh) - 1):max(vh) + 2] = False
    # the chest plate: the grey patch round his shoulder straps (or, with none in view, the one nearest his middle under the shoulders),
    # cut to the columns it has in its top rows
    straps = [(y, x) for y, x in zip(*np.nonzero(np.isin(v, PADS))) if y < boot_top]
    cx = float(np.median([x for _, x in straps])) if straps else float(np.median(np.nonzero(v[sv:sv + 4])[1])) if v[sv:sv + 4].any() else w / 2
    parts = [p for p in components(grey & (np.arange(h)[:, None] < boot_top))]
    near = lambda p: min(abs(x - cx) + abs(y - sv - 2) for y, x in p)
    close = [p for p in parts if near(p) <= 3]
    chest = max(close, key=len) if close else min(parts, key=near) if parts else []
    span = [x for y, x in chest if y <= min(yy for yy, _ in chest) + 1] if chest else []
    x0, x1 = (min(span), max(span)) if span else (w, -1)
    cbot = max(y for y, x in chest if x0 <= x <= x1) if chest else sv
    in_chest = {(y, x) for y, x in chest if x0 <= x <= x1}
    for y, x in zip(*np.nonzero(v)):
        i = int(v[y, x])
        if i in PADS: out[y, x] = GREEN[PADS.index(i) + 1]
        elif i in SUIT:
            if y <= cbot and not x0 <= x <= x1: out[y, x] = ARM_SKIN[i]          # bare arms beside the chest plate
            else: out[y, x] = NAVY[SUIT.index(i)]
    def effect(p):                                  # an attack's white swoosh: in the air (touching nothing of him but greys), or all light greys
        return all(shade[int(v[y, x])] < 2 for y, x in p) or not any(       # (gloves and boots always have their darker outline greys)
            0 <= y + a < h and 0 <= x + b < w and v[y + a, x + b] and not grey[y + a, x + b] for y, x in p for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    hands = grey & (np.arange(h)[:, None] < boot_top)
    for y, x in in_chest: out[y, x] = GREEN[shade[int(v[y, x])]]; hands[y, x] = False
    for p in components(hands):                                                   # a long red wristband, then the bare hand
        if effect(p): continue
        last = max(y for y, _ in p)
        for y, x in p: out[y, x] = (18 if shade[int(v[y, x])] < 2 else 20) if y >= last - 1 else BAND[0 if shade[int(v[y, x])] < 2 else 1]
    for p in components(grey & (np.arange(h)[:, None] >= boot_top)):              # boots: the legband on top
        if effect(p): continue
        top = min(y for y, _ in p)
        for y, x in p: out[y, x] = BAND[0 if shade[int(v[y, x])] < 2 else 1] if y == top else BOOTS[min(2, shade[int(v[y, x])])]
    return out


def head(g, sg):
    """Goku's head (rows above his shoulders, his hair's columns), as {(y, x): LoG2 index} in Bardock's skin."""
    hair = [x for y in range(max(1, sg - 2)) for x in range(g.shape[1]) if g[y, x] == OUTLINE]
    if not hair: return {}
    x0, x1 = min(hair) - 1, max(hair) + 1; out = {}
    for y in range(sg):
        for x in range(max(0, x0), min(g.shape[1], x1 + 1)):
            i = int(g[y, x])
            if not i or i in GOKU_BODY: continue
            out[y, x] = GOKU_SKIN.get(i, i)
    return out


def headband(hd, front):
    """The red band across his forehead: one row, at the top of his face (the first row with his face's light skin), across the head inside
    its outline. Returns the band's row."""
    skin = [y for (y, x), i in hd.items() if i in (17, 18, 19, 20)]
    if not skin: return None
    top = min(skin)
    xs = sorted(x for (yy, x) in hd if yy == top)
    if len(xs) < 3: return None
    for x in xs[1:-1]: hd[top, x] = RED[0]
    return top


def goku_as_bardock(g):
    """Where Vegeta's body can't take Goku's head (arms over it, a spin): Goku's own frame in Bardock's colours, his gi green above his belt and
    dark blue below it, his wristbands red, a red band across his forehead."""
    out = g.copy(); h = g.shape[0]
    belt = [y for y in range(h) if (g[y] == 215).sum() >= 2]; by = belt[len(belt) // 2] if belt else h * 2 // 3
    shade = {32: 0, 33: 1, 34: 2, 35: 3}
    for y in range(h):
        for x in range(g.shape[1]):
            i = int(g[y, x])
            if i in shade: out[y, x] = GREEN[shade[i]] if y < by else NAVY[min(2, shade[i])]
            elif i == 215: out[y, x] = NAVY[1]
            elif i in (79, 80, 81): out[y, x] = BAND[0 if i < 81 else 1]
            elif i in GOKU_SKIN: out[y, x] = GOKU_SKIN[i]
    hd = {(y, x): int(out[y, x]) for y in range(h // 2) for x in range(g.shape[1]) if out[y, x]}
    top = headband(hd, True)
    if top is not None:
        for (y, x), i in hd.items(): out[y, x] = i
    return out


def bardock(v, g, d):
    """One frame: Vegeta's frame v and Goku's frame g (LoG2 indices, the same size or not), direction d (0 down, 1 up, 2/3 side)."""
    sv = shoulder_line(v, set(PADS)) or shoulder_line(v, set(PADS) | set(SUIT)); sg = shoulder_line(g, GOKU_GI)
    if not sv or not sg or sv[0] < 4 or sg[0] < 4 or not head(g, sg[0]): return goku_as_bardock(g)
    out = body(v, sv[0])
    hd = head(g, sg[0])
    if not hd: return out
    # Vegeta's head goes: hair (and its grey highlights), skin and eyes above his shoulders, in his head's columns
    vh = [x for y in range(max(1, sv[0] - 2)) for x in range(v.shape[1]) if v[y, x] == OUTLINE]
    if vh:
        for y in range(sv[0]):
            for x in range(max(0, min(vh) - 1), min(v.shape[1], max(vh) + 2)):
                if int(v[y, x]) in (OUTLINE, EYE) + VEG_SKIN + GREYS: out[y, x] = 0
    dy, dx = sv[0] - sg[0], int(round(sv[1] - sg[1]))
    if sum(1 for (y, x) in hd if not (0 <= y + dy and 0 <= x + dx < out.shape[1])) * 4 > len(hd): return goku_as_bardock(g)     # the head won't fit on him
    hb = dict(hd)
    band = headband(hb, d != 1)
    if d == 1 and band is None:                         # from behind: across his hair at the forehead's height (six rows over his shoulders,
        band = sg[0] - 6                                # as from the front)
        xs = sorted(x for (yy, x) in hb if yy == band)
        for x in xs[1:-1]: hb[band, x] = RED[0]
    if d == 0 and band is not None:                      # his scar: his left cheek, our right, under his eyes
        eyes = [(y, x) for (y, x), i in hb.items() if i == EYE]
        if eyes:
            ey, ex = max(y for y, _ in eyes), max(x for _, x in eyes)
            for k in range(2):
                if (ey + 2 + k, ex - k) in hb and hb[ey + 2 + k, ex - k] in (18, 19, 20, 23): hb[ey + 2 + k, ex - k] = SCAR
    for (y, x), i in hb.items():
        yy, xx = y + dy, x + dx
        if 0 <= yy < sv[0] and 0 <= xx < out.shape[1]: out[yy, xx] = i
    return out


# ---------- into the ROM ----------
def frame_img(l2, rec, k, d, f):
    """LoG2 animation k, direction d, frame f of the record at slice offset rec: (x, y, w, h, attr, tile ptr, pixels) or None."""
    import sprites
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', l2, o)[0]
    dirs = [u(rec + 0x4C + 16 * k + 4 * dd) for dd in range(4)]
    if not any(dirs): return None
    us = sorted(set(x for x in dirs if x))
    r = (dirs[d] or dirs[2] or us[0]) - sprites.L2_BASE + 12 * f
    x, y, w, h = struct.unpack_from('<bbBB', l2, r); attr, tp = struct.unpack_from('<II', l2, r + 4)
    if not (w and h and w * h <= 4096 and sprites.L2_BASE <= tp < sprites.L2_BASE + len(l2)): return None
    o = tp - sprites.L2_BASE; t, size = struct.unpack_from('<II', l2, o)
    data = l2[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(l2, o + 8, size)[0])
    px = np.frombuffer(data, np.uint8)
    if len(px) < w * h: return None
    return x, y, w, h, attr, tp, px[:w * h].reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w).copy()


def frame_count(l2, rec, k):
    import sprites
    u = lambda o: struct.unpack_from('<I', l2, o)[0]
    dirs = [u(rec + 0x4C + 16 * k + 4 * d) for d in range(4)]
    if not any(dirs): return 0
    us = sorted(set(x for x in dirs if x)); gaps = [b - a for a, b in zip(us, us[1:])]
    return min(gaps) // 12 if gaps else 1


def bardock_anim(ins, l2, src, k, cmap, cache, want=0, sl=None):
    """LoG2 Vegeta's animation k (src: his record) as Bardock: a BF animation, as sprites.log2_anim makes. Returns ptr or 0."""
    import sprites
    goku = sprites.log2_rec(l2, GOKU); n = frame_count(l2, src, k)
    if not n: return 0
    idx = list(range(n))[sl] if sl else list(range(n))
    if want and len(idx) < want: idx = [idx[i * len(idx) // want] for i in range(want)]
    ng = frame_count(l2, goku, k); ptrs = []
    for f in idx:
        for d in range(4):
            v = frame_img(l2, src, k, d, f)
            if v is None: return 0
            x, y, w, h, attr, tp, img = v
            assert w * h <= 1024, 'LoG2 frame %dx%d over the one-piece budget' % (w, h)
            g = frame_img(l2, goku, k, d, f % ng) if ng else None
            key = ('bardock', tp, g[5] if g else 0, d in (2, 3))
            if key not in cache:
                out = bardock(img, g[6] if g else None, d) if g else body(img, 0)
                if out.shape != img.shape: x_, y_, w_, h_, attr_ = g[:5]           # Goku's own frame in Bardock's colours: his box
                else: x_, y_, w_, h_, attr_ = x, y, w, h, attr
                bf = cmap[out]
                data = bf.reshape(h_ // 8, 8, w_ // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
                cache[key] = (ins.put(struct.pack('<II', 0, len(data)) + data), (x_, y_, w_, h_, attr_))
            tptr, (x_, y_, w_, h_, attr_) = cache[key]
            box = struct.pack('<bbBB', x_, y_, w_, h_)
            ptrs.append(ins.put(struct.pack('<I', 1) + box + box + struct.pack('<II', (attr & 0x30000000) | (attr_ & ~0x30000000), tptr)))
    return ins.put(struct.pack('<I', len(idx)) + struct.pack('<%dI' % len(ptrs), *ptrs))


# ---------- the vision's world: Planet Vegeta ----------
VISION, SOURCE, MUSIC = 70, 24, 6                    # LoG1's Namek landing site (area 24: the Saiyans' pods in their craters); Frieza's base's music
START = (352, 592)                                   # area 24's own start: the path in at the bottom


def recolour_tiles(pal):
    """Namek's blue ground to Planet Vegeta's rust-red dust, its brown cliffs to dark crimson rock, green to ochre, sand to orange. Greys stay."""
    import colorsys
    out = []
    for r, g, b in pal:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); d = h * 360
        if s > 0.15:
            if 170 <= d <= 250: h, s, v = 14 / 360, min(1, s * 0.85 + 0.1), v * 0.82          # the ground
            elif d < 45 or d > 330: h, s, v = 355 / 360, min(1, s * 1.1), v * 0.7           # cliffs and rocks
            elif d < 70: h, s = 28 / 360, min(1, s * 1.1)                                    # sand
            elif d < 170: h, s, v = 38 / 360, s * 0.8, v * 0.75                              # grass and trees
        out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v)))
    return out


def add_area(L):
    """Area 70 in the converted data: area 24's map with recoloured tiles, no actors or doors."""
    import json, os, re
    from PIL import Image
    M = os.path.join(L, 'assets', 'maps')
    for f in os.listdir(os.path.join(M, 'tiles')):
        m = re.match(r'area%02d(_block\d+)?\.png$' % SOURCE, f)
        if not m: continue
        im = Image.open(os.path.join(M, 'tiles', f)); assert im.mode == 'P'
        pal = im.getpalette(); rgb = [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]
        out = im.copy(); out.putpalette([c for t in recolour_tiles(rgb) for c in t]); out.save(os.path.join(M, 'tiles', 'area%02d%s.png' % (VISION, m.group(1) or '')))
    tmx = open(os.path.join(M, 'area%02d.tmx' % SOURCE)).read()
    tmx = tmx.replace('tiles/area%02d' % SOURCE, 'tiles/area%02d' % VISION).replace('name="area%02d"' % SOURCE, 'name="area%02d"' % VISION)
    tmx = tmx.replace('<property name="area" type="int" value="%d"/>' % SOURCE, '<property name="area" type="int" value="%d"/>' % VISION)
    open(os.path.join(M, 'area%02d.tmx' % VISION), 'w').write(tmx)
    info = json.load(open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % SOURCE)))
    json.dump(dict(info, area=VISION, actors=[], pickups=[], objects=[], triggers=[], start=list(START), music=MUSIC), open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % VISION), 'w'))
