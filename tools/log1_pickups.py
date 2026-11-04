"""LoG1's pickups as Buu's Fury objects, read from rom/log1.gba at build time.

Each pickup is an NPC-class object with one frame, plus a walk-in zone around it that runs its script. Records: 0x5C2258, 24 bytes per id
(+0x0C size, +0x14 -> {palette, 4bpp tiles}). Messages: pointer table 0x5C2FB8, ids 0-30. Ids 31-33 refill energy with no message.
"""
import os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import mapkit  # noqa: E402
from room_test import lab  # noqa: E402

RECS, TEXT, M = 0x5C2258, 0x5C2FB8, 0x1FFFFFF
HERB, SENZU, CAPSULE, CRYSTAL, COOKIE = {11: 0, 12: 1, 13: 2}, 11, 12, 13, 14       # Buu's Fury items: Milk, Tea, Soda, Senzu Bean, Capsule, L. Crystal, Cookie
ENERGY = {31: 5, 32: 10, 33: 20}
BF_ITEM = dict(HERB); BF_ITEM.update({18: COOKIE, 19: SENZU, 21: CAPSULE, 22: CAPSULE, 23: CRYSTAL, 24: CRYSTAL, 25: CRYSTAL})


def message(log1, i):
    if i >= 31: return None
    a = struct.unpack_from('<I', log1, TEXT + 4 * i)[0] & M; return log1[a:log1.index(b'\0', a)].decode('latin1')


def frame(log1, bf, i):
    """32x32 canvas with the pickup bottom-centred, in Buu's Fury's OBJ palette."""
    w = struct.unpack_from('<6I', log1, RECS + i * 24); W, H = w[3] & 0xFFFF, w[3] >> 16; pp, tp = struct.unpack_from('<II', log1, w[5] & M)
    pal = struct.unpack_from('<16H', log1, pp & M); C = np.array([[(v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31] for v in pal], np.uint8)
    obj = mapkit.palette(bf)[256:]; cmap = (1 + ((lab(C)[:, None] - lab(obj[1:])[None]) ** 2).sum(2).argmin(1)).astype(np.uint8); cmap[0] = 0
    tw, th = W // 8, H // 8; raw = np.frombuffer(log1, np.uint8, tw * th * 32, tp & M); px = np.empty(raw.size * 2, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4
    img = np.zeros((H, W), np.uint8)
    for k in range(tw * th): img[(k // tw) * 8:(k // tw) * 8 + 8, (k % tw) * 8:(k % tw) * 8 + 8] = px[k * 64:k * 64 + 64].reshape(8, 8)
    out = np.zeros((32, 32), np.uint8); X = 16 - W // 2; out[32 - H:32, X:X + W] = cmap[img]
    return out
