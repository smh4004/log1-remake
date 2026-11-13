"""Yardrat (post-game): a second planet on the world map, where Goku learns Instant Transmission. All text here is original.

In the series Goku escapes Namek's end in a Ginyu Force pod and lands on Yardrat, whose people teach him Instant Transmission. Here Yardrat is a
floating sign on the world map like Namek's, open once the story has ended (quest 68). Its one area is LoG1's Namek plateau (area 28) in new
colours: lilac ground, slate cliffs. Its people are LoG1's townsfolk in Yardrat colours (pale lavender skin, light robes), made at build time.

The Elder sets a test: catch his three apprentices, who blink away the first time Goku reaches them. With all three caught, he teaches Instant
Transmission (src/skills.c learns it once LEARNED is set). Used where no enemy is near, Instant Transmission opens a picker of every place Goku
has been (src/flight.c) and takes him there; near an enemy it is Buu's Fury's own move.

    add_area(L)             before the areas are built: writes area 69 into the converted LoG1 data
    lists(story)            scene lists: the Yardrats' talks and Instant Transmission's menus
    install(n, a, ...)      for area 69: its people, as log1_side.Side.install does
    picker_rows(...)        Instant Transmission's places for src/flight.c's picker
Flags 395-402.
"""
import json, os, re, shutil, struct, sys, colorsys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
from convert_log1 import split_line  # noqa: E402

AREA, SOURCE, MUSIC = 69, 28, 0                 # LoG1's Namek plateau; the music is LoG1's song 0
START = (472, 584)                              # area 28's own start: the path in at the bottom
QF, NOOP, VISIT, POSTGAME = 420, 895, 800, 420 + 68
MET, BLINK, CAUGHT, LEARNED = 395, 396, 399, 402                     # BLINK and CAUGHT: three each
SPIRIT = 403                                                         # King Kai's secret: the Spirit Bomb (src/skills.c SPIRIT_FLAG)
KING_KAI, KK_SET, KK_SPOT = 13, 43, (304, 216)                       # his planet, his talk (LoG1 set 43), and Instant Transmission's landing: his front door
ELDER = dict(sprite='wiseman', at=(472, 470))
STUDENTS = [dict(sprite='oldman', a=(260, 300), b=(150, 520), look='student1'),
            dict(sprite='oldman', a=(700, 200), b=(850, 470), look='student2'),
            dict(sprite='oldman', a=(560, 560), b=(330, 90), look='student3')]
ROBES = {'elder': (236, 236, 244), 'student1': (200, 222, 255), 'student2': (255, 214, 232), 'student3': (214, 255, 226)}


def recolour_tiles(pal):
    """Namek's blue ground to lilac, its red-brown cliffs to slate, yellow sand to pink and green to teal. Greys stay."""
    out = []
    for r, g, b in pal:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); d = h * 360
        if s > 0.15:
            if 170 <= d <= 250: h, s, v = 272 / 360, s * 0.55, min(1, v * 1.04)
            elif d < 45 or d > 330: h, s = 205 / 360, s * 0.4
            elif d < 70: h, s = 330 / 360, s * 0.5
            elif d < 170: h = 170 / 360
        out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v)))
    return out


def add_area(L):
    """Area 69 in the converted data: area 28's map with recoloured tiles, no actors or doors."""
    from PIL import Image
    M = os.path.join(L, 'assets', 'maps')
    for f in os.listdir(os.path.join(M, 'tiles')):
        m = re.match(r'area%02d(_block\d+)?\.png$' % SOURCE, f)
        if not m: continue
        im = Image.open(os.path.join(M, 'tiles', f)); assert im.mode == 'P'
        pal = im.getpalette(); rgb = [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]
        out = im.copy(); out.putpalette([c for t in recolour_tiles(rgb) for c in t]); out.save(os.path.join(M, 'tiles', 'area%02d%s.png' % (AREA, m.group(1) or '')))
    tmx = open(os.path.join(M, 'area%02d.tmx' % SOURCE)).read()
    tmx = tmx.replace('tiles/area%02d' % SOURCE, 'tiles/area%02d' % AREA).replace('name="area%02d"' % SOURCE, 'name="area%02d"' % AREA)
    tmx = tmx.replace('<property name="area" type="int" value="%d"/>' % SOURCE, '<property name="area" type="int" value="%d"/>' % AREA)
    open(os.path.join(M, 'area%02d.tmx' % AREA), 'w').write(tmx)
    info = json.load(open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % SOURCE)))
    json.dump(dict(info, area=AREA, actors=[], pickups=[], objects=[], triggers=[], start=list(START), music=MUSIC), open(os.path.join(L, 'assets', 'areas', 'area%02d.json' % AREA), 'w'))


