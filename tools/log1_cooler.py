"""Cooler's frames, made at build time from the cart's own art (rom/log1.gba, rom/log12.gba); nothing here holds art.

Owner (Nov 13), of the first try (LoG1's Frieza recoloured): "Cooler looks like Frieza not Cooler, also final form nothing like him at all".

Fourth form. Cooler's equivalent of Frieza's final form: "Cooler's skin is deep purple as opposed to the pure white of his brother. Cooler is
also much taller than Frieza, being similar in height to Goku ... several armor-like carapaces on his chest, shoulders, shins, and head";
"red stripes under his eyes and does not have a middle-colored spot on his chest like Frieza. He also sports a shiny blue spot on his skull"
(Dragon Ball Wiki, Cooler). Sources weighed: LoG1's Frieza forms (first, second, third, final), LoG2's Frieza and King Cold, Buu's Fury's
horned actors; LoG1's final-form Frieza (frieza4) has the build, the dome and the tail, and is drawn at LoG1 Goku's scale like every other foe,
so it is the body. Its colours turn round: his purple carapace becomes white and his white skin deep purple. Every pixel gets its part from
where it sits: the head (above the shoulders) keeps its dome as white carapace with the blue spot on top, the face goes purple with red
stripes under the eyes; the chest under the shoulders becomes the white chest plate (Frieza's gem goes into it); shoulders, forearms and shins
(Frieza's purple plates) are white; the rest of him is purple. He is made two rows taller (Goku's height): a row of his middle and a row of his
legs are drawn twice.

Final form. "He gets taller, and four horns grow out of his head and form a crown. His deltoid covers evolve into shoulder bows, and two
small spikes grow from his forearm covers. He gets blue spots on his legs and arms and his tail gets a white spike; the blue spot ... has
now become a full oval on his crown. His face is masked by a visor that covers all except his new pupil-less red eyes" (the same). LoG2's
record r31 is LoG2's own Cooler in that form (the owner, Nov 13: "Yeah they got the Cooler sprite in LoG2 just use that"), drawn about half
again Goku's height: crowned white carapace, the blue oval, the visor with the red eyes, shoulder bows, forearm spikes, the blue spots, the
spiked tail. It is used as it is, in its own colours, and the fourth form takes its colours from it. Being taller than an actor's 32x32 piece,
it is a big figure (src/flight.c, 64x64): standing, striding (the walk alternates them) and casting, four directions each. LoG2 has no
fourth-form Cooler, hence the rebuilt Frieza above.

    cellf(d, names, bf)          -> cell(row, col, fit): a 32x32 fourth-form frame in Buu's Fury OBJ colours, as log1_sprites.cell
    final_images(l2, bf)         -> [12 64x64 index arrays]: 3 poses x (down, up, side, side mirrored)
    final_tiles(images)          -> their 8bpp tiles, for src/flight.c
    python3 tools/log1_cooler.py check     the audit: prints the rules a frame breaks, exits 1 if any
"""
import numpy as np
import log1_sprites as S
from log1_turles import to_bf

# fourth form: LoG1 frieza4's colour indices
PLATE_I = {2: 0, 3: 0, 4: 1}                # his purple carapace, light to dark (4 its shadow, and its outline where it meets nothing)
SKIN_I = {15: 0, 5: 1, 6: 2, 9: 3}          # his white skin, light to dark (9 is its outline)
# LoG2's own Cooler (r31, his final form) sets the colours, so the two forms match: its purple skin, white plates and blue gem
SKIN = [(224, 32, 224), (168, 32, 168), (120, 32, 120), (32, 32, 64)]            # his purple, light to dark (the last its outline)
PLATE = [(248, 248, 248), (192, 192, 192), (112, 112, 112)]                      # his white carapace: light, shadow, outline
GEM = [(32, 128, 248), (32, 32, 120)]                                            # the blue spot on his skull
STRIPE = (214, 28, 48)                                                           # the red stripes under his eyes
BLACK = (0, 0, 0)
GREY = (176, 176, 196)


def parts(f, col):
    """Where things sit in a frieza4 frame: (top row, shoulder row, head centre column, bottom row), or None (lying down)."""
    ys, xs = np.nonzero(f)
    if not len(ys): return None
    top, bottom = ys.min(), ys.max()
    purple = np.isin(f, list(PLATE_I))
    for y in range(top + 9, bottom):
        if purple[y].sum() >= 2:
            hx = np.nonzero(purple[top:top + 5])[1]
            return top, y, float(hx.mean()), bottom
    return None


