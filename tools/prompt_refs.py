"""The reference pack for docs/art_prompts.md: one folder per prompt ID, files numbered in the order to attach them. Every image is made from
your own ROMs (rom/log1.gba, rom/log12.gba, rom/bf.gba) on your machine; nothing here holds art, and the pack is never committed.

    python3 tools/prompt_refs.py <out dir>

Each sheet is laid out exactly as the prompt asks the new art to be: one frame per cell, frames left to right in the order the prompt lists,
rows DOWN, UP, LEFT; 8 px of background between cells; feet on each cell's bottom row; flat #00FFFF background; every game pixel a 4x4 block.
So a template sheet ("redraw this as ...") and the art that comes back line up cell for cell.
"""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_sprites as S, mapkit, sprites  # noqa: E402
import log1_bardock as B, log1_cooler as C, log1_dodoria as D, log1_movies as M  # noqa: E402

KEY = (0, 255, 255)                     # background: no character here uses cyan
GAP, SCALE = 8, 4
# the enemy sheet: (action, LoG1 row) in column order. stand = the walk's first frame (LoG1's own standing row carries a thought swirl)
ENEMY = [('stand', 0), ('walk1', 0), ('walk2', 1), ('attack1', 3), ('attack2', 4), ('hurt', 2)]
# Bardock's actions: (file suffix, LoG2 animation) in the order of docs/art_prompts.md section 4
PLAYER = [('idle', 0), ('walk', 1), ('run', 2), ('hurt_fall', 3), ('powerup', 4), ('kiblast', 5), ('combo1', 6), ('combo2', 7), ('combo3', 8),
          ('guard_step', 13), ('teleport', 16), ('spirit_cannon', 18)]


def sheet(rows, cell, path):
    """rows: [[RGBA cell arrays]] (None = empty cell) -> PNG at 4x."""
    n = max(len(r) for r in rows); W = n * cell + (n + 1) * GAP; H = len(rows) * cell + (len(rows) + 1) * GAP
    can = np.zeros((H, W, 3), np.uint8) + np.array(KEY, np.uint8)
    for j, r in enumerate(rows):
        for i, im in enumerate(r):
            if im is None: continue
            y0, x0 = GAP + j * (cell + GAP), GAP + i * (cell + GAP); m = im[:, :, 3] > 0
            can[y0:y0 + cell, x0:x0 + cell][m] = im[:, :, :3][m]
    Image.fromarray(can).resize((W * SCALE, H * SCALE), Image.NEAREST).save(path)


def rgba(idx, pal, cell=32):
    out = np.zeros((cell, cell, 4), np.uint8)
    if idx is None: return None
    h, w = idx.shape; oy, ox = cell - h, (cell - w) // 2
    m = idx > 0; sub = np.zeros((h, w, 4), np.uint8); sub[m, :3] = pal[idx[m]][:, :3]; sub[m, 3] = 255
    out[oy:oy + h, ox:ox + w] = sub
    return out


def log1_rows(d, names, sprite, tint=None, rows=ENEMY):
    rec = S.record(d, d[S.SETS + names.index(sprite)]); pal = np.array(S.palette(d, rec), np.uint8)
    if tint: pal = np.array(tint(pal.copy()), np.uint8)
    ident = np.arange(16, dtype=np.uint8)
    return [[rgba(S.cell(d, rec, r, col, ident), pal) for _, r in rows] for col in (0, 1, 2)]


def made_rows(cell, bfpal, rows=ENEMY):
    return [[rgba(cell(r, col), bfpal) for _, r in rows] for col in (0, 1, 2)]


def log2_cell(l2, rec, k, d, f, pal, conv=None, cell=32):
    """A LoG2 frame on a cell: its origin at (16, 24) of a 32x32 cell (as LoG1's), or at (20, 56) of a 64x64 one (log1_cooler.ORIGIN)."""
    try: g = B.frame_img(l2, rec, k, d, f)
    except Exception: return None
    if g is None: return None
    x, y, w, h, attr, tp, img = g
    if conv: img = conv(img, d)
    ox, oy = ((16, 24) if cell == 32 else C.ORIGIN); ox += x; oy += y
    can = np.zeros((cell, cell), np.uint8)
    for yy, xx in zip(*np.nonzero(img)):
        if 0 <= oy + yy < cell and 0 <= ox + xx < cell: can[oy + yy, ox + xx] = img[yy, xx]
    m = can > 0; out = np.zeros((cell, cell, 4), np.uint8); out[m, :3] = pal[can[m]]; out[m, 3] = 255
    return out


