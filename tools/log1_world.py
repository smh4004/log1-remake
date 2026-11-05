"""World map flying on Earth: Buu's Fury's Mode 7 map (0:50) with LoG1's Earth areas as landing spots.

While flying in an Earth area, L takes off to the map. Places open once visited (flag VISIT + area), so flying never skips the story.
Namek is a new floating billboard on the map, using Buu's Fury's unused airship slot for its name and landing: hold B under it to go there once you've been. Other World stays on foot. Uses Gero's worldmap.py, with landing scripts that do nothing for a place not yet visited.
"""
import json, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import types  # noqa: E402
_areas = types.ModuleType('areas'); _areas.BASE = 0x08000000                 # Gero's areas.py needs a generated palette file; worldmap.py only uses this much of it


def _entry_any(rom, world, area):
    t = struct.unpack_from('<I', rom, 0x8A58)[0] - 0x08000000
    for i in range(1000):
        e = t + 56 * i
        if rom[e] == world and rom[e + 1] == area: return e
    raise KeyError((world, area))


_areas.entry_any = _entry_any; sys.modules.setdefault('areas', _areas)
import scenes, worldmap  # noqa: E402

VISIT, UI = 800, 1534
NAMEK_AT = (3216, 420)                                              # open sea in the far north-east, away from every Buu's Fury place
NAMEK_RECT = (NAMEK_AT[0] - 40, NAMEK_AT[1] - 40, NAMEK_AT[0] + 56, NAMEK_AT[1] + 56)
MAP_RECORD = 0x2AD8BC                                                # 0:50's map: +0x24 billboard count, +0x28 records, +0x2C 8bpp graphic
PLACES = [(0, 'roshi', "Roshi's Island"), (2, 'east_district', "Goku's House"), (4, 'fukurou', 'Forest'), (5, 'sw_forest', 'Village'), (9, 'nataday', 'Crash Site'),
          (15, 'lookout', "Kami's Lookout"), (17, 'west_city', 'City'), (22, 'pilaf', 'Military Base'), (23, 'diablo', 'Battlegrounds'), (24, 'airship', 'Namek')]
RECTS = {'west_city': (1193, 1137, 1312, 1296), 'east_district': (2632, 1465, 2712, 1536), 'roshi': (2833, 1633, 2944, 1744), 'lookout': (593, 1025, 704, 1128), 'airship': NAMEK_RECT, 'diablo': (1505, 985, 1648, 1144),
         'pilaf': (2249, 1521, 2360, 1624), 'nataday': (2161, 857, 2232, 928), 'sw_forest': (825, 1761, 904, 1840), 'fukurou': (721, 809, 864, 944)}


# Banner names. LoG1 has no names of its own, so these are read off where each area sits in the story; rooms use the place they're in.
AREA_NAMES = {0: "Roshi's Island", 1: 'Kame House', 2: "Goku's House", 3: 'Snake Way', 4: 'Forest', 5: 'Village', 6: 'Village', 7: 'Village', 8: 'Village', 9: 'Crash Site', 10: "Kami's Lookout",
              11: 'Snake Way', 12: 'Other World', 13: "King Kai's Planet", 14: "King Kai's Planet", 15: "Kami's Lookout", 16: 'Wilderness', 17: 'City', 18: 'City', 19: 'City', 20: 'Capsule Corp', 21: 'City',
              22: 'Military Base', 23: 'Battlegrounds', 24: 'Namek', 25: 'Namek', 26: 'Namek', 27: 'Namek', 28: 'Namek', 30: 'Namek', 31: 'Namek', 32: 'Namek', 33: 'Namek', 34: 'Frieza Base', 35: 'Frieza Base',
              36: 'Frieza Base', 37: 'Frieza Base', 38: 'Frieza Base', 39: 'Frieza Base', 40: 'Namek', 41: 'Namek'}
for _k in range(42, 54): AREA_NAMES[_k] = 'Namekian Temple'
NAME_UI = {}
for _n in sorted(set(AREA_NAMES.values())): NAME_UI[_n] = UI + len(PLACES) + len(NAME_UI)
TITLE_START = 1                                                       # the title menu's first item


def area_name(n):
    """The banner's UI string for this area, or 0 for none (the story pictures)."""
    return NAME_UI.get(AREA_NAMES.get(n), 0)


