"""M4 test of LoG1's story between two quests on the generated build: real doors, pickups, talks and bridge pieces.

    START=2,632,384 OUT=story python3 tools/slice_build.py <deps>
    python3 tools/story_test.py out/slice/story.gba <dir> <log1-decomp> <first quest> <last quest>

<dir> needs a `start` save state. The player is placed by RAM write beside each target and kept alive, so routes and balance are not tested.
"""
import collections, json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness')
rom, D, L, first, last = sys.argv[1:6]; first, last = int(first), int(last); ROM = open(rom, 'rb').read(); BASE = 0x030010BD; QF, TF = 420, 500; cur = ['start']
names = [l.split()[1] for l in open(L + '/assets/areas/SPRITES.txt')]; Q = json.load(open(L + '/assets/story/quests.json'))['quests']; IDS = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10]
AREAS = {n: json.load(open('%s/assets/areas/area%02d.json' % (L, n))) for n in IDS}
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import map_convert as C  # noqa: E402
WALK = {n: C.Area(L, n).L['walkable'] > 0 for n in IDS}


def run(l):
    p = os.path.join(D, '_q.txt'); open(p, 'w').write('\n'.join(['load ' + cur[0]] + l) + '\n'); subprocess.run([H, rom, p, D], capture_output=True)
def rd(n): return open(os.path.join(D, n + '.bin'), 'rb').read()
HP = ['w8 %08x %02x' % (0x03001574 + i, b) for i, b in enumerate(struct.pack('<I', 100 << 16))]
def step(l): run(HP + l + ['save _n']); cur[0] = '_n'
def flag(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); return rd('_f')[0] >> (f & 7) & 1
def setf(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); step(['w8 %08x %02x' % (BASE + (f >> 3), rd('_f')[0] | 1 << (f & 7))])
def player(): run(['dump _p 03001c34 4']); return struct.unpack('<I', rd('_p'))[0]
def area():
    run(['dump _a 03001980 4']); a = struct.unpack('<I', rd('_a'))[0] - 0x08000000; return ROM[a + 1] - 1 if ROM[a] == 26 else -1
