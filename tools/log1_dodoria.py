"""Dodoria's frames (Bardock's vision): LoG1's Nappa made into Frieza's pink, spiked general. Made at build time from rom/log1.gba; nothing
here holds art.

Owner (Nov 13), of the first try (LoG1's Recoome tinted pink): "Dodoria isn't close to accurate". Dodoria, as the Dragon Ball Wiki has him:
"a large and pink alien warrior with protruding spikes on his arms and head. He also wears a blue variant of the common Battle Armor that most
of Frieza's men have, including the brown colored shoulder pads and a green scouter." Sources weighed: LoG1's Nappa, Recoome, Burter and
Frieza's soldiers; LoG2 (no Dodoria; its fat and spiked figures are beasts); Buu's Fury's round actors (Fat Buu, Yakon), drawn at twice LoG1's
scale. LoG1's Nappa wins: bald, big-headed and heavy-set, in Saiyan armour with shoulder pads and bare arms, at the scale of every other foe.

Every pixel gets its part from where it sits, as tools/log1_turles.py does: the head above the shoulder pads (pink; Nappa's moustache becomes
Dodoria's mouth, his brows and eyes stay), the shoulder pads (brown), the chest between them down to the belt (the blue armour), the arms
beside it (pink, bare to the hand), below the belt his dark bodysuit, the boots at the bottom (white, brown toes). Then he is made rounder:
two rows come out of the top of his egg-shaped dome, and each row is widened at his middle, most at the belly, so the outline swells
(Dodoria's barrel shape); he gets his spikes (three up from his scalp, one out from each upper arm) and his green scouter over his left eye.

    cellf(d, names, bf)      -> cell(row, col, fit): a 32x32 frame in Buu's Fury OBJ colours, as log1_sprites.cell, or None
    python3 tools/log1_dodoria.py check     the audit: prints the rules a frame breaks, exits 1 if any
"""
import numpy as np
import log1_sprites as S
from log1_turles import to_bf

# LoG1 Nappa's colour indices: skin light to dark, his armour's greys, blue, yellows, the belt's brown, black
SKIN_I = {3: 0, 4: 1, 5: 2, 11: 3, 6: 4}
GREYS, BLUE_I, YELLOW_I, BELT_I = (2, 14, 15), 7, (8, 9), 10
# Dodoria's colours, light to dark
PINK = [(255, 196, 216), (246, 152, 186), (220, 110, 152), (170, 70, 112), (110, 38, 70)]
ARMOUR = [(150, 178, 236), (98, 128, 206), (58, 84, 158), (30, 42, 96)]
PADS = [(200, 144, 84), (152, 100, 50), (102, 64, 30)]
SUIT = [(72, 64, 104), (48, 42, 74), (26, 22, 44)]
BOOT = [(248, 248, 248), (196, 196, 208)]
TOE = [(214, 162, 64), (150, 104, 30)]
MOUTH = (128, 28, 52)
LENS, FRAME = (72, 228, 96), (160, 164, 176)
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
# how many columns each band of rows gains at his middle: the head, his shoulders, his belly, his hips and legs
WIDEN = dict(head=2, shoulders=2, belly=4, hips=2, legs=2)
WIDEN_SIDE = dict(head=0, shoulders=1, belly=3, hips=1, legs=0)


def parts(f):
    """Where things sit in a Nappa frame: (top, shoulder-pad row, head's middle column, belt row, bottom), or None (lying down)."""
    ys, xs = np.nonzero(f)
    if not len(ys): return None
    top, bottom = int(ys.min()), int(ys.max())
    pads = np.isin(f, YELLOW_I)
    sh = next((y for y in range(top + 8, bottom) if pads[y].sum() >= 2), None)
    if sh is None or bottom - top < 24: return None
    hx = np.nonzero(f[top:top + 5])[1]; cx = float(np.median(hx))
    belts = [((f[y] == BELT_I).sum(), y) for y in range(sh, bottom)]
    bt = max(belts)[1] if max(belts)[0] >= 2 else sh + 7
    return top, sh, cx, bt, bottom


