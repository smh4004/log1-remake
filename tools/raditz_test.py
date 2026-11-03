"""M4 test ROM: LoG1's Raditz fight on Buu's Fury. Art and maps are read from your ROMs at build time; output goes to out/ only.

    python3 tools/raditz_test.py <log1-decomp>

Test rig: area 9 replaces Snake Way (1:1) and area 10 replaces Goku's House (2:1). King Kai's record stands in for the Raditz NPC
and the Bomber's for the enemy, so those two actors get LoG1 frames. HP, EXP and row choice are placeholders until balancing.
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import build_flight, log1_sprites as S, map_convert as C, mapkit, scenes, sprites  # noqa: E402

BB, ROW, HOSTILE, DONE = 0x08000000, 30, 890, 891
ACT_NPC, ACT_ENEMY = 152, 25                        # character indexes = actor id + 9
HP, EXP = 300, 4000


def slots_of(r, actor):
    p = struct.unpack_from('<I', r, sprites.ACTOR_LIST + 4 * actor)[0] - BB; n = struct.unpack_from('<I', r, p)[0] & 0xFF
    return p, [struct.unpack_from('<I', r, p + 0x54 + 4 * i)[0] for i in range(n)]


def put_actor(r, ins, log1, rec, actor, cmap):
    """Each BF slot keeps its own frame count, as the engine reserves memory by it."""
    p, ptrs = slots_of(r, actor); plan = {0: [17, 0], 1: [0, 1], 7: [5]}; done = 0
    for i, a in enumerate(ptrs):
        if a >> 24 != 8: continue
        want = struct.unpack_from('<I', r, a - BB)[0]
        rows = plan.get(i, [3, 4])
        A = S.anim(ins, log1, rec, rows, cmap, want=want) or S.anim(ins, log1, rec, [0], cmap, want=want)
        if A: struct.pack_into('<I', r, p + 0x54 + 4 * i, A); done += 1
    return done


def main():
    L = sys.argv[1]; skip = set(sys.argv[2:]); rom = open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read(); log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read()
    r = bytearray(rom); r += b'\xff' * (0x1000000 - len(r))
    names = [l.split()[1] for l in open(L + '/assets/areas/SPRITES.txt')]; rec = S.record(log1, log1[S.SETS + names.index('raditz')]); cmap = S.colour_map(log1, rec, r)
    ins = sprites.Inserter(r, 0xC00000)
    if 'sprites' not in skip: print('slots', put_actor(r, ins, log1, rec, ACT_NPC, cmap), put_actor(r, ins, log1, rec, ACT_ENEMY, cmap), 'sprite bytes', ins.cur - 0xC00000)
    # enemy row and defeat script: set the flag, then leave for area 10
    at = 0xBF2000; ST = 0x711274; row = bytearray(r[ST + 8 * 28:ST + 9 * 28])
    death = scenes.assemble('call 29 %d; call 120 20; call 119 2 1 1 80 136; call 121 20' % DONE, {}) + b'\x11'; r[at + 0x40:at + 0x40 + len(death)] = death
    struct.pack_into('<I', row, 0, EXP); struct.pack_into('<I', row, 4, HP); struct.pack_into('<I', row, 0x18, BB + at + 0x40); r[ST + ROW * 28:ST + (ROW + 1) * 28] = row
    r[at:at + 32] = struct.pack('<8I', 0x0800FD55, 0, ROW, (152 << 16) | 448, ACT_ENEMY + 9, 0x080555A0, 1, 0x080716EC)
    # maps
    for n, w, ar in ((9, 1, 1), (10, 2, 1)) if 'maps' not in skip else ():
        a = C.Area(L, n); m, st = C.convert(r, a, 'recolour', []); an, dur = C.anim_tiles(r, a); C.reduce_tiles(r, m, 860, [b for b, _ in an])
        P = m.write(r, C.TEMPLATE); C.add_anim(r, P, an, dur); mapkit.link_area(r, w, ar, P); print('area', n, st)
    # talk: sets the hostile flag
    e = mapkit.area_entry(r, 1, 1); n = struct.unpack_from('<I', r, e + 4)[0]; lst = struct.unpack_from('<I', r, e + 0x14)[0] - BB
    b = scenes.assemble('call 29 %d' % HOSTILE, {}) + b'\x11'; step = at + 0x80; r[step:step + 3] = struct.pack('<HB', 1, 0); r[step + 3:step + 3 + len(b)] = b
    sl = at + 0xC0; struct.pack_into('<II', r, sl, BB + step, 0); ok = False
    for k in range(n):
        rc = struct.unpack_from('<I', r, lst + 4 * k)[0] - BB - 8
        if struct.unpack_from('<I', r, rc + 24)[0] == ACT_NPC + 9: struct.pack_into('<I', r, rc + 20, BB + sl); ok = True
    assert ok, 'NPC record not found'
    print('hook bytes', build_flight.install(r, [(HOSTILE, BB + e, BB + at, ACT_NPC + 9)]))
    while len(r) % 0x10000: r.append(0xFF)
    os.makedirs(os.path.join(ROOT, 'out', 'raditz'), exist_ok=True); open(os.path.join(ROOT, 'out', 'raditz', os.environ.get('OUT', 'test') + '.gba'), 'wb').write(r); print('rom', len(r))


if __name__ == '__main__':
    main()
