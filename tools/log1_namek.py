"""Expanded Namek (post-game): Elder Moori's village and the highlands on the way there, his two requests, and Porunga's three wishes.
All text here is original; no art is stored (the new areas are LoG1's own maps in new colours, made at build time).

After the ending the Namekians are home. East of the landing village (area 24) a path climbs into the Namek Highlands (area 72: LoG1's
area 40, the rocky ground of Frieza's last fight, in cool highland colours), and past them lies Elder Moori's Village (area 71: LoG1's
area 31, three Namekian houses, at sunset), with two houses to visit (73, 74: LoG1's 32 and 33). Moori asks two things:
    Frieza's stragglers: three squads of his soldiers still hide in the highlands. Beat all six; Moori gives Goku the Saiyan Boots they left.
    The lost children: three Namekian children wandered off into the highlands. Find each and send him home; Moori's healers give Goku
        three Senzu Beans.
With both done, Moori calls Porunga with the Namekian Dragon Balls, and Porunga grants three wishes (src/flight.c's picker, as Shenron's).

    add_areas(L)                before the areas are built: writes areas 71-74 into the converted LoG1 data
    lists(st)                   talks, the doors between areas, Porunga and his wishes
    checks(st)                  lines for side_check (the last straggler down)
    install(n, a, ...)          each area's people, enemies and edge doors (as log1_side.install)
    porunga_rows(log1, bf, named)   Porunga's choices for src/flight.c's picker: {flag, list, picture}
Flags 920-939 (scene spawn flags stop below 920) and 981-989.
"""
import json, os, re, struct, sys, colorsys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]

NOOP, QF = 895, 420
POSTGAME = QF + 68
VILLAGE, HIGHLANDS, HOUSE_A, HOUSE_B, LANDING = 71, 72, 73, 74, 24
SOURCE = {VILLAGE: 31, HIGHLANDS: 40, HOUSE_A: 32, HOUSE_B: 33}
MUSIC = {VILLAGE: 8, HIGHLANDS: 5, HOUSE_A: 8, HOUSE_B: 8}           # LoG1's Namek village song; the highlands get Namek's open-country song
START = {VILLAGE: (56, 584), HIGHLANDS: (40, 296), HOUSE_A: (176, 136), HOUSE_B: (176, 136)}
NAMES = {VILLAGE: "Moori's Village", HIGHLANDS: 'Namek Highlands', HOUSE_A: "Moori's Village", HOUSE_B: "Moori's Village"}

MET, Q1_OPEN, Q1_PAID, Q2_PAID, PG_DONE, HINT = 920, 921, 922, 923, 924, 925
STRAGGLER = 926                                  # six: 926-931
FOUND = 932                                      # three: 932-934
SAID_DONE = 935                                  # the last straggler's line
PG_ASK, PG_W1, PG_W2 = 981, 982, 983             # src/flight.c porunga_ask; the wishes so far
DB_DARK, DB_POWER, DB_MASTERY, DB_GEAR = 796, 780, 781, 783
SAIYAN_BOOTS, SENZU = 107, 11

MOORI = dict(sprite='guru', at=(470, 196), look='moori')                  # on the open green east of the first house (a roof hides anyone behind it)
HOME = [(436, 236), (476, 236), (516, 236)]                           # where the children stand once they're home
VILLAGERS = [dict(area=VILLAGE, sprite='namekian1', at=(176, 216), talk="Elder Moori says you saved all of Namek. Twice! Or was it once, and very loudly?"),
             dict(area=VILLAGE, sprite='namekian2', at=(780, 300), talk="We planted new Ajissa trees the day we came home. In a hundred years this whole valley will be green again."),
             dict(area=HOUSE_A, sprite='namekian3', at=(120, 96), talk="Make yourself at home. Namekians only drink water, so I'm afraid there's nothing else to offer you."),
             dict(area=HOUSE_B, sprite='namekian4', at=(220, 96), talk="When the Dragon Balls are idle, the Elder keeps them in a stone box under the floor. Don't tell anyone I said that.")]
KIDS = [dict(at=(220, 230), look='kid1', robe=(120, 170, 255), name='Cargo', line="I was chasing a Namek frog and now I don't know where I am..."),
        dict(at=(560, 300), look='kid2', robe=(255, 150, 120), name='Pine', line="I wanted to see the place where Frieza fought. It's just rocks."),
        dict(at=(780, 560), look='kid3', robe=(150, 230, 140), name='Ruu', line="The others dared me to sleep out here. I don't like the noises.")]
