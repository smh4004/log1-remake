"""M4 test of LoG1's story between two quests on the generated build: real doors, pickups, talks and bridge pieces.

    START=2,632,384 OUT=story python3 tools/slice_build.py <deps>
    python3 tools/story_test.py out/slice/story.gba <dir> <log1-decomp> <first quest> <last quest>

<dir> needs a `start` save state. The player is placed by RAM write beside each target and kept alive, so routes and balance are not tested.

Progress is saved after every quest in <dir>/ckpt. RESUME=1 continues from there. On the same ROM that's the exact save state. On a rebuilt ROM a state's
pointers go stale, so it boots fresh, restores game data (flags, inventory, EXP) and warps through the test lists in <rom>.lists.json.
A death reloads the last checkpoint and tries the quest again. Run a full pass without RESUME from time to time, as resumed runs skip the earlier quests.
"""
import collections, hashlib, json, os, re, shutil, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
rom, D, L, first, last = sys.argv[1:6]; first, last = int(first), int(last); ROM = open(rom, 'rb').read(); BASE = 0x030010BD; QF, TF = 420, 500; cur = ['start']
names = [l.split()[1] for l in open(L + '/assets/areas/SPRITES.txt')]; Q = json.load(open(L + '/assets/story/quests.json'))['quests']; IDS = sorted(int(f[4:6]) for f in os.listdir(L + '/assets/areas') if re.match(r'area\d\d\.json', f) and (int(f[4:6]) != 29 or not os.path.exists(L + '/assets/areas/area42.json')))
AREAS = {n: json.load(open('%s/assets/areas/area%02d.json' % (L, n))) for n in IDS}
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import map_convert as C  # noqa: E402
WALK = {n: C.Area(L, n).L['walkable'] > 0 for n in IDS}; FLY = {n: C.Area(L, n).L['flyable'] > 0 for n in IDS}


BLANK = os.path.join(D, 'blank.sav')
if not os.path.exists(BLANK): open(BLANK, 'wb').write(b'\xff' * 8192)   # what an emulator gives a new game; never test with an all-zero save
os.environ['SAVEF'] = BLANK


def run(l):
    p = os.path.join(D, '_q.txt'); open(p, 'w').write('\n'.join(['load ' + cur[0]] + l) + '\n'); subprocess.run([H, rom, p, D], capture_output=True)
def rd(n): return open(os.path.join(D, n + '.bin'), 'rb').read()
HP = ['w8 %08x %02x' % (0x03001574 + i, b) for i, b in enumerate(struct.pack('<I', 30000 << 16))] if not os.environ.get('NO_TOPUP') else []                # NO_TOPUP=1: a difficulty run, where Goku can die
def step(l): run(HP + l + ['save _n']); cur[0] = '_n'
def flag(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); return rd('_f')[0] >> (f & 7) & 1
def setf(f): run(['dump _f %08x 1' % (BASE + (f >> 3))]); step(['w8 %08x %02x' % (BASE + (f >> 3), rd('_f')[0] | 1 << (f & 7))])
def player(): run(['dump _p 03001c34 4']); return struct.unpack('<I', rd('_p'))[0]
def area():
    run(['dump _a 03001980 4']); a = struct.unpack('<I', rd('_a'))[0] - 0x08000000; return ROM[a + 1] - 1 if 0 <= a < len(ROM) and ROM[a] == 26 else -1
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
            if t['kind'] == 'warp' and t['to_area'] in AREAS: g[n].append((t['to_area'], t['rect'], 0))
    for x in Q:
        for a in x['actions']:
            if a['type'] == 'add_warp' and a['area'] in AREAS and a['to_area'] in AREAS: g[a['area']].append((a['to_area'], (a['x1'], a['y1'], a['x2'], a['y2']), QF + x['quest']))
    for x in Q:                                                         # a quest zone that warps (Snake Way's fall into Hell, ...)
        w = next((a for a in x['actions'] if a['type'] == 'warp'), None)
        if w:
            for z in x['tasks']:
                if z['type'] == 'enter_zone' and z['area'] in AREAS: g[z['area']].append((w['area'], (z['x1'], z['y1'], z['x2'], z['y2']), 0))
    return g
