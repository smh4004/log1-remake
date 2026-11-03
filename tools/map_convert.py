"""M3: convert a LoG1 area to a Buu's Fury map with its exact layout. Reads extracted assets; writes out/maps only.

    python3 tools/map_convert.py <log1-decomp> <area> <recolour|match> [donor map addresses...]

Each LoG1 8x8 tile is recoloured to BF's background palette. In `match` mode, a tile is replaced by the closest BF tile from
the donor maps when that tile is close enough and has the same transparent pixels. Layers: bg3 -> BG3, bg2 -> BG2, bg1 -> BG0.
"""
import json, os, re, struct, sys, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import mapkit  # noqa: E402
from room_test import lab, TEMPLATE  # noqa: E402

LIMIT, THRESH = 896, 14.0
LAYERS = (('bg3 (bottom)', 3), ('bg2', 2), ('bg1 (top)', 0))


def tilesheet(path):
    im = Image.open(path); pal = np.array(im.getpalette()[:768], np.uint8).reshape(-1, 3)
    return np.array(im, np.uint8), pal


class Area:
    def __init__(self, log1, n):
        A = os.path.join(log1, 'assets', 'maps'); root = ET.parse('%s/area%02d.tmx' % (A, n)).getroot()
        self.W, self.H = int(root.get('width')), int(root.get('height'))
        self.L = {l.get('name'): np.array([int(x) for x in re.split(r'[,\s]+', l.find('data').text.strip()) if x], np.uint32).reshape(self.H, self.W) for l in root.findall('layer')}
        self.info = json.load(open(os.path.join(log1, 'assets', 'areas', 'area%02d.json' % n)))
        self.sheets = {0: tilesheet('%s/tiles/area%02d.png' % (A, n))}; self.A, self.n = A, n

    def sheet(self, x, y):
        b = self.info['screen_tiles'][(y // 20) * (self.W // 30) + x // 30] if self.info.get('screen_tiles') else 0
        p = '%s/tiles/area%02d_block%d.png' % (self.A, self.n, b)
        if b > 1 and os.path.exists(p):
            if b not in self.sheets: self.sheets[b] = tilesheet(p)
            return self.sheets[b]
        return self.sheets[0]

    def tile(self, gid, x, y):
        img, pal = self.sheet(x, y); s = (int(gid) & 0x3FFFFFFF) - 1; t = img[(s // 16) * 8:(s // 16) * 8 + 8, (s % 16) * 8:(s % 16) * 8 + 8]
        if gid & 0x80000000: t = t[:, ::-1]
        if gid & 0x40000000: t = t[::-1]
        return t, pal


def donors(rom, addrs):
    out = {}; used = 0
    for a in addrs:
        try: s = mapkit.Source(rom, a)
        except (AssertionError, struct.error): continue              # animated-tile maps aren't supported as donors yet
        for i in (3, 2, 1, 0):
            c = s.layer(i)
            for y in range(0, c.shape[0] - 7, 8):
                for x in range(0, c.shape[1] - 7, 8):
                    t = c[y:y + 8, x:x + 8]
                    if t.any(): out[t.tobytes()] = t.copy()
    return list(out.values())


def convert(rom, a, mode, donor_tiles):
    pal = mapkit.palette(rom)[:256]; LP = lab(pal); P1 = LP[1:]; cache = {}; stats = dict(matched=0, recoloured=0)
    if donor_tiles:
        D = np.stack(donor_tiles); DL = LP[D]; DO = D > 0
    W, H = (a.W * 8 + 255) // 256 * 256, (a.H * 8 + 255) // 256 * 256
    m = mapkit.NewMap(W, H); m.walk[:] = 0; m.air[:] = 0
    wk, fl = (a.L['walkable'] > 0), (a.L['flyable'] > 0)
    m.walk[:a.H, :a.W] = wk; m.air[:a.H, :a.W] = wk | fl
    def conv(t, p):
        k = (t.tobytes(), p.tobytes())
        if k in cache: return cache[k]
        rgb = p[t]; Q = lab(rgb); idx = (1 + ((Q[:, :, None] - P1) ** 2).sum(3).argmin(2)).astype(np.uint8); idx[t == 0] = 0; res = idx
        if mode == 'match' and donor_tiles:
            op = t > 0; same = (DO == op).all((1, 2))
            if same.any():
                ds = np.sqrt(((DL[same] - Q) ** 2).sum(3))[:, op].mean(1) if op.any() else None
                if ds is not None and ds.min() < THRESH: res = D[same][ds.argmin()]; stats['matched'] += 1; cache[k] = res; return res
        stats['recoloured'] += 1; cache[k] = res; return res
    for name, bg in LAYERS:
        g = a.L[name]; c = m.can[bg]
        for y in range(a.H):
            for x in range(a.W):
                if g[y, x]:
                    t, p = a.tile(g[y, x], x, y); c[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = conv(t, p)
    uniq = {m.can[i][y:y + 8, x:x + 8].tobytes() for i in (0, 2, 3) for y in range(0, H, 8) for x in range(0, W, 8)}
    stats['tiles'] = len(uniq); stats['size'] = (W, H)
    return m, stats


def ground_swap(a, m, patch, hue, sat=.25, val=.35, layers=('bg3 (bottom)',)):
    """Replace opaque LoG1 tiles of one colour family with a repeating 32x32 BF ground patch. Returns tiles replaced."""
    import colorsys
    n = 0
    for name in layers:
        G = a.L[name]; c = m.can[dict(LAYERS)[name]]
        for y in range(a.H):
            for x in range(a.W):
                if not G[y, x]: continue
                t, p = a.tile(G[y, x], x, y)
                if not t.all(): continue
                h, s_, v = colorsys.rgb_to_hsv(*(p[t].reshape(-1, 3).mean(0) / 255))
                if hue[0] <= h * 360 <= hue[1] and s_ > sat and v > val:
                    c[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = patch[(y % 4) * 8:(y % 4) * 8 + 8, (x % 4) * 8:(x % 4) * 8 + 8]; n += 1
    return n


def main():
    log1, n, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]; addrs = [int(x, 0) for x in sys.argv[4:]]
    rom = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); a = Area(log1, n)
    m, st = convert(rom, a, mode, donors(rom, addrs) if addrs else [])
    print(n, mode, st)
    out = os.path.join(ROOT, 'out', 'maps'); os.makedirs(out, exist_ok=True); tag = 'area%02d_%s' % (n, mode)
    r = bytearray(rom)
    if st['tiles'] > LIMIT: print('  over tile limit: not written'); 
    else:
        P = m.write(r, TEMPLATE); mapkit.link_area(r, 1, 1, P); struct.pack_into('<I', r, mapkit.area_entry(r, 1, 1) + 4, 0)
        open('%s/%s.gba' % (out, tag), 'wb').write(r); m.preview(r, '%s/%s.png' % (out, tag))
    if st['tiles'] > LIMIT:
        p = mapkit.palette(rom); o = np.zeros((m.h, m.w, 3), np.uint8)
        for i in (3, 2, 1, 0):
            k = m.can[i][:m.h, :m.w] > 0; o[k] = p[m.can[i][:m.h, :m.w][k]]
        Image.fromarray(o).save('%s/%s.png' % (out, tag))


if __name__ == '__main__':
    main()
