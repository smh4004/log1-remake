"""M4: choose a portrait for each LoG1 speaker, from Buu's Fury first and LoG2 second. Art is read from your ROMs at build time.

Buu's Fury: an NPC's character ID comes from its spawn record, and its portrait is the speaker its own talk list uses most.
LoG2: script lines name their speaker ("FRIEZA: ..."), and portrait table index = speaker id - 8.
    python3 tools/log1_portraits.py <log1-decomp> <buusfury-decomp> <log2-decomp>     # prints the plan, writes out/portraits.json
"""
import collections, csv, json, os, re, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import mapkit  # noqa: E402
from room_test import lab  # noqa: E402

BB = 0x08000000; AREAS, COUNT = 0x8E2E0, 452
BF_TABLE, BF_LIT, SLOTS = 0x6F393C, 0x12194, 256
L2_SLICE, L2_TABLE, L2_PAL, L2_BASE = 0x800000, 0x3ECB6C, 0x3ECD1C, 0x08800000
# LoG1 sprite set -> (name in BF's scouter table, name in LoG2's scripts)
NAMES = dict(bubbles=('Bubbles', None), bulma=('Bulma', 'BULMA'), chaitzu=('Chiaotzu', None), chichi=('Chi-Chi', 'CHI-CHI'), dende=('Dende', 'DENDE'), gohan1=('Gohan', 'GOHAN'), gohan2=('Gohan', 'GOHAN'), gohan3=('Gohan', 'GOHAN'),
             gregory=('Gregory', None), kingkai=('King Kai', None), kingyema=('King Yemma', None), korrin=('Korin', None), krillin1=('Krillin', 'KRILLIN'), krillin2=('Krillin', 'KRILLIN'), piccolo=('Piccolo', 'PICCOLO'),
             popo=('Mr. Popo', 'MR. POPO'), puar=('Puar', 'PUAR'), roshi=('Master Roshi', 'MASTER ROSHI'), tien=('Tien', 'TIEN'), vegeta1=('Vegeta', 'VEGETA'), vegeta2=('Vegeta', 'VEGETA'), vegeta3=('Vegeta', 'VEGETA'), yamcha=('Yamcha', 'YAMCHA'),
             assist1=("Yemma's Assistant", None), assist2=("Yemma's Assistant", None), assist3=("Yemma's Assistant", None), kami=(None, 'KAMI'), frieza1=(None, 'FRIEZA'), frieza2=(None, 'FRIEZA'), frieza3=(None, 'FRIEZA'), frieza4=(None, 'FRIEZA'),
             namekian1=(None, 'NAMEK'), namekian2=(None, 'NAMEK'), namekian3=(None, 'NAMEK'), namekian4=(None, 'NAMEK'))


# Portrait numbers from Gero's RE notes (identified by eye there). Speaker id = number + 8, which matches Krillin's derived id.
BF_NOTES = dict(piccolo=104, tien=127, yamcha=151, vegeta1=136, vegeta2=136, vegeta3=136)
# LoG2's fixed teen Gohan portrait; LoG1's Gohan is a child, so this one needs checking
L2_NOTES = dict(gohan1=48, gohan2=48, gohan3=48)


def bf_speakers(r):
    """character index -> Counter of speaker ids used by that NPC's talk lists."""
    u = lambda o: struct.unpack_from('<I', r, o)[0]; out = collections.defaultdict(collections.Counter)
    ok = lambda v: BB <= v < BB + len(r) - 4
    for k in range(COUNT):
        e = AREAS + 56 * k; n, lst = r[e + 4], u(e + 0x14)
        if not ok(lst): continue
        for i in range(n):
            p = u(lst - BB + 4 * i) - BB - 8
            if p < 0 or p + 36 > len(r) or u(p) != 0x0800A223: continue
            talk, idx = u(p + 20), u(p + 24)
            if not ok(talk): continue
            q = talk - BB
            for _ in range(80):
                st = u(q); q += 4
                if not ok(st): break
                if r[st - BB + 2] == 5 and r[st - BB + 3] not in (0, 7): out[idx][r[st - BB + 3]] += 1
    return out