SQUADS = [[(330, 150), (370, 170)], [(640, 420), (680, 440)], [(860, 230), (880, 270)]]
SOLDIERS = ['hench2', 'hench4', 'hench6']


def tone(kind):
    """A tile palette's new colours: 'sunset' for the village (blue ground to sea-green, green sea to deep teal, sand to gold, rocks warm),
    'highlands' (blue ground to pale lavender-grey stone, green to dark pine, brown cliffs to slate)."""
    def f(pal):
        out = []
        for r, g, b in pal:
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); d = h * 360
            if s > 0.15:
                if kind == 'sunset':
                    if 170 <= d <= 250: h, s, v = 165 / 360, s * 0.75, v * 0.95
                    elif 70 <= d < 170: h, s, v = 185 / 360, s * 0.85, v * 0.7
                    elif 45 <= d < 70: h, s = 40 / 360, min(1, s * 1.15)
                    else: h, v = (d + 12) % 360 / 360, v * 0.95
                else:
                    if 170 <= d <= 250: h, s, v = 255 / 360, s * 0.35, min(1, v * 1.02)
                    elif 70 <= d < 170: h, s, v = 150 / 360, s * 0.7, v * 0.6
                    elif d < 45 or d > 330: h, s, v = 220 / 360, s * 0.3, v * 0.8
            out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v)))
        return out
    return f


def add_areas(L):
    """Areas 71-74 in the converted data: the source maps with recoloured tiles; the village's houses lead into 73 and 74, which lead back."""
    from PIL import Image
    M = os.path.join(L, 'assets', 'maps')
    for n, src in SOURCE.items():
        t = tone('highlands' if n == HIGHLANDS else 'sunset')
        for f in os.listdir(os.path.join(M, 'tiles')):
            m = re.match(r'area%02d(_block\d+)?\.png$' % src, f)
            if not m: continue
            im = Image.open(os.path.join(M, 'tiles', f)); assert im.mode == 'P'
            pal = im.getpalette(); rgb = [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]
            out = im.copy(); out.putpalette([c for x in t(rgb) for c in x]); out.save(os.path.join(M, 'tiles', 'area%02d%s.png' % (n, m.group(1) or '')))
        tmx = open(os.path.join(M, 'area%02d.tmx' % src)).read()
        tmx = tmx.replace('tiles/area%02d' % src, 'tiles/area%02d' % n).replace('name="area%02d"' % src, 'name="area%02d"' % n)
        tmx = tmx.replace('<property name="area" type="int" value="%d"/>' % src, '<property name="area" type="int" value="%d"/>' % n)
        open(os.path.join(M, 'area%02d.tmx' % n), 'w').write(tmx)
        info = json.load(open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % src)))
        redirect = {32: HOUSE_A, 33: HOUSE_B, 31: VILLAGE}
        doors = [dict(t, to_area=redirect[t['to_area']]) for t in info['triggers'] if t['kind'] == 'warp' and t['to_area'] in redirect]
        json.dump(dict(info, area=n, actors=[], pickups=[], objects=[], triggers=doors, start=list(START[n]), music=MUSIC[n]),
                  open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % n), 'w'))


