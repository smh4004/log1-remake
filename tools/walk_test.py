"""M4 test: walk the player across a LoG1 area using the walkable mask, then step into a warp zone and report the new area.

    python3 tools/walk_test.py <rom> <dir> <state> <log1-decomp> <LoG1 area> <x0> <y0> <x1> <y1> <UP|DOWN|LEFT|RIGHT>

Plans a route in 8 px tiles with a margin from walls, and replans from the real position each chunk. Writes only to <dir>.
"""
import collections, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import map_convert as C  # noqa: E402
H = os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness')
rom, D, st, log1, n = sys.argv[1:6]; rect = [int(v) for v in sys.argv[6:10]]; key = sys.argv[10]; a = C.Area(log1, int(n)); w = a.L['walkable'] > 0


def run(l):
    p = os.path.join(D, '_w.txt'); open(p, 'w').write('\n'.join(l) + '\n'); subprocess.run([H, rom, p, D], capture_output=True)


def rd(f): return open(os.path.join(D, f + '.bin'), 'rb').read()


def u(f): return struct.unpack('<I', rd(f)[:4])[0]


def pos(cur):
    run(['load ' + cur, 'dump _q 03001c34 4', 'dump _a 03001980 4']); q = u('_q'); run(['load ' + cur, 'dump _xy %08x 8' % (q + 0x1A0)])
    x, y = struct.unpack('<2i', rd('_xy')); return x >> 8, y >> 8, u('_a')


def fits(x, y, bw=16, bh=8):
    """The same rule as BF's sub_08009324: every tile the box touches must be set in the mask."""
    if x < 0 or y < 0: return False
    x1, y1 = (x + bw + 7) >> 3, (y + bh + 7) >> 3
    return y1 <= a.H and x1 <= a.W and w[y >> 3:y1, x >> 3:x1].all()


def path(sx, sy, gx, gy):
    """Breadth-first search on a 4 px grid, from the real position to the nearest fitting point of the target zone."""
    S = (sx, sy); prev = {S: None}; q = collections.deque([S]); G = None
    while q:
        c = q.popleft()
        if rect[0] <= c[0] < rect[2] and rect[1] <= c[1] < rect[3]: G = c; break
        for dx, dy, k in ((4, 0, 'RIGHT'), (-4, 0, 'LEFT'), (0, 4, 'DOWN'), (0, -4, 'UP')):
            t = (c[0] + dx, c[1] + dy)
            if t not in prev and fits(*t): prev[t] = (c, k); q.append(t)
    if G is None: return None
    keys = []; c = G
    while prev[c]: keys.append(prev[c][1]); c = prev[c][0]
    return keys[::-1]


cur = st; gx, gy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2; x, y, start = pos(cur); print('start', x, y, hex(start))
for i in range(60):
    x, y, ar = pos(cur)
    if ar != start: print('warped at step', i, 'to area', hex(ar), 'at', x, y); break
    if rect[0] <= x < rect[2] and rect[1] <= y < rect[3]: k, f = key, 24
    else:
        p = path(x, y, gx, gy)
        if not p: k, f = key, 24
        else: k, f = p[0], 3 * max(1, next((j for j, v in enumerate(p) if v != p[0]), len(p)))
        f = min(f, 30)
    if i % 6 == 0: print('step', i, x, y, k, flush=True)
    run(['load ' + cur, '%d %s' % (f, k), 'save _w']); cur = '_w'
else: print('no warp after 60 steps at', x, y)
run(['load ' + cur, '60', 'save end', 'dump _a 03001980 4']); print('final area', hex(u('_a')))