def log2_speakers(path):
    cur = None; c = collections.defaultdict(collections.Counter)
    for l in open(path, errors='ignore'):
        m = re.match(r'(0x[0-9A-Fa-f]{2})\s+\(', l)
        if m: cur = int(m[1], 16); continue
        m = re.match(r'\s+[#@^!]*([A-Z][A-Z\. #0-9-]{1,18}):', l)
        if m and cur is not None: c[m[1]][cur] += 1
    return c


def plan(log1, bf, log2, r):
    L = [l for l in csv.reader(open(bf + '/assets/tables/scouter.csv')) if l and not l[0].startswith('#')]
    ids = collections.defaultdict(set)
    for row in L[1:]:
        d = dict(zip(L[0], row)); ids[d['_name_text'].strip()].add(int(d['character']))
    sp = bf_speakers(r); l2 = log2_speakers(log2 + '/assets/scripts/SPEAKERS.txt'); res = {}
    for s, (bn, ln) in NAMES.items():
        c = collections.Counter()
        for i in ids.get(bn, ()): c.update(sp.get(i, {}))
        if c: res[s] = dict(source='bf', speaker=c.most_common(1)[0][0], votes=c.most_common(1)[0][1]); continue
        if s in BF_NOTES: res[s] = dict(source='bf', speaker=BF_NOTES[s] + 8, votes=0); continue
        if s in L2_NOTES: res[s] = dict(source='log2', index=L2_NOTES[s], name='notes'); continue
        if ln and l2.get(ln) and l2[ln].most_common(1)[0][0] >= 8: res[s] = dict(source='log2', index=l2[ln].most_common(1)[0][0] - 8, name=ln)
    return res


def install(r, combo, res):
    """Move BF's portrait table so it can grow, append the LoG2 portraits needed, and return sprite set -> speaker id."""
    u = lambda o: struct.unpack_from('<I', r, o)[0]; n0 = 163
    objpal = mapkit.palette(r)[256:]; P = lab(objpal[1:])
    ptab = np.frombuffer(combo[L2_SLICE + L2_PAL + 768:L2_SLICE + L2_PAL + 1536], np.uint8).reshape(256, 3)
    from wfz import decompress_stream, unpack
    frame = np.frombuffer(bytes(unpack(r, u(BF_TABLE + 4 * 8) - BB)[0]), np.uint8)[:4096].reshape(64, 64).copy()
    tab = [u(BF_TABLE + 4 * i) for i in range(n0)] + [0] * (SLOTS - n0); added = {}; out = {}
    def put(b):
        while len(r) % 4: r.append(0)
        o = len(r); r.extend(b); return BB + o
    for s, p in sorted(res.items()):
        if p['source'] == 'bf': out[s] = p['speaker']; continue
        k = p['index']
        if k not in added:
            o = struct.unpack_from('<I', combo, L2_SLICE + L2_TABLE + 4 * k)[0] - L2_BASE + L2_SLICE; t = struct.unpack_from('<I', combo, o)[0]
            d = combo[o + 8:o + 8 + 4096] if t == 0 else bytes(decompress_stream(combo, o + 8, 4096)[0])
            win = np.frombuffer(d, np.uint8).reshape(64, 64)[4:60, 4:60]
            uq, inv = np.unique(win, return_inverse=True); j = 1 + ((lab(ptab[uq])[:, None] - P[None]) ** 2).sum(2).argmin(1)
            img = frame.copy(); img[4:60, 4:60] = j[inv.ravel()].reshape(56, 56)
            b = img.astype(np.uint8).tobytes(); slot = n0 + len(added); assert slot < SLOTS
            tab[slot] = put(struct.pack('<II', 0, len(b)) + b); added[k] = slot
        out[s] = added[k]
    struct.pack_into('<I', r, BF_LIT, put(struct.pack('<%dI' % SLOTS, *tab)))
    return out, len(added)


if __name__ == '__main__':
    r = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); res = plan(*sys.argv[1:4], r)
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True); json.dump(res, open(os.path.join(ROOT, 'out', 'portraits.json'), 'w'), indent=1)
    print('bf', {k: (v['speaker'], v['votes']) for k, v in res.items() if v['source'] == 'bf'})
    print('log2', {k: (v['index'], v['name']) for k, v in res.items() if v['source'] == 'log2'})
    print('no plan', [k for k in NAMES if k not in res])
