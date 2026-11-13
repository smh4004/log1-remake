"""The Earth Dragon Ball hunt (post-game): Bulma's Dragon Radar, seven balls across Earth, Shenron and a wish, then the balls scatter again.

    add_pickups(st)        the seven balls as pickups (walk-over zones), at build-chosen spots
    lists(st)              the summon, the wishes, Bulma's radar talk (talk_prefix)
    talk_prefix(st, s)     lines put first in Bulma's LoG1 talk (set 11)
    later(named)           {flag, list} rows for src/flight.c's live_later (the summon runs once the 7th pickup's list has ended)
    wish_rows(log1, bf, named)   Shenron's choices for src/flight.c's picker: {flag, list, picture}
    ball_image(bf, k)      the k-star ball's pickup picture: Buu's Fury's own Dragon Ball item icon (items 16-22)

How it works: until Bulma hands over the radar, src/skills.c keeps every ball's flag set (found), so none shows; the radar clears them. A ball
picked up sets its flag and adds Buu's Fury's Dragon Ball key item. With all seven the summon runs: the sky goes dark and Shenron asks for a
wish in the picker (src/flight.c wish_ptr). The wish's list sets a flag that src/skills.c acts on (stats, mastery) or gives items or gear,
then DB_SCATTER: the balls lose their flags and the items, and wait at their spots for the next hunt. Shenron has no picture: Buu's Fury,
LoG1 and LoG2 have no sprite of him, and he isn't drawn here. All text here is original.
"""
import collections, json, os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]

NOOP, QF = 895, 420
POSTGAME = QF + 68
DB_RADAR, DB_BALL, DB_SUMMON, DB_WISH_ASK, DB_POWER, DB_MASTERY, DB_SCATTER, DB_GEAR, DB_WISHED = 770, 771, 778, 779, 780, 781, 782, 783, 787
DB_DARK = 796                                # src/flight.c dims the screen while it's set
DB_BALL_B, DB_ROUND = 788, 795               # the balls scatter to a second set of spots after each wish, and back: DB_ROUND says which set is out
BALLS = (DB_BALL, DB_BALL_B)
C_FLAGS = dict(DB_RADAR=DB_RADAR, DB_BALL=DB_BALL, DB_BALL_B=DB_BALL_B, DB_ROUND=DB_ROUND, DB_SCATTER=DB_SCATTER, DB_POWER=DB_POWER, DB_MASTERY=DB_MASTERY)
ITEM = 16                                    # Buu's Fury's Dragon Ball 1 (key item); 2-7 follow
ICONS = [0x3BC89C, 0x3BC914, 0x3BC98C, 0x3BCA08, 0x3BCA84, 0x3BCAFC, 0x3BCB7C]   # their 16x16 icons (items.csv)
AREAS = [2, 4, 5, 9, 16, 22, 23]             # Goku's House, Forest, Village, Crash Site, Wilderness, Military Base, Battlegrounds: one ball each (the City's roads have traffic)
NAMES = {2: "Goku's House", 4: 'the Forest', 5: 'the Village', 9: 'the Crash Site', 16: 'the Wilderness', 22: 'the Military Base', 23: 'the Battlegrounds'}
STARS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']
BULMA_SET = 11
GEAR = [(34, 'Dragon Armor'), (35, 'Super Armor'), (40, 'Saiyan Armor'), (150, "Mercury's Cap")]   # the rare-gear wish, one each time
WISHES = [('power', 'Make me stronger'), ('senzu', 'Senzu Beans'), ('mastery', 'Master my forms'), ('gear', 'Rare gear')]


def narrate(text):
    from convert_log1 import split_line
    return ['say narrator ' + p for p in split_line(text)]


def say(st, who, text, name=None):
    if who == 'goku' or who in st.por: return st.say([dict(who=who, text=text)])
    return narrate('%s: %s' % (name or who.title(), text))


