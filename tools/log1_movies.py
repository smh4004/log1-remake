"""Movie bosses (post-game): condensed retellings of Cooler's Revenge, The Tree of Might and Lord Slug, one after another.

    lists(st)       their scenes
    checks(st)      lines for side_check, which runs after a side enemy dies
    install(...)    each area's walk-in scenes and enemies (log1_areas, beside log1_side.install)

Cooler (the owner, Nov 9: "build a Cooler sprite or find one ... Cooler first"): no Buu's Fury, LoG1 or LoG2 sprite exists, so he is LoG1's
own Frieza final form recoloured (COOLER_TINT): his purples turned to Cooler's deep blue-violet and the pinkish white body cooled to a bluish
white, the way tools/log1_party.py recolours Vegeta. His Armored Squadron are LoG1's Frieza soldiers in their own colours.

Turles (the owner, Nov 12: "Use Goku for Turles with reskinned Saiyan armor"): LoG1 Goku's head on LoG1 Vegeta's armour (tools/log1_turles.py).
Lord Slug: LoG1's Piccolo in Slug's black cloak, helmet and bodysuit with his orange scarf (SLUG_TINT). Their soldiers are LoG1's henchmen in
their own colours.

The owner (Nov 12): "Give them a condensed but detailed version of their plots leading into each where possible and make it extend the post
game content's scope", and their own ki attacks "modeled specifically for them, not player use" (src/bosses.c, tools/log1_bossfx.py).

Each film is a lead-in somewhere else, then a chain of fights in its arena with a scene between each:
    Cooler's Revenge: Chi-Chi's note at Goku's House -> the Forest camp: Cooler's eye beam meant for Gohan, the Armored Squadron -> Cooler (his
        fourth form) while Gohan runs for Senzu Beans -> his final form and the Supernova -> into the sun.
    The Tree of Might: Kami calls Goku to the Lookout -> the Wilderness: the tree's roots, the Crusher Corps -> Turles's Power Ball turns Gohan
        into a Great Ape, whom Goku has to stop -> Turles -> the fruit makes him stronger -> a Spirit Bomb drawn from the tree.
    Lord Slug: the City's news of a runaway planet -> the Battlegrounds: Slug young again by the Dragon Balls, the sky blacked out over all
        Earth (src/flight.c's dimming, until he falls), his soldiers -> Slug -> his giant Namekian form; Gohan's whistle stuns him mid-fight
        (src/bosses.c asks for it) -> the Kaioken and a Spirit Bomb into his freezing machine.
    Bardock's vision (any time after the ending): Raditz's pod at the Crash Site pulls Goku into a dream of his father's last stand. On Planet
        Vegeta (tools/log1_bardock.py: area 70; src/skills.c makes Goku Bardock there) Frieza's soldiers, then Dodoria; then Frieza's Supernova,
        Bardock's vision of Kakarot, and Goku wakes by the pod. It plays again until it has been seen through.
Each villain's first form opens after the ending (and after the film before), far above anything in the story (stage 41 plus more, rising).
While a villain is there the area's own animals near the arena keep away (src/flight.c sends off a living one whose "flag clear" condition on
a movie flag, 1000 and up, stops holding). All text here is original.
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


def phase(kind, foes, kills, said, intro=(), effects=()):
    """kind 'crew' (three soldiers) or 'one'; kills: their kill flags; said: the flag set when its intro has played (its foes appear then);
    intro: (speaker, text) lines played when the phase before falls; effects: scene lines run with the intro."""
    return dict(kind=kind, foes=foes, kills=kills, said=said, intro=list(intro), effects=list(effects))


def soldier(name, sprite, look, light, dark): return dict(name=name, sprite=sprite, look=look, tint=squad_tint(light, dark))


# LoG1 Frieza's palette -> Cooler's final form: the plates of his armour in a deeper violet, his white body hardened to steel grey
COOLER2_TINT = {2: (190, 150, 255), 3: (110, 60, 210), 4: (50, 20, 120), 5: (200, 206, 222), 6: (160, 166, 190), 7: (120, 126, 156), 8: (84, 88, 118), 9: (56, 58, 84)}
SKY_DARK = 950                                              # src/flight.c dims the screen while it is set: Slug's cloud over the Earth
SENZU = 11
VISION, FLASH = 70, 898                                     # tools/log1_bardock.py's Planet Vegeta; src/flight.c's white flash

FILMS = [
    dict(key='cooler', area=4, centre=(500, 384), gate=None, met=413, here=1016, lead=1017, paid=418, exp=3,
         lead_area=2, lead_text=[('narrator', "A note on the table at Goku's House, in Chi-Chi's handwriting: \"Gohan and Krillin went camping in the "
                                  "Forest meadow. Back for supper. Don't you dare go fighting anything.\"")],
         arrive=[('narrator', "The meadow is quiet: a campfire, Gohan and Krillin roasting fish. Then the birds stop singing, and a huge round "
                  "ship drops out of the sky and lands in the flowers."),
                 ('cooler', "So this is the Saiyan who killed my little brother. Frieza always was sloppy. I'm not."),
                 ('narrator', "Two red beams flash from Cooler's eyes, straight at Gohan. Goku throws himself in front of them and takes the blast "
                  "across his back."),
                 ('goku', "Gohan... are you hurt? Good. Krillin, get him out of here!"),
                 ('cooler', "Touching. Armored Squadron! Salza, Dore, Neiz. Bring me his head.")],
         phases=[phase('crew', [soldier('Salza', 'hench4', 'salza', (150, 200, 255), (60, 90, 190)),
                                soldier('Dore', 'hench6', 'dore', (140, 210, 120), (40, 110, 50)),
                                soldier('Neiz', 'hench2', 'neiz', (250, 230, 120), (170, 120, 30))], [414, 415, 416], 413),
                 phase('one', [dict(name='Cooler', sprite='frieza4', look='cooler', tint=recolour(COOLER_TINT), moveset=0, extra=14)], [417], 419,
                       [('cooler', "Useless, all of them. Fine. I'll show you the difference between Frieza and me."),
                        ('gohan1', "Dad! Hold on! I'll fly to Korin's Tower and bring back Senzu Beans!"),
                        ('narrator', "Gohan streaks away across the Forest. Goku, still bleeding from the eye beam, squares up to Cooler alone.")]),
                 phase('one', [dict(name='Cooler', sprite='frieza4', look='cooler2', tint=recolour(COOLER2_TINT), moveset=1, extra=17)], [1019], 1018,
                       [('cooler', "Impressive, for a monkey. Frieza only ever had four forms. I have one more."),
                        ('narrator', "Cooler's body swells. Plates of violet armour slide over his skull and a mask snaps shut across his mouth."),
                        ('gohan1', "Dad! Catch!"),
                        ('narrator', "Gohan is back, and tosses Goku a Senzu Bean. Eat it from your items when you need it.")],
                       ['do call 128 %d' % SENZU])],
         ending=[('cooler', "This can't be... a Saiyan, beating me..."),
                 ('narrator', "Cooler gathers everything he has into a burning Supernova. Goku's hair flashes gold. He drives it back with "
                  "everything he has, and the blast carries Cooler up, out of the sky and into the sun."),
                 ('narrator', "Later, Salza tries one last shot from the trees, and a Special Beam Cannon from somewhere far off ends him. "
                  "Piccolo never says a word about it.")],
         reward=dict(gear=33, text="Goku took the Enhanced Space Armor from the wreck of Cooler's ship!"),
         hint="Kami's voice sounds in Goku's head: \"Goku. Come to the Lookout. Something is wrong with the Earth.\""),
    dict(key='turles', area=16, centre=(276, 324), gate='cooler', met=1000, here=1007, lead=944, paid=1005, exp=4,
         lead_area=15, lead_text=[('kami', "Goku, you came. The Earth's life is draining away. In the Wilderness, every tree has gone grey in a "
                                  "single night."),
                                  ('kami', "Something has taken root there. Something that drinks planets. Hurry.")],
         arrive=[('narrator', "The ground shakes. Roots as thick as houses burst up through the Wilderness's ice, and the trees around them "
                  "wither and go grey. Far off, a vast tree is rising."),
                 ('turles', "So you're Kakarot. We look alike, don't we? To Frieza's men, all low-class Saiyans look the same."),
                 ('goku', "Who are you? And what is that thing doing to the land?"),
                 ('turles', "The Tree of Might. It drinks a planet dry and grows one fruit that makes its eater stronger. Crusher Corps, "
                  "get rid of him.")],
         phases=[phase('crew', [soldier('Amond', 'hench1', 'amond', (255, 170, 110), (150, 70, 30)),
                                soldier('Cacao', 'hench3', 'cacao', (200, 200, 220), (80, 80, 110)),
                                soldier('Daiz', 'hench5', 'daiz', (240, 120, 140), (130, 40, 60))], [1001, 1002, 1003], 1000),
                 phase('one', [dict(name='Gohan', sprite='oozaru1', look='great_ape_gohan', moveset=6, extra=12, big=dict(rows=(0, 1, 5)))], [940], 1006,
                       [('turles', "Kakarot's brat came to help? Then let's see what a real Saiyan child can do."),
                        ('narrator', "Turles throws a ball of light into the sky: a Power Ball, a full moon in the middle of the day. Gohan looks up."),
                        ('narrator', "Gohan's eyes go red. He grows, and grows, into a roaring Great Ape."),
                        ('goku', "Gohan, no! ...Sorry, son. I have to stop you, and then cut that tail.")]),
                 phase('one', [dict(name='Turles', sprite='vegeta1', look='turles', moveset=2, extra=18)], [1004], 941,
                       [('narrator', "Goku catches the Great Ape's tail and cuts it. Gohan shrinks back, asleep in the snow."),
                        ('turles', "Soft. A real Saiyan would have let the brat tear you apart. Now you face me.")]),
                 phase('one', [dict(name='Turles', sprite='vegeta1', look='turles2', moveset=3, extra=21)], [943], 942,
                       [('turles', "Not bad, Kakarot. But I have something you don't."),
                        ('narrator', "Turles pulls a glowing fruit from the Tree of Might and bites into it. His muscles bulge and a violet "
                         "light pours off him.")])],
         ending=[('turles', "No... a low-class clown like you... beating me..."),
                 ('narrator', "Goku raises his hands and draws the energy back out of the Tree of Might itself, into a Spirit Bomb. It "
                  "smashes through Turles and the tree, and both crumble to dust."),
                 ('narrator', "One last fruit drops into the snow at Goku's feet.")],
         reward=dict(gear=73, text="Goku found Saiyan Gloves among Turles's things!", fruit=True),
         hint="On the way home, every radio Goku passes in the City is talking about the same thing: something huge in the sky."),
    dict(key='slug', area=23, centre=(380, 316), gate='turles', met=1008, here=1015, lead=945, paid=1013, exp=5,
         lead_area=17, lead_text=[('narrator', "A radio in a shop window: \"...a runaway planet on a collision course with Earth has exploded "
                                  "just short of us. Officials say there is no danger. However, a large object has come down near the old "
                                  "Battlegrounds...\""),
                                  ('goku', "The Battlegrounds? I'd better go take a look.")],
         arrive=[('narrator', "A ship like a giant shell sits in the Battlegrounds, and soldiers in strange armour stand around it. One of "
                  "them holds a sack. Inside: Dragon Balls."),
                 ('slug', "The wish is made. Old age is gone, and I am young again. Now, set the machine."),
                 ('narrator', "A rocket roars into the sky. Black cloud spreads from it until the sun is gone and the air turns bitter cold, "
                  "all over the Earth."),
                 ('slug', "A cold, dark planet. It will make me a fine ship. Medamatcha, Angila, Wings: deal with the Saiyan.")],
         arrive_effects=['set_flag %d' % SKY_DARK],
         phases=[phase('crew', [soldier('Medamatcha', 'hench7', 'medamatcha', (170, 230, 140), (60, 120, 40)),
                                soldier('Angila', 'hench8', 'angila', (140, 220, 230), (30, 100, 120)),
                                soldier('Wings', 'hench1', 'wings', (200, 160, 240), (90, 50, 140))], [1009, 1010, 1011], 1008),
                 phase('one', [dict(name='Lord Slug', sprite='piccolo', look='slug', tint=recolour(SLUG_TINT), moveset=4, extra=22)], [1012], 1014,
                       [('slug', "Must I do everything myself?"),
                        ('goku', "You're a Namekian! Why would a Namekian want to hurt anybody?"),
                        ('slug', "I'm nothing like those soft Namekians. Now kneel.")]),
                 phase('one', [dict(name='Lord Slug', sprite='piccolo', look='slug2', tint=recolour(SLUG_TINT), moveset=5, extra=25, big=dict(rows=(0, 1, 5), scale=2))], [947], 946,
                       [('slug', "You broke my arm? Then see what a Super Namekian can do."),
                        ('narrator', "Slug's arm grows back. He tears off his helmet, and swells into a giant Namekian, tall as the ship behind him.")])],
         ending=[('slug', "This... cannot be... my sky... my ship..."),
                 ('narrator', "Piccolo's last strength pours into Goku. With the Kaioken burning red he punches straight through the giant, "
                  "then flies up through the black cloud to the sun and brings a Spirit Bomb down onto Slug's freezing machine."),
                 ('narrator', "The cloud breaks. Sunlight floods back over the Battlegrounds, and over the whole Earth.")],
         end_effects=['do call 30 %d' % SKY_DARK],
         reward=dict(gear=139, text="Goku found Slug's Pure Black Cape in the wreckage!"),
         hint=None),
    # Bardock's vision (post-game, any time after the ending): Raditz's pod at the Crash Site pulls Goku into a dream of his father's last stand on
    # Planet Vegeta (tools/log1_bardock.py: area 70, and his figure; src/skills.c makes Goku Bardock there). It plays again until it is seen through.
    dict(key='bardock', area=VISION, centre=(352, 470), gate=None, met=951, here=952, lead=953, paid=954, exp=2, replay=True,
         lead_area=9, lead_rect=(296, 96, 424, 208),
         lead_text=[('narrator', "Raditz's pod still lies in its crater, cracked and cold. Inside it, a scouter blinks on by itself."),
                    ('goku', "Raditz said our father was a Saiyan warrior... I wonder what he was like."),
                    ('narrator', "Goku picks up the scouter. Static roars in his head, then a voice that sounds just like his own...")],
         lead_effects=lambda st: ['set_flag %d' % FLASH] + st.warp(VISION, 352, 500),        # clear of the map's foot, where the screen shows past it
         arrive=[('narrator', "Planet Vegeta, long ago. A low-class Saiyan warrior named Bardock has seen the future in his dreams: Frieza is "
                  "coming to wipe out his people."),
                 ('bardock', "Nobody believed me. Fine. Then I'll stop Frieza myself!")],
         attack="Frieza's soldiers pour out of their pods!",
         phases=[phase('crew', [dict(name='a soldier', sprite='hench1', look='fsoldier1', extra=6),
                                dict(name='a soldier', sprite='hench3', look='fsoldier2', extra=6),
                                dict(name='a soldier', sprite='hench5', look='fsoldier3', extra=6)], [955, 956, 957], 951),
                 phase('one', [dict(name='Dodoria', sprite='recoome', look='dodoria', tint=squad_tint((255, 168, 200), (150, 60, 100)), moveset=7, extra=10)],
                       [1020], 1021,
                       [('dodoria', "Well, well. The monkey who thinks he can see the future. Let's see you see this coming!"),
                        ('bardock', "Dodoria! You were at Planet Meat. You killed my whole team!")])],
         ending=[('narrator', "Bardock flies up through a sky full of soldiers to Frieza's ship. Frieza floats out to meet him, smiling."),
                 ('bardock', "Frieza! This is for all of us! Take this!"),
                 ('narrator', "Bardock throws everything he has left: a Final Spirit Cannon. Frieza raises one finger. A sun grows on it, the "
                  "Supernova, and it swallows the blast, Bardock, and Planet Vegeta whole."),
                 ('narrator', "In the last light Bardock sees one more vision: a grown son with his face, standing up to Frieza on a world far away."),
                 ('bardock', "Kakarot... it's up to you now...")],
         end_effects=lambda st: ['set_flag %d' % FLASH] + st.warp(9, 352, 220),
         after=[('narrator', "Goku wakes at the edge of the crater, the scouter dark in his hand."),
                ('goku', "Dad... I never even knew your name. Bardock. I'll remember it.")],
         reward=dict(gear=40, text="Inside Raditz's pod Goku found a spare suit of Saiyan Armor, like his father wore."),
         hint=None),
]
BY_KEY = {f['key']: f for f in FILMS}
WHISTLE, WHISTLE_DONE = 948, 949                            # src/bosses.c sets WHISTLE once the giant has thrown three attacks; src/flight.c runs mv_whistle
BOSS_ACTORS = {}                                            # look -> (actor value, src/bosses.c moveset), filled by install()


def arena(f):
    x, y = f['centre']; return (x - 96, y - 64, x + 96, y + 64)


def spots(f, ph):
    """Where a phase's foes stand: soldiers in a loose line, a single foe up the middle."""
    x, y = f['centre']
    if ph['kind'] == 'crew': return [(x - 40, y + 6), (x + 40, y + 6), (x, y + 32)]
    return [(x, y - 24)]


