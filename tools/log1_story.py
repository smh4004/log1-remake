"""M4: generate LoG1's story up to a chosen quest as Buu's Fury scripts, from extracted data at build time. Output stays in out/.

Flags: quest n = 420 + n, task t = 500 + t, conversation state from 620. A set's state is the entry it starts from next.
Defaults on the review list: no visible followers on escorts, LoG1 pickups mapped to Buu's Fury items (log1_pickups), cutscenes play only
their conversations, and music changes are skipped until the music plan (M8).
"""
import collections, json, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from convert_log1 import chain, conversations, split_line  # noqa: E402
import log1_pickups as P  # noqa: E402
from log1_world import takeoff_lists as world_lists  # noqa: E402

QF, TF, EF, TOK, NOOP = 420, 500, 620, 870, 895
EV, PENDING = 720, 893   # one-shot event flags; a story enemy died, so the map-wide zone should run quest_check
PF = 100                                               # area pickups: PF.. one flag each (Buu's Fury's own story, which used these, is gone)
WORLD = 26
SPEAKER = dict(goku='goku'); NAME = dict(roshi='Master Roshi', chichi='Chi-Chi', kingkai='King Kai', kingyema='King Yemma', korrin='Korin', popo='Mr. Popo', raditz='Raditz', nappa='Nappa')


def _with_energy():
    """Adds 'energy N' to the scene assembler: ki += N, the same code as Buu's Fury's Milk."""
    import scenes
    orig = scenes.assemble
    def assemble(text, actors):
        out = b''
        for part in [p.strip() for p in text.split(';') if p.strip()]:
            out += bytes([0x02, 0x0E, 0x00, int(part.split()[1]), 0x07, 0x03, 0x0E]) if part.startswith('energy ') else orig(part, actors)
        return out
    scenes.assemble = assemble
