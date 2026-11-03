"""Read any Buu's Fury map as tile-index canvases, including maps with animated tiles or empty chunks (static frames only)."""
import os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import mapedit, mapkit  # noqa: E402

B = 0x08000000


class Map:
    def __init__(self, r, addr):
        self.M = M = mapkit.record(r, addr); self.layers = {}
        tiles = mapedit.tiles_of(r, M)
        for i in range(4):
            hp = struct.unpack_from('<I', r, M + 0x18 + 4 * i)[0]
            if hp >> 24 != 8: continue
            h = hp - B; dims = struct.unpack_from('<I', r, h + 0x14)[0]; cw, ch = dims & 0xFF, dims >> 8 & 0xFF
            if struct.unpack_from('<I', r, h)[0] != 0x08008087 or not 0 < cw * ch < 64: continue
            can = np.zeros((ch * 256, cw * 256), np.uint8)
            for k in range(cw * ch):
                cp = struct.unpack_from('<I', r, h + 0x18 + 4 * k)[0]
                if cp >> 24 != 8: continue
                try: m = np.frombuffer(bytes(mapedit.unpack(r, cp - B)[0]), np.uint8)[:2048].view('<u2').reshape(32, 32)
                except Exception: continue
                cy, cx = (k // cw) * 256, (k % cw) * 256
                for ty in range(32):
                    for tx in range(32):
                        v = int(m[ty, tx]); s = v & 0x3FF
                        if not s or s >= len(tiles): continue
                        t = tiles[s]
                        if v & 0x400: t = t[:, ::-1]
                        if v & 0x800: t = t[::-1]
                        can[cy + ty * 8:cy + ty * 8 + 8, cx + tx * 8:cx + tx * 8 + 8] = t
            self.layers[i] = can
        self.h = max((c.shape[0] for c in self.layers.values()), default=0); self.w = max((c.shape[1] for c in self.layers.values()), default=0)

    def layer(self, i):
        o = np.zeros((self.h, self.w), np.uint8); c = self.layers.get(i)
        if c is not None: o[:c.shape[0], :c.shape[1]] = c
        return o