def tint(robe):
    """A LoG1 character in Yardrat colours: skin pale lavender, clothes the robe's colour, outlines and greys kept."""
    def fn(pal):
        out = pal.copy()
        for i, (r, g, b) in enumerate(pal):
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); d = h * 360
            if v < 0.2 or s < 0.12: continue
            if 15 <= d <= 50: nh, ns, nv = 268 / 360, 0.28, min(1, v * 1.08)          # skin
            else: nh, ns, nv = colorsys.rgb_to_hsv(*(c / 255 for c in robe)); nv = nv * (0.55 + 0.45 * v)
            out[i] = [int(round(c * 255)) for c in colorsys.hsv_to_rgb(nh, ns, nv)]
        return out
    return fn


def say(who, text):
    t = text.replace('{', '(').replace('}', ')')
    return ['say goku ' + p for p in split_line(t)] if who == 'goku' else ['narrate ' + p for p in split_line((who + ': ' if who else '') + t)]


# ---------- Instant Transmission's picker ----------
# src/flight.c draws the picker and reads its keys; each place has a travel list and a 192x32 picture: LoG1's own box and font tiles (as the opening),
# "Instant Transmission" over "< place >".
EARTH = [(0, "Roshi's Island"), (2, "Goku's House"), (4, 'Forest'), (5, 'Village'), (9, 'Crash Site'), (15, "Kami's Lookout"), (17, 'City'), (22, 'Military Base'), (23, 'Battlegrounds')]
PLACES = EARTH + [(24, 'Namek'), (KING_KAI, "King Kai's Planet"), (AREA, 'Yardrat')]
STORY_FONT, T_CORNER, T_SIDE, T_TOP, T_FILL = 0x15B2F0, 100, 103, 102, 104
MENU_SLOTS = {2, 8, 9, 103, 193, 217, 218, 223, 224, 225, 236}


