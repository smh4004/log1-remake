"""Bardock's vision (post-game): his figure and Planet Vegeta. The story is a film in tools/log1_movies.py (FILMS 'bardock').

Bardock's figure: Legacy of Goku II's armoured Vegeta (the party's Vegeta, tools/log1_party.py) with LoG2 Goku's
head, in Bardock's colours. Made at build time from rom/log12.gba (the LoG I & II cart); nothing here holds art.

Bardock is Goku's father and looks like him, darker-skinned, with a scar on his left cheek and a red headband. His armour (the TV special, Bardock
- The Father of Goku): a green chest plate, dark navy shoulder and hip guards over a near-black bodysuit, red-brown wristbands, green boots.

Every frame of LoG2 Vegeta's animations (r134) gets the head of LoG2 Goku's frame with the same animation, direction and number (r57; the two
are built alike), placed on Vegeta's shoulders. Vegeta's greys (chest plate, gloves, boots share them) are told apart by where they sit: each
connected patch at the bottom is a boot, the biggest one in the torso is the chest plate, the rest are hands. Where Vegeta's body can't take the
head (an arm over it, a spin), Goku's own frame is used in Bardock's colours. tools/log1_party.py makes the figure a form of Goku's record;
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
GREEN = (240, 241, 242, 243)                          # chest plate and boots, light to dark
NAVY = (244, 245, 246)                                # shoulder and hip guards
BLACK = (247, 248, 249)                               # bodysuit
RED = (250, 251)                                      # headband
BAND = (252, 253)                                     # wristbands
SCAR = 254
COLOURS = {240: (150, 214, 120), 241: (104, 176, 84), 242: (64, 128, 56), 243: (34, 80, 34),
           244: (60, 66, 112), 245: (38, 42, 80), 246: (22, 24, 52),
           247: (48, 46, 60), 248: (30, 28, 40), 249: (16, 14, 22),
           250: (224, 40, 40), 251: (150, 18, 24),
           252: (176, 70, 46), 253: (112, 40, 28),
           254: (96, 40, 30)}


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
    """Vegeta's body in Bardock's colours (LoG2 indices), from his shoulders down."""
    out = v.copy(); h = v.shape[0]
    ys = np.nonzero(v)[0]; bottom = ys.max() if len(ys) else h - 1
    for i in range(3): out[v == PADS[i]] = NAVY[i]
    for i in range(3): out[v == SUIT[i]] = BLACK[i]
    grey = np.isin(v, GREYS)
    shade = {9: 0, 10: 0, 11: 1, 12: 1, 13: 2, 15: 3}
    parts = components(grey)
    torso = [p for p in parts if sv - 2 <= np.mean([y for y, _ in p]) < bottom - 7]
    chest = max(torso, key=len) if torso else []
    for p in parts:
        cy = np.mean([y for y, _ in p])
        if p is chest: kind = 'chest'
        elif cy >= bottom - 7: kind = 'boot'
        else: kind = 'hand'
        top = min(y for y, _ in p)
        for y, x in p:
            s = shade[int(v[y, x])]
            if kind in ('chest', 'boot'): out[y, x] = GREEN[s]
            else: out[y, x] = BAND[0 if s < 2 else 1] if y <= top + 1 else (18 if s < 2 else 20)       # a wristband, then a bare hand
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
    """The red band across his forehead: the two rows from the top of his face (or, from behind, the same height), over the head's width
    but its outline. Returns the band's top row."""
    skin = [y for (y, x), i in hd.items() if i in (18, 19, 20, 23)]
    if not skin: return None
    top = min(skin)
    for y in (top, top + 1):
        xs = sorted(x for (yy, x) in hd if yy == y)
        if len(xs) < 3: continue
        for x in xs[1:-1]: hd[y, x] = RED[0] if y == top else RED[1]
    return top


def goku_as_bardock(g):
    """Where Vegeta's body can't take Goku's head (arms over it, a spin): Goku's own frame in Bardock's colours, his gi green above his belt and
    black below it, his wristbands red-brown, a red band across his forehead."""
    out = g.copy(); h = g.shape[0]
    belt = [y for y in range(h) if (g[y] == 215).sum() >= 2]; by = belt[len(belt) // 2] if belt else h * 2 // 3
    shade = {32: 0, 33: 1, 34: 2, 35: 3}
    for y in range(h):
        for x in range(g.shape[1]):
            i = int(g[y, x])
            if i in shade: out[y, x] = GREEN[shade[i]] if y < by else BLACK[min(2, shade[i])]
            elif i == 215: out[y, x] = BLACK[1]
            elif i in (79, 80, 81): out[y, x] = BAND[0 if i < 81 else 1]
            elif i in GOKU_SKIN: out[y, x] = GOKU_SKIN[i]
    hd = {(y, x): int(out[y, x]) for y in range(h) for x in range(g.shape[1]) if out[y, x]}
    skin = [y for (y, x), i in hd.items() if i in (18, 19, 20, 23) and y < h // 2]
    if skin:
        top = min(skin)
        for y in (top, top + 1):
            xs = sorted(x for x in range(g.shape[1]) if out[y, x])
            for x in xs[1:-1]: out[y, x] = RED[0] if y == top else RED[1]
    return out


def bardock(v, g, d):
    """One frame: Vegeta's frame v and Goku's frame g (LoG2 indices, the same size or not), direction d (0 down, 1 up, 2/3 side)."""
    sv = shoulder_line(v, set(PADS)) or shoulder_line(v, set(PADS) | set(SUIT)); sg = shoulder_line(g, GOKU_GI)
    if not sv or not sg or sv[0] < 4 or sg[0] < 4 or not head(g, sg[0]): return goku_as_bardock(g)
    out = body(v, sv[0])
    hd = head(g, sg[0])
    if not hd: return out
    # Vegeta's head goes: hair, skin and eyes above his shoulders, in his head's columns
    vh = [x for y in range(max(1, sv[0] - 2)) for x in range(v.shape[1]) if v[y, x] == OUTLINE]
    if vh:
        for y in range(sv[0]):
            for x in range(max(0, min(vh) - 1), min(v.shape[1], max(vh) + 2)):
                if int(v[y, x]) in (OUTLINE, EYE) + VEG_SKIN: out[y, x] = 0
    dy, dx = sv[0] - sg[0], int(round(sv[1] - sg[1]))
    if sum(1 for (y, x) in hd if not (0 <= y + dy and 0 <= x + dx < out.shape[1])) * 4 > len(hd): return goku_as_bardock(g)     # the head won't fit on him
    hb = dict(hd)
    band = headband(hb, d != 1)
    if d == 1 and band is None:                         # from behind: a band across the middle of his hair
        ys = sorted({y for (y, x) in hb}); band = ys[len(ys) // 2] if ys else None
        if band is not None:
            for y in (band, band + 1):
                xs = sorted(x for (yy, x) in hb if yy == y)
                for x in xs[1:-1]: hb[y, x] = RED[0] if y == band else RED[1]
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
