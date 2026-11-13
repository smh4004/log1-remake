"""Movie bosses (post-game superbosses): Cooler in the Forest, then Turles in the Wilderness, then Lord Slug in the Battlegrounds.

    lists(st)       their scenes
    checks(st)      lines for side_check, which runs after a side enemy dies
    install(...)    each area's walk-in scenes and enemies (log1_areas, beside log1_side.install)

Cooler (the owner, Nov 9: "build a Cooler sprite or find one ... Cooler first"): no Buu's Fury, LoG1 or LoG2 sprite exists, so he is LoG1's
own Frieza final form recoloured (COOLER_TINT): his purples turned to Cooler's deep blue-violet and the pinkish white body cooled to a bluish
white, the way tools/log1_party.py recolours Vegeta. His Armored Squadron are LoG1's Frieza soldiers in their own colours.

Turles (the owner, Nov 12: "Use Goku for Turles with reskinned Saiyan armor"): LoG1 Goku's head on LoG1 Vegeta's armour (tools/log1_turles.py).
Lord Slug: LoG1's Piccolo in Slug's black cloak, helmet and bodysuit with his orange scarf (SLUG_TINT). Their soldiers are LoG1's henchmen in
their own colours.

Each film runs the same way. After the ending (and once the film before it is won), walking into its arena lands the villain: he sends three
soldiers first, and when the third falls he fights Goku himself, far above anything in the story (stage 41 plus more, rising film to film).
While he is there the area's own animals near the arena keep away (src/flight.c sends off a living one whose "flag clear" condition on
a movie flag, 1000 and up, stops holding).
Beating him pays big EXP and a reward, and hints at the next film. All text here is original.
"""
import os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]

NOOP, QF = 895, 420
POSTGAME = QF + 68
DB_POWER = 780                                              # src/skills.c: +5 strength, power and endurance (the Dragon Ball wish), used by the fruit


def recolour(table):
    def f(pal):
        out = pal.copy()
        for i, c in table.items(): out[i] = c
        return out
    return f


def squad_tint(light, dark):
    """A soldier in one colour family: every coloured index keeps its brightness, in this hue."""
    L, D = np.array(light, float), np.array(dark, float)
    def f(pal):
        out = pal.copy()
        for i, (r, g, b) in enumerate(pal):
            if i < 2: continue
            v = max(r, g, b) / 255; s = max(r, g, b) - min(r, g, b)
            if s < 24: continue                               # greys and whites (armour) stay
            out[i] = (D + (L - D) * v).astype(int)
        return out
    return f


# LoG1 Frieza's palette index -> Cooler's colour: 2-4 the head and shoulders' purple, 5-9 the pinkish white body
COOLER_TINT = {2: (150, 150, 240), 3: (64, 56, 168), 4: (28, 22, 88), 5: (226, 228, 240), 6: (196, 200, 222), 7: (150, 156, 190), 8: (104, 108, 146), 9: (74, 76, 110)}
# LoG1 Piccolo's index -> Slug's: the turban becomes his dark helmet and the cape his black cloak (2, 14, 15), the turban's purple top the helmet's crown
# (9, 10), the gi his black bodysuit (6-8), the sash his orange scarf (11)
SLUG_TINT = {2: (92, 84, 110), 14: (40, 34, 54), 15: (64, 56, 82), 6: (44, 42, 54), 7: (28, 26, 36), 8: (12, 10, 18), 9: (52, 46, 66), 10: (34, 30, 44), 11: (206, 112, 36)}


def film(key, area, centre, flags, boss, crew, gate, level_extra, exp, reward, lines):
    x, y = centre
    return dict(key=key, area=area, arena=(x - 96, y - 64, x + 96, y + 64), centre=centre, gate=gate, exp=exp, reward=reward, lines=lines,
                met=flags[0], killed=flags[1], boss_killed=flags[1] + 3, paid=flags[1] + 4, said=flags[1] + 5, here=flags[2],
                boss=dict(boss, at=(x, y - 24), extra=level_extra[0]),
                crew=[dict(c, at=(x + dx, y + dy), extra=level_extra[1]) for c, (dx, dy) in zip(crew, ((-40, 6), (40, 6), (0, 32)))])


