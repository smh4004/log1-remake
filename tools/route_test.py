"""M4 test of the generated route: opening quests, warp to the forest, then Raditz's talk, fight and exit.

    python3 tools/route_test.py <rom> <dir>     (needs a `start` save state in <dir>)

Doors, pickups, talks and fights are real. The player is placed by RAM write beside each target, and quests between the forest
and Raditz are skipped by setting their flags, so they aren't tested here.
"""
import os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness')
rom, D = sys.argv[1:3]; BASE = 0x030010BD; cur = ['start']; ROM = open(rom, 'rb').read(); QF, TF = 420, 500


def run(l):
    p = os.path.join(D, '_q.txt'); open(p, 'w').write('\n'.join(['load ' + cur[0]] + l) + '\n'); subprocess.run([H, rom, p, D], capture_output=True)
def rd(n): return open(os.path.join(D, n + '.bin'), 'rb').read()
def step(l): run(l + ['save _n']); cur[0] = '_n'
def flag(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); return rd('_f')[0] >> (f & 7) & 1
def setf(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); v = rd('_f')[0] | 1 << (f & 7); step(['w8 %08x %02x' % (BASE + (f >> 3), v)])
def player(): run(['dump _p 03001c34 4']); return struct.unpack('<I', rd('_p'))[0]
def area(): run(['dump _a 03001980 4']); a = struct.unpack('<I', rd('_a'))[0] - 0x08000000; return tuple(ROM[a:a + 2])
def pos(): run(['dump _x %08x 8' % (player() + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]
def place(x, y): P = player() + 0x1A0; step(['w8 %08x %02x' % (P + i, b) for i, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + ['2', '10'])
def walk(k, n=30): step(['%d %s' % (n, k), '10'])
def press_until(f, tries=30):
    for i in range(tries):
        step(['2 A', '30'])
        if flag(f): return i + 1
def clear(n=8):
    for i in range(n): step(['2 A', '30'])
def wait_area(a, tries=12):
    for i in range(tries):
        if area() == a: return True
        step(['2 A', '40'])
    return False


def free(tries=14):
    """Close open text until the player can move."""
    for i in range(tries):
        a = pos(); walk('DOWN', 8); b = pos()
        if a != b: walk('UP', 8); return i
        walk('UP', 8)
        if pos() != a: return i
        step(['2 A', '30'])
    return None


print('start', area(), pos())
def collect(x, y, t, sx=-40, key='RIGHT'):
    place(x + sx, y)
    for i in range(6):
        walk(key, 12)
        if flag(t): break
    print('item', t, bool(flag(t)), free())
def give(t): place(224, 240); walk('RIGHT', 8); print('give', t, press_until(t), free())
collect(160, 84, TF + 0); give(TF + 1)
collect(328, 212, TF + 2, 40, 'LEFT'); give(TF + 3)   # Gohan stands west of this spot
place(256, 160); walk('UP', 40); step(['60']); print('in', area())
collect(168, 132, TF + 4); place(112, 140); walk('DOWN', 40); step(['90']); print('out', area())
give(TF + 5); print('quest 3', flag(QF + 3), 'free', free(30))
place(300, 225); print('zone', pos(), area()); walk('RIGHT', 30); step(['60']); print('warped?', area(), pos(), 'quests', [flag(QF + i) for i in range(4)])
# skip quests between the forest and Raditz
for q in range(4, 22): setf(QF + q)
print('forced quest 21', flag(QF + 21))