# Cooler's own names, used by tools/movies_test.py
C = BY_KEY['cooler']; FOREST, COOLER_MET, COOLER_PAID, COOLER_HERE = 4, C['met'], C['paid'], C['here']


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


def say(st, lines):
    o = []
    for who, t in lines: o += narrate(t) if who == 'narrator' else st.say([dict(who=who, text=t)])
    return o


def lists(st):
    o = []
    for f in FILMS:
        k = f['key']
        # the lead-in, anywhere in its area, once
        o += ['list mv_%s_lead' % k, 'set_flag %d' % NOOP, 'unless_flag %d mv_%s_le' % (POSTGAME, k), 'if_flag %d mv_%s_le' % (f['paid'] if f.get('replay') else f['lead'], k)]
        if f['gate']: o.append('unless_flag %d mv_%s_le' % (BY_KEY[f['gate']]['paid'], k))
        o += say(st, f['lead_text']) + ['set_flag %d' % f['lead']] + (f['lead_effects'](st) if 'lead_effects' in f else []) + ['label mv_%s_le' % k, 'stop']
        # the arena
        o += ['list mv_' + k, 'set_flag %d' % NOOP, 'unless_flag %d mv_%s_end' % (f['lead'], k), 'if_flag %d mv_%s_end' % (f['met'], k)]
        o += say(st, f['arrive']) + f.get('arrive_effects', []) + ['set_flag %d' % f['met'], 'set_flag %d' % f['here']]
        o += narrate(f.get('attack') or "The %s's animals bolt. %s attacks!" % ({4: 'Forest', 16: 'Wilderness', 23: 'Battlegrounds'}[f['area']],
                                                             ' and '.join(x['name'] for x in f['phases'][0]['foes'][:2]) + ' and ' + f['phases'][0]['foes'][2]['name']))
        o += ['label mv_%s_end' % k, 'stop']
    s = BY_KEY['slug']
    o += ['list mv_whistle', 'set_flag %d' % NOOP, 'if_flag %d mv_wh_end' % WHISTLE_DONE, 'set_flag %d' % WHISTLE_DONE]
    o += say(st, [('gohan1', "Hey, big guy! Cover your ears!"),
                  ('narrator', "Gohan puts two fingers in his mouth and whistles, high and shrill. Slug staggers, clutching the sides of his head."),
                  ('piccolo', "Namekian ears can't stand that pitch. Now, Goku!")])
    o += ['label mv_wh_end', 'stop']
    return o


