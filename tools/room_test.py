"""Painted-room test: build one LoG1 one-screen room for Buu's Fury two ways. Writes out/rooms only.

    python3 tools/room_test.py <log1-decomp dir> [area]

A (rebuild): LoG1's walkable mask, with floor, walls and furniture copied from Buu's Fury's kitchen (map 2:01).
B (recolour): LoG1's painting mapped to Buu's Fury's background colours (nearest in Lab), with the same mask.
Each is a test ROM with the room on Snake Way (1:1), Snake Way's NPCs removed.
"""
import os, re, struct, sys, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import mapkit  # noqa: E402

KITCHEN, TEMPLATE = 0x0828C4CC, 0x0829B490


def lab(rgb):
    c = rgb.astype(float) / 255; c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T
    xyz = xyz / np.array([.9505, 1, 1.089]); f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def load_room(log1, n):
    A = os.path.join(log1, 'assets', 'maps'); root = ET.parse('%s/area%02d.tmx' % (A, n)).getroot()
    W, H = int(root.get('width')), int(root.get('height'))
    L = {l.get('name'): np.array([int(x) for x in re.split(r'[,\s]+', l.find('data').text.strip()) if x], np.uint32).reshape(H, W) for l in root.findall('layer')}
    return np.array(Image.open('%s/preview/area%02d.png' % (A, n)).convert('RGB')), (L['walkable'] > 0).astype(np.uint8), (L['shots'] > 0).astype(np.uint8)


def base(walk, air):
    m = mapkit.NewMap(256, 256); h, w = walk.shape
    m.walk[:] = 0; m.air[:] = 0; m.walk[:h, :w] = walk; m.air[:h, :w] = air | walk
    return m


def method_b(rom, pic, walk, air):
    m = base(walk, air); pal = mapkit.palette(rom)[:256]; P = lab(pal[1:])
    px, inv = np.unique(pic.reshape(-1, 3), axis=0, return_inverse=True); Q = lab(px)
    idx = 1 + ((Q[:, None, :] - P[None, :, :]) ** 2).sum(2).argmin(1)
    m.can[3][:160, :240] = idx[inv.ravel()].reshape(160, 240)
    return m


def method_a(rom, walk, air):
    m = base(walk, air); s = mapkit.Source(rom, KITCHEN); g = s.layer(3); o = m.can[3]; T = 8
    def copy(sx, sy, w, h, dx, dy): o[dy:dy + h, dx:dx + w] = g[sy:sy + h, sx:sx + w]
    H, W = walk.shape; tops = {}
    for x in range(W):
        ys = np.nonzero(walk[:, x])[0]
        if len(ys): tops[x] = ys.min()
    for y in range(H):                                       # floor: 16 px tiles from the kitchen
        for x in range(W):
            if walk[y, x]: copy(80 + (x % 2) * T, 168 + (y % 2) * T, T, T, x * T, y * T)
    for x, t in tops.items():                                # wall: plaster, dark top band, grey rim, 7 tiles high
        for k in range(1, 8):
            if t - k >= 0: copy(184 + (x % 2) * T, 32 + ((k - 1) % 2) * T, T, T, x * T, (t - k) * T)
        if t >= 8: copy(184 + (x % 2) * T, 8, T, T, x * T, (t - 8) * T)
    for y in range(H):                                       # grey rim on the bottom and side edges of the floor
        for x in range(W):
            if walk[y, x] or (x in tops and y < tops[x]): continue
            near = any(0 <= y + b < H and 0 <= x + a < W and walk[y + b, x + a] for a, b in ((0, -1), (1, 0), (-1, 0)))
            if near: copy(48 + (x % 2) * T, 200, T, T, x * T, y * T)
    for y in range(H):                                       # a clean rim: lower edge of the kitchen's grey border
        for x in range(W):
            if walk[y, x] or (x in tops and y < tops[x]): continue
            if y > 0 and walk[y - 1, x]: copy(64 + (x % 2) * T, 200, T, T, x * T, y * T)
    copy(88, 16, 88, 72, 8, 48)                              # counters, stove, fridge against the left wall
    copy(64, 40, 24, 40, 128, 56); copy(192, 64, 24, 80, 208, 56)     # plant and cupboard on the right wall
    return m


def install(rom, m, name):
    r = bytearray(rom); P = m.write(r, TEMPLATE); mapkit.link_area(r, 1, 1, P)
    struct.pack_into('<I', r, mapkit.area_entry(r, 1, 1) + 4, 0)       # no NPC objects
    while len(r) % 0x10000: r.append(0xFF)
    open(os.path.join(ROOT, 'out', 'rooms', name + '.gba'), 'wb').write(r)
    m.preview(r, os.path.join(ROOT, 'out', 'rooms', name + '.png')); m.preview(r, os.path.join(ROOT, 'out', 'rooms', name + '_walk.png'), True)
    return r


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    rom = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); pic, walk, air = load_room(sys.argv[1], n)
    os.makedirs(os.path.join(ROOT, 'out', 'rooms'), exist_ok=True)
    Image.fromarray(pic).save(os.path.join(ROOT, 'out', 'rooms', 'original.png'))
    install(rom, method_a(rom, walk, air), 'method_a'); install(rom, method_b(rom, pic, walk, air), 'method_b')
    print('tiles ok; wrote out/rooms')


if __name__ == '__main__':
    main()