FILMS = [
    film('cooler', 4, (500, 384), (413, 414, 1016),
         dict(name='Cooler', sprite='frieza4', look='cooler', tint=recolour(COOLER_TINT)),
         [dict(name='Salza', sprite='hench4', look='salza', tint=squad_tint((150, 200, 255), (60, 90, 190))),
          dict(name='Dore', sprite='hench6', look='dore', tint=squad_tint((140, 210, 120), (40, 110, 50))),
          dict(name='Neiz', sprite='hench2', look='neiz', tint=squad_tint((250, 230, 120), (170, 120, 30)))],
         None, (14, 8), 3, dict(gear=33, text="Goku received the Enhanced Space Armor from the wreckage!"),
         dict(arrive="The birds go quiet. A huge round ship drops out of the sky and lands in the meadow, flattening the flowers.",
              talk=[('boss', "So you're the Saiyan monkey who killed my little brother. Frieza always was sloppy. I'm not."),
                    ('goku', "Your brother?! Wait, how many of you guys are there?"),
                    ('boss', "Enough. Armored Squadron! Salza, Dore, Neiz. Bring me his head.")],
              attack="The Forest's animals bolt into the trees. Cooler's Armored Squadron attacks!",
              crew_down="Useless, all of them. Fine. I'll show you the difference between Frieza and me.",
              boss_down="Impossible... Beaten by a monkey... just like Frieza...",
              after="Cooler's ship lifts off, smoking, and vanishes into the sky. The Forest is quiet again.",
              hint="Far away, the ground of the Wilderness gives a low rumble...")),
    film('turles', 16, (276, 324), (1000, 1001, 1007),
         dict(name='Turles', sprite='vegeta1', look='turles'),
         [dict(name='Amond', sprite='hench1', look='amond', tint=squad_tint((255, 170, 110), (150, 70, 30))),
          dict(name='Cacao', sprite='hench3', look='cacao', tint=squad_tint((200, 200, 220), (80, 80, 110))),
          dict(name='Daiz', sprite='hench5', look='daiz', tint=squad_tint((240, 120, 140), (130, 40, 60)))],
         'cooler', (18, 10), 4, dict(gear=73, text="Goku found Saiyan Gloves among Turles's things!", fruit=True),
         dict(arrive="The ground shakes. Roots as thick as houses burst up through the Wilderness's ice, and the trees around them wither and go grey.",
              talk=[('boss', "So you're Kakarot. We look alike, don't we? To Frieza's men, all low-class Saiyans look the same."),
                    ('goku', "Who are you? And what is that thing doing to the land?"),
                    ('boss', "The Tree of Might. It drinks a planet dry and grows one fruit that makes its eater stronger. Crusher Corps, get rid of him.")],
              attack="The Wilderness's animals flee the dying ground. The Turles Crusher Corps attacks!",
              crew_down="Weaklings. Fine. One bite of the fruit and I'll finish you myself.",
              boss_down="No... a low-class clown like you... beating me...",
              after="Turles falls, and the Tree of Might crumbles to dust. One last fruit drops at Goku's feet.",
              hint="A cold wind blows in from the Battlegrounds...")),
    film('slug', 23, (380, 316), (1008, 1009, 1015),
         dict(name='Slug', sprite='piccolo', look='slug', tint=recolour(SLUG_TINT)),
         [dict(name='Medamatcha', sprite='hench7', look='medamatcha', tint=squad_tint((170, 230, 140), (60, 120, 40))),
          dict(name='Angila', sprite='hench8', look='angila', tint=squad_tint((140, 220, 230), (30, 100, 120))),
          dict(name='Wings', sprite='hench1', look='wings', tint=squad_tint((200, 160, 240), (90, 50, 140)))],
         'turles', (22, 12), 5, dict(gear=139, text="Goku found Slug's Pure Black Cape in the wreckage!"),
         dict(arrive="The sky darkens. A ship shaped like a giant shell lands in the Battlegrounds, and the air turns bitterly cold.",
              talk=[('boss', "A quiet little planet. Once I've blotted out its sun, it will make me a fine ship."),
                    ('goku', "You're a Namekian! Why would a Namekian want to hurt anybody?"),
                    ('boss', "I'm nothing like those soft Namekians. Medamatcha, Angila, Wings: deal with him.")],
              attack="The cold drives the animals away. Lord Slug's soldiers attack!",
              crew_down="Must I do everything myself? Then see what a Super Namekian can do.",
              boss_down="This... cannot be... my sky... my ship...",
              after="Slug's ship breaks apart in the cold wind, and the sun comes out again over the Battlegrounds.",
              hint=None)),
]
BY_KEY = {f['key']: f for f in FILMS}
# Cooler's own names, used by tools/movies_test.py
C = BY_KEY['cooler']; FOREST, COOLER_MET, SQUAD_KILLED, COOLER_KILLED, COOLER_PAID, COOLER_HERE = 4, C['met'], C['killed'], C['boss_killed'], C['paid'], C['here']


