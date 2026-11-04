"""Boss gauntlet: python3 tools/boss_test.py <dir> <data>. Sets Goku to the level each boss's area expects, using the stats a difficulty run reached, then fights each boss once with no top-ups.

Prints time taken, HP left and whether Goku fell. The bot only walks up and punches, so a real player should do better.
"""
import os, shutil, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.environ['NO_TOPUP'] = '1'; D, DATA = sys.argv[1:3]
sys.argv = ['x', D + '/rom.gba', D, DATA, '0', '-1']
exec(open(os.path.join(ROOT, 'tools', 'story_test.py')).read().split("CK = os.path.join(D, 'ckpt')")[0].replace("os.path.abspath(__file__)", repr(os.path.join(ROOT, 'tools', 'story_test.py'))))
resumed = True; sys.path.insert(0, os.path.join(ROOT, 'tools'))
import log1_balance as B  # noqa: E402
def foes():
    run(['dump _e 03001bb0 84']); b = rd('_e'); c = struct.unpack_from('<I', b)[0]; return struct.unpack_from('<%dI' % c, b, 4)
def at(o): run(['dump _x %08x 8' % (o + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]
def ohp(o): run(['dump _o %08x 8' % o]); return struct.unpack_from('<I', rd('_o'), 4)[0]
def hp(): run(['dump _g 03001576 2']); return struct.unpack('<H', rd('_g'))[0]
def goku(L):
    h, s, e = 90 + 16 * L, int(18 + 1.35 * L), int(16 + 1.45 * L); lv = 50 + L
    return ['w8 %08x %02x' % (0x03001576 + i, b) for i, b in enumerate(struct.pack('<HH', h, h))] + ['w8 03001588 %02x' % s, 'w8 0300158a %02x' % e], h
base = cur[0]; done = set(); rows = []
for x in Q:
    for a in x['actions']:
        if a['type'] != 'make_hostile' or a['area'] not in AREAS: continue
        n, want = a['area'], names[a['sprite']]; q = x['quest']
        t = next((t for y in Q for t in y['tasks'] if t['type'] in ('activate', 'defeat') and t.get('sprite') == a['sprite'] and t['area'] == n), None)
        if not t: continue
        cur[0] = base
        for f in range(q + 1): setf(QF + f)
        warp(n); L = B.STAGE[n]; w, h0 = goku(L); step(w + ['20']); npc = next(s for s in AREAS[n]['actors'] if s['sprite'] == want); place(npc['x'] - 30, npc['y']) if fits(n, npc['x'] - 30, npc['y']) else place(npc['x'], npc['y'] + 24); step(['30'])
        L_ = foes(); boss = min(L_, key=lambda o: abs(at(o)[0] - npc['x']) + abs(at(o)[1] - npc['y'])) if L_ else None
        if not boss: print(want, 'no boss'); continue
        start = ohp(boss); frames = 0; low = h0; res = 'timeout'; f = TF + t['id']
        for i in range(150):
            if flag(f): res = 'won'; break
            if area() != n or player() == 0: res = 'GOKU FELL'; break
            if boss not in foes(): res = 'boss gone'; break
            e = at(boss); p = pos(); dx, dy = e[0] - p[0], e[1] - p[1]; k = ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) >= abs(dy) else ('DOWN' if dy > 0 else 'UP')
            if i % 8 == 7:
                for ox, oy in ((-14, 0), (14, 0), (0, 12), (0, -12)):
                    if fits(n, e[0] + ox, e[1] + oy): place(e[0] + ox, e[1] + oy); break
            step(['4 ' + k, '4 A', '10', '4 A', '10', '4 A', '14']); frames += 46; low = min(low, hp())
        print('%-10s area %2d level %2d boss HP %5d  %-9s %3ds  Goku HP left %d/%d' % (want, n, L, start, res, frames // 60, low, h0), flush=True)