def later(named): return [(WHISTLE, named['mv_whistle'])]


def checks(st):
    """In side_check: each phase's fall plays the next one's scene (its foes then appear); the last pays."""
    o = []
    for f in FILMS:
        k, R = f['key'], f['reward']
        for i in range(1, len(f['phases'])):
            prev, ph = f['phases'][i - 1], f['phases'][i]; lab = 'mv_%s_p%d' % (k, i)
            o += ['if_flag %d %s' % (ph['said'], lab)] + ['unless_flag %d %s' % (fl, lab) for fl in prev['kills']] + ['set_flag %d' % ph['said']]
            o += say(st, ph['intro']) + ph['effects'] + ['label ' + lab]
        last = f['phases'][-1]; lab = 'mv_%s_won' % k
        o += ['if_flag %d %s' % (f['paid'], lab)] + ['unless_flag %d %s' % (fl, lab) for fl in last['kills']]
        ef = f.get('end_effects', []); ef = ef(st) if callable(ef) else ef
        o += ['set_flag %d' % f['paid'], 'do call 30 %d' % f['here']] + say(st, f['ending']) + ef + say(st, f.get('after', []))
        o += ['do call 194 %d' % (st.bal.quest_exp(41, True) * f['exp'])]
        if R.get('fruit'): o += ['set_flag %d' % DB_POWER] + narrate("Goku ate the fruit of the Tree of Might! His strength, power and endurance rose.")
        o += ['do call 147 %d' % R['gear']] + narrate(R['text']) + (narrate(f['hint']) if f['hint'] else []) + ['label ' + lab]
    return o