G = doors()
LISTS = json.load(open(rom[:-4] + '.lists.json')) if os.path.exists(rom[:-4] + '.lists.json') else {}


def warp(to):
    """Test list: go straight to an area, for quests whose real route was played before the resume."""
    if str(to) not in LISTS: return False
    step(['w8 %08x %02x' % (0x0300617C + i, b) for i, b in enumerate(struct.pack('<I', LISTS[str(to)]))] + ['150'])
    return area() == to


def travel(to):
    while True:
        n = area()
        if n == to: return True
        seen = {n: None}; todo = [n]
        while todo and to not in seen:
            u = todo.pop(0)
            for v, rect, f in G[u]:
                if v not in seen and (not f or flag(f)): seen[v] = (u, rect); todo.append(v)
        if to not in seen:
            if resumed and warp(to): continue
            print('  no path', n, to); return False
        v = to
        while seen[v][0] != n: v = seen[v][0]
        x0, y0, x1, y1 = [max(0, r) for r in seen[v][1]]; ok = False
        for k, dx, dy in DIRS:                                          # walk in from a clear spot just outside the zone
            for off in (8, 16, 24, 32):
                sx = (x0 + x1) // 2 - 8 + dx * ((x1 - x0) // 2 + off); sy = (y0 + y1) // 2 - 4 + dy * ((y1 - y0) // 2 + off)
                if fits(n, sx, sy): break
            else: continue
            place(sx, sy); walk(k, 40); step(['80'])
            for i in range(3):                                          # a zone's dialogue can stop the walk short
                if area() == v: break
                step(['2 A', '40']); walk(k, 30); step(['80'])
            if area() == v: ok = True; break
        if not ok:                                                      # a door set into a wall: stand inside the zone and press towards it
            for sy in range(y0, y1, 8):
                for sx in range(x0, x1, 8):
                    if ok or not fits(n, sx, sy): continue
                    for k, dx, dy in DIRS:
                        place(sx, sy); walk(k, 20); step(['80'])
                        if area() == v: ok = True; break
        if not ok: ok = fly_into(n, seen[v][1], lambda: area() == v); land()
        if not ok:                                                      # static masks miss quest-opened ground, and a zone's scene can hold the warp back
            for k, dx, dy in DIRS:
                place((x0 + x1) // 2 - 8, (y0 + y1) // 2 - 4); walk(k, 12); step(['40'])
                for i in range(14):
                    if area() == v: ok = True; break
                    step(['2 A', '30'])
                if ok: break
        if not ok: print('  door failed', n, '->', v, seen[v][1]); return False
        step(['90'])                                                    # no free(): walking up here would go back through the door


def land():
    """Back on foot, so later walks use the floor mask. A new area cancels flying by itself."""
    run(['dump _s 0203ff05 1'])
    if rd('_s')[0]: step(['4 R', '20'])


def fly_into(n, rect, done):
    """Zones only flight reaches, like the top of area 3: take off (R), then cross into the zone from each clear side."""
    x0, y0, x1, y1 = [max(0, v) for v in rect]; F = FLY[n]
    run(['dump _s 0203ff05 1'])
    if not rd('_s')[0]: step(['4 R', '20'])
    for k, dx, dy in DIRS:
        sx, sy = (x0 + x1) // 2 - 8 + dx * ((x1 - x0) // 2 + 20), (y0 + y1) // 2 - 4 + dy * ((y1 - y0) // 2 + 20)
        if sy < 0 or sx < 0 or (sy >> 3) + 1 >= F.shape[0] or (sx >> 3) + 2 >= F.shape[1] or not F[sy >> 3:(sy >> 3) + 2, sx >> 3:(sx >> 3) + 3].all(): continue
        place(sx, sy); walk(k, 40); step(['90'])
        if done(): return True
    return False


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
    """Chase and hit the boss: the enemy nearest its NPC's spot when the fight starts, as streamed enemies join the same list."""
    def foes():
        run(['dump _e 03001bb0 84']); b = rd('_e'); c = struct.unpack_from('<I', b)[0]; return struct.unpack_from('<%dI' % c, b, 4)
    def at(o): run(['dump _x %08x 8' % (o + 0x1A0)]); return [v >> 8 for v in struct.unpack('<2i', rd('_x'))]
    want = names[t['sprite']]; a = [x for x in AREAS[n]['actors'] if x['sprite'] == want]
    if a:
        for ox, oy in ((-30, 0), (30, 0), (0, 30), (0, -30), (-60, 0), (60, 0)):
            if fits(n, a[0]['x'] + ox, a[0]['y'] + oy): place(a[0]['x'] + ox, a[0]['y'] + oy); break
        step(['30'])
    for w in range(6):
        L = foes()
        if L: break
        step(['2 A', '30'])
    if not L: print('  no enemy for', want); return bool(flag(f))
    x0, y0 = (a[0]['x'], a[0]['y']) if a else pos(); boss = min(L, key=lambda o: abs(at(o)[0] - x0) + abs(at(o)[1] - y0))
    for i in range(700):
        if os.environ.get('TRACE') and i % 4 == 0: print('   f', i, status()['hp'], 'foes', len(foes()), 'boss', at(boss) if boss in foes() else None, 'me', pos(), flush=True)
        if flag(f) or area() != n: return True
        if dead(): return False
        if boss not in foes():                                          # the one chosen was another of the group, so fight whoever's left instead of standing still
            L = foes()
            if not L: step(['2 A', '30']); continue
            p = pos(); boss = min(L, key=lambda o: abs(at(o)[0] - p[0]) + abs(at(o)[1] - p[1]))
        e = at(boss)
        if i % 8 == 7:                                                  # routes aren't under test: reach a boss hovering over a wall
            for ox, oy in ((-18, 0), (18, 0), (0, 12), (0, -12), (-30, 0), (30, 0), (0, 24), (0, -24)):
                if fits(n, e[0] + ox, e[1] + oy): place(e[0] + ox, e[1] + oy); break
        p = pos(); dx, dy = e[0] - p[0], e[1] - p[1]; k = ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) >= abs(dy) else ('DOWN' if dy > 0 else 'UP')
        if abs(dx) + abs(dy) < 8: walk('DOWN' if k == 'UP' else 'UP' if k == 'DOWN' else 'LEFT' if k == 'RIGHT' else 'RIGHT', 10)   # too close for a punch to connect
        step(['%d %s' % (min(20, max(4, (abs(dx) + abs(dy)) // 2)), k)] if abs(dx) + abs(dy) > 26 else ['4 ' + k, '4 A', '10', '4 A', '10', '4 A', '14'])
        if pos() == p and abs(dx) + abs(dy) > 26: walk(('UP' if i % 2 else 'DOWN') if k in ('LEFT', 'RIGHT') else ('LEFT' if i % 2 else 'RIGHT'), 24)   # blocked: step around
    print('  fight timed out, boss at', at(boss), 'player', pos()); return False


def spend_points():
    """Difficulty runs spend level-up points as a player might: half on strength, half on endurance."""
    if not os.environ.get('NO_TOPUP'): return
    run(['dump _g 03001588 8']); g = rd('_g'); s, p, e, sp, pts = g[0], g[1], g[2], g[3], struct.unpack_from('<I', g, 4)[0]
    if not pts or pts > 2000: return
    step(['w8 03001588 %02x' % min(255, s + pts // 2), 'w8 0300158a %02x' % min(255, e + pts - pts // 2)] + ['w8 %08x 00' % (0x0300158C + i) for i in range(4)])


def status():
    run(['dump _g 03001574 1c']); g = rd('_g'); return dict(hp=struct.unpack_from('<H', g, 2)[0], max=struct.unpack_from('<H', g, 4)[0], xp=struct.unpack_from('<I', g, 0x10)[0], str=g[0x14], end=g[0x16], pts=struct.unpack_from('<I', g, 0x18)[0])


def do_task(t):
    k = t['type']; f = TF + t.get('id', 0)
    if k == 'after_quest' or flag(f): return True
    if not travel(t['area']) and not travel(t['area']): return False
    n = t['area']
    if k == 'spawn_item':
        for i in range(3):                                              # an enemy can knock the player off the way
            if touch(n, t['x'], t['y'], f): return True
        place(t['x'] - 30, t['y']); step(['2']); place(t['x'], t['y']); step(['40']); return bool(flag(f))     # stepping straight into the zone
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
    if k in ('activate', 'defeat'): return fight(n, t, f)
    if k == 'enter_zone':
        x0, y0, x1, y1 = [max(0, v) for v in (t['x1'], t['y1'], t['x2'], t['y2'])]
        for k2, dx, dy in DIRS:
            sx, sy = (x0 + x1) // 2 - 8 + dx * ((x1 - x0) // 2 + 20), (y0 + y1) // 2 - 4 + dy * ((y1 - y0) // 2 + 20)
            if fits(n, sx, sy): place(sx, sy); walk(k2, 40); step(['60'])
            if flag(f): return True
        if flag(f): return True
        r_ = fly_into(n, (x0, y0, x1, y1), lambda: flag(f)); land(); return r_
    if k == 'obstacle': return touch(n, t['x1'], t['y1'], f)
    print('  task type not driven', k); return False


CK = os.path.join(D, 'ckpt'); os.makedirs(CK, exist_ok=True); SHA = hashlib.sha1(ROM).hexdigest(); PROG = os.path.join(CK, 'progress.json'); GAME = (0x03001068, 0xC8)
def ckpt(q):
    run(['dump _g %08x %x' % GAME]); shutil.copy(os.path.join(D, cur[0] + '.ss'), os.path.join(CK, 'last.ss')); json.dump(dict(sha=SHA, quest=q, game=rd('_g').hex()), open(PROG + '.tmp', 'w')); os.replace(PROG + '.tmp', PROG)
def reload():
    shutil.copy(os.path.join(CK, 'last.ss'), os.path.join(D, '_ck.ss')); cur[0] = '_ck'
resumed = False
if os.environ.get('RESUME') and os.path.exists(PROG):
    P = json.load(open(PROG)); resumed = True
    if P['sha'] == SHA: reload(); print('resumed from the save state after quest', P['quest'])
    else:
        step(['w8 %08x %02x' % (GAME[0] + i, b) for i, b in enumerate(bytes.fromhex(P['game']))] + ['10']); print('rebuilt ROM: restored game data after quest', P['quest'])
else:
    for q in range(first): setf(QF + q)
    step(['2']); ckpt(-1)
print('start area', area(), pos())
XP = [0]
def dead():
    """A real game over stays gone, or the bot's own A presses start a new game from its menu, which wipes EXP. Cutscenes and story pictures reload the area, which clears the player for a moment."""
    if player() != 0 and area() >= 0 and status()['xp'] < XP[0]: return True
    for _ in range(4):
        if area() >= 0 and player() != 0: return False
        step(['60'])                                                  # no buttons: A on a game over screen would start a new game
    return True
todo = [x for x in Q[first:last + 1]]
for attempt in range(4):                                                # numeric order isn't always story order, so later passes retry what was blocked
    bad = []
    for x in todo:
        n = x['quest']; res = []
        if flag(QF + n): continue
        for tries in range(3):
            res = []; spend_points()
            for t in x['tasks']:
                ok = do_task(t); free(30); res.append((t['type'], ok, t.get('id')))
                if not ok: print('  FAILED', t['type'], {k: v for k, v in t.items() if k not in ('label', 'raw', 'type')})
            free(30)
            if not dead(): break
            print('  GAME OVER in quest', n, ': reloading', flush=True)
            if os.environ.get('TRACE'): run(['shot dead_q%d_%d' % (n, tries)])
            reload(); step([str(29 + 37 * tries)])                        # the emulator is deterministic, so a retry has to differ or it just repeats
        done = flag(QF + n)
        print('pass', attempt, 'quest', n, x.get('name'), 'done' if done else 'NOT DONE', [r[1] for r in res], 'area', area(), pos(), flush=True)
        if os.environ.get('NO_TOPUP'): print('   ', status(), flush=True)
        if done: ckpt(n); XP[0] = status()['xp']
        else: bad.append(x)
    todo = bad
    if not todo: break
bad = [x['quest'] for x in todo]
print('not done:', bad)
