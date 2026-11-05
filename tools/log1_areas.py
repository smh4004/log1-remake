"""M4: add LoG1 areas to Buu's Fury as new table entries (world 26, area = LoG1 area + 1).

Each area gets its converted map, warp doors from LoG1's trigger zones, and NPCs whose sprite set has a Buu's Fury character.
Other NPCs are listed in the return value, not guessed. Talk lists come from `talk`, keyed by conversation set.
"""
import json, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import map_convert as C  # noqa: E402

BB, WORLD = 0x08000000, 26
AREAS, COUNT, TABLE_LIT, COUNT_INSN = 0x8E2E0, 452, 0x8A58, 0x125E0     # same values as Gero's tools/areas.py
# first-listed scouter ID is used until forms are confirmed
import log1_split, log1_world  # noqa: E402
BF_IDX = dict(roshi=186, bulma=41, krillin1=166, krillin2=166, goku=115, chichi=66, piccolo=222, yamcha=302, tien=264, chaitzu=65, kingkai=161, kingyema=163, popo=193, korrin=165, puar=233, dende=77, bubbles=40, gregory=135)


def door_dir(a, rect):
    """The key that walks through a zone. A zone at the map's edge leaves over that edge, across its short side. Elsewhere the player
    comes in from the open side, so the key points away from it."""
    w = a.L['walkable'] > 0; x0, y0, x1, y1 = rect; W, H = a.W * 8, a.H * 8; horiz = x1 - x0 <= y1 - y0
    edges = dict(left=x0 <= 8, right=x1 >= W - 8, up=y0 <= 8, down=y1 >= H - 8)
    for k in (('left', 'right', 'up', 'down') if horiz else ('up', 'down', 'left', 'right')):
        if edges[k]: return k
    tx0, ty0, tx1, ty1 = x0 // 8, y0 // 8, (x1 - 1) // 8, (y1 - 1) // 8
    def side(ys, xs):
        v = w[max(ys[0], 0):min(ys[1], a.H), max(xs[0], 0):min(xs[1], a.W)]; return v.mean() if v.size else 0
    came = dict(up=side((ty1 + 1, ty1 + 3), (tx0, tx1 + 1)), down=side((ty0 - 2, ty0), (tx0, tx1 + 1)), left=side((ty0, ty1 + 1), (tx1 + 1, tx1 + 3)), right=side((ty0, ty1 + 1), (tx0 - 2, tx0)))
    if max(x1 - x0, y1 - y0) >= 1.5 * min(x1 - x0, y1 - y0):      # a long zone is crossed through its short side
        for k in (('left', 'right') if horiz else ('up', 'down')): came[k] += 1
    return max(came, key=came.get)


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