def big_data(actors, s):
    """A big villain's figure for src/flight.c's 32x64 sprite: three poses (two walking, one casting), each four directions of 2 KB.
    The Great Ape is LoG1's own 32x64 sprite; giant Slug is Piccolo's frames in Slug's colours at twice the size (a pose too wide for that
    keeps its walking frame)."""
    import log1_actors, log1_sprites as S
    rec = S.record(actors.log1, actors.log1[S.SETS + actors.names.index(s['sprite'])]); cmap = S.colour_map(actors.log1, rec, actors.r, s.get('tint'))
    sets = []
    for row in s['big']['rows']:
        if 'scale' not in s['big']: sets += actors.big_images(rec, row, cmap); continue
        ims = []
        for c in range(3):
            im = S.cell(actors.log1, rec, row, c, cmap)
            xs = np.nonzero(im)[1] if im is not None else []
            if im is None or not len(xs) or (xs.max() - xs.min() + 1) * s['big']['scale'] > 32: im = S.cell(actors.log1, rec, s['big']['rows'][0], c, cmap)
            ims.append(log1_actors.upscaled(im, s['big']['scale']))
        sets += [ims[0], ims[1], ims[2], ims[2][:, ::-1]]
    return actors.ins.put(log1_actors.big_tiles(sets))


def install(n, a, fits, r, actors, put, named, spawns, foe, walkins, BF_IDX):
    for f in FILMS:
        if n == f['lead_area']: walkins.append((n,) + f.get('lead_rect', (0, 0, a.W * 8, a.H * 8)) + (named['mv_%s_lead' % f['key']],))      # anywhere in the area, or its rect
        if n != f['area']: continue
        walkins.append((n,) + arena(f) + (named['mv_' + f['key']],))       # walking into the arena
        for ph in f['phases']:
            for i, (s, at) in enumerate(zip(ph['foes'], spots(f, ph))):
                if 'moveset' in s:
                    v = actors.actor(s['sprite'], True, s.get('tint'), s['look']); big = 0
                    if 'big' in s: actors.hidden(v); big = big_data(actors, s)
                    BOSS_ACTORS[s['look']] = (v, s['moveset'], big)
                foe(s['sprite'], at[0], at[1], 'set:%d & clear:%d' % (ph['said'], ph['kills'][i]), ph['kills'][i],
                    s.get('extra', 8 + 2 * FILMS.index(f)), True, 41, tint=s.get('tint'), look=s['look'])
