"""Bot test of the later side content: python3 tools/side2_test.py <dir with rom.gba, rom.lists.json, blank.sav and a start state> out/converted/log1data"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = sys.argv[1]; L = sys.argv[2]
sys.argv = ['x', D + '/rom.gba', D, L, '0', '-1']
src = open(os.path.join(ROOT, 'tools', 'story_test.py')).read().split("CK = os.path.join(D, 'ckpt')")[0].replace("os.path.abspath(__file__)", repr(os.path.join(ROOT, 'tools', 'x.py')))
exec(src); resumed = True
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import log1_side as S  # noqa: E402
head = open(os.path.join(ROOT, 'tools', 'side_test.py')).read(); exec(head[head.index('def near('):head.index("print('bounty enemy before")])
def setf(f):
    run(['dump _b %08x 1' % (BASE + (f >> 3))]); step(['w8 %08x %02x' % (BASE + (f >> 3), rd('_b')[0] | 1 << (f & 7)), '2'])
def stats(): run(['dump _h 03001574 4']); step(['w8 03001576 ff', 'w8 03001577 7f', '1'])
print('start', area(), pos(), flush=True)
setf(S.BUTLER['after']); print('warp 11', warp(11), area()); step(['40']); x, y = near(11, *S.BUTLER['at']); print('butler talk', talk(11, x, y, S.BUTLER_OPEN), free(30), flush=True)
for i, (spot_, _) in enumerate(S.SLIPPERS):
    x, y = near(11, *spot_); place(x - 30 if fits(11, x - 30, y) else x, y); step(['20']); place(x, y); step(['60']); free(30); print('slipper', i, flag(S.SLIPPER + i), flush=True)
x, y = near(11, *S.BUTLER['at']); print('butler paid', talk(11, x, y, S.BUTLER_PAID), free(30), flush=True)
setf(S.COACH['after']); print('warp 13', warp(13), area()); step(['40']); x, y = near(13, *S.COACH['at']); print('coach talk', talk(13, x, y, S.COACH_OPEN), free(30), flush=True)
for i, spot_ in enumerate(S.COACH['foes']):
    stats(); x, y = near(13, *spot_); print('ghost', i, kill(13, x, y, S.COACH_KILLED + i), free(30), flush=True)
print('coach paid', flag(S.COACH_PAID), flush=True)
setf(S.AFTER_ELITES)
for i, e in enumerate(S.ELITES):
    stats(); n = e['area']; print('warp', n, warp(n), area()); x, y = near(n, *e['at']); print('elite', i, kill(n, x, y, S.ELITE_KILLED + i), free(30), 'paid', flag(S.ELITE_PAID + i), flush=True)
setf(S.ELDER['after']); print('warp 24', warp(24), area()); step(['40']); x, y = near(24, *S.ELDER['at']); print('elder', talk(24, x, y, S.ELDER_PAID), free(30), flush=True)
setf(S.ANNOUNCER['after']); print('warp 0', warp(0), area()); step(['40'])
for i, m in enumerate(S.REMATCHES):
    x, y = near(0, *S.ANNOUNCER['at']); print('announcer', i, talk(0, x, y, S.RM_OPEN + i), free(30), flush=True)
    stats(); x, y = near(0, *m['at']); print('rematch', m['name'], kill(0, x, y, S.RM_KILLED + i), free(30), 'paid', flag(S.RM_PAID + i), flush=True)
print('done', area(), pos(), flush=True)