def edge(a, fits, side, y0, y1):
    """A walk-in rectangle at the map's west or east edge, over the rows y0-y1: from the edge to just inside the farthest ground Goku can
    stand on there (positions are a 16x8 footprint's corner), and a spot a little further in, to arrive at coming the other way."""
    W = a.W * 8
    xs = [x for x in range(0, W, 4) for y in range(y0, y1, 4) if fits(a, x, y)]
    assert xs, (a, side, y0, y1)
    if side == 'west':
        x = min(xs); ys = [y for y in range(y0, y1, 4) if fits(a, x, y)]; y = ys[len(ys) // 2]
        return (0, y0, x + 4, y1), (x + 24, y)
    x = max(xs); ys = [y for y in range(y0, y1, 4) if fits(a, x, y)]; y = ys[len(ys) // 2]
    return (x - 3, y0, W, y1), (x - 24, y)


# the doors between areas: (area, side, rows) -> (area, side, rows); filled in by install() as each area is built
PATHS = [((LANDING, 'east', (200, 330)), (HIGHLANDS, 'west', (230, 340))), ((HIGHLANDS, 'east', (340, 430)), (VILLAGE, 'west', (540, 620)))]
EDGES = {}                                                          # (area, side) -> (rect, arrival)


def say(st, who, text):
    from convert_log1 import split_line
    if who == 'narrator': return ['say narrator ' + p for p in split_line(text)]
    return st.say([dict(who=who, text=text)])


def narrate(text): return say(None, 'narrator', text)


def lists(st):
    o = []; S = lambda who, t: say(st, who, t)
    G = lambda t: S('goku', t); E = lambda t: S('moori', t); P = lambda t: narrate('Porunga: ' + t)
    # the doors: each edge warps to the edge it faces (arrival spots come from install(), which runs after the lists: see door_lists)
    # the hint on landing, once
    o += ['list nm_hint', 'set_flag %d' % NOOP, 'unless_flag %d nm_hint_e' % POSTGAME, 'if_flag %d nm_hint_e' % HINT, 'set_flag %d' % HINT]
    o += narrate("A Namekian waves from a doorway: \"Elder Moori has been hoping you'd come. His village is past the highlands, east of here.\"")
    o += ['label nm_hint_e', 'stop']
    # Elder Moori
    o += ['list nm_moori', 'set_flag %d' % NOOP, 'if_flag %d nm_m1' % MET]
    o += E("Son Goku. Welcome. I am Moori, elder of this village. Every Namekian alive owes you our home.")
    o += G("Aw, it was nothing. Well, it was something. Is everybody doing okay out here?")
    o += E("Mostly. But two things trouble me. A few of Frieza's soldiers were left behind, and they hide in the highlands and raid our gardens.")
    o += E("And three of our children have wandered off into those same highlands. Cargo, Pine and Ruu. If you see them, send them home.")
    o += G("Leave it to me!") + ['set_flag %d' % MET, 'set_flag %d' % Q1_OPEN] + narrate("Elder Moori's requests: drive off Frieza's stragglers, and find the three lost children.") + ['stop']
    o += ['label nm_m1', 'if_flag %d nm_m2' % Q1_PAID] + ['unless_flag %d nm_m2' % (STRAGGLER + i) for i in range(6)]
    o += E("The soldiers are gone? Then our gardens are safe. They left these behind. Their armour never fit a Namekian anyway.")
    o += ['do call 147 %d' % SAIYAN_BOOTS, 'set_flag %d' % Q1_PAID] + narrate("Goku received the Saiyan Boots!") + ['goto nm_m4']
    o += ['label nm_m2', 'if_flag %d nm_m3' % Q2_PAID] + ['unless_flag %d nm_m3' % (FOUND + i) for i in range(3)]
    o += E("All three children are home, scolded and fed. Our healers want you to have these. Senzu Beans travel well, they tell me.")
    o += ['do call 128 %d' % SENZU] * 3 + ['set_flag %d' % Q2_PAID] + narrate("Goku received three Senzu Beans!") + ['goto nm_m4']
    o += ['label nm_m3', 'unless_flag %d nm_m5' % Q1_PAID, 'unless_flag %d nm_m5' % Q2_PAID, 'if_flag %d nm_m6' % PG_DONE, 'goto nm_pg']
    o += ['label nm_m4', 'unless_flag %d nm_m5' % Q1_PAID, 'unless_flag %d nm_m5' % Q2_PAID, 'if_flag %d nm_m6' % PG_DONE]
    o += ['label nm_pg'] + E("You have done everything I asked and more. We have gathered our Dragon Balls again. Let Porunga thank you properly.")
    o += narrate("Moori sets out seven Dragon Balls, each the size of a boulder, and calls out in the old Namekian tongue.")
    o += ['set_flag %d' % DB_DARK] + narrate("The sky goes black. A towering figure with great horns and folded arms rises over the village.")
    o += P("I AM PORUNGA. I WILL GRANT ANY THREE WISHES WITHIN MY POWER. SPEAK THE FIRST.") + G("Three?! Shenron only gives one!")
    o += ['do call 30 %d' % PG_W1, 'do call 30 %d' % PG_W2, 'set_flag %d' % PG_ASK, 'stop']
    o += ['label nm_m5']
    o += ['if_flag %d nm_m5a' % Q1_PAID] + E("Frieza's stragglers still hide in the highlands. There are six of them.") + ['label nm_m5a']
    o += ['if_flag %d nm_m5b' % Q2_PAID] + E("Cargo, Pine and Ruu are still out in the highlands. Please, find them.") + ['label nm_m5b', 'stop']
    o += ['label nm_m6'] + E("Rest here whenever you like, Goku. This village will always be glad to see you.") + ['stop']
    # Porunga's wishes: each grants, then asks for the next, or says farewell after the third
    for key, line, grant in WISH_LINES:
        lab = 'nm_w_' + key
        o += ['list ' + lab, 'set_flag %d' % NOOP] + G(line) + P("IT SHALL BE DONE.") + grant(st)
        o += ['if_flag %d %s_3' % (PG_W2, lab), 'if_flag %d %s_2' % (PG_W1, lab), 'set_flag %d' % PG_W1] + P("SPEAK YOUR SECOND WISH.") + ['set_flag %d' % PG_ASK, 'stop']
        o += ['label %s_2' % lab, 'set_flag %d' % PG_W2] + P("SPEAK YOUR LAST WISH.") + ['set_flag %d' % PG_ASK, 'stop']
        o += ['label %s_3' % lab] + P("YOUR WISHES ARE GRANTED. FAREWELL.") + ['do call 30 %d' % DB_DARK, 'set_flag %d' % PG_DONE]
        o += narrate("Porunga is gone, and the Dragon Balls turn to grey stone. In a year they'll wake again.") + ['stop']
    # villagers and the children
    for i, v in enumerate(VILLAGERS): o += ['list nm_v%d' % i, 'set_flag %d' % NOOP] + S('narrator', v['talk']) + ['stop']
    for i, k in enumerate(KIDS):
        o += ['list nm_k%d' % i, 'set_flag %d' % NOOP, 'if_flag %d nm_k%d_e' % (FOUND + i, i)] + narrate('%s: %s' % (k['name'], k['line']))
        o += G("Elder Moori's looking for you! Head straight home, okay? I'll keep the path clear.") + narrate("%s runs off toward the village." % k['name'])
        o += ['set_flag %d' % (FOUND + i), 'label nm_k%d_e' % i, 'stop']
        o += ['list nm_kh%d' % i, 'set_flag %d' % NOOP] + narrate("%s: Thanks for finding me, Goku! I'm never going out there again. Probably." % k['name']) + ['stop']
    return o


def _gear(st):
    import log1_dragonballs as D
    o = []
    for i, (g, name) in enumerate(D.GEAR):
        o += ['if_flag %d nm_g%d_%%s' % (DB_GEAR + i, i), 'set_flag %d' % (DB_GEAR + i), 'do call 147 %d' % g] + narrate("Goku received the %s!" % name) + ['goto nm_gd_%s']
        o += ['label nm_g%d_%%s' % i]
    o += ['do call 147 %d' % D.GEAR[0][0]] + narrate("Goku received another %s!" % D.GEAR[0][1]) + ['label nm_gd_%s']
    return o


WISH_LINES = [('power', "Make me stronger!", lambda st: ['set_flag %d' % DB_POWER] + narrate("Power floods in! Strength, power and endurance each rise by 5.")),
              ('senzu', "Senzu Beans, please! Lots!", lambda st: ['do call 128 %d' % SENZU] * 10 + narrate("Ten Senzu Beans fall out of the sky.")),
              ('mastery', "Make my Kaioken and Super Saiyan perfect!", lambda st: ['set_flag %d' % DB_MASTERY] + narrate("The Kaioken and Super Saiyan are both mastered: Level 3.")),
              ('gear', "Something really rare to wear!", lambda st: [l.replace('%s', 'w') for l in _gear(st)])]
WISHES = [('power', 'Make me stronger'), ('senzu', 'Senzu Beans'), ('mastery', 'Master my forms'), ('gear', 'Rare gear')]


def porunga_rows(log1, bf, named):
    import log1_yardrat
    return [(NOOP, named['nm_w_' + key], log1_yardrat.picker_art(log1, bf, name, "Porunga's wish")[0]) for key, name in WISHES]


def checks(st):
    """In side_check: the last straggler down."""
    o = ['if_flag %d nm_c1' % SAID_DONE] + ['unless_flag %d nm_c1' % (STRAGGLER + i) for i in range(6)] + ['set_flag %d' % SAID_DONE]
    o += narrate("That was the last of Frieza's stragglers. Elder Moori will want to hear about it.") + ['label nm_c1']
    return o


def kid_tint(robe):
    """A Namekian child in his own robe colour: green skin and outlines kept."""
    def f(pal):
        out = pal.copy()
        for i, (r, g, b) in enumerate(pal):
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); d = h * 360
            if v < 0.2 or s < 0.15 or 70 <= d <= 170: continue                              # outlines, whites, green skin
            nh, ns, nv = colorsys.rgb_to_hsv(*(c / 255 for c in robe)); out[i] = [int(round(c * 255)) for c in colorsys.hsv_to_rgb(nh, ns, nv * (0.5 + 0.5 * v))]
        return out
    return f


def install(n, a, fits, r, actors, put, named, spawns, foe, walkins, BF_IDX, spot, npc_rec):
    """This area's Namek content. spot(x, y): the nearest place an actor fits; npc_rec(sprite, x, y, talk, tint, look) -> (record, actor)."""
    for (fa, fs, fr), (ta, ts, tr) in PATHS:                       # the doors along the way, both directions
        for (sa, ss, sr), (da, ds, dr) in (((fa, fs, fr), (ta, ts, tr)), ((ta, ts, tr), (fa, fs, fr))):
            if n == sa:
                rect, _ = EDGES[(sa, ss)]; walkins.append((n,) + rect + (named['nm_door_%d_%s' % (sa, ss)],))
    if n == LANDING: walkins.append((n, 0, 0, a.W * 8, a.H * 8, named['nm_hint']))
    if n == VILLAGE:
        x, y = spot(*MOORI['at']); rec, _ = npc_rec(MOORI['sprite'], x, y, named['nm_moori'], None, MOORI['look']); spawns.append((POSTGAME, n, rec, 0, 0))
        for i, k in enumerate(KIDS):                                 # home, once found
            x, y = spot(*HOME[i]); rec, _ = npc_rec('namekboy', x, y, named['nm_kh%d' % i], kid_tint(k['robe']), k['look'] + '_home')
            spawns.append((FOUND + i, n, rec, 0, 0))
    for i, v in enumerate(VILLAGERS):
        if v['area'] == n: x, y = spot(*v['at']); rec, _ = npc_rec(v['sprite'], x, y, named['nm_v%d' % i], None, None); spawns.append((POSTGAME, n, rec, 0, 0))
    if n == HIGHLANDS:
        for i, k in enumerate(KIDS):                                 # out in the highlands until found, then gone
            x, y = spot(*k['at']); rec, idx = npc_rec('namekboy', x, y, named['nm_k%d' % i], kid_tint(k['robe']), k['look'])
            spawns.append((MET, n, rec, 0, FOUND + i)); spawns.append((FOUND + i, n, 0, idx, 0))
        for s, squad in enumerate(SQUADS):
            for j, at in enumerate(squad):
                k = STRAGGLER + 2 * s + j
                foe(SOLDIERS[s], at[0], at[1], 'set:%d & clear:%d' % (Q1_OPEN, k), k, 6 + 2 * s, False, 41)
        for at, sprite in (((200, 420), 'ptero2'), ((480, 200), 'trex'), ((720, 330), 'ptero2'), ((420, 520), 'trex'), ((880, 470), 'ptero2')):
            foe(sprite, at[0], at[1], 'set:%d' % POSTGAME, NOOP, 4, False, 41)


def door_lists(st):
    """The edge doors' lists: each warps to the edge it faces (the edges are worked out here, before install() needs them)."""
    import map_convert as MC
    from log1_areas import fits
    areas = {n: MC.Area(st.log1dir, n) for n in (LANDING, HIGHLANDS, VILLAGE)}
    for (fa, fs, fr), (ta, ts, tr) in PATHS:
        EDGES[(fa, fs)] = edge(areas[fa], fits, fs, *fr); EDGES[(ta, ts)] = edge(areas[ta], fits, ts, *tr)
    o = []
    for (fa, fs, fr), (ta, ts, tr) in PATHS:
        for (sa, ss), (da, ds) in (((fa, fs), (ta, ts)), ((ta, ts), (fa, fs))):
            o += ['list nm_door_%d_%s' % (sa, ss), 'set_flag %d' % NOOP, 'unless_flag %d nm_d_%d_%s' % (POSTGAME, sa, ss)] + st.warp(da, *EDGES[(da, ds)][1])
            o += ['label nm_d_%d_%s' % (sa, ss), 'stop']
    return o
