"""M4 test bot: from a saved state with a live enemy, chase it and attack, then report the defeat flag and player stats.

    python3 tools/chain_test.py <rom> <dir> <start state> <enemy object hex> <flag>

Each step runs a short harness chunk from the last save state. Writes only to <dir>.
"""
import os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness')
rom, D, st, enemy, flag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
FB = 0x030010BD + (flag >> 3); PLAYER = 0x0202E4C8


def run(lines):
    p = os.path.join(D, '_b.txt'); open(p, 'w').write('\n'.join(lines) + '\n')
    subprocess.run([H, rom, p, D], capture_output=True)


def rd(n): return open(os.path.join(D, n + '.bin'), 'rb').read()


cur = st
for step in range(80):
    run(['load ' + cur, 'dump _p %08x 8' % PLAYER, 'dump _e %s 200' % enemy, 'dump _c 03001bb0 4', 'dump _f %08x 1' % FB, 'dump _h 03001574 4'])
    px, py = struct.unpack('<2i', rd('_p')); ex, ey = struct.unpack_from('<2i', rd('_e'), 0x1A0)
    n = struct.unpack('<I', rd('_c'))[0]; f = rd('_f')[0] >> (flag & 7) & 1; hp = struct.unpack('<I', rd('_h'))[0] >> 16
    if step % 8 == 0 or n == 0 or f: print('step', step, 'player', px >> 8, py >> 8, 'enemy', ex >> 8, ey >> 8, 'enemies', n, 'flag', f, 'hp', hp, flush=True)
    if n == 0 or f or hp == 0: break
    dx, dy = (ex - px) >> 8, (ey - py) >> 8
    if abs(dx) > 26 or abs(dy) > 12:
        key = ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) >= abs(dy) else ('DOWN' if dy > 0 else 'UP')
        act = ['10 ' + key]
    else:
        act = ['2 ' + ('RIGHT' if dx > 0 else 'LEFT'), '4 A', '8', '4 A', '8']
    run(['load ' + cur] + act + ['save _s']); cur = '_s'
run(['load ' + cur, '120', 'dump _f %08x 1' % FB, 'dump _c 03001bb0 4', 'dump _chr 03001560 d0'])
print('end: flag', rd('_f')[0] >> (flag & 7) & 1, 'enemies', struct.unpack('<I', rd('_c'))[0])
