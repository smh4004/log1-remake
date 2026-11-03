"""M1: convert Legacy of Goku's exported data into a Buu's Fury plan. Everything it writes goes to out/ (ROM-derived).

    python3 tools/convert_log1.py <log1-decomp dir>

Writes out/converted/quests.scene (one list per quest's results), areas.json, conversations.json, report.json.
Scene code is checked with Gero's parser and assembler. IDs that M2 must map (speakers, items, music, skills, areas)
stay symbolic in comments; the numbers in `do` lines are Buu's Fury natives:
  0x1D set_flag, 0x23 music, 0x77 load area, 0x78/0x79 fades, 0x80 give item, 0xA4 add skill, 0xC2 add EXP.
Task and action types are classed: `generated` (the converter writes it), `wired` (needs an engine hook placed per
area at M4, known mechanism) or `manual` (no direct Buu's Fury equivalent found yet).
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'vendor', 'gero-tools', 'tools'))
import scenes  # noqa: E402

FLAG_QUEST, FLAG_TASK, FLAG_ENTRY = 420, 500, 620       # BF's array has 896 flags; a new story can reuse low ones too
FLAG_END = 896
LINE_LIMIT = 100                                        # longer dialogue lines reset BF (found in Ultimate Edition)
TASKS = dict(after_quest='generated', after_conversation='generated', defeat='wired', talk_with_item='wired', talk_with_kind='wired',
             spawn_item='wired', enter_zone='wired', activate='wired', spawn_character='manual', escort='manual',
             place_item='manual', obstacle='manual')
ACTIONS = dict(conversation='generated', set_entry='generated', give_exp='generated', give_pickup='generated', music='generated',
               warp='generated', actor_leave='generated', change_actor='generated', add_warp='wired', learn='wired', add_scene_zone='wired',
               scene='manual', set_walkable='manual', speed_up='manual', end_game='manual')


def conversations(log1):
    sets = {}
    for p in sorted(glob.glob(log1 + '/assets/dialogue/set*.txt')):
        n = int(re.search(r'set(\d+)', p)[1]); L = {}
        for ln in open(p, encoding='utf-8'):
            m = re.match(r'(\d+): (\S+) > (\d+)(?: \| (.*))?$', ln.rstrip('\n'))
            if m: L[int(m[1])] = dict(who=m[2], next=int(m[3]), text=m[4] or '')
        sets[n] = L
    return sets


def chain(lines, entry):
    out, seen, i = [], set(), entry
    while i in lines and i not in seen:
        seen.add(i); l = lines[i]
        if l['who'] == 'end': return out, l['next']
        out.append(l); i = l['next']
    return out, None


def split_line(t, n=LINE_LIMIT):
    parts = []
    while len(t) > n:
        c = t.rfind(' ', 0, n)
        c = c if c > 0 else n
        parts.append(t[:c]); t = t[c:].strip()
    return parts + [t]


def main():
    log1 = sys.argv[1]; out = os.path.join(ROOT, 'out', 'converted'); os.makedirs(out, exist_ok=True)
    sets = conversations(log1)
    q = json.load(open(log1 + '/assets/story/quests.json'))['quests']
    areas = [json.load(open(p)) for p in sorted(glob.glob(log1 + '/assets/areas/area*.json'))]
    entry_flag = {}

    def eflag(s, e):
        k = (s, e)
        if k not in entry_flag: entry_flag[k] = FLAG_ENTRY + len(entry_flag)
        return entry_flag[k]

    txt, manual, tc, ac, used_conv = [], [], Counter(), Counter(), set()
    tasks_seen = sorted({t['id'] for x in q for t in x['tasks'] if 'id' in t})
    tflag = {t: FLAG_TASK + i for i, t in enumerate(tasks_seen)}
    for x in q:
        n = x['quest']; txt += ['list quest%02d_done' % n, 'set_flag %d' % (FLAG_QUEST + n)]
        for t in x['tasks']:
            tc[t['type']] += 1
            if TASKS[t['type']] == 'manual': manual.append(dict(quest=n, kind='task', type=t['type'], area=t.get('area')))
        for a in x['actions']:
            k = a['type']; ac[k] += 1
            if ACTIONS[k] == 'manual': manual.append(dict(quest=n, kind='action', type=k, area=a.get('area')))
            if k == 'conversation':
                L, _ = chain(sets[a['set']], a['entry']); used_conv.add((a['set'], a['entry']))
                for l in L:
                    for part in split_line(l['text']): txt.append('say narrator %s' % part.replace('\n', ' '))
            elif k == 'set_entry': txt.append('set_flag %d' % eflag(a['set'], a['entry']))
            elif k == 'give_exp': txt.append('do call 194 %d' % a['amount'])
            elif k == 'give_pickup': txt += ['# give LoG1 pickup %d (item map: M2)' % a['item'], 'do call 128 0']
            elif k == 'music': txt += ['# LoG1 track %d (music map: M8)' % a['track'], 'do music 0']
            elif k == 'warp': txt += ['# warp LoG1 area %d at %d,%d (area map: M3)' % (a['area'], a['x'], a['y']), 'do call 120 20; call 119 1 1 1 %d %d; call 121 20' % (a['x'], a['y'])]
            elif k in ('actor_leave', 'change_actor'): txt.append('set_flag %d' % eflag(('actor', a['area'], a['sprite']), a.get('param', 0)))
            else: txt.append('# %s %s: %s' % (ACTIONS[k], k, json.dumps({f: v for f, v in a.items() if f not in ('label', 'raw')})))
    path = os.path.join(out, 'quests.scene'); open(path, 'w', encoding='utf-8').write('\n'.join(txt) + '\n')
    sc = scenes.parse(path)
    for s in sc['steps']:
        if s[0] == 'do': scenes.assemble(s[1], {})
    used = FLAG_ENTRY + len(entry_flag)
    assert used <= FLAG_END and FLAG_TASK + len(tflag) <= FLAG_ENTRY, 'flag ranges overlap or overflow'

    # warp graph from the start area
    g = defaultdict(set); bad = []
    for a in areas:
        for t in a['triggers']:
            if t['kind'] == 'warp':
                g[a['area']].add(t['to_area'])
                if not 0 <= t['to_area'] < len(areas): bad.append((a['area'], t['to_area']))
    for x in q:
        for a in x['actions']:
            if a['type'] == 'add_warp': g[a['area']].add(a['to_area'])
    warp_to = {a['area'] for x in q for a in x['actions'] if a['type'] == 'warp'}
    seen, todo = {0}, [0] + sorted(warp_to)
    seen |= warp_to
    while todo:
        for b in g[todo.pop()]:
            if b not in seen: seen.add(b); todo.append(b)
    orphan = sorted({a['area'] for a in areas} - seen)
    lines = [l for L in sets.values() for l in L.values() if l['who'] != 'end']
    long_ = [l for l in lines if len(l['text']) > LINE_LIMIT]
    speakers = Counter(l['who'] for l in lines)
    enemy_sprites = Counter(ac_['sprite'] for a in areas for ac_ in a['actors'] if ac_['kind'] == 2)
    npc_sprites = Counter(ac_['sprite'] for a in areas for ac_ in a['actors'] if ac_['kind'] != 2)
    json.dump(dict(sets={str(k): {str(i): l for i, l in v.items()} for k, v in sets.items()}), open(out + '/conversations.json', 'w'))
    json.dump(areas, open(out + '/areas.json', 'w'))
    rep = dict(quests=len(q), areas=len(areas), conversation_sets=len(sets), lines=len(lines), tasks=tc, actions=ac,
               generated_steps=len(sc['steps']), manual=manual, manual_by_type=Counter(m['type'] for m in manual),
               quests_with_manual=len({m['quest'] for m in manual}), lines_over_limit=len(long_), longest=max(len(l['text']) for l in lines),
               speakers=speakers, enemy_sprites=enemy_sprites, npc_sprites=npc_sprites, unreachable_areas=orphan, bad_warps=bad, flags_used=used)
    json.dump(rep, open(out + '/report.json', 'w'), indent=1)
    for k in ('quests', 'areas', 'conversation_sets', 'lines', 'generated_steps', 'quests_with_manual', 'lines_over_limit', 'longest', 'unreachable_areas', 'bad_warps', 'flags_used'):
        print(k, rep[k])
    print('manual', dict(rep['manual_by_type']))
    print('speakers', len(speakers), 'enemy sprites', len(enemy_sprites), dict(enemy_sprites.most_common()))


if __name__ == '__main__':
    main()
