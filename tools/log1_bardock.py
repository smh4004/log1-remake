"""Bardock's vision (post-game): his figure and Planet Vegeta. The story is a film in tools/log1_movies.py (FILMS 'bardock').

Bardock's figure: Legacy of Goku II's Goku (r57), every frame of every animation his own, recoloured into Bardock. Made at build time from
rom/log12.gba (the LoG I & II cart); nothing here holds art.

Bardock is Goku's father and looks like him, darker-skinned, with a scar on his left cheek and a red headband. The Dragon Ball Wiki, of the TV
special: "He wears a unique model of Battle Armor that is dark blue and green in color with shoulder straps ... In addition, he wears dark
blue pants, long red wristbands with matching legbands ... and dark blue and green boots", and later "Tora's blood-soaked armband as a
headband". The owner (Nov 13), of the first two tries (LoG2 Vegeta's armoured body with Goku's head pasted on): "neither is Bardock"
accurate, then "Bardock looks like shit and frames are bugged too and head is misaligned again". So no more pasting: LoG2 Goku is drawn
alike in every animation, head, body and all, and only his colours change, so nothing can come loose or jump.

Goku's colours are told apart by where they sit. His gi top (above his belt, between his arms: the columns it spans under his shoulders) is
Bardock's green chest armour; the blue of his undershirt between them, at the neck, is the dark blue bodysuit; the blue on his upper arms
(his undershirt's sleeves) is bare skin; the blue further down his arms (his wristbands) is a long red wristband, one row longer up the
forearm; his belt is the armour's dark green lower edge; his orange trousers are dark blue, their last row above the boots (the bottom five
rows) a red legband; the boots, laces and all, are dark. Lying down, the gi nearer his head is armour and the rest trousers. His skin is
darker, a red band crosses his forehead (one row, three above his eyes, or from behind as high above his shoulders; only across his head,
never his raised arms), and the scar runs down his left cheek (our right, from the front).
tools/log1_party.py makes the figure a form of Goku's record; src/skills.c puts it on him while he is on Planet Vegeta.

Planet Vegeta (area 70): LoG1's Namek landing site (area 24, Saiyan pods in their craters) in Planet Vegeta's rust reds, written into the
converted data like Yardrat (tools/log1_yardrat.py). No doors: the vision's lists take Goku there and back.

    COLOURS                                       LoG2 colour slot -> RGB for the new colours, for log1_party.colour_map
    as_bardock(g, d)                              one LoG2 Goku frame (LoG2 indices) in Bardock's colours, direction d (0 down, 1 up, 2/3 side)
    bardock_anim(ins, l2, src, k, cmap, cache, want, sl)    one BF animation from LoG2 animation k (as sprites.log2_anim)
    check(l2)                                     the audit: python3 tools/log1_bardock.py check
    add_area(L)                                   before the areas are built: writes area 70 into the converted LoG1 data
"""
import struct
import numpy as np

GOKU = 'r57'
VEGETA = 'r134'                                       # (not used for him any more)
# LoG2 colour indices (one OBJ palette for every LoG2 sprite): Goku's
OUTLINE, EYE = 1, 2
ORANGE = (32, 33, 34, 35)                             # his gi, light to dark
BLUE = (79, 80, 81, 215)                              # his undershirt, wristbands, belt and boots, light to dark
FACE = (114, 115, 116)                                # his face's skin, light to dark
SKIN = {114: 18, 115: 19, 116: 20, 19: 20, 20: 20, 21: 23, 22: 23, 23: 23}   # his skin in Vegeta's darker shades
ARM = {79: 18, 80: 19, 81: 20, 215: 23}               # an undershirt sleeve as bare arm
# new colours in LoG2 slots no source frame uses
GREEN = (240, 241, 242, 243)                          # chest armour, light to dark
NAVY = (244, 245, 246)                                # bodysuit and pants
BOOTS = (247, 248, 249)                               # dark blue-green boots
RED = (250, 251)                                      # headband
BAND = (252, 253)                                     # wristbands and legbands
SCAR = 254
COLOURS = {240: (124, 200, 104), 241: (80, 156, 70), 242: (50, 112, 50), 243: (28, 70, 32),
           244: (58, 64, 124), 245: (38, 42, 90), 246: (22, 24, 58),
           247: (54, 86, 98), 248: (34, 58, 68), 249: (18, 34, 40),
           250: (230, 36, 36), 251: (150, 18, 24),
           252: (214, 40, 40), 253: (140, 20, 24),
           254: (96, 40, 30)}


