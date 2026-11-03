"""Build brand-new Buu's Fury maps from pieces of existing ones (verified in the emulator 2026-11-02).

A map is four 8bpp canvases (BG0-BG3) plus two 1-bit masks (walkable floor, play area), written as a new map record by
Gero's Legacy's mapedit.save (its own tile list and pages, so no shared page table to grow).

    src = Source(rom, 0x081A44A8)                 # any BF map record address (index.csv 'address' column)
    m = NewMap(1024, 512)
    m.fill_ground(src, (96, 96, 200, 192))        # copy 32x32 ground blocks from a plain region of the source's BG3
    m.stamp(src, 'tree', [(70, 40)], 16, 0, base=True, footprint=(16, 40, 56, 72), tall=True)
    P = m.write(rom, template=0x0829B490)         # appends to the ROM, returns the map's object pointer (M + 4)
    link_area(rom, world=1, area=1, P=P)

Engine facts this relies on (RE_NOTES in vendor/gero-tools has the full record layout):
- Record word 3 (+0x0C) = camera limits: (width - 240 + 1) | (height - 160 + 1) << 16.
- Every layer present: a record with no BG0 loads to a black screen on Snake Way. Unused layers are written empty.
- BG priorities (word 2) 0x03030302: BG0 above sprites (tree tops), BG1-3 below.
- Floor mask (+0x38) and play-area mask (+0x3C): 256x256 tiles, 1 bit each, rows LSB first, WFZ type 0.
- At most 896 unique 8x8 tiles per map (BG VRAM); colours come from the shared master palette (or a per-world one).
"""
import os, sys, struct, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'vendor', 'gero-tools', 'tools'))
import mapedit                                  # noqa: E402  (Gero's Legacy)

B = 0x08000000
u32 = lambda r, o: struct.unpack_from('<I', r, o)[0]


def record(r, addr):
    """ROM offset M of the map record for an index.csv address (some list P = M + 4 or M + 8)."""
    o = addr - B
    for d in (0, -4, -8, -12):
        if u32(r, o + d + 0x48) == addr + d: return o + d
    return o


def palette(r):
    return np.frombuffer(bytes(r[0x701B0:0x701B0 + 1536]), np.uint8).reshape(512, 3)


class Source:
    def __init__(self, r, addr):
        self.M = record(r, addr)
        self.L = mapedit.load(r, self.M)                 # {layer: (canvas, header)}
        self.h, self.w = max(c.shape[0] for c, _ in self.L.values()), max(c.shape[1] for c, _ in self.L.values())

    def layer(self, i):
        c = self.L.get(i)
        out = np.zeros((self.h, self.w), np.uint8)
        if c: out[:c[0].shape[0], :c[0].shape[1]] = c[0]
        return out


