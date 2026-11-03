"""M4 slice build: new game starts on LoG1's area 0. Reads your ROMs and extracted assets; writes out/slice only.

    python3 tools/slice_build.py <log1-decomp>
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_areas, log1_portraits, log1_talk, map_convert as C, scenes, text_tool  # noqa: E402


def main():
    L = sys.argv[1]; bf = os.path.join(ROOT, 'rom', 'bf.gba'); O = os.path.join(ROOT, 'out', 'slice'); os.makedirs(os.path.join(O, 'text'), exist_ok=True)
    ids = [0, 1]; sets = sorted({a['param'] for n in ids for a in C.Area(L, n).info['actors'] if a['kind'] != 2})
    base = bytearray(open(bf, 'rb').read()); plan = log1_portraits.plan(L, os.path.expanduser('~/repos/buusfury-decomp'), os.path.expanduser('~/repos/log2-decomp'), base)
    ptr = {k: (v['speaker'] if v['source'] == 'bf' else 163 + i) for i, (k, v) in enumerate(sorted(plan.items()))}
    talk = os.path.join(O, 'talk.scene')
    tmp = bytearray(base); tmp += b'\xff' * (0x1000000 - len(tmp)); combo = open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read(); ptr, nadd = log1_portraits.install(tmp, combo, plan); print('portraits added', nadd)
    print(log1_talk.generate(L, sets, talk, ptr))
    sc = [scenes.parse(os.path.join(ROOT, 'src', 'scenes', 'opening.scene')), scenes.parse(talk)]
    if not os.path.exists(os.path.join(O, 'text', 'ui.txt')): text_tool.export(bf, os.path.join(O, 'text'))
    r = bytearray(text_tool.build(bf, os.path.join(O, 'text'), extra=scenes.texts(sc))); print('after text', hex(len(r)))
    r += b'\xff' * max(0, 0x1000000 - len(r))
    ptr2, _ = log1_portraits.install(r, combo, plan); assert ptr2 == ptr
    end = len(r); r += bytes(0x80000)
    fin = scenes.compile_all(r, sc, text_tool.EXTRA_REFS, scenes.aliases(''), end); del r[(fin + 3) & ~3:]
    tab, skipped = log1_areas.build(r, L, ids, {int(k[8:]): v for k, v in scenes.NAMED.items() if k.startswith('talk_set')}); print('skipped NPCs', skipped)
    while len(r) % 0x10000: r.append(0xFF)
    open(os.path.join(O, 'slice.gba'), 'wb').write(r); print('rom', len(r))


if __name__ == '__main__':
    main()
