"""Checks a walking player can reach every side character and foe: python3 tools/side_reach.py <deps>. Walks the real collision map from the area's doors."""
import collections, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_split, log1_areas, log1_side as Z
import map_convert as C
L = log1_split.build(os.path.join(sys.argv[1], 'log1-decomp')); cache = {}
def area(n): return cache.setdefault(n, C.Area(L, n)) if n not in cache else cache[n]
def spot(a, x, y):
    for d in range(0, 200, 4):
        for ox in range(-d, d + 1, 4):
            for oy in range(-d, d + 1, 4):
                if max(abs(ox), abs(oy)) == d and log1_areas.fits(a, x + ox, y + oy): return x + ox, y + oy
targets = collections.defaultdict(list)
for d in (Z.BUTLER, Z.COACH, Z.ELDER, Z.ANNOUNCER): targets[d['area']].append(('npc', d['at']))
for at in Z.COACH['foes']: targets[Z.COACH['area']].append(('foe', at))
for e in Z.ELITES: targets[e['area']].append(('elite', e['at']))
for m in Z.REMATCHES: targets[Z.ANNOUNCER['area']].append((m['name'], m['at']))
for b in Z.BOUNTIES: targets[b['area']].append((b['name'], b['at']))
for at, _ in Z.SLIPPERS: targets[Z.BUTLER['area']].append(('slipper', at))
for n, want in sorted(targets.items()):
    a = area(n); starts = []
    for m in range(54):
        try: tr = area(m).info['triggers']
        except Exception: continue
        for t in tr:
            if t['kind'] == 'warp' and t['to_area'] == n: starts.append(spot(a, t['to_x'], t['to_y']))
    if not starts: print(n, 'no doors lead here; flying only'); starts = []
    seen = set(s for s in starts if s); q = collections.deque(seen)
    while q:
        x, y = q.popleft()
        for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4)):
            p = (x + dx, y + dy)
            if p not in seen and log1_areas.fits(a, *p): seen.add(p); q.append(p)
    for name, at in want:
        s = spot(a, *at); near = s and any(abs(p[0] - s[0]) <= 24 and abs(p[1] - s[1]) <= 24 for p in seen)
        print(n, name, at, '->', s, 'reachable' if near else 'NOT REACHABLE', flush=True)