def picker_art(log1, bf, name, title='Instant Transmission'):
    """192x32 8bpp, as three 64x32 sprites one after another (each 8x4 tiles of 64 bytes, row by row)."""
    import bios, mapkit
    B = 0x08000000; f = struct.unpack_from('<II', log1, STORY_FONT); font = bios.unpack(log1, f[1] - B)[0]
    pal = [((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31) for v in struct.unpack_from('<16H', log1, f[0] - B)]
    obj = mapkit.palette(bf)[256:].astype(int); ok = [i for i in range(1, 256) if i not in MENU_SLOTS]
    cmap = [0] + [min(ok, key=lambda i: sum((obj[i][k] - c[k]) ** 2 for k in range(3))) for c in pal[1:]]
    W, H = 24, 4; img = np.zeros((H * 8, W * 8), np.uint8)
    def tile(x, y, t, flip=0, over=False):             # over: a letter drawn on the box's fill, its clear pixels showing the fill
        src = font[t * 32:t * 32 + 32]
        for j in range(8):
            for i in range(8):
                sx, sy = (7 - i if flip & 1 else i), (7 - j if flip & 2 else j); v = src[sy * 4 + sx // 2]; v = v >> 4 if sx & 1 else v & 15
                if v or not over: img[y * 8 + j, x * 8 + i] = cmap[v] if v else 0
    tile(0, 0, T_CORNER); tile(W - 1, 0, T_CORNER, 1); tile(0, H - 1, T_CORNER, 2); tile(W - 1, H - 1, T_CORNER, 3)
    for x in range(1, W - 1): tile(x, 0, T_TOP); tile(x, H - 1, T_TOP, 2)
    for y in range(1, H - 1): tile(0, y, T_SIDE); tile(W - 1, y, T_SIDE, 1)
    for y in range(1, H - 1):
        for x in range(1, W - 1): tile(x, y, T_FILL)
    for row, text in ((1, title), (2, '< %s >' % name)):
        x0 = 1 + (W - 2 - len(text)) // 2
        for i, ch in enumerate(text):
            if ch != ' ': tile(x0 + i, row, ord(ch) - 30, over=True)
    out = bytearray()
    for sp in range(3):
        for ty in range(4):
            for tx in range(8): out += img[ty * 8:ty * 8 + 8, (sp * 8 + tx) * 8:(sp * 8 + tx) * 8 + 8].tobytes()
    return bytes(out), img


def picker_rows(log1, bf, named):
    """(visited flag, travel list, picture) per place, for build_flight's it table."""
    return [(VISIT + n, named['it_%d' % n], picker_art(log1, bf, name)[0]) for n, name in PLACES if 'it_%d' % n in named]


def lists(st, log1):
    """Scene lists for the talks and the menus. st: log1_story.Story (its spots, warps and balance)."""
    o = []
    # the Elder
    s = 'yd_elder'; o += ['list ' + s, 'set_flag %d' % NOOP, 'if_flag %d %s_done' % (LEARNED, s)]
    o += ['unless_flag %d %s_wait' % (CAUGHT + k, s) for k in range(3)] + ['goto %s_teach' % s, 'label %s_wait' % s, 'if_flag %d %s_hint' % (MET, s), 'set_flag %d' % MET]
    o += say('Yardrat Elder', "An Earthling! No... a Saiyan, raised on Earth, if I read your energy right. Welcome to Yardrat.")
    o += say('goku', "Hi! I felt something strange from way out here, so I flew over. What's this place?")
    o += say('Yardrat Elder', "We are a small people, and not very strong. So we learned instead to be somewhere else, very quickly.")
    o += say('Yardrat Elder', "We call it Instant Transmission. Feel a person's energy, anywhere in the universe, and you can be there in a moment.")
    o += say('goku', "Wow! Can you teach me? Please?")
    o += say('Yardrat Elder', "First, a test. My three apprentices are hiding around the village. Catch all three of them. They will not make it easy.")
    o += ['stop', 'label %s_hint' % s] + say('Yardrat Elder', "Catch all three of my apprentices. They blink away the first time you reach them, so feel for where they went.") + ['stop']
    o += ['label %s_teach' % s] + say('Yardrat Elder', "All three! You are quicker than you look. Now, close your eyes. Feel for the energy of someone far away...")
    o += say('goku', "...I can feel Krillin! And Chi-Chi, and Master Roshi... and way out there, King Kai! It's like they're right next to me!")
    o += say('Yardrat Elder', "Then go to them. That is Instant Transmission.")
    o += ['set_flag %d' % LEARNED, 'do call 194 %d' % st.bal.quest_exp(AREA, True)]
    o += say(None, "Goku learned Instant Transmission! Choose it with L and press B where no enemy is near to go anywhere you've been.") + ['stop']
    o += ['label %s_done' % s] + say('Yardrat Elder', "Where no enemy is near, Instant Transmission takes you anywhere you have been. Near one, it takes you behind him. Use it kindly.") + ['stop']
    # the apprentices: one talk where they start, which sends them elsewhere, and one where they end up
    lines = [("Ha! Too slow, Earthling!", "Okay, okay, you got me! How did you find me so fast?"),
             ("You'll never catch me! Bye!", "Hey! I was sure you'd look by the cliffs. You're good."),
             ("Oh! Um. Look over there! *blink*", "Fine, I'm caught. Please don't tell the Elder I hid behind a rock.")]
    for k, (first, caught) in enumerate(lines):
        o += ['list yd_s%da' % k, 'set_flag %d' % NOOP] + say('Apprentice', first) + ['set_flag %d' % (BLINK + k), 'stop']
        o += ['list yd_s%db' % k, 'set_flag %d' % NOOP, 'if_flag %d yd_s%db_c' % (CAUGHT + k, k)] + say('Apprentice', caught) + ['set_flag %d' % (CAUGHT + k), 'stop']
        o += ['label yd_s%db_c' % k] + say('Apprentice', "The Elder is waiting for you in the middle of the village.") + ['stop']
    # Instant Transmission: one travel list per place, which src/flight.c's picker runs
    import log1_world
    spot = log1_world.spots(log1, st.ids, None)
    for n, name in PLACES:
        if n == KING_KAI: spot[n] = KK_SPOT
        if n in spot: o += ['list it_%d' % n, 'set_flag %d' % NOOP, 'do call 120 20; call 119 26 %d 1 %d %d; call 121 20' % (n + 1, spot[n][0], spot[n][1]), 'stop']
    o += ['list dbgscene_yardrat_map', 'set_flag %d' % NOOP, 'do call 120 20; call 118 0 50 0 %d %d; call 121 20' % (log1_world.YARDRAT_AT[0] + 16, log1_world.YARDRAT_AT[1] + 40), 'stop']   # test: on the map below Yardrat
    return o


def king_kai(st):
    """Lines put first in King Kai's talk (set 43): after the ending, the only way back to his planet is Instant Transmission, and he teaches the
    Spirit Bomb for it (the owner, Nov 9: "a post game secret reward ... maybe King Kai again")."""
    k = lambda t: st.say([dict(who='kingkai', text=t)]); g = lambda t: st.say([dict(who='goku', text=t)])
    o = ['unless_flag %d kk_pg_skip' % POSTGAME, 'if_flag %d kk_pg_done' % SPIRIT]
    o += k("Wh-what?! Goku! How did you get all the way out here? You didn't die again, did you?")
    o += g("Nope! The people on Yardrat taught me Instant Transmission. I felt your energy and here I am!")
    o += k("Instant Transmission... hmph. Showing off. Well, since you came all this way, there is one last technique I never taught you.")
    o += k("Raise your hands to the sky and borrow a little energy from every living thing: the trees, the animals, the people. All of it, gathered into one ball.")
    o += k("The Spirit Bomb! Only someone with a pure heart can use it. Gather it in a fight, then let it fly. It takes a while to grow, so pick your moment!")
    o += g("Wow, thanks, King Kai! Hey, want to hear a joke? Why did the Saiyan cross Snake Way? To get to the other... side!")
    o += k("...Pfft. Hah! HAHAHA! Okay, that one was good. Now get out of here!")
    o += ['set_flag %d' % SPIRIT, 'do call 194 %d' % st.bal.quest_exp(AREA, True)]
    o += say(None, "Goku learned the Spirit Bomb! Choose it with L and press B in a fight. It grows over Goku's head, then flies the way he faces.") + ['stop']
    o += ['label kk_pg_done'] + k("Go on, the Spirit Bomb needs time to grow. And come back when you have a new joke!") + ['stop', 'label kk_pg_skip']
    return o


def install(n, a, fits, r, actors, put, named, spawns, BB=0x08000000):
    """Area 69's people: the Elder and three apprentices. Returns the object records to add to the area."""
    def spot(x, y):
        for d in range(0, 200, 4):
            for ox in range(-d, d + 1, 4):
                for oy in range(-d, d + 1, 4):
                    if max(abs(ox), abs(oy)) == d and fits(a, x + ox, y + oy): return x + ox, y + oy
        raise ValueError((n, x, y))
    recs = []
    def rec(idx, x, y, cond, talk):
        x, y = spot(x, y); return struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, cond, (y << 16) | x, talk, idx, 1, 0)
    elder = actors.actor(ELDER['sprite'], False, tint(ROBES['elder']), 'yardrat_elder')
    recs.append(rec(elder, *ELDER['at'], 0x20002, named['yd_elder']))
    for k, s_ in enumerate(STUDENTS):
        idx = actors.actor(s_['sprite'], False, tint(ROBES[s_['look']]), 'yardrat_' + s_['look'])
        recs.append(rec(idx, *s_["a"], 0x20000 | (BLINK + k), named["yd_s%da" % k]))           # where he starts, until he blinks away (0x20000: while the flag is clear)
        b = put(rec(idx, *s_['b'], 0x20002, named['yd_s%db' % k])); struct.pack_into('<I', r, b - BB + 32, b)
        spawns.append((BLINK + k, n, b + 8, idx, CAUGHT + k))                                   # where he ends up (not once caught)
        spawns.append((CAUGHT + k, n, 0, idx, 0))                                                # caught: gone
    return recs