def ui_text(path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('[ui:%d]\n= Press Start\n\n' % TITLE_START)
        for i, (_, _, name) in enumerate(PLACES): f.write('[ui:%d]\n= %s\n\n' % (UI + i, name))
        for name, i in NAME_UI.items(): f.write('[ui:%d]\n= %s\n\n' % (i, name))


def landing_code(dests):
    """Fade, load and hand back only when the place has been visited."""
    tail = scenes.assemble('call 121 30; call 47; call 51 0', {}) + b'\x11'; out = b''
    for d in dests:
        w, a, x, y = d['to']; body = scenes.assemble('call 120 30; call 119 %d %d 1 %d %d' % (w, a, x, y), {}) + tail
        out += worldmap.cond_code(d['when']) + b'\x13' + struct.pack('>h', 2 + len(body)) + body
    return out


def spots(log1, ids, arrival):
    """(area, map x, map y) for each place that exists in this build: the first warp into the area, or its quest warp."""
    out = {}
    for n, bf, name in PLACES:
        if n not in ids: continue
        for m in ids:
            for t in json.load(open('%s/assets/areas/area%02d.json' % (log1, m)))['triggers']:
                if t['kind'] == 'warp' and t['to_area'] == n and n not in out: out[n] = (t['to_x'], t['to_y'])
        if n not in out:
            q = json.load(open(log1 + '/assets/story/quests.json'))['quests']; w = [a for x in q for a in x['actions'] if a['type'] == 'warp' and a['area'] == n]
            aw = [a for x in q for a in x['actions'] if a['type'] == 'add_warp' and a['to_area'] == n]
            if w: out[n] = (w[0]['x'], w[0]['y'])
            elif aw: out[n] = (aw[0]['to_x'], aw[0]['to_y'])
    return out


def install(r, log1, ids, world, at=0xAE0000):
    assert r[at:at + 16] == b'\xff' * 16, 'world map data would overwrite something'
    pos = spots(log1, ids, None); cfg = dict(locations=[dict(key=bf, bf=bf, ui=UI + i, rect=RECTS[bf], dests=[dict(when='set:%d' % (VISIT + n), to=[world, n + 1, *pos[n]])]) for i, (n, bf, name) in enumerate(PLACES) if n in pos])
    path = os.path.join(ROOT, 'out', 'slice', 'world.json'); json.dump(cfg, open(path, 'w'))
    worldmap.landing_code = landing_code; e = _entry_any(r, 0, 50); r[e + 4] = 0              # Buu's Fury's map enemies would be out of place and far too strong
    res = worldmap.apply(r, path, at)
    add_namek(r, res[0], e)
    return res


def add_namek(r, at, e):
    """A 95th billboard with Namek's frame added to the map's graphic, stored uncompressed, and the airship exits moved under it."""
    from wfz import decompress_stream
    B = 0x08000000; m = MAP_RECORD; n, recs, gfx = struct.unpack_from('<III', r, m + 0x24); t, s = struct.unpack_from('<II', r, gfx - B)
    data = bytes(decompress_stream(r, gfx - B + 8, s)[0]) if t else bytes(r[gfx - B + 8:gfx - B + 8 + s]); tile = len(data) // 32
    def put(b):
        nonlocal at
        a = at; r[a:a + len(b)] = b; at = (a + len(b) + 3) & ~3; assert at <= 0xAFFF00; return B + a
    fr = namek_frame(); new = data + b''.join(fr[y:y + 8, x:x + 8].tobytes() for y in range(0, 32, 8) for x in range(0, 32, 8))
    x, y = NAMEK_AT; rec = bytes(r[recs - B:recs - B + 24 * n]) + struct.pack('<4IHHI', x, y, x + 32, y + 32, 0x2000, 0x8000, (0x138 << 16) | tile)   # the same flags as the Lookout, which floats
    struct.pack_into('<III', r, m + 0x24, n + 1, put(rec), put(struct.pack('<II', 0, len(new)) + new))
    xp = struct.unpack_from('<I', r, e + 0x10)[0] - B; L, N = worldmap.BF_PLACES['airship']
    for i in L + [N]:
        struct.pack_into('<I', r, xp + 8 * i, 0); o = struct.unpack_from('<I', r, xp + 8 * i + 4)[0] - B; struct.pack_into('<4H', r, o + 8, *NAMEK_RECT)
    for i in L: struct.pack_into('<I', r, struct.unpack_from('<I', r, xp + 8 * i + 4)[0] - B + 4, worldmap.ASCENDED)


def takeoff_lists(ids):
    """Scene lists: one take-off per Earth area, over its place on the map."""
    out = []
    for n, bf, _ in PLACES:
        if n not in ids: continue
        x0, y0, x1, y1 = RECTS[bf]; out += ['list fly_%d' % n, 'do call 120 20; call 118 0 50 0 %d %d; call 121 20' % ((x0 + x1) // 2, (y0 + y1) // 2), 'stop']
    return out


def namek_frame():
    """Namek as a 32x32 8bpp billboard, drawn from scratch: a shaded green planet with teal seas and a little cloud. Colours are indexes into the world map's OBJ palette."""
    import numpy as np
    ramp, sea, cloud, edge = [111, 216, 217, 227, 60], [71, 186, 252, 198], 120, 111
    out = np.zeros((32, 32), np.uint8); cx, cy, R = 15.5, 15.5, 14.5
    def land(x, y):                                                 # a few overlapping blobs for continents
        s = 0
        for bx, by, br in ((-.45, -.35, .42), (.35, -.5, .3), (.25, .2, .45), (-.35, .5, .33), (.75, .55, .22)): s = max(s, 1 - ((x - bx) ** 2 + (y - by) ** 2) / br ** 2)
        return s > 0
    for j in range(32):
        for i in range(32):
            x, y = (i - cx) / R, (j - cy) / R; d = x * x + y * y
            if d > 1: continue
            z = (1 - d) ** .5; light = max(0, -.5 * x - .6 * y + .62 * z); k = light + (.06 if (i + j) & 1 else -.06)
            c = ramp if land(x, y) else sea; v = c[min(len(c) - 1, int(k * len(c)))]
            if d > .86: v = edge if light < .25 else c[0]
            if abs(y + .1 + .12 * x) < .05 and -.8 < x < .2 and d < .8 and (i % 7) > 1: v = cloud
            out[j, i] = v
    return out


def art():
    """The 64-byte minimap marker tile for the hook."""
    import numpy as np
    m = np.zeros((8, 8), np.uint8)
    for y in range(8):
        for x in range(8):
            d = abs(x - 3.5) + abs(y - 3.5); m[y, x] = 249 if d < 2.2 else (77 if d < 3.3 else 0)
    return m.tobytes()


def markers():
    """(visited flag, minimap x, y) per place: the map's arrow sits at x = 152 + map x / 45, y = map y / 45 - 9, and is 16 wide where a marker is 8."""
    out = []
    for n, bf, _ in PLACES:
        x0, y0, x1, y1 = RECTS[bf]; out.append((VISIT + n, int(156 + (x0 + x1) / 2 * .02227), int((y0 + y1) / 2 * .022 - 5) & 255))
    return out
