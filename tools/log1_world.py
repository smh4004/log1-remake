"""World map flying on Earth: Buu's Fury's Mode 7 map (0:50) with LoG1's Earth areas as landing spots.

While flying in an Earth area, L takes off to the map. Places open once visited (flag VISIT + area), so flying never skips the story.
Namek and Other World stay on foot. Uses Gero's worldmap.py, with landing scripts that do nothing for a place not yet visited.
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
          (15, 'lookout', "Kami's Lookout"), (17, 'west_city', 'City'), (22, 'pilaf', 'Military Base'), (23, 'diablo', 'Battlegrounds')]
RECTS = {'west_city': (1193, 1137, 1312, 1296), 'east_district': (2632, 1465, 2712, 1536), 'roshi': (2833, 1633, 2944, 1744), 'lookout': (593, 1025, 704, 1128), 'diablo': (1505, 985, 1648, 1144),
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
    worldmap.landing_code = landing_code
    return worldmap.apply(r, path, at)


def takeoff_lists(ids):
    """Scene lists: one take-off per Earth area, over its place on the map."""
    out = []
    for n, bf, _ in PLACES:
        if n not in ids: continue
        x0, y0, x1, y1 = RECTS[bf]; out += ['list fly_%d' % n, 'do call 120 20; call 118 0 50 0 %d %d; call 121 20' % ((x0 + x1) // 2, (y0 + y1) // 2), 'stop']
    return out