def build(r, log1, ids, story, named, actors):
    picks = []; foes_out = []; follows = []; walkins = []
    """Add areas `ids` from the story plan. Returns (table offset, hook spawn rows, hook walk rows, skipped characters)."""
    tmpl = next(bytes(r[e:e + 56]) for e in range(AREAS, AREAS + 56 * COUNT, 56) if r[e] == 1 and r[e + 1] == 1)
    cache = {}; entries = []; skipped = []; idset = set(ids); moved = []; addr = {}; spawns = []; D = {'down': 0, 'up': 1, 'left': 2, 'right': 3}
    def put(b):
        while len(r) % 4: r.append(0)
        o = len(r); r.extend(b); return BB + o
    def get(n): return cache.setdefault(n, C.Area(log1, n)) if n not in cache else cache[n]
    NEW_BASE = 56 * COUNT
    for k, n in enumerate(ids): addr[n] = k
    for n in ids:
        a = get(n); m, st = C.convert(r, a, 'recolour', []); an, dur = C.anim_tiles(r, a); C.reduce_tiles(r, m, 860, [b for b, _ in an])
        P = m.write(r, C.TEMPLATE); C.add_anim(r, P, an, dur); exits = []
        for t in a.info['triggers']:
            if t['kind'] == 'warp' and t['to_area'] in idset and t['mode'] & 1 and t['to_area'] != n and not (n >= 42 and t['to_area'] >= 42):
                name = door_dir(a, t['rect']); key = D[name]; dest = key | (WORLD << 8) | ((t['to_area'] + 1) << 16) | (1 << 24)
                land = arrival(get(t['to_area']), t['to_x'], t['to_y'], name); assert land, 'no clear arrival in area %d' % t['to_area']; moved.append((n, t['to_area'], land[2]))
                x0, y0, x1, y1 = [max(0, v) for v in t['rect']]; exits.append(struct.pack('<II', 0, put(struct.pack('<IIHHHHII', 0x08007675, 0x0800776D, x0, y0, x1, y1, dest, (land[1] << 16) | land[0]))))
        zones_first = []                                     # a quest zone on a door's rectangle has to run before the door takes the player away
        for d in story.doors.get(n, []):
            x0, y0, x1, y1 = [max(0, v) for v in d['rect']]
            if d['list'].startswith(('pk', 'pick_', 'trg', 'obst_', 'place_')): walkins.append((n, x0, y0, x1, y1, named[d['list']])); continue    # quest zones stay real exits, which run before a door on the same spot
            zones_first.append(struct.pack('<II', 0, put(struct.pack('<IIHHHHI', 0x0800742D, 0x080077DF, x0, y0, x1, y1, named[d['list']]))))
        exits = zones_first + exits
        recs = bytearray(); offs = []; enemy_objs = []
        flags = story.qof
        # BF's object list takes 27 area objects (it ends before the table at 0x03001CC8), so enemies and pickups stream in (src/flight.c).
        foe_i = 0
        for s in a.info['actors']:
            cond = 0x20002
            if s['show'] == 1: cond = 0x20000 | (story.QF + flags[s['flag']])
            elif s['show'] == 2: cond = 0x10000 | (story.QF + flags[s['flag']])
            sid = story.names.index(s['sprite'])
            if s['kind'] == 2 and (n, sid) in {(k[0], v[1]) for k, v in story.forms.items()}: continue   # this form arrives when the one before it falls (Vegeta)
            if s['kind'] == 2:
                d_ = story.death_script(n, sid, put); row = actors.row(s['sprite'], d_ or 0, story.boss_gives_exp(n, sid), None, n, False); ch = actors.actor(s['sprite'], True)   # story enemies like the robbers fight as normal enemies
                beat_ = story.beaten_flag(n, sid); foes_out.append((n, foe_i, s['x'], s['y'], put(struct.pack('<8I', 0x0800FD55, (0x20000 | beat_) if beat_ else 0 if s['show'] == 0 else cond, row, (s['y'] << 16) | s['x'], ch, 0x080555A0, 1, 0x080716EC)))); foe_i += 1; assert foe_i <= 64; continue
            idx = BF_IDX.get(s['sprite']) or actors.actor(s['sprite'], False)
            talk = named.get('talk_set%02d' % s['param'], 0); offs.append(len(recs))
            recs += struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, cond, (s['y'] << 16) | s['x'], talk, idx, 1, 0)
            if (n, sid) in story.hostile:
                def boss(sprite_id, flag, remove):
                    nm = story.names[sprite_id]; d_ = story.death_script(n, sprite_id, put); row = actors.row(nm, d_ or 0, story.boss_gives_exp(n, sprite_id), None, n, True)
                    spawns.append((flag, n, put(struct.pack('<8I', 0x0800FD55, 0, row, (s['y'] << 16) | s['x'], actors.actor(nm, True), 0x080555A0, 1, 0x080716EC)), remove, story.beaten_flag(n, sprite_id)))
                boss(sid, story.hostile[(n, sid)], idx); cur = sid
                while (n, cur) in story.forms: f_, nxt = story.forms[(n, cur)]; boss(nxt, f_, 0); cur = nxt      # the next form takes over
        import worldmap_cond
        foe_i = story.side.install(n, a, fits, r, actors, put, named, spawns, foes_out, follows, walkins, foe_i, BF_IDX, worldmap_cond.cond_code)
        if n == 17:                                          # Officer Pudding stands in the City from the start
            offs.append(len(recs)); recs += bytes(r[story.side.board_rec - 8 - BB:story.side.board_rec - 8 - BB + 36])
        # story characters: waiting until they join the player, then at the escort's end with their after-talk
        for x in story.q:
            for t in x['tasks']:
                if t['type'] == 'spawn_character' and t['area'] == n:
                    idx = BF_IDX.get(story.names[t['sprite']]) or actors.actor(story.names[t['sprite']], False); f = story.TF + t['id']
                    offs.append(len(recs)); recs += struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20000 | f, (t['y'] << 16) | t['x'], named.get('talk_set%02d' % t['set'], 0), idx, 1, 0)
                    spawns.append((f, n, 0, idx, 0))
                    end = next((u for y_ in story.q for u in y_['tasks'] if u['type'] == 'escort' and u['follower'] == t['sprite']), None)
                    if end:
                        rec_ = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, 0, named['no_talk'], idx, 1, 0)); struct.pack_into('<I', r, rec_ - BB + 32, rec_); follows.append((f, story.TF + end['id'], rec_ + 8))
                elif t['type'] == 'escort' and t['area'] == n:
                    sp = story.names[t['follower']]; idx = BF_IDX.get(sp) or actors.actor(sp, False)
                    offs.append(len(recs)); recs += struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x10000 | (story.TF + t['id']), (t['y'] << 16) | t['x'], named.get('talk_set%02d' % t['after_set'], 0), idx, 1, 0)
        # pickups stream in (src/flight.c): an object 8 px below LoG1's spot, as its frame is bottom-centred
        def item(i, x, y, f):
            rec = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, ((y + 8) << 16) | x, named['no_talk'], actors.pickup(i), 1, 0)); struct.pack_into('<I', r, rec - BB + 32, rec); picks.append((n, f, x, y + 8, rec + 8))
        for p in story.pickups.get(n, []): item(p['id'], p['x'], p['y'], p['flag'])
        for i_, f_, x_, y_ in story.placed.get(n, []): item(i_, x_, y_, f_ | 0x8000)      # a stone or sapling once placed
        for x_ in story.q:
            for t in x_['tasks']:
                if t['type'] == 'spawn_item' and t['area'] == n: item(t['item'], t['x'], t['y'], story.TF + t['id'])
        objs = []
        if recs:
            blk = put(bytes(recs))
            for off in offs: struct.pack_into('<I', r, blk - BB + off + 32, blk + off); objs.append(blk + off + 8)
        objs += enemy_objs
        e = bytearray(tmpl); e[0], e[1], e[2], e[3] = WORLD, n + 1, 1, len(exits); struct.pack_into('<I', e, 4, len(objs))
        struct.pack_into('<I', e, 0x10, put(b''.join(exits)) if exits else 0); struct.pack_into('<I', e, 0x14, put(b''.join(struct.pack('<I', o) for o in objs)) if objs else 0)
        struct.pack_into('<I', e, 0x24, 255 if n >= log1_split.PIC_FIRST else 53 + a.info['music'])   # log1_music; story pictures keep the song that's playing
        struct.pack_into('<I', e, 0x0C, log1_world.area_name(n))
        struct.pack_into('<I', e, 0x2C, put(struct.pack('<I', P))); entries.append(bytes(e))
    cnt = COUNT + len(entries); tab = put(bytes(r[AREAS:AREAS + 56 * COUNT]) + b''.join(entries))
    struct.pack_into('<I', r, TABLE_LIT, tab); a_ = min(0xFF, cnt // 2)
    struct.pack_into('<4H', r, COUNT_INSN, 0x2000 | a_, 0x0040, 0x3000 | (cnt - 2 * a_), 0x4770)
    ent = lambda n: tab + 56 * (COUNT + addr[n])
    return tab, [(f, ent(n), rec, idx, u) for f, n, rec, idx, u in spawns], [(f, ent(n), x1, y1, x2, y2) for f, n, x1, y1, x2, y2 in story.walks if n in idset], [(ent(n), f, x, y, rec) for n, f, x, y, rec in picks], [(ent(n), f, x, y, rec) for n, f, x, y, rec in foes_out], [(ent(n), max(0, x0), max(0, y0), max(0, x1), max(0, y1), d, m) for n, (x0, y0, x1, y1), d, m in story.zones if n in idset], skipped, moved, named['quest_check'], follows, [(ent(n), x0, y0, x1, y1, l) for n, x0, y0, x1, y1, l in walkins]
