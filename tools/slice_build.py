"""M4 slice build: new game starts on LoG1's area 0. Reads your ROMs and extracted assets; writes out/slice only.

    python3 tools/slice_build.py <folder holding log1-decomp, buusfury-decomp and log2-decomp>
"""
import collections, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import build_flight, log1_actors, log1_areas, log1_portraits, log1_story, scenes, text_tool  # noqa: E402


IDS = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10]; LAST_QUEST = 23


def main():
    DEPS = sys.argv[1]; L = os.path.join(DEPS, 'log1-decomp'); bf = os.path.join(ROOT, 'rom', 'bf.gba'); O = os.path.join(ROOT, 'out', 'slice'); os.makedirs(os.path.join(O, 'text'), exist_ok=True)
    conv = os.path.join(ROOT, 'out', 'converted', 'scenes.json')
    if not os.path.exists(conv): subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'log1_scenes.py')])
    base = bytearray(open(bf, 'rb').read()); plan = log1_portraits.plan(L, os.path.join(DEPS, 'buusfury-decomp'), os.path.join(DEPS, 'log2-decomp'), base)
    combo = open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read(); log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read()
    tmp = bytearray(base); tmp += b'\xff' * (0x1000000 - len(tmp)); ptr, nadd = log1_portraits.install(tmp, combo, plan); print('portraits added', nadd)
    st = log1_story.Story(L, LAST_QUEST, IDS, ptr, conv); path = os.path.join(O, 'story.scene'); print(st.generate(path))
    sc = [scenes.parse(os.path.join(ROOT, 'src', 'scenes', 'opening.scene')), scenes.parse(path)]
    if not os.path.exists(os.path.join(O, 'text', 'ui.txt')): text_tool.export(bf, os.path.join(O, 'text'))
    r = bytearray(text_tool.build(bf, os.path.join(O, 'text'), extra=scenes.texts(sc))); r += b'\xff' * max(0, 0x1000000 - len(r))
    assert log1_portraits.install(r, combo, plan)[0] == ptr
    end = len(r); r += bytes(0x100000); fin = scenes.compile_all(r, sc, text_tool.EXTRA_REFS, scenes.aliases(''), end); del r[(fin + 3) & ~3:]
    act = log1_actors.Actors(r, log1, L, 0xC00000)
    tab, spawns, walks, skipped, moved = log1_areas.build(r, L, IDS, st, dict(scenes.NAMED), act); new, cur = act.finish()
    print('actors added', new, 'without frames', act.missing, 'end', hex(cur)); print('arrival moves', [m for m in moved if m[2]]); print('skipped', collections.Counter(s[2] for s in skipped))
    print('hook', build_flight.install(r, spawns, walks), 'spawns', len(spawns), 'walks', len(walks))
    while len(r) % 0x10000: r.append(0xFF)
    open(os.path.join(O, 'slice.gba'), 'wb').write(r); print('rom', len(r))


if __name__ == '__main__':
    main()
