"""M4: add LoG1 characters and enemies to a Buu's Fury ROM. Frames come from rom/log1.gba at build time; nothing here holds art.

New actors are appended as Gero's sprites.build_actors does. Stats rows reuse Buu's Fury's table, because the remake doesn't use its enemies.
HP and EXP scaling is a placeholder until balancing (M8).
"""
import csv, os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_sprites as S, sprites  # noqa: E402
import log1_turles, log1_cooler, log1_dodoria  # noqa: E402
MADE = {'turles': log1_turles.cellf, 'turles2': log1_turles.cellf_fruit, 'cooler': log1_cooler.cellf, 'cooler2': log1_cooler.cellf,
        'dodoria': log1_dodoria.cellf}                                  # look -> its frames' maker
BIG = ('oozaru1', 'oozaru2')                                            # taller than an actor's frame; src/flight.c draws them
ROWS, ST_REFS = 256, (0xFCE4, 0xFD70, 0x1BA90, 0x24F28, 0x279DC, 0x2CD18, 0x2F5E4, 0x32D3C, 0x335B8, 0x39BD4, 0x39D90, 0x3A384, 0x3A698)
BB = 0x08000000; ST = 0x711274; T_NPC, T_ENEMY = 152, 25; COUNT = 298


class Actors:
    def __init__(self, r, log1_rom, log1_dir, at):
        # the enemy stat table only has room for 150 rows, so it moves to a bigger one
        self.st = len(r); r.extend(r[ST:ST + 150 * 28]); r.extend(bytes((ROWS - 150) * 28))
        for ref in ST_REFS:
            assert struct.unpack_from('<I', r, ref)[0] == BB + ST; struct.pack_into('<I', r, ref, BB + self.st)
        self.pose_anims = {}
        self.r, self.log1 = r, log1_rom; self.names = [l.split()[1] for l in open(log1_dir + '/assets/areas/SPRITES.txt')]
        self.table = list(struct.unpack_from('<%dI' % COUNT, r, sprites.ACTOR_LIST)); self.at = at; self.ins = sprites.Inserter(r, at + 4 * 512); self.ids = {}; self.missing = []
        self.enemies = {e['name']: e for e in csv.DictReader(open(log1_dir + '/assets/tables/enemies.csv'))}; self.rows = {}; self.next_row = 60
        self.row_map = self.log1[0x15A69C:0x15A69C + 109]; self.csv = list(csv.DictReader(open(log1_dir + '/assets/tables/enemies.csv')))

    def actor(self, sprite, enemy, tint=None, look=None):
        """tint, look: a recoloured copy (log1_yardrat's Yardrats), kept apart by its look's name."""
        key = (sprite, enemy) + ((look,) if look else ())
        if key in self.ids: return self.ids[key]
        rec = S.record(self.log1, self.log1[S.SETS + self.names.index(sprite)]); cmap = S.colour_map(self.log1, rec, self.r, tint)
        cf = MADE[look](self.log1, self.names, self.r) if look in MADE else None          # a figure made from two LoG1 characters
        tp = self.table[T_ENEMY if enemy else T_NPC] - BB; n = struct.unpack_from('<I', self.r, tp)[0] & 0xFF; R = bytearray(self.r[tp:tp + 0x54 + 4 * n]); struct.pack_into('<I', R, 0x50, 0); ok = 0
        plan = {0: [17, 0], 1: [0, 1], 7: [5]}
        for i in range(n):
            a = struct.unpack_from('<I', R, 0x54 + 4 * i)[0]
            if a >> 24 != 8: continue
            want = struct.unpack_from('<I', self.r, a - BB)[0]; A = S.anim(self.ins, self.log1, rec, plan.get(i, [3, 4]), cmap, want=want, cellf=cf) or S.anim(self.ins, self.log1, rec, [0, 1, 2, 3, 4, 5, 17], cmap, want=want, cellf=cf) or S.anim(self.ins, self.log1, rec, plan.get(i, [3, 4]), cmap, want=want, fit=True, cellf=cf) or S.anim(self.ins, self.log1, rec, [0, 1, 2, 3, 4, 5, 17], cmap, want=want, fit=True, cellf=cf)
            if A: struct.pack_into('<I', R, 0x54 + 4 * i, A); ok += 1
        if not ok: self.missing.append(sprite)
        self.ids[key] = len(self.table) + 9; self.table.append(self.ins.put(bytes(R)))
        return self.ids[key]

    def pose_rows(self, rows, idx_of):
        """rows: (flag, actor sprite, sprite whose frame to show or None to let go, its row). -> rows for src/flight.c's pose table. The player's frames shrink the same way as big creatures."""
        out = []
        for flag, nm, src, row in rows:
            A = big = 0
            if src:
                rec = S.record(self.log1, self.log1[S.SETS + self.names.index(src)]); m = S.colour_map(self.log1, rec, self.r)
                if src in BIG:
                    if (src, row) not in self.pose_anims: self.pose_anims[(src, row)] = self.big_frames(rec, row, m)
                    big = self.pose_anims[(src, row)]; A = self.pose_anims.setdefault('blank', self.ins.anim([[np.zeros((32, 32), np.uint8)] * 2] * 3))
                else: A = self.pose_anims.setdefault((src, row), S.anim(self.ins, self.log1, rec, [row], m, want=2, fit=True))
                if not A: self.missing.append('%s pose %d' % (src, row)); continue
            out.append((flag, idx_of(nm), A, big))
        return out

    def big_frames(self, rec, row, cmap):
        """A 32x64 8bpp sprite's tiles for each of Buu's Fury's directions: down, up, side, side mirrored."""
        return self.ins.put(big_tiles(self.big_images(rec, row, cmap)))

    def big_images(self, rec, row, cmap):
        """A 32x64 sprite's frames (index arrays) for each of Buu's Fury's directions: down, up, side, side mirrored."""
        def col(c):
            p = S.u32(self.log1, (S.u32(self.log1, rec + 0x28) & S.MASK) + 4 * (row * 4 + c)) & S.MASK; _, _, w, h = struct.unpack_from('<hhHH', self.log1, p); gfx = S.u32(self.log1, p + 12) & S.MASK
            assert (w, h) == (32, 64); raw = np.frombuffer(self.log1, np.uint8, w * h // 2, gfx); px = np.empty(w * h, np.uint8); px[0::2] = raw & 15; px[1::2] = raw >> 4; im = np.zeros((h, w), np.uint8)
            for k in range(w * h // 64): im[(k // 4) * 8:(k // 4) * 8 + 8, (k % 4) * 8:(k % 4) * 8 + 8] = px[k * 64:k * 64 + 64].reshape(8, 8)
            return cmap[im]
        d, u, s = col(0), col(1), col(2)
        return [d, u, s, s[:, ::-1]]

    def hidden(self, value):
        """Hide an actor's own sprite (each frame's OBJ turned off, its box kept for hits): src/flight.c draws a big figure in its place.
        Its animations and frames are copied first, as frames are shared between actors with the same art."""
        tp = self.table[value - 9] - BB; n = struct.unpack_from('<I', self.r, tp)[0] & 0xFF
        for i in range(n):
            a = struct.unpack_from('<I', self.r, tp + 0x54 + 4 * i)[0]
            if a >> 24 != 8: continue
            k = struct.unpack_from('<I', self.r, a - BB)[0]; ptrs = list(struct.unpack_from('<%dI' % (4 * k), self.r, a - BB + 4))
            for j, f in enumerate(ptrs):
                c = struct.unpack_from('<I', self.r, f - BB)[0]; F = bytearray(self.r[f - BB:f - BB + 4 + 16 * c])
                for q in range(c): F[4 + 16 * q + 9] |= 0x02                 # attr0 bit 9: not drawn
                ptrs[j] = self.ins.put(bytes(F))
            struct.pack_into('<I', self.r, tp + 0x54 + 4 * i, self.ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs)))


    def pickup(self, i):
        """An NPC actor showing LoG1 pickup i in every direction and frame."""
        key = ('pickup', i)
        if key in self.ids: return self.ids[key]
        import log1_pickups, log1_dragonballs
        img = log1_dragonballs.ball_image(self.r, i[1]) if isinstance(i, tuple) else log1_pickups.frame(self.log1, self.r, i); tp = self.table[T_NPC] - BB; n = struct.unpack_from('<I', self.r, tp)[0] & 0xFF; R = bytearray(self.r[tp:tp + 0x54 + 4 * n]); struct.pack_into('<I', R, 0x50, 0)
        for k in range(n):
            a = struct.unpack_from('<I', R, 0x54 + 4 * k)[0]
            if a >> 24 != 8: continue
            want = struct.unpack_from('<I', self.r, a - BB)[0]; struct.pack_into('<I', R, 0x54 + 4 * k, self.ins.anim([[img] * want] * 3))
        self.ids[key] = len(self.table) + 9; self.table.append(self.ins.put(bytes(R)))
        return self.ids[key]

    def row(self, sprite, death=0, no_exp=False, hp_set=None, area=0, boss=False, extra=0):
        key = (sprite, death, area, boss, extra, no_exp)
        if key in self.rows: return self.rows[key]
        R = bytearray(self.r[ST + 8 * 28:ST + 9 * 28]); lv, hp, exp, a, p, e = self.bal.enemy(area, boss, extra)
        struct.pack_into('<II', R, 0, 0 if no_exp else exp, hp_set or hp); R[0xC:0x10] = bytes((min(lv, 255), a, p, e)); struct.pack_into('<I', R, 0x18, death)
        k = self.next_row; self.next_row += 1; assert k < ROWS, 'enemy rows'; self.r[self.st + k * 28:self.st + (k + 1) * 28] = R; self.rows[key] = k; return k

    def finish(self):
        self.r[self.at:self.at + 4 * len(self.table)] = struct.pack('<%dI' % len(self.table), *self.table)
        for lit in sprites.ACTOR_LITERALS: struct.pack_into('<I', self.r, lit, BB + self.at + 4)
        return len(self.table) - COUNT, self.ins.cur


def big_tiles(images):
    """32x64 index arrays -> their 8bpp tiles, one after another."""
    return b''.join(im[y:y + 8, x:x + 8].tobytes() for im in images for y in range(0, 64, 8) for x in range(0, 32, 8))


def upscaled(cell, scale=2):
    """A 32x32 actor frame drawn `scale` times bigger on a 32x64 canvas, its feet on the canvas's (the bottom rows line up), centred."""
    out = np.zeros((64, 32), np.uint8); c = 15.5
    for y in range(64):
        sy = 31 - int((63 - y) / scale)
        if sy < 0: continue
        for x in range(32):
            sx = int(np.floor(c + (x - c) / scale + 0.5))
            if 0 <= sx < 32: out[y, x] = cell[sy, sx]
    return out
