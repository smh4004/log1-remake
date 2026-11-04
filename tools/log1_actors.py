"""M4: add LoG1 characters and enemies to a Buu's Fury ROM. Frames come from rom/log1.gba at build time; nothing here holds art.

New actors are appended as Gero's sprites.build_actors does. Stats rows reuse Buu's Fury's table, because the remake doesn't use its enemies.
HP and EXP scaling is a placeholder until balancing (M8).
"""
import csv, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_sprites as S, sprites  # noqa: E402
BB = 0x08000000; ST = 0x711274; T_NPC, T_ENEMY = 152, 25; COUNT = 298


class Actors:
    def __init__(self, r, log1_rom, log1_dir, at):
        self.r, self.log1 = r, log1_rom; self.names = [l.split()[1] for l in open(log1_dir + '/assets/areas/SPRITES.txt')]
        self.table = list(struct.unpack_from('<%dI' % COUNT, r, sprites.ACTOR_LIST)); self.at = at; self.ins = sprites.Inserter(r, at + 4 * 512); self.ids = {}; self.missing = []
        self.enemies = {e['name']: e for e in csv.DictReader(open(log1_dir + '/assets/tables/enemies.csv'))}; self.rows = {}; self.next_row = 60
        self.row_map = self.log1[0x15A69C:0x15A69C + 109]; self.csv = list(csv.DictReader(open(log1_dir + '/assets/tables/enemies.csv')))

    def actor(self, sprite, enemy):
        key = (sprite, enemy)
        if key in self.ids: return self.ids[key]
        rec = S.record(self.log1, self.log1[S.SETS + self.names.index(sprite)]); cmap = S.colour_map(self.log1, rec, self.r)
        tp = self.table[T_ENEMY if enemy else T_NPC] - BB; n = struct.unpack_from('<I', self.r, tp)[0] & 0xFF; R = bytearray(self.r[tp:tp + 0x54 + 4 * n]); struct.pack_into('<I', R, 0x50, 0); ok = 0
        plan = {0: [17, 0], 1: [0, 1], 7: [5]}
        for i in range(n):
            a = struct.unpack_from('<I', R, 0x54 + 4 * i)[0]
            if a >> 24 != 8: continue
            want = struct.unpack_from('<I', self.r, a - BB)[0]; A = S.anim(self.ins, self.log1, rec, plan.get(i, [3, 4]), cmap, want=want) or S.anim(self.ins, self.log1, rec, [0, 1, 2, 3, 4, 5, 17], cmap, want=want) or S.anim(self.ins, self.log1, rec, plan.get(i, [3, 4]), cmap, want=want, fit=True) or S.anim(self.ins, self.log1, rec, [0, 1, 2, 3, 4, 5, 17], cmap, want=want, fit=True)
            if A: struct.pack_into('<I', R, 0x54 + 4 * i, A); ok += 1
        if not ok: self.missing.append(sprite)
        self.ids[key] = len(self.table) + 9; self.table.append(self.ins.put(bytes(R)))
        return self.ids[key]

    def pickup(self, i):
        """An NPC actor showing LoG1 pickup i in every direction and frame."""
        key = ('pickup', i)
        if key in self.ids: return self.ids[key]
        import log1_pickups
        img = log1_pickups.frame(self.log1, self.r, i); tp = self.table[T_NPC] - BB; n = struct.unpack_from('<I', self.r, tp)[0] & 0xFF; R = bytearray(self.r[tp:tp + 0x54 + 4 * n]); struct.pack_into('<I', R, 0x50, 0)
        for k in range(n):
            a = struct.unpack_from('<I', R, 0x54 + 4 * k)[0]
            if a >> 24 != 8: continue
            want = struct.unpack_from('<I', self.r, a - BB)[0]; struct.pack_into('<I', R, 0x54 + 4 * k, self.ins.anim([[img] * want] * 3))
        self.ids[key] = len(self.table) + 9; self.table.append(self.ins.put(bytes(R)))
        return self.ids[key]

    def row(self, sprite, death=0, no_exp=False, hp_set=None):
        if (sprite, death) in self.rows: return self.rows[(sprite, death)]
        e = self.csv[self.row_map[self.names.index(sprite)]]; R = bytearray(self.r[ST + 8 * 28:ST + 9 * 28]); hp = int(e['hp']); exp = 0 if no_exp else int(e['exp'])
        struct.pack_into('<I', R, 0, exp); struct.pack_into('<I', R, 4, hp_set or max(20, min(1500, hp // 10 if hp > 400 else hp * 4))); struct.pack_into('<I', R, 0x18, death)
        k = self.next_row; self.next_row += 1; assert k < 150; self.r[ST + k * 28:ST + (k + 1) * 28] = R; self.rows[(sprite, death)] = k; return k

    def finish(self):
        self.r[self.at:self.at + 4 * len(self.table)] = struct.pack('<%dI' % len(self.table), *self.table)
        for lit in sprites.ACTOR_LITERALS: struct.pack_into('<I', self.r, lit, BB + self.at + 4)
        return len(self.table) - COUNT, self.ins.cur