def fourth(f, col):
    """One frieza4 frame (LoG1 indices) as Cooler's fourth form: {(y, x): RGB}, before stretching."""
    p = parts(f, col); out = {}
    if p is None:                                           # lying down: colours only, by index
        for (y, x) in zip(*np.nonzero(f)):
            i = int(f[y, x]); out[y, x] = PLATE[PLATE_I[i]] if i in PLATE_I else SKIN[SKIN_I[i]] if i in SKIN_I else BLACK if i == 1 else GREY
        return out
    top, sh, cx, bottom = p; half = 3 if col == 2 else 4
    edge = lambda y, x: any(not (0 <= y + a < 32 and 0 <= x + b < 32) or not f[y + a, x + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for (y, x) in zip(*np.nonzero(f)):
        i = int(f[y, x])
        if i == 1: out[y, x] = BLACK
        elif i == 14: out[y, x] = GREY
        elif i in PLATE_I: out[y, x] = PLATE[2] if i == 4 and y <= sh + 1 and edge(y, x) else PLATE[PLATE_I[i]]       # below his shoulders the plates are too thin to outline
        elif sh < y <= sh + 4 and (abs(x - cx) <= half if col != 2 else cx - half <= x <= cx) and i != 9:
            out[y, x] = PLATE[0 if SKIN_I[i] < 2 else 1]        # his chest plate (from the side, the front of his chest)
        else: out[y, x] = SKIN[SKIN_I.get(i, 1)]
    # the blue spot on top of his skull: the dome's light pixels in its top rows, nearest its middle
    dome = sorted(((abs(x - cx) + abs(y - top - 2), y, x) for (y, x) in out if top + 1 <= y <= top + 3 and f[y, x] in (2, 3)))[:3]
    for k, (_, y, x) in enumerate(dome): out[y, x] = GEM[0 if k == 0 else 1]
    if col == 0:                                            # red stripes under his eyes, on the outer side of each
        eyes = sorted((x, y) for (y, x) in out if top + 6 <= y < sh and f[y, x] == 1 and f[y, x - 1] in (5, 15, 6) and f[y, x + 1] in (5, 15, 6))
        if len(eyes) == 2:
            for (x, y), dx in zip(eyes, (-1, 1)):
                if f[y + 1, x + dx] in (5, 15, 6): out[y + 1, x + dx] = STRIPE
    return out


def stretch(img, f, col, rows=2):
    """Two rows taller: a row of his middle (below the chest plate) and one of his legs drawn twice, the rest moved up to make room."""
    p = parts(f, col)
    if p is None: return img
    top, sh, _, bottom = p; n = min(rows, top)
    at = [sh + 6, bottom - 5][:n]
    out = img
    for a in sorted(at):                                        # each insert pushes everything above it up a row
        out = np.concatenate([out[1:a + 1], out[a:a + 1], out[a + 1:]], 0)
    return out


def cellf(d, names, bf):
    rec = S.record(d, d[S.SETS + names.index('frieza4')]); ident = np.arange(16, dtype=np.uint8); bfc = to_bf(bf)

    def cell(row, col, fit=False):
        if row == 17: return None                               # his standing frames carry Frieza's thought swirl: the walk's first frame stands in
        f = S.cell(d, rec, row, col, ident, fit)
        if f is None: return None
        out = np.zeros((32, 32), np.uint8)
        for (y, x), c in fourth(f, col).items(): out[y, x] = bfc(c)
        return stretch(out, f, col)
    return cell


# ---------- the final form: LoG2 r31, a 64x64 big figure ----------
FINAL = 'r31'
POSES = [(0, 0), (1, 1), (5, 0)]                              # (LoG2 animation, frame): standing, striding (the walk alternates them), casting
ORIGIN = (20, 56)                                             # where LoG2's origin goes on the 64x64 canvas: his body's middle on column 32, his
                                                              # feet on the last row (src/flight.c puts the canvas's (32, 56) on the actor's spot)
AXIS = 32                                                     # the side frame is mirrored about his middle, so he doesn't jump when he turns


def final_images(l2, bf):
    import sprites, log1_bardock as B
    rec = sprites.log2_rec(l2, FINAL); bfc = to_bf(bf)
    pal = np.frombuffer(l2[sprites.L2_PAL + 768:sprites.L2_PAL + 1536], np.uint8).reshape(256, 3)
    cmap = np.zeros(256, np.uint8)
    for i in range(1, 256): cmap[i] = bfc(tuple(int(v) for v in pal[i]))           # its own colours (the owner, Nov 13: "just use that")
    out = []
    for k, fr in POSES:
        ims = []
        for d in (0, 1, 2):
            x, y, w, h, attr, tp, img = B.frame_img(l2, rec, k, d, fr)
            can = np.zeros((64, 64), np.uint8); ox, oy = ORIGIN[0] + x, ORIGIN[1] + y
            ys, xs = np.nonzero(img)
            for yy, xx in zip(ys, xs):
                if 0 <= oy + yy < 64 and 0 <= ox + xx < 64: can[oy + yy, ox + xx] = cmap[img[yy, xx]]
            ims.append(can)
        side = ims[2]; mir = np.zeros_like(side)
        for c in range(64):
            if 0 <= 2 * AXIS - c < 64: mir[:, c] = side[:, 2 * AXIS - c]
        out += [ims[0], ims[1], side, mir]
    return out


def final_tiles(images):
    """64x64 index arrays -> their 8bpp tiles (OBJ 1D order: eight tiles a row), one after another."""
    return b''.join(im[y:y + 8, x:x + 8].tobytes() for im in images for y in range(0, 64, 8) for x in range(0, 64, 8))


# ---------- the audit ----------
def check(log1, l2, bf, names):
    """Fails (returns the broken rules) when: a fourth-form frame keeps any of Frieza's colours; his standing and walking frames don't line
    up (top of the dome, feet); a made frame lost pixels at the canvas edge; the final form's feet aren't on the canvas's last row (7 below the actor's spot, as LoG1's and LoG2's frames have them), its frames touch the
    canvas edge (cut off), or its side and mirrored side frames don't share his middle."""
    bad = []; bfc = to_bf(bf); ok = {bfc(c) for c in SKIN + PLATE + GEM + [STRIPE, BLACK, GREY]}
    cell = cellf(log1, names, bf)
    for row in (0, 1, 2, 3, 4, 5):
        for col in (0, 1, 2):
            f = cell(row, col)
            if f is None: continue
            stray = set(np.unique(f)) - ok - {0}
            if stray: bad.append('fourth form row %d col %d: colours not his %s' % (row, col, sorted(stray)))
    for col in (0, 1, 2):
        a, b = cell(0, col), cell(1, col)
        ta, tb = np.nonzero(a)[0].min(), np.nonzero(b)[0].min(); fa, fb = np.nonzero(a)[0].max(), np.nonzero(b)[0].max()
        if abs(int(ta) - int(tb)) > 1 or fa != fb: bad.append('fourth form col %d: standing and walking frames out of line (top %d/%d, feet %d/%d)' % (col, ta, tb, fa, fb))
    ims = final_images(l2, bf)
    for i, im in enumerate(ims):
        ys, xs = np.nonzero(im)
        if ys.max() != 63: bad.append('final form frame %d: feet on row %d, not 63' % (i, ys.max()))
        if xs.min() == 0 or xs.max() == 63 or ys.min() == 0: bad.append('final form frame %d: cut off at the edge' % i)
    for p in range(len(POSES)):
        s, m = ims[4 * p + 2], ims[4 * p + 3]
        if abs(np.nonzero(s)[1].mean() - (2 * AXIS - np.nonzero(m)[1].mean())) > 0.01: bad.append('final form pose %d: mirrored side off its middle' % p)
    return bad


if __name__ == '__main__':
    import os, sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path[:0] = [os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
    log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); bf = open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()
    l2 = open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read()[0x800000:]
    names = [l.split()[1] for l in open(os.path.join(ROOT, 'out', 'converted', 'log1data', 'assets', 'areas', 'SPRITES.txt'))]
    bad = check(log1, l2, bf, names)
    print('\n'.join(bad) or 'Cooler: all rules hold'); sys.exit(1 if bad else 0)
