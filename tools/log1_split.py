"""Split LoG1's Namekian Temple (area 29) into its 12 walled sections, which connect only through warp squares.

At 240x240 tiles it needs 120 map chunks across its layers, about 240 KB once loaded, while Buu's Fury's largest maps use 60 and the game hangs loading it. Each section
becomes a smaller area of its own, cropped on a chunk boundary, with every coordinate shifted to match. This writes a copy of the
exported data to out/converted/log1data, with symlinks to the unchanged files, so everything else reads it as plain LoG1 data with areas 42-53 in place of 29.
"""
import json, os, re, shutil, struct, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as ni
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA, FIRST, PAD = 29, 42, (15, 10)
ALL = [n for n in range(42) if n != AREA]


PIC_FIRST, PICS, PIC_TABLE = 54, 15, 0x5C2198                          # LoG1's full-screen story pictures, each added as a one-screen area


def ids(): return ALL + [FIRST + k for k in range(12)] + [PIC_FIRST + k for k in range(PICS)]


def add_pictures(L, out):
    """Each story picture becomes a 30x20 area with its own tiles, so Buu's Fury's dialogue draws over it as usual. Built from your ROM at build time."""
    log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); B = ET.parse('%s/assets/maps/area07.tmx' % L); info = json.load(open('%s/assets/areas/area07.json' % L))
    for k in range(PICS):
        data = struct.unpack_from('<I', log1, PIC_TABLE + 12 * k + 4)[0]; im = Image.open('%s/assets/gfx/blocks/gUnknown_%08X.png' % (L, data)); assert im.mode == 'P' and im.size == (240, 160)
        px = np.array(im, np.uint8); sheet = np.zeros((38 * 8, 128), np.uint8)
        for i in range(600):
            y, x = i // 30, i % 30; sheet[i // 16 * 8:i // 16 * 8 + 8, i % 16 * 8:i % 16 * 8 + 8] = px[y * 8:y * 8 + 8, x * 8:x * 8 + 8]
        n = PIC_FIRST + k; s = Image.fromarray(sheet, 'P'); s.putpalette(im.getpalette()); s.save('%s/assets/maps/tiles/area%02d.png' % (out, n))
        r2 = ET.fromstring(ET.tostring(B.getroot()))
        for l in r2.findall('layer'):
            nm = l.get('name'); v = [i + 1 for i in range(600)] if nm.startswith('bg3') else [1024] * 600 if nm in ('walkable', 'flyable', 'shots') else [0] * 600
            l.find('data').text = ','.join(map(str, v))
        for ts in r2.findall('tileset'):
            for im_ in ts.findall('image'):
                if 'area07' in im_.get('source'): im_.set('source', 'tiles/area%02d.png' % n); im_.set('height', str(38 * 8))
            if ts.get('name') == 'area07': ts.set('name', 'area%02d' % n); ts.set('tilecount', '608')
        for p in r2.iter('property'):
            if p.get('name') == 'area': p.set('value', str(n))
        ET.ElementTree(r2).write('%s/assets/maps/area%02d.tmx' % (out, n))
        json.dump(dict(info, area=n, actors=[], pickups=[], objects=[], triggers=[], start=[8, 8], tile_anim=None), open('%s/assets/areas/area%02d.json' % (out, n), 'w'))