def wild(n, x, y):
    """The condition for one of an area's own enemies (log1_areas), or None: the animals near a film's arena keep away while its villain is there
    ("flag clear" on its HERE flag; src/flight.c sends a living one off once that flag is set, for flags from 1000 up)."""
    for f in FILMS:
        cx, cy = f['centre']
        if n == f['area'] and abs(x - cx) <= 300 and abs(y - cy) <= 240: return 0x20000 | f['here']
    return None


def narrate(text):
    from convert_log1 import split_line
    return ['say narrator ' + p for p in split_line(text)]


def lists(st):
    o = []
    for f in FILMS:
        k, L = f['key'], f['lines']; B = lambda t: narrate('%s: %s' % (f['boss']['name'], t))
        o += ['list mv_' + k, 'set_flag %d' % NOOP, 'unless_flag %d mv_%s_end' % (POSTGAME, k), 'if_flag %d mv_%s_end' % (f['met'], k)]
        if f['gate']: o.append('unless_flag %d mv_%s_end' % (BY_KEY[f['gate']]['paid'], k))
        o += narrate(L['arrive'])
        for who, t in L['talk']: o += B(t) if who == 'boss' else st.say([dict(who='goku', text=t)])
        o += ['set_flag %d' % f['met'], 'set_flag %d' % f['here']] + narrate(L['attack']) + ['label mv_%s_end' % k, 'stop']
    return o


def checks(st):
    """In side_check: each crew's fall brings its villain; the villain's fall pays."""
    o = []
    for f in FILMS:
        k, L, R = f['key'], f['lines'], f['reward']; B = lambda t: narrate('%s: %s' % (f['boss']['name'], t))
        o += ['if_flag %d mv_%s_sq' % (f['boss_killed'], k)] + ['unless_flag %d mv_%s_sq' % (f['killed'] + i, k) for i in range(3)]
        o += ['if_flag %d mv_%s_sq' % (f['said'], k), 'set_flag %d' % f['said']] + B(L['crew_down']) + ['label mv_%s_sq' % k]
        o += ['if_flag %d mv_%s_co' % (f['paid'], k), 'unless_flag %d mv_%s_co' % (f['boss_killed'], k), 'set_flag %d' % f['paid'], 'do call 30 %d' % f['here']]
        o += B(L['boss_down']) + narrate(L['after']) + ['do call 194 %d' % (st.bal.quest_exp(41, True) * f['exp'])]
        if R.get('fruit'): o += ['set_flag %d' % DB_POWER] + narrate("Goku ate the fruit of the Tree of Might! His strength, power and endurance rose.")
        o += ['do call 147 %d' % R['gear']] + narrate(R['text']) + (narrate(L['hint']) if L['hint'] else []) + ['label mv_%s_co' % k]
    return o


def install(n, a, fits, r, actors, put, named, spawns, foe, walkins, BF_IDX):
    for f in FILMS:
        if n != f['area']: continue
        walkins.append((n,) + f['arena'] + (named['mv_' + f['key']],))       # walking into the arena
        for i, s in enumerate(f['crew']):
            foe(s['sprite'], s['at'][0], s['at'][1], 'set:%d & clear:%d' % (f['met'], f['killed'] + i), f['killed'] + i, s['extra'], True, 41,
                tint=s['tint'], look=s['look'])
        b = f['boss']
        foe(b['sprite'], b['at'][0], b['at'][1], ' & '.join(['set:%d' % (f['killed'] + i) for i in range(3)] + ['clear:%d' % f['boss_killed']]),
            f['boss_killed'], b['extra'], True, 41, tint=b.get('tint'), look=b['look'])
