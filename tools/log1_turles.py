"""Turles's frames: Legacy of Goku I's Goku, head and hair, on LoG1 Vegeta's Saiyan armour, in Turles's colours. Made at build time from
rom/log1.gba; nothing here holds art.

The owner (Nov 12): "Use Goku for Turles with reskinned Saiyan armor", then "You can do better on the Turles sprite and armor/colors". LoG1's own
armour is used rather than LoG2's, as it is drawn at LoG1 Goku's scale and in LoG1's style, and enemies use LoG1's frame rows. Turles as the
Tree of Might shows him (Dragon Ball Wiki): Goku's face and build with darker skin, a red-lensed scouter,
his tail wrapped round his waist, dark charcoal chest plate, slate grey shoulder and hip guards, a near-black bodysuit, white gloves and boots.

Every pixel of the armour gets its part from where it sits (LoG1 Vegeta's chest, gloves and boots share colours): the shoulder rows, the chest
between them and the belt, the hands beside it, the hip guards under the belt, the boots below them. The belt row becomes his tail.

    cellf(d, names, bf)      -> cell(row, col, fit): a 32x32 frame in Buu's Fury OBJ colours, as log1_sprites.cell, or None
"""
import numpy as np
import log1_sprites as S

# Turles's colours, light to dark
SKIN = [(196, 136, 88), (168, 110, 64), (138, 86, 46), (104, 62, 30), (80, 46, 22)]
SUIT = [(52, 50, 66), (34, 32, 46), (16, 14, 24)]
CHEST = [(112, 114, 124), (84, 86, 96), (60, 62, 70), (38, 40, 46)]
PADS = [(176, 186, 198), (138, 148, 162), (104, 112, 126), (72, 78, 90)]
WHITE = [(248, 248, 248), (214, 214, 222), (168, 168, 180), (110, 110, 124)]
TAIL = [(132, 86, 44), (100, 62, 30), (68, 40, 18)]
LENS, FRAME = (232, 36, 36), (156, 160, 168)
BLACK = (0, 0, 0)

# LoG1 Goku: 1 black, 3-6 skin, 14-15 eye whites; LoG1 Vegeta: 2 and 13-15 the armour's four shades (dark to light), 3-7 skin, 8-10 suit, 11-12 belt
GOKU_SKIN, VEG_SKIN, VEG_SUIT, VEG_BELT = [3, 4, 5, 6], [3, 4, 5, 6, 7], [8, 9, 10], [11, 12]
ARMOUR_SHADE = {15: 0, 14: 1, 13: 2, 2: 3}
GOKU_BODY, VEG_BODY = set(range(7, 14)), set(range(8, 13))
HEAD = {1, 2, 3, 4, 5, 6, 14, 15}                                    # Goku's hair, skin and eyes
# Vegeta frames whose head faces another way than Goku's frame of the same row: (row, col) -> Goku's (row, col). Vegeta's hurt frame (2) faces
# the front every way; Goku's idle frames (17) carry an effect over his head, so his first walking frame stands in.
HEAD_FROM = {(2, 1): (0, 0), (2, 2): (0, 0), (17, 0): (0, 0), (17, 1): (0, 1), (17, 2): (0, 2)}


def shoulders(f, body):
    """The first row with two or more body pixels, and the torso's middle (the median body column over the next 8 rows, so an arm held out
    doesn't pull it): (y, x), or None."""
    for y in range(32):
        if sum(f[y, x] in body for x in range(32)) >= 2:
            xs = [x for yy in range(y, min(32, y + 8)) for x in range(32) if f[yy, x] in body]
            return y, float(np.median(xs))
    return None


def to_bf(bf):
    """RGB -> the nearest Buu's Fury OBJ colour, as log1_sprites.colour_map."""
    import mapkit
    from room_test import lab
    P = lab(mapkit.palette(bf)[256:][1:]); cache = {}
    def f(c):
        if c not in cache: cache[c] = 1 + int(((lab(np.array([c], np.uint8))[0][None] - P) ** 2).sum(1).argmin())
        return cache[c]
    return f


def armour(vb, sv, col):
    """Turles's colour for each pixel of a Vegeta frame from his shoulders down: {(y, x): RGB}."""
    out = {}; cx = sv[1]; y0 = sv[0]
    belts = [(sum(vb[y, x] in VEG_BELT for x in range(32)), y) for y in range(y0, 32)]
    belt = max(belts)[1] if max(belts)[0] else y0 + 4                 # the row with the most of the belt
    half = 3 if col == 2 else 4
    for y in range(y0, 32):
        for x in range(32):
            i = int(vb[y, x])
            if not i: continue
            if i == 1: out[y, x] = BLACK
            elif i in VEG_SKIN: out[y, x] = SKIN[VEG_SKIN.index(i)]
            elif y == belt and abs(x - cx) <= half + 1: out[y, x] = TAIL[0 if i in (11, 15, 14) else 1 if i in (12, 13, 8, 9) else 2]      # his tail round his waist
            elif i in VEG_SUIT: out[y, x] = SUIT[VEG_SUIT.index(i)]
            elif i in VEG_BELT: out[y, x] = TAIL[VEG_BELT.index(i)]
            else:
                s = ARMOUR_SHADE.get(i, 1)
                if y <= y0 + 1: out[y, x] = PADS[s]                  # shoulders
                elif y < belt: out[y, x] = CHEST[s] if abs(x - cx) <= half else WHITE[s]      # chest, or the gloves beside it
                elif y <= belt + 4: out[y, x] = PADS[s] if abs(x - cx) <= half else WHITE[s]       # hip guards, or his hands
                else: out[y, x] = WHITE[s]                           # boots
    return out