def log1_big(d, rec, row, col):
    """A LoG1 32x64 frame (the Great Ape's) as an index array (as log1_actors.Actors.big_images reads it)."""
    import struct
    q = S.u32(d, (S.u32(d, rec + 0x28) & S.MASK) + 4 * (row * 4 + col)) & S.MASK; _, _, w, h = struct.unpack_from('<hhHH', d, q); gfx = S.u32(d, q + 12) & S.MASK
    raw = np.frombuffer(d, np.uint8, w * h // 2, gfx); px = np.empty(w * h, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4; im = np.zeros((h, w), np.uint8)
    for k in range(w * h // 64): im[(k // (w // 8)) * 8:(k // (w // 8)) * 8 + 8, (k % (w // 8)) * 8:(k % (w // 8)) * 8 + 8] = px[k * 64:k * 64 + 64].reshape(8, 8)
    return im


def main(out):
    d = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); bf = open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()
    l2 = open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read()[0x800000:]
    names = [l.split()[1] for l in open(os.path.join(ROOT, 'out', 'converted', 'log1data', 'assets', 'areas', 'SPRITES.txt'))]
    bfpal = np.array(mapkit.palette(bf)[256:], np.uint8)
    l2pal = np.frombuffer(l2[sprites.L2_PAL + 768:sprites.L2_PAL + 1536], np.uint8).reshape(256, 3).copy()
    bdpal = l2pal.copy()
    for k, v in B.COLOURS.items(): bdpal[k] = v
    done = []

    def put(folder, name, rows, cell=32):
        os.makedirs(os.path.join(out, folder), exist_ok=True); p = os.path.join(out, folder, name); sheet(rows, cell, p); done.append(p)

    # C1 Cooler's fourth form
    put('C1', '01_template_log1_frieza_final_form.png', log1_rows(d, names, 'frieza4'))
    put('C1', '02_colours_current_cooler.png', made_rows(C.cellf(d, names, bf), bfpal))
    r31 = sprites.log2_rec(l2, C.FINAL)
    put('C1', '03_style_log2_cooler_final_form.png', [[log2_cell(l2, r31, k, dd, f, l2pal, cell=64) for k, f in ((0, 0), (1, 1), (1, 3), (6, 1))] for dd in (0, 1, 2)], 64)
    put('C1', '04_height_log1_goku.png', log1_rows(d, names, 'goku'))
    # D1 Dodoria
    put('D1', '01_template_log1_nappa.png', log1_rows(d, names, 'nappa'))
    put('D1', '02_colours_current_dodoria.png', made_rows(D.cellf(d, names, bf), bfpal))
    put('D1', '03_armour_log1_frieza_soldier.png', log1_rows(d, names, 'hench4'))
    # S1 Lord Slug, S2 the giant
    slug = M.recolour(M.SLUG_TINT)
    put('S1', '01_template_log1_piccolo.png', log1_rows(d, names, 'piccolo'))
    put('S1', '02_colours_current_slug.png', log1_rows(d, names, 'piccolo', slug))
    big = lambda rows: [[None if im is None else np.kron(im, np.ones((2, 2, 1), np.uint8)) for im in r] for r in rows]
    put('S2', '01_template_piccolo_at_giant_size.png', big(log1_rows(d, names, 'piccolo', slug)), 64)
    ape = S.record(d, d[S.SETS + names.index('oozaru1')]); apal = np.array(S.palette(d, ape), np.uint8); ident = np.arange(16, dtype=np.uint8)
    put('S2', '02_scale_log1_great_ape.png', [[rgba(log1_big(d, ape, r, col), apal, 64) for r in (0, 1, 5)] for col in (0, 1, 2)], 64)
    # B1 Bardock: one template per action (LoG2 Goku), then his colours and the armour's cut
    goku, veg = sprites.log2_rec(l2, B.GOKU), sprites.log2_rec(l2, B.VEGETA)
    for name, k in PLAYER:
        n = B.frame_count(l2, goku, k)
        put('B1', 'a_%02d_template_%s.png' % (k, name), [[log2_cell(l2, goku, k, dd, f, l2pal) for f in range(n)] for dd in (0, 1, 2)])
    put('B1', 'b_colours_current_bardock.png', [[log2_cell(l2, goku, k, dd, 0, bdpal, B.as_bardock) for k in (0, 1, 6)] for dd in (0, 1, 2)])
    put('B1', 'c_armour_cut_log2_vegeta.png', [[log2_cell(l2, veg, k, dd, 0, l2pal) for k in (0, 1, 6)] for dd in (0, 1, 2)])
    print('\n'.join(done))


if __name__ == '__main__':
    main(sys.argv[1])
