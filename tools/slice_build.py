"""M4 slice build: new game starts on LoG1's area 0. Reads your ROMs and extracted assets; writes out/slice only.

    python3 tools/slice_build.py <folder holding log1-decomp and buusfury-decomp>
"""
import collections, json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_balance, log1_music, log1_split, build_flight, log1_actors, log1_areas, log1_portraits, log1_story, log1_world, scenes, text_tool  # noqa: E402


IDS = [int(v) for v in os.environ['IDS'].split(',')] if os.environ.get('IDS') else log1_split.ids(); LAST_QUEST = int(os.environ.get('LAST_QUEST', 74))


def main():
    DEPS = sys.argv[1]; L = log1_split.build(os.path.join(DEPS, 'log1-decomp')); bf = os.path.join(ROOT, 'rom', 'bf.gba'); O = os.path.join(ROOT, 'out', 'slice'); os.makedirs(os.path.join(O, 'text'), exist_ok=True)
    conv = os.path.join(ROOT, 'out', 'converted', 'scenes.json')
    if not os.path.exists(conv): subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'log1_scenes.py')])
    base = bytearray(open(bf, 'rb').read()); plan = log1_portraits.plan(L, os.path.join(DEPS, 'buusfury-decomp'), base)
    combo = open(os.path.join(ROOT, 'rom', 'log12.gba'), 'rb').read(); log1 = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read()
    tmp = bytearray(base); tmp += b'\xff' * (0x1000000 - len(tmp)); ptr, nadd = log1_portraits.install(tmp, combo, plan); print('portraits added', nadd)
    bal = log1_balance.Balance(os.path.join(DEPS, 'buusfury-decomp')); st = log1_story.Story(L, LAST_QUEST, IDS, ptr, conv, bal); path = os.path.join(O, 'story.scene'); print(st.generate(path))
    op = os.path.join(ROOT, 'src', 'scenes', 'opening.scene')
    if os.environ.get('START'):                          # test builds: START=area,x,y begins somewhere else
        an, x, y = os.environ['START'].split(','); op2 = os.path.join(O, 'opening_test.scene'); open(op2, 'w').write(open(op).read().replace('call 119 26 1 1 184 72', 'call 119 26 %d 1 %s %s' % (int(an) + 1, x, y))); op = op2
    sc = [scenes.parse(op), scenes.parse(path)]
    if not os.path.exists(os.path.join(O, 'text', 'ui.txt')): text_tool.export(bf, os.path.join(O, 'text'))
    log1_world.ui_text(os.path.join(O, 'text', 'ui_log1.txt'))
    r = bytearray(text_tool.build(bf, os.path.join(O, 'text'), extra=scenes.texts(sc))); r += b'\xff' * max(0, 0x1000000 - len(r))
    assert log1_portraits.install(r, combo, plan)[0] == ptr
    act = log1_actors.Actors(r, log1, L, 0xC00000)
    act.bal = bal; s_ = log1_balance.START; struct.pack_into('<HHHBBBB', r, 0x6FDA4C, s_['level'], s_['hp'], s_['ep'], s_['str'], s_['pow'], s_['end'], s_['spd'])
    idx = {n: (log1_areas.BF_IDX.get(n) or act.actor(n, False)) - 9 for n in st.move_names}   # scene walks name their actors
    end = len(r); r += bytes(0x100000); fin = scenes.compile_all(r, sc, text_tool.EXTRA_REFS, scenes.aliases(''), end, idx); del r[(fin + 3) & ~3:]
    tab, spawns, walks, picks, foes, zones, skipped, moved, qc, follows, walkins = log1_areas.build(r, L, IDS, st, dict(scenes.NAMED), act); new, cur = act.finish()
    print('actors added', new, 'without frames', act.missing, 'end', hex(cur)); print('arrival moves', [m for m in moved if m[2]]); print('skipped', collections.Counter(s[2] for s in skipped))
    print('music bytes', log1_music.install(r, log1))
    print('world map', log1_world.install(r, L, IDS, log1_areas.WORLD)); fly = [(tab + 56 * (log1_areas.COUNT + IDS.index(n)), scenes.NAMED['fly_%d' % n]) for n, _, _ in log1_world.PLACES if n in IDS]
    print('hook', build_flight.install(r, spawns, walks, picks, foes, zones, qc, follows, fly, log1_world.art(), log1_world.markers(), walkins), 'spawns', len(spawns), 'walks', len(walks), 'pickups', len(picks), 'enemies', len(foes), 'hurt zones', len(zones), 'walk-in zones', len(walkins))
    json.dump(dict({str(n): scenes.NAMED['dbg_%d' % n] for n in IDS}, **{'x%d' % n: scenes.NAMED['dbgx_%d' % n] for n in IDS}), open(os.path.join(O, os.environ.get('OUT', 'slice') + '.lists.json'), 'w'))
    while len(r) % 0x10000: r.append(0xFF)
    open(os.path.join(O, os.environ.get('OUT', 'slice') + '.gba'), 'wb').write(r); print('rom', len(r))


if __name__ == '__main__':
    main()
