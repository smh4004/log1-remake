"""M4: add LoG1 areas to Buu's Fury as new table entries (world 26, area = LoG1 area + 1).

Each area gets its converted map, warp doors from LoG1's trigger zones, and NPCs whose sprite set has a Buu's Fury character.
Other NPCs are listed in the return value, not guessed. Talk lists come from `talk`, keyed by conversation set.
"""
import json, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_talk, map_convert as C  # noqa: E402

BB, WORLD = 0x08000000, 26
AREAS, COUNT, TABLE_LIT, COUNT_INSN = 0x8E2E0, 452, 0x8A58, 0x125E0     # same values as Gero's tools/areas.py
# first-listed scouter ID is used until forms are confirmed
BF_IDX = dict(roshi=186, bulma=41, krillin1=166, krillin2=166, gohan1=107, gohan2=107, gohan3=107, goku=115, chichi=66, piccolo=222, yamcha=302, tien=264, chaitzu=65, kingkai=161, kingyema=163, popo=193, korrin=165, puar=233, dende=77, bubbles=40, gregory=135)


def door_dir(a, rect):
    """The way the player walks into a zone: towards the edge of the zone that is most walled off."""
    w = a.L['walkable'] > 0; x0, y0, x1, y1 = rect
    tx0, ty0 = max(x0 // 8, 0), max(y0 // 8, 0); tx1, ty1 = min((x1 - 1) // 8, a.W - 1), min((y1 - 1) // 8, a.H - 1)
    open_ = dict(up=w[ty0, tx0:tx1 + 1].mean(), down=w[ty1, tx0:tx1 + 1].mean(), left=w[ty0:ty1 + 1, tx0].mean(), right=w[ty0:ty1 + 1, tx1].mean())
    return min(open_, key=open_.get)


def fits(a, x, y, bw=16, bh=8):
    """Buu's Fury's collision rule (sub_08009324) with the player's live 16x8 box."""
    if x < 0 or y < 0: return False
    x1, y1 = (x + bw + 7) >> 3, (y + bh + 7) >> 3
    return y1 <= a.H and x1 <= a.W and bool((a.L['walkable'][y >> 3:y1, x >> 3:x1] > 0).all())


def arrival(a, x, y, key):
    """BF walks the player about 14 px in the door's direction on arrival. Returns the point to load at, so the walk ends
    on LoG1's spot or the nearest clear point, and every pixel of the walk is clear. Returns (x, y, moved distance)."""
    dx, dy = dict(up=(0, -1), down=(0, 1), left=(-1, 0), right=(1, 0))[key]
    best = None
    for r_ in range(0, 65, 4):
        for ox in range(-r_, r_ + 1, 4):
            for oy in range(-r_, r_ + 1, 4):
                if max(abs(ox), abs(oy)) != r_: continue
                ex, ey = x + ox, y + oy
                if all(fits(a, ex - dx * k, ey - dy * k) for k in range(0, 21, 2)): best = (ex - dx * 14, ey - dy * 14, r_); break
            if best: break
        if best: break
    return best


def build(r, log1, ids, talk=None, named=None):
    """r: ROM bytearray, at least 16 MB. ids: LoG1 areas to add. Returns (start of new table, skipped NPC list)."""
    cache = {}; moved = []; entries = []; skipped = []; tmpl = next(bytes(r[e:e + 56]) for e in range(AREAS, AREAS + 56 * COUNT, 56) if r[e] == 1 and r[e + 1] == 1); idset = set(ids)
    def put(b):
        while len(r) % 4: r.append(0)
        o = len(r); r.extend(b); return BB + o
    for n in ids:
        a = C.Area(log1, n); m, st = C.convert(r, a, 'recolour', []); an, dur = C.anim_tiles(r, a); C.reduce_tiles(r, m, 860, [b for b, _ in an])
        P = m.write(r, C.TEMPLATE); C.add_anim(r, P, an, dur)
        exits = []
        for t in a.info['triggers']:
            if t['kind'] == 'warp' and t['to_area'] in idset and t['mode'] & 1:
                x0, y0, x1, y1 = t['rect']; D = {'down': 0, 'up': 1, 'left': 2, 'right': 3}; name = door_dir(a, t['rect']); key = D[name]
                dest = key | (WORLD << 8) | ((t['to_area'] + 1) << 16) | (1 << 24)
                ta = cache.setdefault(t['to_area'], C.Area(log1, t['to_area'])) if t['to_area'] not in cache else cache[t['to_area']]
                land = arrival(ta, t['to_x'], t['to_y'], name); assert land, 'no clear arrival in area %d' % t['to_area']
                moved.append((n, t['to_area'], land[2]))
                exits.append(struct.pack('<II', 0, put(struct.pack('<IIHHHHII', 0x08007675, 0x0800776D, x0, y0, x1, y1, dest, (land[1] << 16) | land[0]))))
        for q, (fa, fx, fy) in log1_talk.FIND.items():            # pickups: LoG1 collects them by walking over them
            if fa != n or not named: continue
            exits.append(struct.pack('<II', 0, put(struct.pack('<IIHHHHI', 0x0800742D, 0x080077DF, fx - 8, fy - 8, fx + 16, fy + 16, named['find_q%d' % q]))))
        recs = bytearray(); offs = []
        for s in a.info['actors']:
            if s['kind'] == 2 or s['show'] != 0 or s['sprite'] not in BF_IDX: skipped.append((n, s['sprite'], s['kind'], s['show'])); continue
            offs.append(len(recs)); recs += struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x00020002, (s['y'] << 16) | s['x'], (talk or {}).get(s['param'], 0), BF_IDX[s['sprite']], 1, 0)
        objs = []
        if recs:
            blk = put(bytes(recs))
            for off in offs: struct.pack_into('<I', r, blk - BB + off + 32, blk + off); objs.append(blk + off + 8)
        e = bytearray(tmpl); e[0], e[1], e[2], e[3] = WORLD, n + 1, 1, len(exits); struct.pack_into('<I', e, 4, len(objs))
        struct.pack_into('<I', e, 0x10, put(b''.join(exits)) if exits else 0); struct.pack_into('<I', e, 0x14, put(b''.join(struct.pack('<I', o) for o in objs)) if objs else 0)
        struct.pack_into('<I', e, 0x2C, put(struct.pack('<I', P)))
        entries.append(bytes(e))
    cnt = COUNT + len(entries); tab = put(bytes(r[AREAS:AREAS + 56 * COUNT]) + b''.join(entries))
    struct.pack_into('<I', r, TABLE_LIT, tab); a_ = min(0xFF, cnt // 2)
    struct.pack_into('<4H', r, COUNT_INSN, 0x2000 | a_, 0x0040, 0x3000 | (cnt - 2 * a_), 0x4770)
    print('arrivals (from, to, px moved)', moved)
    return tab, skipped