def layout(g):
    """Where things sit in a Goku frame: (shoulder row, gi's first and last column under it, belt rows, first boot row, bottom), or None
    (no gi in view)."""
    h, w = g.shape; ys, xs = np.nonzero(g)
    if not len(ys): return None
    if xs.max() - xs.min() > ys.max() - ys.min(): return None             # lying down: no rows to go by
    bottom = int(ys.max()); org = np.isin(g, ORANGE); blu = np.isin(g, BLUE)
    sh = next((y for y in range(h) if org[y].sum() >= 2), None)
    if sh is None: return None
    tx = [x for y in range(sh + 1, min(h, sh + 4)) for x in range(w) if org[y, x]]
    if not tx: return None
    t0, t1 = min(tx), max(tx)
    boot = bottom - 4
    rows = [(int(blu[y, t0:t1 + 1].sum()), -y) for y in range(sh + 2, boot - 1)]
    if rows and max(rows)[0] >= 2:
        by = -max(rows)[1]; belt = {by}
        if by + 1 < boot and blu[by + 1, t0:t1 + 1].sum() * 2 >= blu[by, t0:t1 + 1].sum(): belt.add(by + 1)
    else: belt = {(sh + boot) // 2}
    return sh, t0, t1, belt, boot, bottom


def as_bardock(g, d):
    """One LoG2 Goku frame (LoG2 indices) in Bardock's colours (LoG2 indices and the new slots), the same size, nothing moved."""
    out = g.copy(); h, w = g.shape; L = layout(g)
    hy, hx = np.nonzero(g == OUTLINE)
    near = None
    if L is None and len(hx):                           # lying down (or no gi in view): the gi nearer his head is armour, the rest trousers
        cx = float(np.median(hx)); far = max(np.nonzero(g)[1], key=lambda x: abs(x - cx)); near = lambda x: abs(x - cx) <= abs(far - cx) / 2
    for y, x in zip(*np.nonzero(g)):
        i = int(g[y, x])
        if i in SKIN: out[y, x] = SKIN[i]
        elif L is None:
            if i in ORANGE: out[y, x] = GREEN[ORANGE.index(i)] if near is None or near(x) else NAVY[min(2, ORANGE.index(i))]
            elif i in BLUE: out[y, x] = NAVY[min(2, BLUE.index(i))]
    if L is None: return out
    sh, t0, t1, belt, boot, bottom = L; top_belt = min(belt)
    for y, x in zip(*np.nonzero(g)):
        i = int(g[y, x]); inside = t0 <= x <= t1
        if i in ORANGE:
            s = ORANGE.index(i)
            out[y, x] = (BOOTS[min(2, s)] if y >= boot else BAND[s >= 2] if y == boot - 1 else GREEN[s] if y < top_belt else GREEN[3] if y in belt
                         else NAVY[min(2, s)])                                       # boots (his laces), the legband above them, armour, pants
        elif i in BLUE:
            s = BLUE.index(i)
            if y >= boot: out[y, x] = BOOTS[min(2, s)]                              # boots
            elif inside and y in belt: out[y, x] = GREEN[2 if s < 2 else 3]         # the armour's lower edge
            elif inside and y < top_belt: out[y, x] = NAVY[min(2, s)]               # the bodysuit at his neck
            elif not inside and y <= sh + 2: out[y, x] = ARM[i]                     # bare upper arms
            elif not inside: out[y, x] = BAND[s >= 2]                               # long red wristbands
            else: out[y, x] = NAVY[min(2, s)]
    # the wristbands one row longer, up the forearm
    for y, x in zip(*np.nonzero(np.isin(out, BAND))):
        if sh + 2 < y < boot and y > 0 and not t0 <= x <= t1 and int(g[y - 1, x]) in SKIN and not np.isin(out[y - 1, x], BAND):
            if int(g[y, x]) in BLUE: out[y - 1, x] = BAND[0]
    # the headband: one row across his head, inside its outline, at the top of his face (from behind, as high above his shoulders)
    eyes = [(y, x) for y, x in zip(*np.nonzero(g[:sh] == EYE))      # his eyes: white beside his face's skin, in the seven rows over his
            if y >= sh - 7 and any(0 <= x + b < w and int(g[y, x + b]) in FACE + (19, 20, 23) for b in (-1, 1))]    # shoulders (not a sparkle)
    band = min(y for y, _ in eyes) - 3 if eyes else sh - 6
    hair = [x for y, x in zip(*np.nonzero(g[max(0, band - 3):band + 4] == OUTLINE))]
    if 0 <= band < sh and hair:                         # across his head only: the run round its middle, at most a head wide (arms raised beside it stay)
        c = int(np.median(hair)); x0 = x1 = c
        while x0 - 1 >= max(0, c - 7) and g[band, x0 - 1]: x0 -= 1
        while x1 + 1 <= min(w - 1, c + 7) and g[band, x1 + 1]: x1 += 1
        for x in range(x0 + 1, x1):
            if g[band, x]: out[band, x] = RED[0]
    # the scar: his left cheek (our right from the front), down from under the eye
    if d == 0:
        if eyes:
            ey, ex = max(y for y, _ in eyes), max(x for _, x in eyes)
            for k in range(2):
                yy, xx = ey + 1 + k, ex + 1 - k
                if yy < sh and 0 <= xx < w and int(g[yy, xx]) in SKIN: out[yy, xx] = SCAR
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
    """LoG2 Goku's animation k (src: his record) as Bardock: a BF animation, as sprites.log2_anim makes. Returns ptr or 0."""
    n = frame_count(l2, src, k)
    if not n: return 0
    idx = list(range(n))[sl] if sl else list(range(n))
    if want and len(idx) < want: idx = [idx[i * len(idx) // want] for i in range(want)]
    ptrs = []
    for f in idx:
        for d in range(4):
            g = frame_img(l2, src, k, d, f)
            if g is None: return 0
            x, y, w, h, attr, tp, img = g
            assert w * h <= 1024, 'LoG2 frame %dx%d over the one-piece budget' % (w, h)
            key = ('bardock', tp, d == 0)                     # the scar is drawn on front frames only
            if key not in cache:
                bf = cmap[as_bardock(img, d)]
                data = bf.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
                cache[key] = ins.put(struct.pack('<II', 0, len(data)) + data)
            box = struct.pack('<bbBB', x, y, w, h)
            ptrs.append(ins.put(struct.pack('<I', 1) + box + box + struct.pack('<II', attr, cache[key])))
    return ins.put(struct.pack('<I', len(idx)) + struct.pack('<%dI' % len(ptrs), *ptrs))


def check(l2):
    """Fails when: a Bardock frame keeps Goku's orange or blue; a frame's size or place differs from Goku's (nothing may move); the standing
    front frame has no headband, scar or green chest; a frame with his gi in view has no red wristband or legband."""
    import sprites
    bad = []; src = sprites.log2_rec(l2, GOKU)
    for k in range(22):
        for f in range(frame_count(l2, src, k)):
            for d in range(3):
                try: g = frame_img(l2, src, k, d, f)
                except struct.error: g = None                    # (an animation the figure doesn't use: its table runs out)
                if g is None: continue
                out = as_bardock(g[6], d)
                left = set(np.unique(out)) & set(ORANGE + BLUE)
                if left: bad.append('animation %d frame %d dir %d: Goku colours left %s' % (k, f, d, sorted(left)))
                if (out > 0).sum() != (g[6] > 0).sum(): bad.append('animation %d frame %d dir %d: pixels moved' % (k, f, d))
    g = frame_img(l2, src, 0, 0, 0)[6]; out = as_bardock(g, 0)
    for what, idx in (('headband', RED), ('scar', (SCAR,)), ('green chest', GREEN), ('wristbands', BAND)):
        if not np.isin(out, idx).any(): bad.append('standing front: no %s' % what)
    return bad


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


if __name__ == '__main__':
    import os, sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path[:0] = [os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
    bad = check(open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read()[0x800000:])
    print('\n'.join(bad) or 'Bardock: all rules hold'); sys.exit(1 if bad else 0)
