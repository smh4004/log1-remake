"""Check every LoG1 warp with Buu's Fury's 16x8 collision box. Reports zones the body can't reach from each arrival point.

    python3 tools/reach_log1.py <log1-decomp>
"""
import collections, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import map_convert as C  # noqa: E402
L = sys.argv[1]; A = {n: C.Area(L, n) for n in range(42)}; arr = collections.defaultdict(set)
for a in A.values():
    arr[a.n].add(tuple(a.info['start']))
    for t in a.info['triggers']:
        if t['kind'] == 'warp' and t['to_area'] < 42: arr[t['to_area']].add((t['to_x'], t['to_y']))


def flood(a, s, walk):
    def fits(x, y):
        if x < 0 or y < 0: return False
        x1, y1 = (x + 23) >> 3, (y + 15) >> 3
        return y1 <= a.H and x1 <= a.W and walk[y >> 3:y1, x >> 3:x1].all()
    if not fits(*s): return None
    seen = {s}; q = collections.deque([s])
    while q:
        x, y = q.popleft()
        for t in ((x + 4, y), (x - 4, y), (x, y + 4), (x, y - 4)):
            if t not in seen and fits(*t): seen.add(t); q.append(t)
    return seen


res = dict(arrivals=0, arrivals_blocked=[], warps=0, warps_unreached=[]); per = {}
for n, a in A.items():
    walk = a.L['walkable'] > 0; reach = set()
    for s in arr[n]:
        res['arrivals'] += 1; f = flood(a, s, walk)
        if f is None: res['arrivals_blocked'].append((n, s))
        else: reach |= f
    for t in a.info['triggers']:
        if t['kind'] != 'warp' or t['mode'] == 2: continue
        res['warps'] += 1; x0, y0, x1, y1 = t['rect']
        if not any(x0 - 16 < x < x1 and y0 - 8 < y < y1 for x, y in reach): res['warps_unreached'].append((n, t['rect'], t['to_area']))
    per[n] = len(reach)
print('arrivals', res['arrivals'], 'blocked', len(res['arrivals_blocked']), res['arrivals_blocked'][:14])
print('walk-mode warps', res['warps'], 'unreached', len(res['warps_unreached']), res['warps_unreached'][:24])
json.dump(res, open(os.path.join(ROOT, 'out', 'reach.json'), 'w'), indent=1)