def build(L):
    out = os.path.join(ROOT, 'out', 'converted', 'log1data'); stamp = os.path.join(out, '.done')
    if os.path.exists(stamp): return out
    shutil.rmtree(out, ignore_errors=True); os.makedirs(os.path.join(out, 'assets', 'maps', 'tiles')); os.makedirs(os.path.join(out, 'assets', 'areas')); os.makedirs(os.path.join(out, 'assets', 'story'))
    for d in os.listdir(L + '/assets'):
        if d not in ('maps', 'areas', 'story'): os.symlink(os.path.abspath(L + '/assets/' + d), out + '/assets/' + d)
    for f in os.listdir(L + '/assets/maps/tiles'): os.symlink(os.path.abspath(L + '/assets/maps/tiles/' + f), out + '/assets/maps/tiles/' + f)
    for f in os.listdir(L + '/assets/maps'):
        if f != 'tiles': os.symlink(os.path.abspath(L + '/assets/maps/' + f), out + '/assets/maps/' + f)
    for f in os.listdir(L + '/assets/areas'):
        if not re.match(r'area\d\d\.json', f): os.symlink(os.path.abspath(L + '/assets/areas/' + f), out + '/assets/areas/' + f)
    tree = ET.parse('%s/assets/maps/area%02d.tmx' % (L, AREA)); root = tree.getroot(); W, H = int(root.get('width')), int(root.get('height'))
    layers = {l.get('name'): np.array([int(x) for x in re.split(r'[,\s]+', l.find('data').text.strip()) if x], np.uint32).reshape(H, W) for l in root.findall('layer')}
    walk = layers['walkable'] > 0; lab, n = ni.label(walk); sizes = ni.sum(walk, lab, range(1, n + 1)); big = [i + 1 for i, s in enumerate(sizes) if s > 40]; assert len(big) == 12, big
    keep = np.isin(lab, big) * lab; idx = ni.distance_transform_edt(keep == 0, return_distances=False, return_indices=True); near = keep[idx[0], idx[1]]; sec = {c: FIRST + k for k, c in enumerate(big)}
    def section(x, y):
        return sec[int(near[min((max(y, 0) + 4) >> 3, H - 1), min((max(x, 0) + 8) >> 3, W - 1)])]
    # each section is cropped to its own smaller map, as a map that big with empty chunks still fails to load; origin is in tiles, on a chunk boundary
    box = {}
    for k, c in sec.items():
        m = lab == k; grow = ni.binary_dilation(m, np.ones((PAD[1] * 2 + 1, PAD[0] * 2 + 1), bool)); ys, xs = np.where(grow); ox, oy = int(xs.min()) // 32 * 32, int(ys.min()) // 32 * 32
        box[c] = dict(m=m, grow=grow, ox=ox, oy=oy, w=int(xs.max()) + 1 - ox, h=int(ys.max()) + 1 - oy)
    def shift(c, x, y): return x - box[c]['ox'] * 8, y - box[c]['oy'] * 8
    info = json.load(open('%s/assets/areas/area%02d.json' % (L, AREA))); data = {c: dict(info, actors=[], pickups=[], triggers=[], origin=[box[c]['ox'], box[c]['oy'], W]) for c in sec.values()}
    for a in info['actors']:
        c = section(a['x'], a['y']); x, y = shift(c, a['x'], a['y']); data[c]['actors'].append(dict(a, x=x, y=y))
    for p in info['pickups']:
        c = section(p['x'], p['y']); x, y = shift(c, p['x'], p['y']); data[c]['pickups'].append(dict(p, x=x, y=y))
    def to_section(t):
        c = section(t['to_x'], t['to_y']); x, y = shift(c, t['to_x'], t['to_y']); return dict(t, to_area=c, to_x=x, to_y=y)
    for t in info['triggers']:
        r = t['rect']; c = section(max(0, r[0]) + 4, max(0, r[1]) + 4); a0, b0 = shift(c, r[0], r[1]); a1, b1 = shift(c, r[2], r[3]); t = dict(t, rect=[a0, b0, a1, b1])
        if t['kind'] == 'warp' and t['to_area'] == AREA: t = to_section(t)
        data[c]['triggers'].append(t)
    for k, c in sec.items():
        b = box[c]; d = data[c]; json.dump(d, open(out + '/assets/areas/area%02d.json' % c, 'w'))
        r2 = ET.fromstring(ET.tostring(root)); r2.set('width', str(b['w'])); r2.set('height', str(b['h']))
        for l in r2.findall('layer'):
            v = layers[l.get('name')] * (b['m'] if l.get('name') in ('walkable', 'flyable', 'shots') else b['grow']); v = v[b['oy']:b['oy'] + b['h'], b['ox']:b['ox'] + b['w']]; l.set('width', str(b['w'])); l.set('height', str(b['h'])); l.find('data').text = ','.join(map(str, v.ravel().tolist()))
        for ts in r2.findall('tileset'):
            if ts.get('source'): ts.set('source', os.path.basename(ts.get('source')))
        ET.ElementTree(r2).write(out + '/assets/maps/area%02d.tmx' % c)
        for f in os.listdir(L + '/assets/maps/tiles'):
            g = re.match(r'area%02d(.*)' % AREA, f)
            if g: os.symlink(os.path.abspath(L + '/assets/maps/tiles/' + f), out + '/assets/maps/tiles/area%02d%s' % (c, g.group(1)))
    for n_ in range(42):
        if n_ == AREA: continue
        a = json.load(open('%s/assets/areas/area%02d.json' % (L, n_)))
        a['triggers'] = [to_section(t) if t['kind'] == 'warp' and t['to_area'] == AREA else t for t in a['triggers']]
        json.dump(a, open(out + '/assets/areas/area%02d.json' % n_, 'w'))
    q = json.load(open(L + '/assets/story/quests.json'))
    for x in q['quests']:
        for L_ in (x['tasks'], x['actions']):
            for i_, t in enumerate(L_):
                k = t['type']
                if k == 'add_warp':
                    if t['area'] == AREA:
                        c = section(t['x1'], t['y1']); a0, b0 = shift(c, t['x1'], t['y1']); a1, b1 = shift(c, t['x2'], t['y2']); t = dict(t, area=c, x1=a0, y1=b0, x2=a1, y2=b1)
                    if t['to_area'] == AREA: t = to_section(t)
                elif t.get('area') == AREA:
                    if 'x' in t:
                        c = section(t['x'], t['y']); x_, y_ = shift(c, t['x'], t['y']); t = dict(t, area=c, x=x_, y=y_)
                    elif 'x1' in t:
                        c = section(t['x1'], t['y1']); a0, b0 = shift(c, t['x1'], t['y1']); a1, b1 = shift(c, t['x2'], t['y2']); t = dict(t, area=c, x1=a0, y1=b0, x2=a1, y2=b1)
                    else: raise ValueError(t)
                L_[i_] = t
    json.dump(q, open(out + '/assets/story/quests.json', 'w')); add_pictures(L, out); open(stamp, 'w').write('ok')
    return out
