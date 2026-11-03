"""Recolour every LoG1 area and report whether it fits Buu's Fury. Writes out/maps/all.json only.

    python3 tools/convert_all.py <log1-decomp>
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import map_convert as C, mapkit  # noqa: E402

rom = bytearray(open(os.path.join(C.ROOT, 'rom', 'bf.gba'), 'rb').read()); res = []
for n in range(42):
    a = C.Area(sys.argv[1], n); m, st = C.convert(rom, a, 'recolour', [])
    row = dict(area=n, w=a.W, h=a.H, tiles=st['tiles'], over=st['tiles'] > C.LIMIT, anim=a.info.get('tile_anim'), blocks=len({b for b in a.info.get('screen_tiles', []) if b}))
    if not row['over']:
        r = bytearray(rom); before = len(r); m.write(r, C.TEMPLATE); row['bytes'] = len(r) - before
    res.append(row); print(n, row['w'], row['h'], row['tiles'], 'OVER' if row['over'] else row.get('bytes'), row['blocks'], flush=True)
json.dump(res, open(os.path.join(C.ROOT, 'out', 'maps', 'all.json'), 'w'), indent=1)
print('over:', [(r['area'], r['tiles'], r['blocks']) for r in res if r['over']], 'total MB', sum(r.get('bytes', 0) for r in res) / 1e6, 'animated', sum(1 for r in res if r['anim'] and r['anim'].get('count')))