class NewMap:
    PAD = 256

    def __init__(self, w, h, seed=7):
        assert w % 256 == 0 and h % 256 == 0, 'size in 256 px chunks'
        self.w, self.h, self.rnd = w, h, random.Random(seed)
        self.can = {i: np.zeros((h + self.PAD, w + self.PAD), np.uint8) for i in range(4)}
        self.walk = np.ones(((h + self.PAD) // 8, (w + self.PAD) // 8), np.uint8)
        self.air = np.ones_like(self.walk)

    def fill_ground(self, src, region, block=32):
        x0, y0, x1, y1 = region
        pool = [(x, y) for x in range(x0, x1 - block + 1, 8) for y in range(y0, y1 - block + 1, 8)]
        g = src.layer(3)
        for by in range(0, self.h + self.PAD, block):
            for bx in range(0, self.w + self.PAD, block):
                sx, sy = self.rnd.choice(pool)
                self.can[3][by:by + block, bx:bx + block] = g[sy:sy + block, sx:sx + block]
        self._ground = set(np.unique(g[y0:y1, x0:x1]).tolist())

    def stamp(self, src, name, seeds, x, y, base=False, footprint=None, tall=False):
        """Copy the object(s) under `seeds` (points on the source's BG1/BG2) to (x, y). BG1 parts go to BG0 (over the
        player), BG2 parts to BG2. base=True also copies the non-ground pixels of BG3 under the lower 2/3 (trunks,
        shadows). footprint = (x0, y0, x1, y1) relative to the object's box: not walkable; tall=True also blocks the
        play-area mask."""
        from scipy import ndimage
        if not hasattr(src, '_lab'):
            src._obj = (src.layer(1) > 0) | (src.layer(2) > 0)
            src._lab, _ = ndimage.label(ndimage.binary_dilation(src._obj, iterations=2))
        m = np.zeros_like(src._obj)
        for sx, sy in seeds: m |= src._lab == src._lab[sy, sx]
        m &= src._obj
        ys, xs = np.nonzero(m)
        x0, y0, x1, y1 = xs.min() & ~7, ys.min() & ~7, (xs.max() + 8) & ~7, (ys.max() + 8) & ~7
        h, w = y1 - y0, x1 - x0
        for si, di in ((2, 2), (1, 0)):
            s = src.layer(si)[y0:y1, x0:x1]; k = m[y0:y1, x0:x1] & (s > 0)
            self.can[di][y:y + h, x:x + w][k] = s[k]
        if base:
            s = src.layer(3)[y0:y1, x0:x1]; k = ~np.isin(s, list(self._ground)); k[:h // 3] = False
            self.can[3][y:y + h, x:x + w][k] = s[k]
        if footprint:
            fx0, fy0, fx1, fy1 = footprint
            sl = np.s_[(y + fy0) // 8:(y + fy1) // 8, (x + fx0) // 8:(x + fx1) // 8]
            self.walk[sl] = 0
            if tall: self.air[sl] = 0
        return (x0, y0, x1, y1)

    def finish(self, border=(2, 2, 1, 1)):
        """Crop the padding and block the edges (top, bottom, left, right) in tiles."""
        t, b, l, rr = border
        can = {i: c[:self.h, :self.w].copy() for i, c in self.can.items()}
        walk = self.walk[:self.h // 8, :self.w // 8].copy(); air = self.air[:self.h // 8, :self.w // 8].copy()
        walk[:t] = 0; walk[walk.shape[0] - b:] = 0; walk[:, :l] = 0; walk[:, walk.shape[1] - rr:] = 0
        return can, walk, air

    def write(self, r, template):
        """Append the map to bytearray r (grown in place). template = a BF map record address to copy the record's
        other words from (its built-in door object and handlers). Returns P = map object pointer (record + 4)."""
        can, walk, air = self.finish()
        TM = record(r, template)
        hdr0 = u32(r, u32(r, TM + 0x18 + 4 * 3) - B)                 # layer handler function
        at = (len(r) + 0xFF) & ~0xFF
        r += bytes(at - len(r) + 0x100000)
        layers = {i: (can[i], [hdr0, 0x400, 0x400, 0, 0, (self.w // 256) | (self.h // 256) << 8]) for i in range(4)}
        Mbus, end = mapedit.save(r, TM, layers, at)
        M = Mbus - B
        blobs = []
        for mk in (walk, air):
            full = np.zeros((256, 256), np.uint8); full[:mk.shape[0], :mk.shape[1]] = mk
            d = np.packbits(full, axis=1, bitorder='little').tobytes()
            blob = struct.pack('<II', 0, len(d)) + d
            o = (end + 3) & ~3; r[o:o + len(blob)] = blob; blobs.append(B + o); end = o + len(blob)
        w = list(struct.unpack_from('<21I', r, M))
        w[1] = 0                                                      # no blending
        w[2] = 0x03030302                                             # BG0 over sprites
        w[3] = (self.w - 240 + 1) | (self.h - 160 + 1) << 16          # camera limits
        w[10] = w[11] = w[12] = 0                                     # no door regions
        w[14], w[15] = blobs
        w[17] = 1                                                     # ambient effect id (5 hangs; 1 is safe)
        struct.pack_into('<21I', r, M, *w)
        del r[(end + 0xFF) & ~0xFF:]
        self.can_final, self.walk_final = can, walk
        return Mbus + 4

    def preview(self, r, path, collision=False):
        from PIL import Image
        pal = palette(r); can = self.can_final
        out = np.zeros((self.h, self.w, 3), np.uint8)
        for i in (3, 2, 1, 0):
            k = can[i] > 0; out[k] = pal[can[i][k]]
        if collision:
            wm = np.kron(self.walk_final, np.ones((8, 8), np.uint8)) == 0
            out[wm] = (out[wm] * 0.4).astype(np.uint8)
        Image.fromarray(out).save(path)


def area_entry(r, world, area):
    tab = u32(r, 0x8A58) - B
    h = struct.unpack_from('<4H', r, 0x125E0)
    cnt = 0xFF + (h[1] & 0xFF) if h[0] == 0x20FF else 2 * (h[0] & 0xFF) + (h[2] & 0xFF)
    for k in range(cnt):
        e = tab + 56 * k
        if r[e] == world and r[e + 1] == area: return e
    raise KeyError((world, area))


def link_area(r, world, area, P, room=1):
    """Point room `room` of an existing area at map P."""
    st = u32(r, area_entry(r, world, area) + 0x2C) - B
    struct.pack_into('<I', r, st + 4 * (room - 1), P)
