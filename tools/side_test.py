"""Bot test of the side content: python3 tools/side_test.py <dir with rom.gba, rom.lists.json and a start state> out/converted/log1data"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = sys.argv[1]; L = sys.argv[2]
sys.argv = ['x', D + '/rom.gba', D, L, '0', '-1']
src = open(os.path.join(ROOT, 'tools', 'story_test.py')).read().split("CK = os.path.join(D, 'ckpt')")[0].replace("os.path.abspath(__file__)", repr(os.path.join(ROOT, 'tools', 'story_test.py')))
exec(src); resumed = True
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import log1_side as S  # noqa: E402
def near(n, x, y):
    for d in range(0, 200, 4):
        for ox in range(-d, d + 1, 4):
            for oy in range(-d, d + 1, 4):
                if max(abs(ox), abs(oy)) == d and fits(n, x + ox, y + oy): return x + ox, y + oy
def foes():
    run(['dump _e 03001bb0 84']); b = rd('_e'); c = struct.unpack_from('<I', b)[0]; return struct.unpack_from('<%dI' % c, b, 4)
def at(o): run(['dump _x %08x 8' % (o + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]
def kill(n, x, y, f):
    idle = 0
    for i in range(900):                                                # placeholder HP is high for a fresh Goku, about 9 damage a hit
        if flag(f): return True
        if i % 8 == 7 and foes():
            ex, ey = at(min(foes(), key=lambda e: abs(at(e)[0] - x) + abs(at(e)[1] - y))); place(*near(n, ex - 14, ey))
        elif i == 0: place(*near(n, x - 30, y)); step(['20'])
        L_ = foes()
        if not L_:
            step(['20']); idle += 1
            if idle > 40: print('  no enemy here'); return False
            continue
        idle = 0
        o = min(L_, key=lambda e: abs(at(e)[0] - x) + abs(at(e)[1] - y)); e = at(o); p = pos(); dx, dy = e[0] - p[0], e[1] - p[1]; k = ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) >= abs(dy) else ('DOWN' if dy > 0 else 'UP')
        step(['%d %s' % (min(20, max(4, (abs(dx) + abs(dy)) // 2)), k)] if abs(dx) + abs(dy) > 26 else ['4 ' + k, '4 A', '10', '4 A', '10', '4 A', '14'])
    return False
print('bounty enemy before the board opens: warp 4'); warp(4); place(*near(4, *S.BOUNTIES[0]['at'])); step(['40']); print(' enemies near', [at(o) for o in foes()][:6], 'spot', near(4, *S.BOUNTIES[0]['at']))
warp(17); x, y = near(17, 360, 320); print('board at', x, y, 'talk', talk(17, x, y, S.OPEN), free(30))
for i, b in enumerate(S.BOUNTIES):
    n = b['area']; print('warp', warp(n), area()); x, y = near(n, *b['at']); ok = kill(n, x, y, S.KILLED + i); free(30); print('bounty', i, b['name'], 'killed', ok, 'paid', flag(S.PAID + i), area(), pos(), flush=True)
print('talk board again', warp(17), talk(17, *near(17, 360, 320), S.OPEN), free(30))
for i, c in enumerate(S.CHESTS):
    n = c['area']; warp(n); x, y = c['at']; print('chest', i, n, c['gear'], 'fits', fits(n, x, y), end=' '); step(['20']); place(*near(n, 8, 8)); step(['10']); place(x, y); step(['40']); got = flag(S.CHEST + i); step(['2 A', '40', '2 A', '40']); a_ = pos(); walk('RIGHT', 12); walk('LEFT', 12); walk('DOWN', 12); walk('UP', 12); print('got', got, 'moves', pos() != a_ or a_, pos(), flush=True)
run(['dump _s 03001c50 4']); print('objs', rd('_s').hex())
setf(S.GATHERED); warp(12); step(['40'])
run(['dump _o 03001c50 90']); b_ = rd('_o'); n_ = struct.unpack_from('<I', b_)[0]; print('objects', n_, [at(p) for p in struct.unpack_from('<%dI' % min(n_, 34), b_, 4)][:n_]); print('spirit spots', [near(12, *s['at']) for s in S.SPIRITS], 'flag', flag(S.GATHERED))
for i, s in enumerate(S.SPIRITS):
    x, y = near(12, *s['at']); print('spirit', i, s['sprite'], 'talk', talk(12, x, y, S.S_START + i), free(30), 'follow', end=' ')
    run(['dump _f 0203ff74 4']); print(rd('_f').hex(), end=' ')
    place(*near(12, 80, 760)); step(['30']); place(*near(12, 76, 708)); step(['60']); free(30); print('delivered', flag(S.S_DONE + i), flush=True)
print('steve open', flag(S.STEVE_OPEN)); x, y = near(12, *S.STEVE['at']); print('steve killed', kill(12, x, y, S.STEVE_DEAD), free(30), 'paid', flag(S.STEVE_PAID), area(), pos())
step(['20', 'shot side_end']); print('done', area(), pos())
