"""M1: measure Legacy of Goku's data against Buu's Fury's engine limits. Reads extracted assets; writes out/ only.

    python3 tools/measure_log1.py <log1-decomp dir> <buusfury-decomp dir> <rom/log1.gba>

Limits checked: masks 256x256 tiles; 896 unique BG tiles per map (mapkit); character frames one 32x32 piece.
Corridor fit: share of walkable tiles a square body of N tiles can stand on, compared with Buu's Fury's own floors.
"""
import csv, glob, json, os, re, struct, sys, statistics as st, xml.etree.ElementTree as ET
from collections import Counter
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLIP = 0xC0000000
MAX_MASK, MAX_TILES = 256, 896


def fit(mask, n):
    """Tiles covered by some n x n all-walkable square, as a share of walkable tiles."""
    m = mask.astype(bool); tot = int(m.sum())
    if not tot: return None
    h, w = m.shape
    if h < n or w < n: return 0.0
    I = np.zeros((h + 1, w + 1), np.int64); I[1:, 1:] = m.cumsum(0).cumsum(1)
    ok = (I[n:, n:] - I[:-n, n:] - I[n:, :-n] + I[:-n, :-n]) == n * n
    cov = np.zeros((h + 1, w + 1), np.int64)
    ys, xs = np.nonzero(ok)
    np.add.at(cov, (ys, xs), 1); np.add.at(cov, (ys + n, xs), -1); np.add.at(cov, (ys, xs + n), -1); np.add.at(cov, (ys + n, xs + n), 1)
    return float(((cov.cumsum(0).cumsum(1)[:h, :w] > 0) & m).sum()) / tot


def area(path, jpath):
    root = ET.parse(path).getroot(); W, H = int(root.get('width')), int(root.get('height'))
    L = {}
    for l in root.findall('layer'):
        vals = [int(v) for v in re.split(r'[,\s]+', l.find('data').text.strip()) if v]
        L[l.get('name')] = np.array(vals, np.uint32).reshape(H, W)
    j = json.load(open(jpath)); blocks = j.get('screen_tiles') or []
    sx = W // 30; used = set()
    for name in ('bg1 (top)', 'bg2', 'bg3 (bottom)'):
        g = L[name]
        for y, x in zip(*np.nonzero(g)):
            slot = (int(g[y, x]) & 0x3FFFFFFF) - 1
            b = blocks[y // 20 * sx + x // 30] if slot >= 346 and blocks else 0
            used.add((b if slot >= 346 else 0, slot))
    walk, fly = L['walkable'] > 0, L['flyable'] > 0
    tr = Counter((t['kind'], t['mode']) for t in j['triggers'])
    return dict(area=j['area'], w=W, h=H, screens=W // 30 * (H // 20), tiles=len(used), blocks=len({b for b in blocks if b}),
                walk=int(walk.sum()), fly_only=int((fly & ~walk).sum()), fit2=fit(walk, 2), fit3=fit(walk, 3), fit4=fit(walk, 4),
                npcs=sum(a['kind'] != 2 for a in j['actors']), enemies=sum(a['kind'] == 2 for a in j['actors']),
                warps=sum(t['kind'] == 'warp' for t in j['triggers']), fly_triggers=sum(t['mode'] == 2 for t in j['triggers']),
                both_triggers=sum(t['mode'] == 3 for t in j['triggers']), kinds=dict(('%s/%s' % k, v) for k, v in tr.items()))


def sprites(rom, names):
    d = open(rom, 'rb').read(); u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    out = {}
    base = 0x5C0C80
    for i in range(84):
        o = (u32(base + 4 * i)) & 0x1FFFFFF; pal, tab = struct.unpack_from('<2I', d, o + 0x24)
        tab &= 0x1FFFFFF; mw = mh = n = big = 0; seen = set()
        for k in range(76):
            p = u32(tab + 4 * k)
            if not p or p in seen: continue
            seen.add(p); p &= 0x1FFFFFF
            w, h = struct.unpack_from('<HH', d, p + 4); mw, mh = max(mw, w), max(mh, h); n += 1; big += w > 32 or h > 32
        out[i] = dict(max_w=mw, max_h=mh, frames=n, over32=big)
    return out


def main():
    log1, bf, rom = sys.argv[1:4]
    rows = [area(p, p.replace('/maps/', '/areas/').replace('.tmx', '.json')) for p in sorted(glob.glob(log1 + '/assets/maps/area*.tmx'))]
    q = json.load(open(log1 + '/assets/story/quests.json'))['quests']
    tasks, acts = Counter(), Counter()
    for x in q:
        tasks.update(t['type'] for t in x['tasks']); acts.update(a['type'] for a in x['actions'])
    bf2, bf3, bf4 = [], [], []
    for p in glob.glob(bf + '/assets/maps/*/floor.png'):
        m = np.array(Image.open(p).convert('L')) > 127
        ys, xs = np.nonzero(m)
        if not len(ys) or m.sum() < 100: continue
        m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        for arr, n in ((bf2, 2), (bf3, 3), (bf4, 4)): arr.append(fit(m, n))
    spr = sprites(rom, None)
    res = dict(areas=rows, tasks=tasks, actions=acts, quests=len(q), sprites=spr,
               bf_fit=dict(n=len(bf2), median2=st.median(bf2), median3=st.median(bf3), median4=st.median(bf4)))
    os.makedirs(ROOT + '/out', exist_ok=True); json.dump(res, open(ROOT + '/out/log1_measure.json', 'w'), indent=1)
    print('area  tiles(WxH) scr  uniq blk flyonly fit2 fit3 fit4 npc enm wrp flyT')
    for r in rows:
        print('%3d %4dx%-4d %4d %5d %3d %6d %4.2f %4.2f %4.2f %3d %3d %3d %3d%s' % (r['area'], r['w'], r['h'], r['screens'], r['tiles'], r['blocks'], r['fly_only'],
              r['fit2'] or 0, r['fit3'] or 0, r['fit4'] or 0, r['npcs'], r['enemies'], r['warps'], r['fly_triggers'] + r['both_triggers'],
              ' OVER-MASK' if max(r['w'], r['h']) > MAX_MASK else ''))
    print('over mask:', [r['area'] for r in rows if max(r['w'], r['h']) > MAX_MASK])
    print('over %d tiles (as stored):' % MAX_TILES, [(r['area'], r['tiles']) for r in rows if r['tiles'] > MAX_TILES])
    print('BF floors', res['bf_fit'])
    print('LoG1 median fit', [round(st.median(r[k] for r in rows if r[k] is not None), 3) for k in ('fit2', 'fit3', 'fit4')])
    print('tasks', dict(tasks)); print('actions', dict(acts))
    print('sprite max', max(s['max_w'] for s in spr.values()), max(s['max_h'] for s in spr.values()), 'records over 32:', [i for i, s in spr.items() if s['over32']])


if __name__ == '__main__':
    main()
