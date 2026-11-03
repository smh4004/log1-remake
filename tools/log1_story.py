"""M4: generate LoG1's story up to a chosen quest as Buu's Fury scripts, from extracted data at build time. Output stays in out/.

Flags: quest n = 420 + n, task t = 500 + t, conversation state from 620. A set's state is the entry it starts from next.
Defaults on the review list: no visible followers on escorts, Senzu Beans for pickups, no item graphics, cutscenes play only
their conversations, and music changes are skipped until the music plan (M8).
"""
import collections, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from convert_log1 import chain, conversations, split_line  # noqa: E402

QF, TF, EF, TOK, NOOP = 420, 500, 620, 870, 895
WORLD, SENZU = 26, 21
SPEAKER = dict(goku='goku'); NAME = dict(roshi='Master Roshi', chichi='Chi-Chi', kingkai='King Kai', kingyema='King Yemma', korrin='Korin', popo='Mr. Popo', raditz='Raditz', nappa='Nappa')


class Story:
    QF, TF = QF, TF

    def __init__(self, log1, last_quest, ids, portraits, scenes_json):
        self.sets = conversations(log1); self.names = [l.split()[1] for l in open(log1 + '/assets/areas/SPRITES.txt')]
        d = json.load(open(log1 + '/assets/story/quests.json')); self.q = [x for x in d['quests'] if x['quest'] <= last_quest]; self.qof = d['quest_of_flag']
        self.ids, self.por = set(ids), portraits or {}; self.scenes = {s['scene']: s for s in json.load(open(scenes_json))}
        self.out = []; self.doors = collections.defaultdict(list); self.walks = []; self.hostile = {}; self.deaths = {}; self.log = collections.Counter(); self.state = {}
        self.pick = {}; self.area_sets = set()
        for n in ids:
            for a in json.load(open('%s/assets/areas/area%02d.json' % (log1, n)))['actors']:
                if a['kind'] != 2: self.area_sets.add(a['param'])
        self.area_sets |= {t['after_set'] for x in self.q for t in x['tasks'] if t['type'] == 'escort' and t['area'] in self.ids}
        self._states(); self._place_groups()

    def _states(self):
        """Entries a set can start from later, other than 0."""
        want = collections.defaultdict(set)
        for x in self.q:
            for a in x['actions']:
                if a['type'] == 'set_entry': want[a['set']].add(a['entry'])
        for s in self.area_sets | set(want):
            L = self.sets.get(s, {}); todo = [0] + list(want[s]); seen = set()
            while todo:
                e = todo.pop()
                if e in seen or e not in L: continue
                seen.add(e); _, n = chain(L, e)
                if n is not None: todo.append(n); want[s].add(n)
            want[s].discard(0)
        f = EF
        for s in sorted(want):
            self.state[s] = {}
            for e in sorted(want[s]):
                if e in self.sets.get(s, {}): self.state[s][e] = f; f += 1
        assert f <= TOK, 'conversation flags overflow (%d)' % f

    def _place_groups(self):
        """place_item uses up any pickup of its kind. Items for each group are the unused spawn_items in that area, and a unary counter
        of token flags tracks how many the player holds. Placing happens on walking into the spot (LoG1 uses a menu)."""
        self.token = {}; self.tokens = []; used = {t['item'] for x in self.q for t in x['tasks'] if t['type'] == 'talk_with_item'}
        for x in self.q:
            for t in x['tasks']:
                if t['type'] != 'place_item': continue
                g = next((g for g in self.tokens if g['area'] == t['area'] and g['kind'] == t['kind']), None)
                if not g:
                    items = [i['id'] for y in self.q for i in y['tasks'] if i['type'] == 'spawn_item' and i['area'] == t['area'] and i['item'] not in used and y['quest'] <= x['quest']]
                    g = dict(area=t['area'], kind=t['kind'], items=items, flags=[TOK + sum(len(h['flags']) for h in self.tokens) + k for k in range(len(items))]); self.tokens.append(g)
                    assert items and g['flags'][-1] < NOOP
                    for i in items: self.token[i] = g

    def place_lists(self):
        for x in self.q:
            for t in x['tasks']:
                if t['type'] != 'place_item': continue
                g = next(g for g in self.tokens if g['area'] == t['area'] and g['kind'] == t['kind']); i = t['id']
                self.doors[t['area']].append(dict(kind='walk', rect=(t['x1'] - 8, t['y1'] - 8, t['x2'] + 8, t['y2'] + 8), list='place_t%d' % i))
                r = ['list place_t%d' % i, 'set_flag %d' % NOOP, 'if_flag %d pl%d_end' % (TF + i, i)]
                for k, f in reversed(list(enumerate(g['flags']))): r.append('if_flag %d pl%d_%d' % (f, i, k))
                r.append('goto pl%d_end' % i)
                for k, f in enumerate(g['flags']): r += ['label pl%d_%d' % (i, k), 'do call 30 %d' % f, 'goto pl%d_do' % i]
                r += ['label pl%d_do' % i, 'set_flag %d' % (TF + i), 'narrate You put the item in place.', 'run quest_check', 'label pl%d_end' % i, 'stop']
                self.out += r

    def say(self, body):
        r = []
        for l in body:
            who = 'goku' if l['who'] == 'goku' else ('#%d' % self.por[l['who']] if l['who'] in self.por else None)
            pre = '' if who else NAME.get(l['who'], l['who'].rstrip('0123456789').title()) + ': '
            r += ['say %s %s' % (who or 'narrator', p) for p in split_line(pre + l['text'].replace('{', '(').replace('}', ')').strip())]
        return r

    def set_state(self, s, e):
        r = ['do call 30 %d' % f for k, f in self.state.get(s, {}).items() if k != e]
        if e in self.state.get(s, {}): r.append('set_flag %d' % self.state[s][e])
        return r

    def warp(self, area, x, y): return ['do call 120 20; call 119 %d %d 1 %d %d; call 121 20' % (WORLD, area + 1, x, y)]

    def scene(self, i):
        """Cutscenes keep their conversations for now. Other commands (walks, animation, effects) are counted, not played."""
        r = []
        for c in self.scenes[i]['commands']:
            if c['fn'] == '0800CC61':
                b = bytes.fromhex(c['raw']); r += self.say(chain(self.sets[b[0]], b[1])[0])
            else: self.log['scene command skipped'] += 1
        return r

    def actions(self, x):
        r = []
        for a in x['actions']:
            k = a['type']
            if k == 'give_exp': r.append('do call 194 %d' % a['amount'])
            elif k == 'give_pickup': r.append('do call 128 %d' % SENZU); self.log['pickup uses Senzu Bean'] += 1
            elif k == 'conversation': r += self.say(chain(self.sets[a['set']], a['entry'])[0])
            elif k == 'set_entry': r += self.set_state(a['set'], a['entry'])
            elif k == 'scene': r += self.scene(a['index'])
            elif k == 'warp': r += self.warp(a['area'], a['x'], a['y'])
            elif k == 'make_hostile': f = QF + x['quest']; self.hostile[(a['area'], a['sprite'])] = f
            elif k == 'set_walkable': self.walks.append((QF + x['quest'], a['area'], a['x1'] // 8, a['y1'] // 8, (a['x2'] + 7) // 8, (a['y2'] + 7) // 8))
            elif k == 'add_warp':
                name = 'warp_q%d' % x['quest']; self.doors[a['area']].append(dict(kind='walk', rect=(a['x1'], a['y1'], a['x2'], a['y2']), list=name))
                self.out += ['list ' + name, 'set_flag %d' % NOOP, 'unless_flag %d w%d_end' % (QF + x['quest'], x['quest'])] + self.warp(a['to_area'], a['to_x'], a['to_y']) + ['label w%d_end' % x['quest'], 'stop']
            else: self.log['action skipped: ' + k] += 1
        return r

    def check_list(self):
        r = ['list quest_check', 'set_flag %d' % NOOP]; pending = []
        for x in self.q:
            n = x['quest']; lab = 'c%d' % n; body = ['if_flag %d %s' % (QF + n, lab)]; ok = True
            for t in x['tasks']:
                if t['type'] == 'after_quest': body.append('unless_flag %d %s' % (QF + t['quest'], lab))
                else: body.append('unless_flag %d %s' % (TF + t['id'], lab))
            r += body + ['set_flag %d' % (QF + n)] + self.actions(x) + ['label ' + lab]
        r += ['stop']
        return r

    def add_token(self, i):
        g = self.token.get(i)
        if not g: return []
        r = []
        for k, f in enumerate(g['flags']): r += ['if_flag %d tk%d_%d' % (f, i, k), 'set_flag %d' % f, 'goto tk%d_end' % i, 'label tk%d_%d' % (i, k)]
        return r + ['label tk%d_end' % i]

    def talk_lists(self):
        tasks = collections.defaultdict(list)
        for x in self.q:
            for t in x['tasks']:
                if t['type'] in ('talk_with_item', 'talk_with_kind', 'spawn_character', 'escort') and 'set' in t: tasks[t['set']].append((x, t))
            for t in x['tasks']:
                if t['type'] == 'spawn_item':
                    self.pick[(x['quest'], t['item'])] = t['id']; self.doors[t['area']].append(dict(kind='walk', rect=(t['x'] - 8, t['y'] - 8, t['x'] + 16, t['y'] + 16), list='pick_t%d' % t['id']))
                    self.out += ['list pick_t%d' % t['id'], 'set_flag %d' % NOOP, 'if_flag %d p%d' % (TF + t['id'], t['id']), 'set_flag %d' % (TF + t['id'])] + self.add_token(t['id']) + ['narrate You found an item.', 'run quest_check', 'label p%d' % t['id'], 'stop']
        after = collections.defaultdict(list)
        for x in self.q:
            for t in x['tasks']:
                if t['type'] == 'after_conversation': after[t['set']].append(t)
        for s in sorted(self.area_sets | set(tasks) | set(self.state)):
            if s not in self.sets: continue
            L = self.sets[s]; r = ['list talk_set%02d' % s, 'set_flag %d' % NOOP]
            for x, t in tasks[s]:
                lab = 't%d_next' % t['id']; r.append('if_flag %d %s' % (TF + t['id'], lab))
                if t['type'] == 'talk_with_item': r.append('unless_flag %d %s' % (TF + self.pick.get((x['quest'], t['item']), 0), lab))
                elif t['type'] == 'talk_with_kind': r.append('unless_flag %d %s' % (QF + 17, lab))
                elif t['type'] == 'escort':
                    src = next(p for p in x['tasks'] if p['type'] == 'spawn_character') if any(p['type'] == 'spawn_character' for p in x['tasks']) else None
                    if src: r.append('unless_flag %d %s' % (TF + src['id'], lab))
                    else:
                        prior = next((p for y in self.q for p in y['tasks'] if p['type'] == 'spawn_character' and p['sprite'] == t['follower']), None)
                        if prior: r.append('unless_flag %d %s' % (TF + prior['id'], lab))
                r += self.say(chain(L, t['entry'])[0]) + ['set_flag %d' % (TF + t['id']), 'run quest_check', 'stop', 'label ' + lab]
            st = self.state.get(s, {})
            for e in sorted(st, reverse=True): r.append('if_flag %d e%d_%d' % (st[e], s, e))
            r.append('goto e%d_0' % s)
            for e in [0] + sorted(st):
                if e not in L: continue
                body, nxt = chain(L, e); r += ['label e%d_%d' % (s, e)] + self.say(body)
                if nxt is not None and nxt != e: r += self.set_state(s, nxt)
                for t in after[s]:
                    if t['entry'] == e: r += ['set_flag %d' % (TF + t['id']), 'run quest_check']
                r.append('stop')
            self.out += r

    def death_script(self, n, sprite, put):
        """Bytecode run when a hostile boss dies: finish its 'activate' task. Quest results that need dialogue wait for the next talk or arrival."""
        import scenes
        code = b''; next_area = None
        for x in self.q:
            for t in x['tasks']:
                if t['type'] == 'activate' and t['sprite'] == sprite and t['area'] == n:
                    code += scenes.assemble('call 29 %d; call 29 %d' % (TF + t['id'], QF + x['quest']), {})
                    for a in x['actions']:
                        if a['type'] == 'warp': next_area = a
        if next_area: code += scenes.assemble('call 120 20; call 119 %d %d 1 %d %d; call 121 20' % (WORLD, next_area['area'] + 1, next_area['x'], next_area['y']), {})
        return put(code + b'\x11')

    def generate(self, path):
        chk = self.check_list(); self.talk_lists(); self.place_lists(); self.out = chk + self.out
        open(path, 'w', encoding='utf-8').write('\n'.join(self.out) + '\n')
        return dict(lines=sum(l.startswith('say') or l.startswith('narrate') for l in self.out), steps=len(self.out), doors=sum(map(len, self.doors.values())), hostile=len(self.hostile), walks=len(self.walks), flags_state=sum(map(len, self.state.values())), log=dict(self.log))
