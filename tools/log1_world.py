"""World map flying on Earth: Buu's Fury's Mode 7 map (0:50) with LoG1's Earth areas as landing spots.

While flying in an Earth area, L takes off to the map. Places open once visited (flag VISIT + area), so flying never skips the story.
The map's floating Lookout is reskinned as Namek: hold B under it to go there once you've been. Other World stays on foot. Uses Gero's worldmap.py, with landing scripts that do nothing for a place not yet visited.
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
PLACES = [(0, 'roshi', "Roshi's Island"), (2, 'east_district', "Goku's House"), (4, 'fukurou', 'Forest'), (5, 'sw_forest', 'Village'), (9, 'nataday', 'Crash Site'),
          (15, 'papaya', "Kami's Lookout"), (17, 'west_city', 'City'), (22, 'pilaf', 'Military Base'), (23, 'diablo', 'Battlegrounds'), (24, 'lookout', 'Namek')]
RECTS = {'west_city': (1193, 1137, 1312, 1296), 'east_district': (2632, 1465, 2712, 1536), 'roshi': (2833, 1633, 2944, 1744), 'lookout': (593, 1025, 704, 1128), 'papaya': (1953, 2041, 2096, 2200), 'diablo': (1505, 985, 1648, 1144),
         'pilaf': (2249, 1521, 2360, 1624), 'nataday': (2161, 857, 2232, 928), 'sw_forest': (825, 1761, 904, 1840), 'fukurou': (721, 809, 864, 944)}


def ui_text(path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (_, _, name) in enumerate(PLACES): f.write('[ui:%d]\n= %s\n\n' % (UI + i, name))


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
    return worldmap.apply(r, path, at)


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
    """Bytes for the hook: Namek's 1024-byte frame, then the 64-byte minimap marker tile."""
    import numpy as np
    fr = namek_frame(); f = b''.join(fr[y:y + 8, x:x + 8].tobytes() for y in range(0, 32, 8) for x in range(0, 32, 8)); m = np.zeros((8, 8), np.uint8)   # OBJ tiles, 8x8 at a time
    for y in range(8):
        for x in range(8):
            d = abs(x - 3.5) + abs(y - 3.5); m[y, x] = 249 if d < 2.2 else (77 if d < 3.3 else 0)
    return f + m.tobytes()


def markers():
    """(visited flag, minimap x, y) per place: the map's arrow sits at x = 152 + map x / 45, y = map y / 45 - 9, and is 16 wide where a marker is 8."""
    out = []
    for n, bf, _ in PLACES:
        x0, y0, x1, y1 = RECTS[bf]; out.append((VISIT + n, int(156 + (x0 + x1) / 2 * .02227), int((y0 + y1) / 2 * .022 - 5) & 255))
    return out