_with_energy()


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
        self._states(); self._place_groups(); self.rom = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); self.pickups = {}; f = PF
        for n in ids:
            self.pickups[n] = []
            for k, p in enumerate(json.load(open('%s/assets/areas/area%02d.json' % (log1, n)))['pickups']): self.pickups[n].append(dict(p, flag=f, list='pk%d_%d' % (n, k))); f += 1
        assert f <= 398, 'pickup flags overflow'           # Buu's Fury's world map uses 398-408
        self.areas = {n: json.load(open('%s/assets/areas/area%02d.json' % (log1, n))) for n in ids}; self.labels = dict(l.rstrip('\n').split('\t', 1) for l in open(log1 + '/assets/text/strings.txt', encoding='latin1') if '\t' in l)
        self.forms = {}; self.zones = []; self.move_names = set(); self.placed = self.placed_items()
        self.hostile_all = {(a['area'], a['sprite']) for x in self.q for a in x['actions'] if a['type'] == 'make_hostile'}
        for n, a in self.areas.items(): self.area_sets |= {t['arg'] for t in a['triggers'] if t['kind'] == 'event'}

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

    def placed_items(self):
        """{area: [(pickup id, task flag, x, y)]}: what each place_item spot shows once used."""
        out = collections.defaultdict(list); items = {t['id']: t['item'] for x in self.q for t in x['tasks'] if t['type'] == 'spawn_item'}; n_ = collections.Counter()
        for x in self.q:
            for t in x['tasks']:
                if t['type'] == 'place_item':
                    g = next(g for g in self.tokens if g['area'] == t['area'] and g['kind'] == t['kind']); k = (t['area'], t['kind']); i = g['items'][n_[k] % len(g['items'])]; n_[k] += 1
                    out[t['area']].append((items[i], TF + t['id'], (t['x1'] + t['x2']) // 2 - 8, (t['y1'] + t['y2']) // 2 - 8))
        return out

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

    def movable(self, area, sprite):
        """A character a scene can walk: always in this area and never hostile there. The player is left out for now."""
        name = self.names[sprite] if sprite < len(self.names) else None
        if name == 'goku': return dict(x=None)                 # the player: actor index 0 in Buu's Fury's scripts
        if not name or area not in self.areas or (area, sprite) in self.hostile_all: return None
        return next((a for a in self.areas[area]['actors'] if a['kind'] != 2 and a['sprite'] == name and a['show'] == 0), None)

    def scene(self, i, area=None):
        """Plays a cutscene's conversations and its walks between characters on the map. Other commands (animation, effects, sound, camera) are counted, not played."""
        r = []
        for c in self.scenes[i]['commands']:
            b = bytes.fromhex(c['raw']); f = c['fn']
            if f == '0800CC61': r += self.say(chain(self.sets[b[0]], b[1])[0]); continue
            if f == '0800DF15':                                  # the closing text
                a_ = struct.unpack_from('<I', b)[0] & 0x1FFFFFF; r += ['narrate ' + p for p in split_line(self.rom[a_:self.rom.index(b'\0', a_)].decode('latin1').replace('{', '(').replace('}', ')').strip())]; continue
            if f == '0800CB25' or f == '0800D9C5':
                a = self.movable(area, b[0])
                if f == '0800CB25': x, y = struct.unpack_from('<HH', b, 4)
                else:
                    o = self.movable(area, b[2])
                    if not o or o['x'] is None: a = None                # no fixed spot to walk to
                    else: x, y = o['x'] + struct.unpack_from('<h', b, 4)[0], o['y'] + struct.unpack_from('<h', b, 6)[0]
                if a:
                    nm = self.names[b[0]]
                    if nm == 'goku': r.append('do call 56; call 96 0 %d %d; call 58' % (x, y)); continue
                    self.move_names.add(nm); r.append('do call 56; call 96 %s %d %d; call 58' % (nm, x, y)); continue
            self.log['scene command skipped'] += 1
        return r

    def actions(self, x):
        r = []; area = next((t['area'] for t in x['tasks'] if t.get('area', 255) != 255), None); zones = {(a['x1'], a['y1'], a['x2'], a['y2']): a['scene'] for a in x['actions'] if a['type'] == 'add_scene_zone'}
        for a in x['actions']:
            k = a['type']
            if k == 'give_exp': r.append('do call 194 %d' % a['amount'])
            elif k == 'give_pickup':
                if a['item'] in P.BF_ITEM: r.append('do call 128 %d' % P.BF_ITEM[a['item']])
                else: self.log['pickup with no Buu\'s Fury item: %d' % a['item']] += 1
                t = P.message(self.rom, a['item'])
                if t: r.append('narrate ' + t.replace('{', '(').replace('}', ')'))
            elif k == 'conversation': r += self.say(chain(self.sets[a['set']], a['entry'])[0])
            elif k == 'set_entry': r += self.set_state(a['set'], a['entry'])
            elif k == 'scene': r += self.scene(a['index'], area)
            elif k == 'warp': r += self.warp(a['area'], a['x'], a['y']); area = a['area']
            elif k == 'add_scene_zone': pass                     # played by the warp zone with the same rectangle
            elif k == 'make_hostile': f = QF + x['quest']; self.hostile[(a['area'], a['sprite'])] = f
            elif k == 'set_walkable': self.walks.append((QF + x['quest'], a['area'], a['x1'] // 8, a['y1'] // 8, (a['x2'] + 7) // 8, (a['y2'] + 7) // 8))
            elif k == 'add_warp':
                name = 'warp_q%d' % x['quest']; self.doors[a['area']].append(dict(kind='walk', rect=(a['x1'], a['y1'], a['x2'], a['y2']), list=name))
                self.out += ['list ' + name, 'set_flag %d' % NOOP, 'unless_flag %d w%d_end' % (QF + x['quest'], x['quest'])] + (self.scene(zones[(a['x1'], a['y1'], a['x2'], a['y2'])], a['area']) if (a['x1'], a['y1'], a['x2'], a['y2']) in zones else []) + self.warp(a['to_area'], a['to_x'], a['to_y']) + ['label w%d_end' % x['quest'], 'stop']
            elif k == 'change_actor':
                if self.names[a['sprite']] == 'goku': self.log['player sprite change skipped'] += 1
                else: self.forms[(a['area'], a['sprite'])] = (QF + x['quest'], a['param'])
            elif k == 'end_game': r += ['do call 120 25', 'do call 209', 'do call 119 %d 1 1 232 240; call 121 30' % WORLD]   # native 0xD1 rolls Buu's Fury's credits, as its own ending does; then free roam from Kame House
            elif k in ('learn', 'speed_up'): self.log[k + ' left to the level system'] += 1
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

    def zone(self, x, y): return (x - 10, y - 6, x + 26, y + 24)

    def pickup_lists(self):
        self.out += ['list no_talk', 'set_flag %d' % NOOP, 'stop']
        for n, L in self.pickups.items():
            for p in L:
                self.doors[n].append(dict(kind='walk', rect=self.zone(p['x'], p['y']), list=p['list'])); e = p['flag']; r = ['list ' + p['list'], 'set_flag %d' % NOOP, 'if_flag %d pk_e%d' % (e, e), 'set_flag %d' % e]
                if p['id'] in P.ENERGY: r.append('do energy %d' % P.ENERGY[p['id']])
                else:
                    if p['id'] in P.BF_ITEM: r.append('do call 128 %d' % P.BF_ITEM[p['id']])
                    r.append('narrate ' + P.message(self.rom, p['id']).replace('{', '(').replace('}', ')'))
                self.out += r + ['label pk_e%d' % e, 'stop']

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
                    self.pick[(x['quest'], t['item'])] = t['id']; self.doors[t['area']].append(dict(kind='walk', rect=self.zone(t['x'], t['y']), list='pick_t%d' % t['id']))
                    self.out += ['list pick_t%d' % t['id'], 'set_flag %d' % NOOP, 'if_flag %d p%d' % (TF + t['id'], t['id']), 'set_flag %d' % (TF + t['id'])] + self.add_token(t['id']) + ['narrate ' + P.message(self.rom, t['item']).replace('{', '(').replace('}', ')'), 'run quest_check', 'label p%d' % t['id'], 'stop']
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

    def beaten_flag(self, n, sprite):
        return next((TF + t['id'] for x in self.q for t in x['tasks'] if t['type'] in ('activate', 'defeat') and t['sprite'] == sprite and t['area'] == n), 0)

    def boss_gives_exp(self, n, sprite):
        return any(t['type'] in ('activate', 'defeat') and t['sprite'] == sprite and t['area'] == n and any(a['type'] == 'give_exp' for a in x['actions']) for x in self.q for t in x['tasks'])

    def death_script(self, n, sprite, put):
        """Bytecode run when a story enemy dies: mark its tasks, then run quest_check, which plays the quest's dialogue and warps. None if it has no task."""
        import scenes
        ts = [t for x in self.q for t in x['tasks'] if t['type'] in ('activate', 'defeat') and t['sprite'] == sprite and t['area'] == n]
        if not ts: return None
        return put(scenes.assemble('; '.join('call 29 %d' % (TF + t['id']) for t in ts) + '; call 29 %d' % PENDING, {}) + b'\x11')

    def test_warps(self):
        """One warp list per area for tools/story_test.py, so a fixed build can resume from saved progress."""
        r = []
        for n, a in self.areas.items():
            spot = next(((t['to_x'], t['to_y']) for m in self.areas.values() for t in m['triggers'] if t['kind'] == 'warp' and t['to_area'] == n), None)
            if not spot: spot = next(((b['x'], b['y']) for x in self.q for b in x['actions'] if b['type'] == 'warp' and b['area'] == n), None)
            if not spot: spot = next(((b['to_x'], b['to_y']) for x in self.q for b in x['actions'] if b['type'] == 'add_warp' and b['to_area'] == n), None)
            if not spot: spot = next(((t['x'] - 20, t['y']) for t in a['actors']), (64, 64))
            r += ['list dbg_%d' % n, 'set_flag %d' % NOOP] + self.warp(n, *spot) + ['stop']
        return r

    def zone_lists(self):
        """Walk-in zones: quest zones, artifact spots, LoG1's events, messages, heal zones, warp squares and warps only flying reaches."""
        once = EV; pick_item = {t['item']: t['id'] for x in self.q for t in x['tasks'] if t['type'] == 'spawn_item'}
        for x in self.q:
            for t in x['tasks']:
                i = t.get('id')
                if t['type'] == 'enter_zone':
                    self.doors[t['area']].append(dict(kind='walk', rect=(t['x1'], t['y1'], t['x2'], t['y2'] + (16 if t['y2'] - t['y1'] < 16 else 0)), list='zone_t%d' % i))   # thin zones against a wall: BF's player stops short of LoG1's
                    self.out += ['list zone_t%d' % i, 'set_flag %d' % NOOP, 'if_flag %d zn%d' % (TF + i, i), 'set_flag %d' % (TF + i), 'run quest_check', 'label zn%d' % i, 'stop']
                elif t['type'] == 'obstacle':                           # the spot takes the artifact of the same number
                    self.doors[t['area']].append(dict(kind='walk', rect=(t['x1'] - 8, t['y1'] - 8, t['x2'] + 8, t['y2'] + 8), list='obst_t%d' % i)); need = pick_item.get(t['param'])
                    self.out += ['list obst_t%d' % i, 'set_flag %d' % NOOP, 'if_flag %d ob%d' % (TF + i, i)] + (['unless_flag %d ob%d' % (TF + need, i)] if need is not None else []) + ['set_flag %d' % (TF + i), 'narrate You put the artifact in place.', 'run quest_check', 'label ob%d' % i, 'stop']
        for n, a in self.areas.items():
            for k, t in enumerate(a['triggers']):
                name = 'trg%d_%d' % (n, k); rect = tuple(t['rect'])
                if t['kind'] == 'event':
                    s_ = t['arg']; L = self.sets.get(s_, {})
                    if t['entry'] not in L: continue
                    body, nxt = chain(L, t['entry']); r = self.say(body)
                    if nxt is not None and nxt != t['entry']: r += self.set_state(s_, nxt)
                    for x in self.q:
                        for u in x['tasks']:
                            if u['type'] == 'after_conversation' and u['set'] == s_ and u['entry'] == t['entry']: r += ['set_flag %d' % (TF + u['id']), 'run quest_check']
                    assert once < 800; self.out += ['list ' + name, 'set_flag %d' % NOOP, 'if_flag %d %s_e' % (once, name), 'set_flag %d' % once] + r + ['label %s_e' % name, 'stop']; once += 1
                elif t['kind'] == 'message':
                    txt = self.labels.get(t['text'])
                    if not txt: self.log['message without text'] += 1; continue
                    self.out += ['list ' + name, 'set_flag %d' % NOOP] + ['narrate ' + p for p in split_line(txt.replace('{', '(').replace('}', ')').strip())] + ['stop']
                elif t['kind'] == 'hp_zone':
                    if t['hp'] < 0: self.zones.append((n, rect, -t['hp'], t['mode'])); continue
                    self.out += ['list ' + name, 'set_flag %d' % NOOP, 'do heal', 'stop']
                elif t['kind'] == 'warp' and t['to_area'] in self.areas and (t['to_area'] == n or not t['mode'] & 1 or (n >= 42 and t['to_area'] >= 42)):   # warp squares work from any side
                    self.out += ['list ' + name, 'set_flag %d' % NOOP] + self.warp(t['to_area'], t['to_x'], t['to_y']) + ['stop']
                else: continue
                self.doors[n].append(dict(kind='walk', rect=rect, list=name))

    def generate(self, path):
        chk = self.check_list(); self.talk_lists(); self.place_lists(); self.pickup_lists(); self.zone_lists(); self.out = chk + self.out + world_lists(self.ids) + self.test_warps()
        open(path, 'w', encoding='utf-8').write('\n'.join(self.out) + '\n')
        return dict(lines=sum(l.startswith('say') or l.startswith('narrate') for l in self.out), steps=len(self.out), doors=sum(map(len, self.doors.values())), hostile=len(self.hostile), walks=len(self.walks), flags_state=sum(map(len, self.state.values())), log=dict(self.log))
