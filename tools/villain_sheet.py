"""Preview sheets of the post-game villains and Bardock, read from a built ROM: one PNG each, every animation's frames facing down, up and
to the side (the Great Ape and giant Slug as their big 32x64 figure: walking, walking, casting; Cooler's final form by his own 64x64 frames). Nothing here holds art; run it on your own
build.

    python3 tools/villain_sheet.py <rom> <out dir>

out/skills.syms (from the same build) must be present.
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import anims, mapkit  # noqa: E402

BB = 0x08000000
NAMES = {0: 'Cooler', 1: 'Cooler (final form)', 2: 'Turles', 3: 'Turles (after the fruit)', 4: 'Lord Slug', 5: 'Lord Slug (giant)',
         6: 'Great Ape Gohan', 7: 'Dodoria'}                 # src/bosses.c's movesets
BARDOCK_FORM = 60


def main(rom, out):
    r = open(rom, 'rb').read(); A = anims.Actors(r); pal = mapkit.palette(r)[256:].astype(np.uint8)
    orig = A.piece_img

    def piece_img(attr, tptr):                               # frames this build wrote are stored raw (a 0 header), not compressed
        o = tptr - BB
        if struct.unpack_from('<I', r, o)[0] != 0: return orig(attr, tptr)
        a0, a1 = attr & 0xFFFF, attr >> 16; w, h = anims.SZ[(a0 >> 14) & 3][(a1 >> 14) & 3]; d = r[o + 8:o + 8 + w * h]; tw = w // 8
        img = np.zeros((h, w), np.uint8)
        for t in range(len(d) // 64): img[(t // tw) * 8:(t // tw) * 8 + 8, (t % tw) * 8:(t % tw) * 8 + 8] = np.frombuffer(d[64 * t:64 * t + 64], np.uint8).reshape(8, 8)
        return img[:, ::-1] if a1 & 0x1000 else img
    A.piece_img = piece_img
    syms = {l.split()[-1]: int(l.split()[0], 16) for l in open(os.path.join(ROOT, 'out', 'skills.syms')) if len(l.split()) >= 2}

    def rgb(idx):
        c = pal[idx].copy(); c[idx == 0] = (34, 72, 40); return c

    def sheet(rows, title, path, scale=3):
        """rows: [(label, [index arrays])] -> one PNG with a label over each row."""
        cw = max(im.shape[1] for _, ims in rows for im in ims); ch = max(im.shape[0] for _, ims in rows for im in ims)
        W = max(len(ims) for _, ims in rows) * (cw + 4) * scale + 8; H = 28 + len(rows) * (ch * scale + 22)
        can = Image.new('RGB', (W, H), (22, 22, 28)); d = ImageDraw.Draw(can); d.text((8, 6), title, fill=(255, 210, 120)); y = 28
        for label, ims in rows:
            d.text((8, y), label, fill=(200, 200, 210)); y += 14
            for i, im in enumerate(ims):
                tile = Image.fromarray(rgb(im)).resize((im.shape[1] * scale, im.shape[0] * scale), Image.NEAREST)
                can.paste(tile, (8 + i * (cw + 4) * scale, y + (ch - im.shape[0]) * scale))
            y += ch * scale + 8
        can.save(path)

    def actor_rows(rec, slots=12, box=48):
        n = struct.unpack_from('<I', r, rec - BB)[0] & 0xFF; rows = []
        for s in range(min(n, slots)):
            ap = struct.unpack_from('<I', r, rec - BB + 0x54 + 4 * s)[0]
            if ap >> 24 != 8: continue
            an = A.anim(ap)
            if not an: continue
            ims = [A.frame(an[f][d], (box, box), (box // 2, box - 8)) for d in (0, 1, 2) for f in range(min(4, len(an)))]
            rows.append(('animation %d: %d frames x down, up, side' % (s, min(4, len(an))), ims))
        return rows

    def big_rows(big):
        """src/flight.c's big figure: 32x64."""
        rows = []; w = 32; size = 64 * w; tw = w // 8
        for pose, what in enumerate(('walking', 'walking', 'casting')):
            ims = []
            for d in range(4):
                o = big - BB + pose * 4 * size + d * size; img = np.zeros((64, w), np.uint8)
                for t in range(size // 64): img[(t // tw) * 8:(t // tw) * 8 + 8, (t % tw) * 8:(t % tw) * 8 + 8] = np.frombuffer(r[o + 64 * t:o + 64 * t + 64], np.uint8).reshape(8, 8)
                ims.append(img)
            rows.append((what + ': down, up, left, right', ims))
        return rows

    os.makedirs(out, exist_ok=True); done = []
    t = syms['boss_table'] - BB
    for i in range(12):
        rec, m, big = struct.unpack_from('<III', r, t + 12 * i)
        if not rec: break
        name = NAMES.get(m, 'villain %d' % m); path = os.path.join(out, name.lower().replace(' ', '_').replace('(', '').replace(')', '') + '.png')
        sheet(big_rows(big) if big > 1 else actor_rows(rec, box=72 if big else 48), name, path); done.append(path)      # 1: drawn tall by his own frames
    ft = struct.unpack_from('<I', r, syms['forms_at'] - BB)[0] - BB; val = struct.unpack_from('<H', r, ft + 24 * BARDOCK_FORM + 0x0E)[0]
    rec = struct.unpack_from('<I', r, 0xC00000 + 4 * (val - 9))[0]
    path = os.path.join(out, 'bardock.png'); sheet(actor_rows(rec, 24), "Bardock (Goku's form in the vision)", path, scale=2); done.append(path)
    print('\n'.join(done))


if __name__ == '__main__':
    main(*sys.argv[1:3])
