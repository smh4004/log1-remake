"""M4 test: play LoG1's quests 0-3 in the slice build: walk over three items, deliver each to Roshi, get the reward.

    python3 tools/quest_test.py <rom> <dir>        (needs a `start` save state in <dir>)

Presses A only until the expected flag changes, so a finished talk isn't reopened. The player is placed by RAM write next to
each target, but doors and talks are real. Writes only to <dir>.
"""
import os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness')
rom, D = sys.argv[1:3]; BASE = 0x030010BD; cur = ['start']


def run(l):
    p = os.path.join(D, '_q.txt'); open(p, 'w').write('\n'.join(['load ' + cur[0]] + l) + '\n'); subprocess.run([H, rom, p, D], capture_output=True)


def rd(n): return open(os.path.join(D, n + '.bin'), 'rb').read()


def step(l):
    run(l + ['save _n']); cur[0] = '_n'


def flag(f):
    run(['dump _f %08x 1' % (BASE + (f >> 3))]); return rd('_f')[0] >> (f & 7) & 1


def player():
    run(['dump _p 03001c34 4']); return struct.unpack('<I', rd('_p'))[0]


def area():
    run(['dump _a 03001980 4']); a = struct.unpack('<I', rd('_a'))[0] - 0x08000000
    return tuple(open(rom, 'rb').read()[a:a + 2])


def pos():
    run(['dump _x %08x 8' % (player() + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]


def place(x, y):
    P = player() + 0x1A0; step(['w8 %08x %02x' % (P + i, b) for i, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + ['2', '10'])


def press_until(f, tries=30):
    for i in range(tries):
        step(['2 A', '30'])
        if flag(f): return i + 1
    return None


def settle(n=14):
    """After a flag fires, finish any remaining lines. Stops once the player can walk."""
    for i in range(n):
        a = pos(); step(['20 DOWN', '5']); b = pos(); step(['20 UP', '5']); 
        if a != b or pos() != a: return i
        step(['2 B', '20', '2 A', '30'])
    return None


def walk(key, frames=30): step(['%d %s' % (frames, key), '10'])


Q = 700; print('start', area(), pos())
def collect(x, y, f):
    place(x - 40, y)
    for i in range(6):
        walk('RIGHT', 12)
        if flag(f): break
    print('found', f, bool(flag(f)), pos())
    for i in range(3): step(['2 A', '30'])
def give(f):
    place(224, 240); walk('RIGHT', 8); n = press_until(f); print('delivered', f, n, pos())
collect(160, 84, Q); give(Q + 1); print(' free', settle(), pos())
collect(328, 212, Q + 2); give(Q + 3); print(' free', settle(), pos())
place(256, 160); walk('UP', 40); print('door in', area(), pos())
collect(168, 132, Q + 4)
place(112, 140); walk('DOWN', 40); step(['90']); print('door out', area(), pos())
give(Q + 5); print('reward', press_until(Q + 6, 4) or flag(Q + 6)); print('flags', {f: flag(f) for f in range(Q, Q + 7)})
print('final free', settle(), pos(), area()); run(['dump _c 03001560 d0']); os.replace(os.path.join(D, '_c.bin'), os.path.join(D, 'chr_end.bin'))