def head(gb, sg, col):
    """Turles's colour for each pixel of Goku's head (above his shoulders, hair columns only): {(y, x): RGB}, with the scouter."""
    hair = [x for y in range(max(0, sg[0] - 2)) for x in range(32) if gb[y, x] in (1, 2)]
    x0, x1 = min(hair) - 1, max(hair) + 1; out = {}
    for y in range(sg[0]):
        for x in range(max(0, x0), min(32, x1 + 1)):
            i = int(gb[y, x])
            if i not in HEAD: continue
            out[y, x] = SKIN[GOKU_SKIN.index(i)] if i in GOKU_SKIN else BLACK if i in (1, 2) else ((255, 255, 255) if i == 15 else (180, 180, 180))
    eyes = [(x, y) for (y, x), c in out.items() if c in ((255, 255, 255), (180, 180, 180))]
    if col != 1 and eyes:
        ex = max(x for x, y in eyes) if col == 0 else min(x for x, y in eyes)      # his left eye: the right one from the front, the one seen from the side
        lens = [(x, y) for x, y in eyes if abs(x - ex) <= (0 if col == 2 else 1) and (col == 2 or x >= ex - 1 and x > min(x_ for x_, _ in eyes) + 2)]
        for x, y in lens: out[y, x] = LENS
        ey = max(y for x, y in lens)
        side = [x for (y, x), c in out.items() if y == ey and c in SKIN and (x > ex if col == 0 else True)]
        if side: out[ey, max(side)] = FRAME                          # the earpiece, at the side of his head
    return out


def cellf(d, names, bf):
    g = S.record(d, d[S.SETS + names.index('goku')]); v = S.record(d, d[S.SETS + names.index('vegeta1')])
    ident = np.arange(16, dtype=np.uint8); bfc = to_bf(bf)

    def cell(row, col, fit=False):
        vb = S.cell(d, v, row, col, ident)
        if vb is None: return None
        gr, gc = HEAD_FROM.get((row, col), (row, col))
        gb = S.cell(d, g, gr, gc, ident)
        sv, sg = shoulders(vb, VEG_BODY), shoulders(gb, GOKU_BODY) if gb is not None else None
        if gb is None or sg is None or sg[0] < 6:                       # no head to take here (lying): Goku's standing frame this way
            gb = S.cell(d, g, 0, gc, ident); sg = shoulders(gb, GOKU_BODY)
        out = np.zeros((32, 32), np.uint8)
        if sv is None: return out
        for (y, x), c in armour(vb, sv, col).items(): out[y, x] = bfc(c)
        dy, dx = sv[0] - sg[0], int(round(sv[1] - sg[1]))
        for (y, x), c in head(gb, sg, gc).items():
            if 0 <= y + dy < sv[0] and 0 <= x + dx < 32: out[y + dy, x + dx] = bfc(c)
        return out
    return cell


AURA = [(236, 200, 255), (176, 104, 240), (112, 48, 184)]


def cellf_fruit(d, names, bf):
    """Turles after the Tree of Might's fruit: the same figure in a violet aura (a two-pixel glow round him, brightest against his body),
    his plates and skin a shade richer."""
    base = cellf(d, names, bf); bfc = to_bf(bf)
    near, mid, far = (bfc(c) for c in AURA)

    def cell(row, col, fit=False):
        f = base(row, col, fit)
        if f is None: return None
        out = f.copy(); body = f > 0
        ring1 = np.zeros_like(body); ring2 = np.zeros_like(body)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ring1 |= np.roll(np.roll(body, dy, 0), dx, 1)
        ring1 &= ~body
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                if abs(dy) + abs(dx) <= 2: ring2 |= np.roll(np.roll(body, dy, 0), dx, 1)
        ring2 &= ~body & ~ring1
        out[ring1] = near
        yy = np.arange(32)[:, None]
        out[ring2 & (yy < 16)] = mid                                         # the glow streams up off him, fading
        out[ring2 & (yy >= 16) & ((yy + np.arange(32)[None]) % 2 == 0)] = far
        out[0, :] = np.where(body[0], out[0], 0); out[:, 0] = np.where(body[:, 0], out[:, 0], 0); out[:, 31] = np.where(body[:, 31], out[:, 31], 0)
        return out
    return cell
