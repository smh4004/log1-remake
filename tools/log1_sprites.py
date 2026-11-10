"""Import Legacy of Goku character frames into a Buu's Fury ROM at build time. Nothing here contains ROM art.

Reads rom/log1.gba: gCharacterTable (0x5C0C80), sprite-set byte table (0x15A709), 76 frame records per character
(19 rows x 4 directions: down, up, side, side mirrored). Frames are 4 bpp with a 16-colour palette; they become 8 bpp
Buu's Fury frames using the nearest OBJ colours in Lab. Row meanings vary by character (see ROWS), so confirm per character.
"""
import os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import mapkit, sprites  # noqa: E402
from room_test import lab  # noqa: E402

CHARS, SETS, N_SETS, N_CHARS = 0x5C0C80, 0x15A709, 109, 84
ROWS = dict(walk=[0, 1], death=[2], melee=[3, 4], idle=[17])
MASK = 0x1FFFFFF
u32 = lambda d, o: struct.unpack_from('<I', d, o)[0]


def record(d, c): return u32(d, CHARS + 4 * c) & MASK


def palette(d, rec):
    p = u32(d, rec + 0x24) & MASK; v = struct.unpack_from('<16H', d, p)
    return np.array([[(x & 31) * 255 // 31, (x >> 5 & 31) * 255 // 31, (x >> 10 & 31) * 255 // 31] for x in v], np.uint8)


def colour_map(d, rec, bf, tint=None):
    """LoG1 palette index -> BF OBJ palette index (index 0 stays transparent). tint: a function of the 16 RGB colours, for a recoloured character."""
    obj = mapkit.palette(bf)[256:]; P = lab(obj[1:]); Q = lab(tint(palette(d, rec)) if tint else palette(d, rec))
    m = (1 + ((Q[:, None] - P[None]) ** 2).sum(2).argmin(1)).astype(np.uint8); m[0] = 0
    return m


def cell(d, rec, row, col, cmap, fit=False):
    """One frame on a 32x32 canvas with LoG1's origin at the bottom centre, or None."""
    p = u32(d, (u32(d, rec + 0x28) & MASK) + 4 * (row * 4 + col))
    if not p: return None
    o = p & MASK; x, y, w, h = struct.unpack_from('<hhHH', d, o); gfx = u32(d, o + 12) & MASK
    tw, th = w // 8, h // 8; raw = np.frombuffer(d, np.uint8, tw * th * 32, gfx)
    px = np.empty(raw.size * 2, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4
    img = np.zeros((h, w), np.uint8)
    for k in range(tw * th):
        img[(k // tw) * 8:(k // tw) * 8 + 8, (k % tw) * 8:(k % tw) * 8 + 8] = px[k * 64:k * 64 + 64].reshape(8, 8)
    out = np.zeros((32, 32), np.uint8); X, Y = x + 8, y + 24
    if not (0 <= X and X + w <= 32 and 0 <= Y and Y + h <= 32):
        if not fit: return None
        f = max(w, h) / 32 if max(w, h) > 32 else 1                    # big creatures shrink to BF's 32x32 limit for character frames
        nw, nh = max(1, int(w / f)), max(1, int(h / f)); ys = (np.arange(nh) * h // nh); xs = (np.arange(nw) * w // nw)
        out[32 - nh:32, (32 - nw) // 2:(32 - nw) // 2 + nw] = cmap[img[ys][:, xs]]; return out
    out[Y:Y + h, X:X + w] = cmap[img]
    return out


def anim(ins, d, rec, rows, cmap, want=0, fit=False):
    rows = [r for r in rows if all(cell(d, rec, r, c, cmap, fit) is not None for c in (0, 1, 2))]
    if not rows: return 0
    if want and len(rows) < want: rows = [rows[i * len(rows) // want] for i in range(want)]
    return ins.anim([[cell(d, rec, r, c, cmap, fit) for r in rows] for c in (0, 1, 2)])


def check_all(log1, bf):
    """Every character record: can each 32x32-or-smaller frame be placed? -> (fits, skipped frames, details)."""
    ok = bad = 0; big = []
    for c in range(N_CHARS):
        rec = record(log1, c); m = colour_map(log1, rec, bf); cbad = 0
        for r in range(19):
            for col in range(4):
                p = u32(log1, (u32(log1, rec + 0x28) & MASK) + 4 * (r * 4 + col))
                if p:
                    if cell(log1, rec, r, col, m) is None: bad += 1; cbad += 1
                    else: ok += 1
        if cbad: big.append((c, cbad))
    return ok, bad, big


if __name__ == '__main__':
    log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); bf = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read())
    print(check_all(log1, bf))