def colours(f, col):
    """Dodoria's colour for each pixel of a Nappa frame: {(y, x): RGB}, and the frame's parts."""
    p = parts(f); out = {}
    if p is None:                                           # lying down: by colour alone
        for y, x in zip(*np.nonzero(f)):
            i = int(f[y, x])
            out[y, x] = PINK[SKIN_I[i]] if i in SKIN_I else BLACK if i == 1 else ARMOUR[1] if i == BLUE_I else PADS[1] if i in YELLOW_I else ARMOUR[0] if i in GREYS else ARMOUR[3]
        return out, None
    top, sh, cx, bt, bottom = p; half = 3 if col == 2 else 4
    eye_rows = [y for y in range(top, sh) if (f[y] == 15).any()]
    ey = max(eye_rows) if eye_rows else sh - 4
    boots = next((y for y in range(bt + 2, bottom + 1) if np.isin(f[y], GREYS + (BLUE_I,)).sum() >= 2), bottom - 4)
    for y, x in zip(*np.nonzero(f)):
        i = int(f[y, x]); inner = abs(x - cx) <= half
        if y < sh:                                          # the head (and the top of his shoulders)
            if i in SKIN_I: out[y, x] = PINK[SKIN_I[i]]
            elif i == 1: out[y, x] = MOUTH if y > ey and col != 1 else BLACK          # Nappa's moustache: Dodoria's mouth
            elif i in (14, 15): out[y, x] = WHITE if i == 15 else BOOT[1]
            else: out[y, x] = PINK[3]
        elif y >= boots:                                    # his boots
            out[y, x] = BLACK if i == 1 else BOOT[0] if i == BLUE_I else BOOT[1] if i in GREYS else TOE[0] if i == 8 else TOE[1] if i == 9 else SUIT[1]
        elif y > bt + 1:                                    # below the belt: his bodysuit
            out[y, x] = BLACK if i == 1 else SUIT[min(2, SKIN_I.get(i, 1))] if i in SKIN_I else SUIT[1]
        elif i in SKIN_I: out[y, x] = PINK[SKIN_I[i]]
        elif i in YELLOW_I and not inner and y <= sh + 3: out[y, x] = PADS[0 if i == 8 else 1]     # shoulder pads
        elif not inner and y > sh + 3:                      # his forearms and hands: bare (Nappa's wristbands too)
            out[y, x] = BLACK if i == 1 else PINK[2]
        else:                                               # the armour, down to its lower edge at the belt
            out[y, x] = BLACK if i == 1 and (not inner or y >= bt) else ARMOUR[0] if i in (14, 15) else ARMOUR[1] if i in (2, BLUE_I) else ARMOUR[2] if i in YELLOW_I else ARMOUR[3]
    # the shoulder pads sit over the tops of his arms: skin touching a pad in the rows round it is pad too (Dodoria's are broad)
    pad = {k for k, c in out.items() if c in PADS}
    for (y, x) in list(out):
        if sh - 1 <= y <= sh + 2 and abs(x - cx) > half and out[y, x] in PINK[:3] and any((y + a, x + b) in pad for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))):
            out[y, x] = PADS[1]
    return out, p


def squashed(img, p):
    """Two rows out of the top of his dome (rows 2 and 3 of the head), the head lowered to close the gap: Nappa's tall egg of a head becomes
    Dodoria's rounder one, and his spikes get the room above it."""
    if p is None: return img
    top = p[0]
    return np.concatenate([np.zeros((2, 32, 4), np.uint8), img[:top + 2], img[top + 4:]], 0)


def widened(img, p, col):
    """Each row widened at his middle by its band's columns (the middle column repeated), the row kept centred: the outline swells at the belly."""
    if p is None: return img
    top, sh, cx, bt, bottom = p; w = WIDEN_SIDE if col == 2 else WIDEN; c = int(round(cx))
    out = np.zeros_like(img)
    for y in range(32):
        k = w['head'] if y < sh - 1 else w['shoulders'] if y < sh + 2 else w['belly'] if y <= bt else w['hips'] if y <= bt + 3 else w['legs']
        row = img[y]; new = np.concatenate([row[:c], np.repeat(row[c:c + 1], k, 0), row[c:]], 0)
        left = k // 2; out[y] = new[left:left + 32]
    return out