def spots(log1, away=None):
    """One spot per area in AREAS: the reachable point farthest (on foot) from where Goku comes in, kept clear of doors, pickups and people.
    Buu's Fury's 16x8 body box, 4 px steps, as tools/reach_log1.py."""
    import map_convert as C
    A = {n: C.Area(log1, n) for n in range(42) if os.path.exists(os.path.join(log1, 'assets', 'areas', 'area%02d.json' % n))}
    arrive = collections.defaultdict(set)
    for a in A.values():
        arrive[a.n].add(tuple(a.info['start']))
        for t in a.info['triggers']:
            if t['kind'] == 'warp' and t['to_area'] < 42: arrive[t['to_area']].add((t['to_x'], t['to_y']))
    out = {}
    for n in AREAS:
        a = A[n]; walk = a.L['walkable'] > 0
        def fits(x, y):
            if x < 0 or y < 0: return False
            x1, y1 = (x + 23) >> 3, (y + 15) >> 3
            return y1 <= a.H and x1 <= a.W and bool(walk[y >> 3:y1, x >> 3:x1].all())
        dist = {}
        q = collections.deque()
        for s in arrive[n]:
            s = (s[0] - s[0] % 4, s[1] - s[1] % 4)
            if fits(*s) and s not in dist: dist[s] = 0; q.append(s)
        while q:
            x, y = q.popleft()
            for t in ((x + 4, y), (x - 4, y), (x, y + 4), (x, y - 4)):
                if t not in dist and fits(*t): dist[t] = dist[(x, y)] + 1; q.append(t)
        avoid = [((t['rect'][0] + t['rect'][2]) // 2, (t['rect'][1] + t['rect'][3]) // 2, 56) for t in a.info['triggers'] if t['kind'] == 'warp']
        avoid += [(p['x'], p['y'], 40) for p in a.info.get('pickups', [])] + [(p['x'], p['y'], 40) for p in a.info.get('actors', [])]
        if away: avoid.append((away[n][0], away[n][1], 240))                                   # the other set's spot: somewhere new to look
        ok = [(d, p) for p, d in dist.items() if all(abs(p[0] - x) > r or abs(p[1] - y) > r for x, y, r in avoid)
              and all(fits(p[0] + dx, p[1] + dy) for dx in (-8, 8) for dy in (-8, 8))           # a little room around it
              and 48 <= p[0] <= a.W * 8 - 80 and 48 <= p[1] <= a.H * 8 - 64]                       # and off the map's edges
        assert ok, 'no spot for a Dragon Ball in area %d' % n
        out[n] = max(ok)[1]
    return out


def add_pickups(st):
    """The balls as pickups, two sets: walking over one runs its list (log1_story.pickup_lists sets the flag first). src/skills.c keeps the set
    that isn't out flagged as found, so it doesn't show."""
    a = spots(st.log1dir); st.db_spots = [a, spots(st.log1dir, a)]
    for r, base in enumerate(BALLS):
        for k, n in enumerate(AREAS):
            x, y = st.db_spots[r][n]
            side = narrate("Goku found the %s-star Dragon Ball!" % STARS[k]) + ['do call 128 %d' % (ITEM + k)]
            side += ['unless_flag %d db_k%d_%d' % (base + j, r, k) for j in range(7)] + ['set_flag %d' % DB_SUMMON, 'label db_k%d_%d' % (r, k)]
            st.pickups[n].append(dict(x=x, y=y, id=('dragonball', k), flag=base + k, list='pk_db%d_%d' % (r, k), side=side,
                                      rect=(x - 26, y - 22, x + 42, y + 46)))   # wider than a pickup's: the ball's body blocks Goku before he reaches the usual zone


def lists(st):
    S = lambda t: narrate('Shenron: ' + t); G = lambda t: say(st, 'goku', t)
    o = ['list db_summon', 'set_flag %d' % NOOP]
    o += narrate("The seven Dragon Balls begin to glow...") + ['set_flag %d' % DB_DARK] + narrate("The sky goes dark, and the wind stops dead.")
    o += narrate("A huge shape coils up into the clouds, eyes burning red.")
    o += S("YOU WHO HAVE GATHERED THE SEVEN DRAGON BALLS. I SHALL GRANT YOU ONE WISH. SPEAK IT.")
    o += G("Hiya, Shenron! Let me think...") + ['set_flag %d' % DB_WISH_ASK, 'stop']
    end = S("YOUR WISH HAS BEEN GRANTED. FAREWELL.") + ['do call 30 %d' % DB_DARK] + narrate("Shenron is gone, and the sky clears. The Dragon Balls rise into the air and scatter across the Earth. The radar will find them again.")
    end += ['set_flag %d' % DB_WISHED, 'set_flag %d' % DB_SCATTER, 'stop']
    o += ['list db_wish_power', 'set_flag %d' % NOOP] + G("Make me stronger! There's always someone tougher out there.")
    o += S("SO BE IT.") + ['set_flag %d' % DB_POWER] + narrate("Power floods in! Strength, power and endurance each rise by 5.") + end
    o += ['list db_wish_senzu', 'set_flag %d' % NOOP] + G("Senzu Beans! A whole bunch of them!")
    o += S("SO BE IT.") + ['do call 128 11'] * 10 + narrate("A pile of ten Senzu Beans lands at Goku's feet.") + end
    o += ['list db_wish_mastery', 'set_flag %d' % NOOP] + G("Teach my body the Kaioken and Super Saiyan, all the way!")
    o += S("SO BE IT.") + ['set_flag %d' % DB_MASTERY] + narrate("The Kaioken and Super Saiyan are both mastered: Level 3.") + end
    o += ['list db_wish_gear', 'set_flag %d' % NOOP] + G("Something really rare to wear!") + S("SO BE IT.")
    for i, (g, name) in enumerate(GEAR):
        o += ['if_flag %d db_g%d' % (DB_GEAR + i, i), 'set_flag %d' % (DB_GEAR + i), 'do call 147 %d' % g] + narrate("Goku received the %s!" % name) + ['goto db_gd', 'label db_g%d' % i]
    o += ['do call 147 %d' % GEAR[0][0]] + narrate("Goku received another %s!" % GEAR[0][1]) + ['label db_gd'] + end
    return o


def talk_prefix(st, s):
    """Bulma, after the ending: the radar the first time, then where the balls still are."""
    if s != BULMA_SET: return []
    B = lambda t: say(st, 'bulma', t); G = lambda t: say(st, 'goku', t)
    o = ['unless_flag %d db_skip' % POSTGAME, 'if_flag %d db_radar' % DB_RADAR]
    o += B("Goku! With Frieza gone, I finally fixed up the old Dragon Radar. The Earth's Dragon Balls are all out there, waiting.")
    o += G("The Dragon Balls! Can I go find them?")
    o += B("Take it. Gather all seven and Shenron grants a wish. Just don't wish for anything dumb, okay? Ask me if you want a reading.")
    o += ['set_flag %d' % DB_RADAR] + ['do call 30 %d' % (DB_BALL + k) for k in range(7)]
    o += narrate("Goku got the Dragon Radar! The Dragon Balls are hidden around the Earth.") + ['stop']
    o += ['label db_radar'] + B("Let's see what the radar says...") + ['if_flag %d db_rb' % DB_ROUND]
    for r, base in enumerate(BALLS):
        if r: o += ['label db_rb']
        for k, n in enumerate(AREAS):
            o += ['if_flag %d db_r%d_%d' % (base + k, r, k)] + narrate("The radar blinks: a Dragon Ball in %s." % NAMES[n]) + ['label db_r%d_%d' % (r, k)]
        o += ['goto db_rend']
    o += ['label db_rend'] + B("That's everything it picks up. Off you go!") + ['stop', 'label db_skip']
    return o


def later(named): return [(DB_SUMMON, named['db_summon'])]


def wish_rows(log1, bf, named):
    import log1_yardrat
    return [(NOOP, named['db_wish_' + key], log1_yardrat.picker_art(log1, bf, name, "Shenron's wish")[0]) for key, name in WISHES]


def ball_image(bf, k):
    """32x32 picture (Buu's Fury OBJ indices) of the k-star ball, its item icon in the middle."""
    from wfz import decompress_stream
    o = ICONS[k]; t, size = struct.unpack_from('<II', bf, o)
    d = bytes(decompress_stream(bf, o + 8, size)[0]) if t == 1 else bytes(bf[o + 8:o + 8 + size])
    img = np.zeros((32, 32), np.uint8); img[14:30, 8:24] = np.frombuffer(d[:256], np.uint8).reshape(16, 16)
    return img