def pos(): run(['dump _x %08x 8' % (player() + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]
def place(x, y): P = player() + 0x1A0; step(['w8 %08x %02x' % (P + i, b) for i, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + ['2', '10'])
def walk(k, n=30): step(['%d %s' % (n, k), '10'])
def fits(n, x, y):
    W = WALK[n]
    if x < 0 or y < 0 or (y + 7) >> 3 >= W.shape[0] or (x + 15) >> 3 >= W.shape[1]: return False
    return bool(W[y >> 3:((y + 7) >> 3) + 1, x >> 3:((x + 15) >> 3) + 1].all())
DIRS = [('RIGHT', -1, 0), ('LEFT', 1, 0), ('UP', 0, 1), ('DOWN', 0, -1)]


def free(tries=24):
    """Close any open text."""
    for i in range(tries):
        a = pos(); walk('DOWN', 6); b = pos()
        if a != b: walk('UP', 6); return True
        walk('UP', 6)
        if pos() != a: return True
        step(['2 A', '30'])
    return False


def doors():
    g = collections.defaultdict(list)
    for n, a in AREAS.items():
        for t in a['triggers']:
            if t['kind'] == 'warp' and t['to_area'] in AREAS and t['mode'] & 1: g[n].append((t['to_area'], t['rect'], 0))
    for x in Q:
        for a in x['actions']:
            if a['type'] == 'add_warp' and a['area'] in AREAS and a['to_area'] in AREAS: g[a['area']].append((a['to_area'], (a['x1'], a['y1'], a['x2'], a['y2']), QF + x['quest']))
    return g
G = doors()


def travel(to):
    while True:
        n = area()
        if n == to: return True
        seen = {n: None}; todo = [n]
        while todo and to not in seen:
            u = todo.pop(0)
            for v, rect, f in G[u]:
                if v not in seen and (not f or flag(f)): seen[v] = (u, rect); todo.append(v)
        if to not in seen: print('  no path', n, to); return False
        v = to
        while seen[v][0] != n: v = seen[v][0]
        x0, y0, x1, y1 = [max(0, r) for r in seen[v][1]]; ok = False
        for k, dx, dy in DIRS:                                          # walk in from a clear spot just outside the zone
            for off in (8, 16, 24, 32):
                sx = (x0 + x1) // 2 - 8 + dx * ((x1 - x0) // 2 + off); sy = (y0 + y1) // 2 - 4 + dy * ((y1 - y0) // 2 + off)
                if fits(n, sx, sy): break
            else: continue
            place(sx, sy); walk(k, 40); step(['80'])
            if area() == v: ok = True; break
        if not ok:                                                      # a door set into a wall: stand inside the zone and press towards it
            for sy in range(y0, y1, 8):
                for sx in range(x0, x1, 8):
                    if ok or not fits(n, sx, sy): continue
                    for k, dx, dy in DIRS:
                        place(sx, sy); walk(k, 20); step(['80'])
                        if area() == v: ok = True; break
        if not ok: print('  door failed', n, '->', v, seen[v][1]); return False
        step(['90'])                                                    # no free(): walking up here would go back through the door


def touch(n, x, y, want, keys=None):
    """Walk onto a spot from a clear side until flag `want` is set."""
    for k, dx, dy in DIRS:
        for off in (24, 32, 40):
            sx, sy = x + dx * off, y + dy * off
            if all(fits(n, x + dx * d, y + dy * d) for d in range(0, off + 1, 4)): break
        else: continue
        place(sx, sy); walk(k, 24); step(['30'])
        if flag(want): return True
        free(8)
    return False


def talk(n, x, y, want, tries=36):
    for k, dx, dy in DIRS:
        sx, sy = x + dx * 17, y + dy * 9
        if not fits(n, sx, sy): continue
        place(sx, sy); walk(k, 6)
        for i in range(tries // 4):
            step(['2 A', '40'])
            if flag(want): return True
        free()
    return False


def actor(n, sprite, st=None):
    return [a for a in AREAS[n]['actors'] if a['kind'] != 2 and a['sprite'] == sprite and (st is None or a['param'] == st)]


def fight(n, t, f):
    """Talk to the boss's NPC is done by the quest before; chase the last enemy in the list and hit it."""
    for i in range(200):
        if flag(f) or flag(QF + 23) or area() != n: return True
        run(['dump _e 03001bb0 84']); b = rd('_e'); c = struct.unpack_from('<I', b)[0]
        if not c: step(['2 A', '30']); continue
        run(['dump _x %08x 8' % (struct.unpack_from('<I', b, 4 * c)[0] + 0x1A0)]); e = [v >> 8 for v in struct.unpack('<2i', rd('_x'))]; p = pos()
        dx, dy = e[0] - p[0], e[1] - p[1]; k = ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) >= abs(dy) else ('DOWN' if dy > 0 else 'UP')
        step(['%d %s' % (min(20, max(4, (abs(dx) + abs(dy)) // 2)), k)] if abs(dx) + abs(dy) > 26 else ['4 ' + k, '4 A', '10', '4 A', '10', '4 A', '14'])
    return False


def do_task(t):
    k = t['type']; f = TF + t.get('id', 0)
    if k == 'after_quest' or flag(f): return True
    if not travel(t['area']): return False
    n = t['area']
    if k == 'spawn_item': return touch(n, t['x'], t['y'], f)
    if k == 'place_item':
        place(t['x1'], t['y2'] + 20); walk('UP', 16); step(['30'])    # the gap before this one is open by now
        return bool(flag(f)) or touch(n, t['x1'], t['y1'], f)
    if k == 'spawn_character': return talk(n, t['x'], t['y'], f)
    if k in ('talk_with_item', 'talk_with_kind', 'escort'):
        a = actor(n, names[t['sprite']])
        if not a: print('  no actor', names[t['sprite']]); return False
        return talk(n, a[0]['x'], a[0]['y'], f)
    if k == 'after_conversation':
        a = [x for x in AREAS[n]['actors'] if x['kind'] != 2 and x['param'] == t['set']]
        if not a: print('  no actor for set', t['set']); return False
        for i in range(4):
            if talk(n, a[0]['x'], a[0]['y'], f): return True
        return False
    if k == 'activate': return fight(n, t, f)
    print('  task type not driven', k); return False


for q in range(first): setf(QF + q)
print('start area', area(), pos()); bad = []
for x in Q[first:last + 1]:
    n = x['quest']; res = []
    for t in x['tasks']:
        ok = do_task(t); free(30); res.append((t['type'], ok, t.get('id')))
        if not ok: print('  FAILED', t['type'], {k: v for k, v in t.items() if k not in ('label', 'raw', 'type')})
    free(30); done = flag(QF + n)
    print('quest', n, x.get('name'), 'done' if done else 'NOT DONE', [r[1] for r in res], 'area', area(), pos(), flush=True)
    if not done: bad.append(n)
print('not done:', bad)
if last >= 10 and first <= 8: place(200, 455); walk('UP', 70); print('crossed the bridge:', pos(), area())