def spikes(img, col):
    """Three spikes up from his scalp, one out from each upper arm (from the side: two up from the back of his head, one off the arm), each
    two pixels long, pink with a dark tip-line."""
    m = img[:, :, 3] > 0; ys, xs = np.nonzero(m)
    if not len(ys): return img
    top = int(ys.min()); row = np.nonzero(m[top + 1])[0]
    x0, x1 = int(row.min()), int(row.max())
    out = img.copy()
    if col == 2: tops = [x1 - 1, x1 - 3]                    # facing left: the back of his head is on the right
    else: tops = [x0 + 1, (x0 + x1) // 2, x1 - 1]
    for x in tops:
        y = int(np.nonzero(m[:, x])[0].min()) if m[:, x].any() else top
        for k in (1, 2):
            if y - k >= 0: out[y - k, x] = PINK[1] + (1,) if k == 1 else PINK[4] + (1,)
    return out


def arm_spikes(img, p_rows, col):
    """One spike out from each upper arm, two rows under the shoulder pads: the outermost pixel of that row, pushed out two."""
    sh = p_rows; out = img.copy(); m = img[:, :, 3] > 0; y = sh + 2
    if y >= 32 or not m[y].any(): return out
    xs = np.nonzero(m[y])[0]
    for x, dx in ((int(xs.min()), -1), (int(xs.max()), 1)):
        if col == 2 and dx < 0: continue                     # from the side only the near arm's
        for k in (1, 2):
            if 0 <= x + dx * k < 32: out[y, x + dx * k] = PINK[1] + (1,) if k == 1 else PINK[4] + (1,)
    return out


def scouter(img, f, p, col):
    """The green scouter over his left eye (our right from the front; the eye we see from the side), its earpiece at the side of his head."""
    if p is None or col == 1: return img
    top, sh, cx, bt, bottom = p; out = img.copy()
    eyes = [(y, x) for y in range(top, sh) for x in range(32) if tuple(out[y, x]) == WHITE + (1,)]
    if not eyes: return out
    if col == 0: ex = max(x for y, x in eyes)
    else: ex = min(x for y, x in eyes)
    lens = [(y, x) for y, x in eyes if x == ex]
    for y, x in lens: out[y, x] = LENS + (1,)
    ey = max(y for y, x in lens); m = out[:, :, 3] > 0
    xs = np.nonzero(m[ey])[0]
    if col == 0 and len(xs): out[ey, int(xs.max())] = FRAME + (1,)    # the earpiece at the edge of his head
    return out


def cellf(d, names, bf):
    rec = S.record(d, d[S.SETS + names.index('nappa')]); ident = np.arange(16, dtype=np.uint8); bfc = to_bf(bf)

    def cell(row, col, fit=False):
        if row == 17: return None
        f = S.cell(d, rec, row, col, ident, fit)
        if f is None: return None
        cols, p = colours(f, col)
        img = np.zeros((32, 32, 4), np.uint8)                   # RGB and a painted flag (black is a colour here)
        for (y, x), c in cols.items(): img[y, x] = c + (1,)
        img = scouter(img, f, p, col)
        img = widened(squashed(img, p), p, col)
        if p is not None: img = arm_spikes(spikes(img, col), p[1], col)
        out = np.zeros((32, 32), np.uint8)
        for y, x in zip(*np.nonzero(img[:, :, 3])): out[y, x] = bfc(tuple(int(v) for v in img[y, x, :3]))
        return out
    return cell


def check(log1, bf, names):
    """Fails when: a frame keeps a colour that isn't Dodoria's; a standing frame and the walk's first frame differ in height, head or feet;
    a frame's widened figure was cut by the canvas edge; a front or back frame has no spikes above the head."""
    bad = []; bfc = to_bf(bf)
    ok = {bfc(c) for c in PINK + ARMOUR + PADS + SUIT + BOOT + TOE + [MOUTH, LENS, FRAME, BLACK, WHITE]}
    cell = cellf(log1, names, bf); rec = S.record(log1, log1[S.SETS + names.index('nappa')]); ident = np.arange(16, dtype=np.uint8)
    for row in range(6):
        for col in (0, 1, 2):
            g = cell(row, col)
            if g is None: continue
            stray = set(np.unique(g)) - ok - {0}
            if stray: bad.append('row %d col %d: colours not his %s' % (row, col, sorted(stray)))
            src = S.cell(log1, rec, row, col, ident); ys, xs = np.nonzero(g)
            if (xs.min() == 0 or xs.max() == 31) and not (np.nonzero(src)[1].min() == 0 or np.nonzero(src)[1].max() == 31): bad.append('row %d col %d: cut at the edge' % (row, col))
    for col in (0, 1, 2):
        a, b = cell(0, col), cell(1, col); ya, yb = np.nonzero(a)[0], np.nonzero(b)[0]
        if abs(int(ya.min()) - int(yb.min())) > 1 or ya.max() != yb.max(): bad.append('col %d: walking frames out of line' % col)
    for col in (0, 1):
        g = cell(0, col); src = S.cell(log1, rec, 0, col, ident)
        if np.nonzero(g)[0].min() >= np.nonzero(src)[0].min() + 2: bad.append('col %d: no spikes above his head' % col)
    return bad


if __name__ == '__main__':
    import os, sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path[:0] = [os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
    log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); bf = open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()
    names = [l.split()[1] for l in open(os.path.join(ROOT, 'out', 'converted', 'log1data', 'assets', 'areas', 'SPRITES.txt'))]
    bad = check(log1, bf, names)
    print('\n'.join(bad) or 'Dodoria: all rules hold'); sys.exit(1 if bad else 0)
