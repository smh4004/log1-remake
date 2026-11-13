"""M4: generate LoG1's story up to a chosen quest as Buu's Fury scripts, from extracted data at build time. Output stays in out/.

Flags: quest n = 420 + n, task t = 500 + t, conversation state from 620. A set's state is the entry it starts from next.
Defaults on the review list: no visible followers on escorts, LoG1 pickups mapped to Buu's Fury items (log1_pickups), cutscenes play only
their conversations, and LoG1's music plays through log1_music.
"""
import collections, json, os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from convert_log1 import chain, conversations, split_line  # noqa: E402
import log1_pickups as P  # noqa: E402
from log1_world import takeoff_lists as world_lists  # noqa: E402
import log1_yardrat, log1_party, log1_dragonballs  # noqa: E402
import log1_side  # noqa: E402

QF, TF, EF, TOK, NOOP = 420, 500, 620, 870, 895
PIC_SAVE, PIC_BACK, PIC_FIRST = 896, 897, 54                            # src/flight.c and log1_split: story pictures
PAN = 30                                                                 # frames for a camera pan
NEW_GAME_SPOT = (224, 232)                                                  # where LoG1 puts Goku after its opening (0x0800FEE0)
POSE_FLAG = 960                                                          # src/flight.c's pose table
FLASH_FLAG, MOVIE_FLAG, SPAWN_FLAG = 898, 899, 901                       # src/flight.c: cutscene flash, the two movies, characters that appear mid-scene
MOVIE_LISTS = {0x084E4F20: 0, 0x081CA144: 1}                             # LoG1's lists that play a movie -> src/flight.c's movie
import log1_music  # noqa: E402
MUSIC_BASE = 53                                        # log1_music.BASE: LoG1's songs follow Buu's Fury's 53
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

    def __init__(self, log1, last_quest, ids, portraits, scenes_json, balance=None):
        self.bal = balance
        self.sets = conversations(log1); self.names = [l.split()[1] for l in open(log1 + '/assets/areas/SPRITES.txt')]
        d = json.load(open(log1 + '/assets/story/quests.json')); self.q = [x for x in d['quests'] if x['quest'] <= last_quest]; self.qof = d['quest_of_flag']
        self.ids, self.por, self.log1dir = set(ids), portraits or {}, log1; self.scenes = {s['scene']: s for s in json.load(open(scenes_json))}
        self.scene_spawns = []; self.out = []; self.doors = collections.defaultdict(list); self.walks = []; self.hostile = {}; self.deaths = {}; self.log = collections.Counter(); self.state = {}
        self.pick = {}; self.area_sets = set()
        for n in ids:
            for a in json.load(open('%s/assets/areas/area%02d.json' % (log1, n)))['actors']:
                if a['kind'] != 2: self.area_sets.add(a['param'])
        self.area_sets |= {t['after_set'] for x in self.q for t in x['tasks'] if t['type'] == 'escort' and t['area'] in self.ids}
        self._states(); self._place_groups(); self.rom = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); self.pickups = {}; f = PF
        for n in ids:
            self.pickups[n] = []
            for k, p in enumerate(json.load(open('%s/assets/areas/area%02d.json' % (log1, n)))['pickups']): self.pickups[n].append(dict(p, flag=f, list='pk%d_%d' % (n, k))); f += 1
        assert f <= 340, 'pickup flags overflow'           # side content 340-365; Buu's Fury's world map uses 398-408
        self.areas = {n: json.load(open('%s/assets/areas/area%02d.json' % (log1, n))) for n in ids}; self.labels = dict(l.rstrip('\n').split('\t', 1) for l in open(log1 + '/assets/text/strings.txt', encoding='latin1') if '\t' in l)
        self.forms = {}; self.zones = []; self.move_names = set(); self.pose_rows = []; self.pose_flags = {}; self.placed = self.placed_items()
        self.side = log1_side.Side(self); self.side.add_pickups(); log1_dragonballs.add_pickups(self)
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
            who = 'goku' if l['who'] in ('goku', 'ssgoku', 'gokumallet') else ('#%d' % self.por[l['who']] if l['who'] in self.por else None)   # Goku's forms speak with his face
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
        """Plays a cutscene: dialogue, walks, pictures, movies, music, sound effects, fades, flashes and characters appearing. Poses and sprite swaps go through src/flight.c's pose table."""
        r = []; pic = dark = False; cmds = self.scenes[i]['commands']; appeared = set()
        panned = False; cam = [None]; focus = [None]; where = {}; walked = set(); posed = {}; alias = {}                                    # actors currently holding a pose -> keep it through walks?; LoG1 sprite swapped in -> the actor on the map
        def actor_of(who):
            who = alias.get(who, who); nm = self.names[who] if who < len(self.names) else None
            return nm if nm and (nm == 'goku' or who in appeared or self.movable(area, who)) else None
        def pose(who, src, row, keep=False):
            """Shows LoG1 frame `row` of sprite `src` on an actor. Row 0 of its own sprite is its usual standing frame, so that just lets go of any pose."""
            nm = actor_of(who)
            if nm is None: return False
            if src == nm and row == 0: unpose(nm, True); return True
            r.append('do call 29 %d; call 136 2' % self.pose_flag(nm, src, row)); posed[nm] = keep
            return True
        def unpose(nm, swaps=False):
            if nm in posed and (swaps or not posed[nm]): r.append('do call 29 %d; call 136 2' % self.pose_flag(nm, None, 0)); del posed[nm]
        if area is None: area = self.home_area(i)
        def back():
            sx, sy = self.areas[area]['start'] if area in self.areas else (8, 8)
            return 'do call 120 15; call 119 26 %d 1 %d %d; call 29 %d; call 136 2; call 121 15' % ((area or 0) + 1, sx, sy, PIC_BACK)
        def light():
            nonlocal dark
            if dark and not pic: r.append('do call 121 15')
            dark = False
        for k, c in enumerate(cmds):
            b = bytes.fromhex(c['raw']); f = c['fn']
            if f == '0800CC61': light(); r += self.say(chain(self.sets[b[0]], b[1])[0]); continue
            if f == '0800CC75':                                  # a full-screen picture; the dialogue that follows draws over it
                if k and cmds[k - 1]['fn'] == '0800CA69' and bytes.fromhex(cmds[k - 1]['raw'])[:4] and b[0] == getattr(self, '_after_movie', None): self._after_movie = None; continue
                r.append('do ' + ('call 29 %d; call 136 2; ' % PIC_SAVE if not pic else '') + 'call 120 15; call 119 26 %d 1 8 8; call 121 15' % (PIC_FIRST + b[0] + 1)); pic = True; dark = False
                nxt = next((x['fn'] for x in cmds[k + 1:] if x['fn'] != '0800D26D'), None)
                if nxt != '0800CC61': r.append('do call 136 150')
                continue
            if f == '0800E065':                                  # back to the map
                if pic:
                    r.append(back()); pic = False
                    if cam[0]: r.append(cam[0])                        # the map reloaded, so the camera is back on Goku
                continue
            if f == '0800CA69':                                  # a movie, then whatever comes next as a backdrop for its closing text
                m = MOVIE_LISTS[struct.unpack_from('<I', b)[0]]; nx = next((x for x in cmds[k + 1:] if x['fn'] == '0800CC75'), None)
                r.append('do ' + ('call 29 %d; call 136 2; ' % PIC_SAVE if not pic else '') + 'call 120 1; call 29 %d; call 136 4' % (MOVIE_FLAG + m)); pic = True
                if nx is not None: self._after_movie = bytes.fromhex(nx['raw'])[0]; r.append('do call 119 26 %d 1 8 8; call 121 15' % (PIC_FIRST + self._after_movie + 1))
                else: r.append(back()); pic = False
                dark = False; continue
            if f == '0800E079': r.append('do call 35 %d' % (MUSIC_BASE + b[0])); continue
            if f == '0800D26D': r.append('do call 31 %d' % (log1_music.SFX_BASE + struct.unpack_from('<I', b)[0])); continue
            if f == '0800CD29':                                  # fade to black
                if not dark: r.append('do call 120 64'); dark = True
                continue
            if f == '0800CDAF': r.append('do call 29 %d; call 136 30' % FLASH_FLAG); continue    # a white flash
            if f == '0800CC03':                                  # the camera pans to a character, or where they're about to appear
                who = alias.get(b[0], b[0]); nm = actor_of(who); light(); m_ = self.movable(area, who) if nm != 'goku' else None
                spot = where.get(who) or (m_ and m_.get('x') is not None and (m_['x'], m_['y'])) or next((struct.unpack_from('<HH', bytes.fromhex(l['raw']), 0) for l in cmds[k + 1:] if l['fn'] == '0800CAC9' and struct.unpack_from('<H', bytes.fromhex(l['raw']), 4)[0] == who), None)
                if nm == 'goku': cam[0] = 'do call 49 0 %d' % PAN
                elif spot and area in self.areas: cam[0] = 'do call 50 %d %d %d' % (max(0, spot[0] - 120), max(0, spot[1] - 80), PAN)   # by position: a character who isn't on the map would crash the actor commands
                else: r.append('do call 136 20'); continue
                r.append(cam[0]); panned = True; focus[0] = who; continue
            if f in ('0800CA75', '0800DC49') and len(b) >= 2:    # an animation frame; CA75 waits for it
                who = alias.get(b[0], b[0]); nm = self.names[who] if who < len(self.names) else None
                if nm:
                    light(); kept = pose(who, self.names[b[0]], b[1], who != b[0])
                    if not kept: self.log['scene pose on someone not on the map'] += 1
                    elif f == '0800CA75': r.append('do call 136 30')
                continue
            if f == '0800DC0D':                                  # a sprite swap: Vegeta to his Great Ape and back
                who = alias.get(b[0], b[0]); home = who == b[1]; alias.pop(b[0], None)
                if not home: alias[b[1]] = who
                light(); pose(who, self.names[b[1]], 0, not home); continue
            if f == '0800DC8B':                                  # turn to a direction
                nm = actor_of(b[0])
                if nm: light(); self.move_names.add(nm) if nm != 'goku' else None; r.append('do call 83 %s %d; call 136 8' % ('0' if nm == 'goku' else nm, b[1]))
                continue
            if f in ('0800CAC9', '0800CDF5'):                    # a character appears, standing where their first walk would take them
                who = struct.unpack_from('<H', b, 4)[0]; x, y = struct.unpack_from('<HH', b, 0); nm = self.names[who] if who < len(self.names) else None
                if f == '0800CDF5':
                    near = self.movable(area, struct.unpack_from('<H', b, 0x10)[0]) if len(b) >= 0x18 else None
                    if near and near.get('x') is not None: x, y = near['x'] + struct.unpack_from('<h', b, 0x14)[0], near['y'] + struct.unpack_from('<h', b, 0x16)[0]
                for later in cmds[k + 1:]:
                    lb = bytes.fromhex(later['raw'])
                    if later['fn'] == '0800CB25' and lb[0] == who: x, y = struct.unpack_from('<HH', lb, 4); break
                if nm == 'goku' or self.movable(area, who): continue    # already on the map: walking it to where a copy stands would never finish
                if nm and area in self.areas and x and y:
                    appeared.add(who); where[who] = (x, y); flag = SPAWN_FLAG + 2 * len(self.scene_spawns); self.scene_spawns.append((area, flag, nm, x, y, flag + 1)); light(); r.append('do call 29 %d; call 136 10' % flag); self._scene_end = getattr(self, '_scene_end', []) + [flag + 1]; continue
            if f == '0800DF15':                                  # the closing text
                a_ = struct.unpack_from('<I', b)[0] & 0x1FFFFFF; r += ['narrate ' + p for p in split_line(self.rom[a_:self.rom.index(b'\0', a_)].decode('latin1').replace('{', '(').replace('}', ')').strip())]; continue
            if f == '0800CB25' or f == '0800D9C5':
                who = alias.get(b[0], b[0]); swapped = who != b[0]
                a = self.movable(area, who) or (dict() if who in appeared else None)
                if f == '0800CB25':
                    x, y = struct.unpack_from('<HH', b, 4)
                    if who in appeared and who not in walked: walked.add(who); a = None   # a character who appeared this scene already stands at the end of their first walk
                else:
                    t = alias.get(b[2], b[2]); o = self.movable(area, t); spot = where.get(t) or (o and o.get('x') is not None and (o['x'], o['y']))
                    if not spot: a = None                               # no fixed spot to walk to
                    else: x, y = spot[0] + struct.unpack_from('<h', b, 4)[0], spot[1] + struct.unpack_from('<h', b, 6)[0]
                if a is not None:
                    light(); nm = self.names[who]; where[who] = (x, y)
                    if panned and (swapped or who == focus[0]) and nm != 'goku':     # the camera doesn't follow a character, so it goes to where they're heading first, and they walk into shot
                        cam[0] = 'do call 50 %d %d %d' % (max(0, x - 120), max(0, y - 80), PAN); r.append(cam[0]); focus[0] = who
                    unpose(nm)
                    if nm == 'goku': r.append('do call 56; call 96 0 %d %d; call 58' % (x, y)); continue
                    self.move_names.add(nm); r.append('do call 56; call 96 %s %d %d; call 58' % (nm, x, y)); continue
            self.log['scene command skipped'] += 1
        if pic: r.append(back())
        elif dark: r.append('do call 121 15')
        for nm in list(posed): unpose(nm, True)
        if panned: r.append('do call 49 0 %d; call 51 0' % PAN)
        for fl in getattr(self, '_scene_end', []): r.append('do call 29 %d' % fl)
        self._scene_end = []
        return r

    def pose_flag(self, actor, src, row):
        """The flag that makes src/flight.c hold this pose on an actor, or let go when src is None."""
        k = (actor, src, row)
        if k not in self.pose_flags:
            self.pose_flags[k] = POSE_FLAG + len(self.pose_flags); assert self.pose_flags[k] < 1024; self.pose_rows.append((self.pose_flags[k], actor, src, row))
        return self.pose_flags[k]

    def home_area(self, i):
        """The area a scene with no task area plays in: where its first character stands."""
        for c in self.scenes[i]['commands']:
            b = bytes.fromhex(c['raw'])
            if c['fn'] in ('0800CB25', '0800CA75', '0800D9C5', '0800CC03') and b:
                nm = self.names[b[0]] if b[0] < len(self.names) else None
                for n, a in self.areas.items():
                    if any(x['sprite'] == nm for x in a['actors']): return n
        return None

    def actions(self, x):
        r = []; area = next((t['area'] for t in x['tasks'] if t.get('area', 255) != 255), None); zones = {(a['x1'], a['y1'], a['x2'], a['y2']): a['scene'] for a in x['actions'] if a['type'] == 'add_scene_zone'}
        for a in x['actions']:
            k = a['type']
            if k == 'give_exp': r.append('do call 194 %d' % self.bal.quest_exp(area if area is not None else 0, any(t['type'] in ('activate', 'defeat') for t in x['tasks'])))
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
            elif k == 'music': r.append('do call 35 %d' % (MUSIC_BASE + a['track']))
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
        r += ['run side_check', 'stop']
        return r

    def zone(self, x, y): return (x - 10, y - 6, x + 26, y + 24)

    def pickup_lists(self):
        self.out += ['list no_talk', 'set_flag %d' % NOOP, 'stop']
        for n, L in self.pickups.items():
            for p in L:
                self.doors[n].append(dict(kind='walk', rect=p.get('rect') or self.zone(p['x'], p['y']), list=p['list'])); e = p['flag']; r = ['list ' + p['list'], 'set_flag %d' % NOOP, 'if_flag %d pk_e%d' % (e, e), 'set_flag %d' % e]
                if 'side' in p: r += p['side']
                elif p['id'] in P.ENERGY: r.append('do energy %d' % P.ENERGY[p['id']])
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
            L = self.sets[s]; r = ['list talk_set%02d' % s, 'set_flag %d' % NOOP] + (log1_yardrat.king_kai(self) if s == log1_yardrat.KK_SET else []) + log1_party.talk_prefix(self, s) + log1_dragonballs.talk_prefix(self, s)
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

    def bal_level(self, n):
        import log1_balance
        return log1_balance.STAGE.get(n, 10)

    def test_warps(self):
        """One warp list per area for tools/story_test.py, so a fixed build can resume from saved progress."""
        r = []
        for n, a in self.areas.items():
            spot = next(((t['to_x'], t['to_y']) for m in self.areas.values() for t in m['triggers'] if t['kind'] == 'warp' and t['to_area'] == n), None)
            if not spot: spot = next(((b['x'], b['y']) for x in self.q for b in x['actions'] if b['type'] == 'warp' and b['area'] == n), None)
            if not spot: spot = next(((b['to_x'], b['to_y']) for x in self.q for b in x['actions'] if b['type'] == 'add_warp' and b['to_area'] == n), None)
            if not spot and n == log1_yardrat.AREA: spot = tuple(a['start'])
            if not spot: spot = next(((t['x'] - 20, t['y']) for t in a['actors']), (64, 64))
            r += ['list dbg_%d' % n, 'set_flag %d' % NOOP] + self.warp(n, *spot) + ['stop']
            if self.bal: r += ['list dbgx_%d' % n, 'set_flag %d' % NOOP, 'do call 194 %d' % self.bal.exp[self.bal_level(n) + 1], 'stop']
        if os.environ.get('SCENE_TEST'):                                     # test builds only: each cutscene as a list of its own
            for k,c in enumerate(['call 136 30','call 60 0 0','call 60 0 32','call 56; call 60 0 32; call 58','call 81 0 32 30','call 56; call 81 0 32 30; call 58','call 56; call 96 0 300 256; call 58','call 83 0 2']): r += ['list dbgscene_t%d'%k,'set_flag %d'%NOOP,'do '+c,'set_flag %d'%(860+k),'stop']
            for x in self.q:
                area = next((t['area'] for t in x['tasks'] if t.get('area', 255) != 255), None)
                for a in x['actions']:
                    if a['type'] == 'scene': r += ['list dbgscene_%d' % a['index'], 'set_flag %d' % NOOP] + self.scene(a['index'], area) + ['stop']
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
                    if t['hp'] < 0: self.zones.append((n, rect, max(1, -t['hp'] // 10), t['mode'])); continue   # LoG1's numbers would take a third of early HP a second
                    self.out += ['list ' + name, 'set_flag %d' % NOOP, 'do heal', 'stop']
                elif t['kind'] == 'warp' and t['to_area'] in self.areas and (t['to_area'] == n or not t['mode'] & 1 or (n >= 42 and t['to_area'] >= 42)):   # warp squares work from any side
                    self.out += ['list ' + name, 'set_flag %d' % NOOP] + self.warp(t['to_area'], t['to_x'], t['to_y']) + ['stop']
                else: continue
                self.doors[n].append(dict(kind='walk', rect=rect, list=name))

    def generate(self, path):
        self.out += ['list new_game_opening', 'set_flag %d' % NOOP, 'do call 120 1; call 29 958; call 136 4', 'do call 119 26 1 1 %d %d; call 136 2; call 121 15' % NEW_GAME_SPOT, 'stop']
        self.out += ['list game_saved', 'narrate Game saved.']
        chk = self.check_list(); self.talk_lists(); self.place_lists(); self.pickup_lists(); self.zone_lists(); self.out = chk + self.out + world_lists(self.ids) + self.test_warps() + self.side.lists() + log1_yardrat.lists(self, self.log1dir) + log1_party.lists(self) + log1_dragonballs.lists(self)
        open(path, 'w', encoding='utf-8').write('\n'.join(self.out) + '\n')
        return dict(lines=sum(l.startswith('say') or l.startswith('narrate') for l in self.out), steps=len(self.out), doors=sum(map(len, self.doors.values())), hostile=len(self.hostile), walks=len(self.walks), flags_state=sum(map(len, self.state.values())), log=dict(self.log))
