"""Post-game allies: Vegeta, Piccolo and Krillin join the party (Buu's Fury's own party system: record +0 bit 0, native 151 join, Switch Character).

L + SELECT opens Buu's Fury's Switch Character screen (src/flight.c) once anyone has joined. All text here is original. No art is stored: the figures
are made at build time from Legacy of Goku II's player animations (rom/log12.gba, the LoG I & II cart), the way Buu's Fury Ultimate makes its armoured
Vegeta and Piccolo (ultimate/build.py, ultimate/actors.json), recoloured to Legacy of Goku I's colours (the owner, Nov 9: "still use LoG1 accurate
sprites especially for Vegeta").

    actors(act)                   before act.finish(): the new figures; returns {name: actor value (id + 9)}
    form_rows(rows, first, figs)  the form table's new rows; returns (bytes, {name: form})
    lists(st)                     scene lists: joins, the gravity room, Switch Character
    talk_prefix(st, s)            lines put first in a LoG1 talk set (Dr. Brief's gravity machine)
    checks(st)                    lines for side_check, which runs after a side enemy dies
    install(...)                  each area's new people and enemies (log1_areas, as log1_side.install)

Vegeta (the owner, Nov 9): after the ending he waits at Capsule Corp and joins when Goku talks to him. Dr. Brief then opens the gravity machine
to Vegeta alone: three holograms of Kakarot at 100 times Earth's gravity. Beating them makes him a Super Saiyan.
"""
import os, struct, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import sprites  # noqa: E402

NOOP = 895
B = 0x08000000
COMBO = os.path.join(ROOT, 'rom', 'log12.gba')
FORMS, FORM_COUNT, FORM_SIZE = 0x6B82EC, 54, 24
OBJ_PAL = 0x701B0 + 768
MENU_SLOTS = {2, 8, 9, 103, 193, 217, 218, 223, 224, 225, 236}
# Buu's Fury slot -> LoG2 animation (BFU actors.json "_slots"): 0 idle, 1 walk, 2 run, 3 hurt and fall, 4 charge, 5 ki, 6-8 melee
SLOTS = {0: 0, 1: 1, 2: 2, 3: '4@0:3', 4: 6, 5: 7, 6: 8, 7: '3@0:1', 8: 5, 9: 5, 10: 4, 12: 0, 13: 4, 14: 7, 15: '3@0:1', 16: 3, 17: 3, 18: '3@3:0:-1', 19: 0, 20: 6, 21: 5}
# LoG2 colour -> LoG1 colour: LoG2's violet suit and olive shoulder pads become LoG1's deep blue and gold
LOG1_VEGETA = {79: (49, 49, 189), 80: (41, 41, 148), 81: (0, 0, 98), 40: (238, 189, 0), 41: (205, 160, 4), 42: (172, 131, 8)}
FIGURES = {
    'vegeta': dict(template=270, log2='r134', colours=LOG1_VEGETA),
    'vegeta_ss': dict(template=273, log2='r136', colours=LOG1_VEGETA),
    'piccolo': dict(template=213, log2='r101', colours={}, overrides={9: 5, 21: 5}),        # BFU's Piccolo (its log2_overrides)
    # LoG2's Krillin (bald, Turtle School gi, as in LoG1) has animations 0-6 and 12 (flying): the rest borrow the nearest
    'krillin': dict(template=157, log2='r73', colours={}, overrides={5: 6, 6: 6, 14: 5, 15: 12, 18: 5, 22: 4, 23: 6}),
}
# Bardock (his vision, post-game: tools/log1_bardock.py): LoG2 Vegeta's armoured animations with LoG2 Goku's head, in Bardock's colours. A form of
# Goku's own record, which src/skills.c puts on while Goku is on Planet Vegeta (area 70).
def _bardock_spec():
    import log1_bardock
    return dict(template=270, log2=log1_bardock.VEGETA, colours=log1_bardock.COLOURS, conv=log1_bardock.bardock_anim)
# form rows: copy = Buu's Fury's row used as the template, owner = character record
ROWS = [dict(id='vegeta', copy=26, figure='vegeta', owner=4, up='vegeta_ss', portrait='vegeta1'),
        dict(id='vegeta_ss', copy=28, figure='vegeta_ss', owner=4, down='vegeta', portrait='vegeta1'),
        dict(id='piccolo', copy=49, figure='piccolo', owner=1, flags=0x10, portrait='piccolo'),
        dict(id='krillin', copy=48, figure='krillin', owner=2, flags=0x10, portrait='krillin1'),          # Buu's Fury's guest Piccolo row; 0x10: earns EXP
        dict(id='bardock', copy=0, figure='bardock', owner=0)]                                               # a form of Goku's: his base row
PORTRAITS = {}                                       # LoG1 speaker -> portrait (speaker id), set by slice_build from log1_portraits
# moves on joining (src/skills.c party_join): Energy Blast first, as everyone in Buu's Fury. Vegeta: Galick Gun and Big Bang (the owner, Nov 9),
# and Super Saiyan from the gravity room. Piccolo: his LoG2 moves, Scatter Shot (new: five Energy Blasts fanned out), Energy Punch and the Special Beam Cannon.
# Krillin: the Destructo Disc, the Kamehameha and the Solar Flare (all his in the series).
VEGETA, PICCOLO, KRILLIN = 4, 1, 2                                          # their records: Vegeta's own, Gohan's and Goten's (never played here)
SKILLS = {VEGETA: (7, 26, 2), PICCOLO: (7, 29, 8, 27), KRILLIN: (7, 28, 15, 25)}      # Krillin: Destructo Disc, Kamehameha, Solar Flare
LEAN = {VEGETA: (110, 115, 100), PICCOLO: (100, 105, 115), KRILLIN: (95, 100, 95)}       # strength, power, endurance against the player's
FIRST_FORM = 54 + 2                                                          # Buu's Fury's 54, the two Kaioken rows (build_skills.KAIOKEN), then ROWS
BARDOCK_FORM = FIRST_FORM + [r_['id'] for r_ in ROWS].index('bardock')      # src/skills.c BARDOCK_FORM
JOIN = 232                                                                   # native party_join(character, form)
ADD_SKILL = 164                                                              # native: add a skill (character, skill)
QF, POSTGAME = 420, 420 + 68
VEG_JOINED, GRAV_OPEN, GRAV_KILLED, GRAV_DONE, AS_VEGETA = 404, 405, 406, 409, 410   # GRAV_KILLED: three; AS_VEGETA: src/skills.c keeps it = playing as Vegeta
PIC_JOINED, KRI_JOINED = 411, 412
CAPSULE, BRIEF_SET, LOOKOUT = 20, 13, 15
PICCOLO_NPC = dict(sprite='piccolo', at=(264, 232))
ROSHI_ISLAND, KRILLIN_SET = 0, 47                                            # Kame House; Krillin's LoG1 talk set                                                  # Capsule Corp's lab; Dr. Brief's LoG1 talk set
VEGETA_NPC = dict(sprite='vegeta1', at=(184, 96))
HOLOGRAMS = [(64, 80), (184, 80), (124, 52)]
HOLO_TINT = (96, 232, 255)
u32 = lambda r, o: struct.unpack_from('<I', r, o)[0]


def colour_map(l2, bf, colours):
    """LoG2 OBJ index -> Buu's Fury OBJ index, after LoG1's colours."""
    from room_test import lab
    pl = np.frombuffer(l2[sprites.L2_PAL + 768:sprites.L2_PAL + 1536], np.uint8).reshape(256, 3).astype(np.int64).copy()
    for i, c in colours.items(): pl[i] = c
    pal = np.frombuffer(bytes(bf[OBJ_PAL:OBJ_PAL + 768]), np.uint8).reshape(256, 3)
    usable = [i for i in range(1, 256) if i not in MENU_SLOTS]
    P, Q = lab(pal[usable]), lab(pl)
    m = np.array(usable)[((Q[:, None] - P[None]) ** 2).sum(2).argmin(1)]
    m[0] = 0
    return m.astype(np.uint8)


def player_lengths(r, table):
    """Longest animation per slot across Buu's Fury's player forms: skills pick frames by number (BFU player_anim_lengths)."""
    out = {}
    for f in range(FORM_COUNT):
        ch = struct.unpack_from('<H', r, FORMS + FORM_SIZE * f + 0x0E)[0]
        if ch < 9: continue
        rec = table[ch - 9] - B
        for s in range(u32(r, rec) & 0xFF):
            a = u32(r, rec + 0x54 + 4 * s)
            if a: out[s] = max(out.get(s, 0), u32(r, a - B))
    return out


def figure(act, l2, spec, lengths):
    r = act.r; tp = act.table[spec['template']] - B; n = u32(r, tp) & 0xFF
    rec = bytearray(r[tp:tp + 0x54 + 4 * min(n, 22)]) + bytes(4 * (24 - min(n, 22)))       # 24 slots: 22 = charge pose, 23 = charged hit
    struct.pack_into('<I', rec, 0, (u32(rec, 0) & ~0xFF) | 24); struct.pack_into('<I', rec, 0x50, 0)
    src = sprites.log2_rec(l2, spec['log2']); cmap = colour_map(l2, r, spec['colours']); cache = {}
    has_fire = u32(l2, src + 0x4C + 16 * 18 + 8)
    plan = {**SLOTS, 18: 18 if has_fire else 5, 22: 13, 23: 16, **spec.get('overrides', {})}
    for slot, k in plan.items():
        old = u32(rec, 0x54 + 4 * slot); want = u32(r, old - B) if old else 0
        k, sl = (str(k).split('@') + [None])[:2]
        sl = slice(*map(int, sl.split(':'))) if sl else None
        p = (spec.get('conv') or sprites.log2_anim)(act.ins, l2, src, int(k), cmap, cache, want, sl)
        if p: struct.pack_into('<I', rec, 0x54 + 4 * slot, p)
    for slot, want in lengths.items():                  # at least as long as a retail player's
        if slot >= 24: continue
        ap = u32(rec, 0x54 + 4 * slot)
        if not ap: continue
        k = u32(r, ap - B)
        if k >= want: continue
        old = struct.unpack_from('<%dI' % (4 * k), r, ap - B + 4)
        grown = [old[(i * k // want) * 4 + d] for i in range(want) for d in range(4)]
        struct.pack_into('<I', rec, 0x54 + 4 * slot, act.ins.put(struct.pack('<I', want) + struct.pack('<%dI' % len(grown), *grown)))
    act.table.append(act.ins.put(bytes(rec)))
    return len(act.table) - 1 + 9


def actors(act):
    l2 = open(COMBO, 'rb').read()[0x800000:]; lengths = player_lengths(act.r, act.table)
    out = {name: figure(act, l2, spec, lengths) for name, spec in FIGURES.items()}
    out['bardock'] = figure(act, l2, _bardock_spec(), lengths)
    return out


def form_rows(rows, first, figs):
    """rows: the form table so far (Buu's Fury's, then the Kaioken's); first: the next row's number."""
    index = {row['id']: first + k for k, row in enumerate(ROWS)}; out = bytearray()
    for row in ROWS:
        x = bytearray(rows[FORM_SIZE * row['copy']:FORM_SIZE * (row['copy'] + 1)])
        if 'flags' in row: struct.pack_into('<H', x, 0, row['flags'])
        x[0x0C] = row['owner']; struct.pack_into('<H', x, 0x0E, figs[row['figure']])
        if row.get('portrait') in PORTRAITS: x[0x10:0x16] = bytes([PORTRAITS[row['portrait']]]) * 6       # the status page and the dialogue face
        x[0x16] = index[row['up']] if 'up' in row else 255; x[0x17] = index[row['down']] if 'down' in row else 255
        out += x
    return bytes(out), index


def narrate(text):
    from convert_log1 import split_line
    return ['say narrator ' + p for p in split_line(text)]
def say(st, who, text, name=None):
    """With the speaker's portrait when the build has one, else their name in the box."""
    if who == 'goku' or who in st.por: return st.say([dict(who=who, text=text)])
    return narrate('%s: %s' % (name or who.title(), text))


def lists(st):
    o = ['list party_switch', 'set_flag %d' % NOOP, 'do call 141 16', 'stop']           # Switch Character (menu 16)
    o += ['list dbgscene_join_all', 'set_flag %d' % NOOP, 'do call %d %d %d' % (JOIN, VEGETA, FIRST_FORM), 'set_flag %d' % VEG_JOINED,
          'do call %d %d %d' % (JOIN, PICCOLO, FIRST_FORM + 2), 'set_flag %d' % PIC_JOINED,
          'do call %d %d %d' % (JOIN, KRILLIN, FIRST_FORM + 3), 'set_flag %d' % KRI_JOINED, 'stop']     # test: everyone joins
    V = lambda t: say(st, 'vegeta1', t); G = lambda t: say(st, 'goku', t)
    o += ['list party_vegeta', 'set_flag %d' % NOOP]
    o += V("Kakarot. Don't look so pleased to see me. Frieza is dead, and the one who should have killed him... wasn't me.")
    o += G("Vegeta! You're staying at Capsule Corp? Bulma said you eat more than I do!")
    o += V("Hmph. This planet's food is the only thing on it worth my time. And you. I will surpass you, Kakarot. So I'll train where I can watch you.")
    o += G("Great! Let's train together, then!")
    o += V("Don't misunderstand. I am not your friend.")
    o += ['do call %d %d %d' % (JOIN, VEGETA, FIRST_FORM), 'set_flag %d' % VEG_JOINED, 'do call 194 1']
    o += narrate("Vegeta joined! Hold L and press SELECT to switch characters.") + ['stop']
    P_ = lambda t: say(st, 'piccolo', t)
    o += ['list party_piccolo', 'set_flag %d' % NOOP]
    o += P_("Goku. I felt you coming. Kami and I share the same mind, so I'll say it for both of us: the Earth is quiet now.")
    o += G("Yeah! Isn't it great?")
    o += P_("It's dull. Frieza is gone, but there will be others. Someone has to keep you from going soft, and the Lookout has nothing left to teach me.")
    o += P_("I'm coming with you. Don't make it weird.")
    o += ['do call %d %d %d' % (JOIN, PICCOLO, FIRST_FORM + 2), 'set_flag %d' % PIC_JOINED, 'do call 194 1']
    o += narrate("Piccolo joined! Hold L and press SELECT to switch characters.") + ['stop']
    return o


def ui_text(path):
    """The party records' names on the status page: Piccolo and Krillin stand in Gohan's and Goten's records."""
    with open(path, 'w', encoding='utf-8') as f:
        for ui, name in ((159, 'Piccolo'), (175, 'PICCOLO'), (160, 'Krillin'), (176, 'KRILLIN')): f.write('[ui:%d]\n= %s\n\n' % (ui, name))


def holo_tint(pal):
    """A LoG1 Goku as a hologram: every colour a shade of cyan, outlines kept."""
    out = pal.copy()
    for i, (r, g, b) in enumerate(pal):
        v = max(r, g, b) / 255
        if v < 0.2: continue
        out[i] = [int(c * (0.35 + 0.65 * v)) for c in HOLO_TINT]
    return out


def talk_prefix(st, s):
    if s == KRILLIN_SET:
        K = lambda t: say(st, 'krillin1', t); G = lambda t: say(st, 'goku', t)
        o = ['unless_flag %d kr_skip' % POSTGAME, 'if_flag %d kr_skip' % KRI_JOINED]
        o += K("Goku! Man, it's boring around here now. Master Roshi just reads magazines, and the turtle beats me at cards.")
        o += G("Then come with me, Krillin! There's always someone strong out there to fight!")
        o += K("Ha! Just like old times, huh? Okay, but if anything scary shows up, I'm hiding behind you. Destructo Disc and all!")
        o += ['do call %d %d %d' % (JOIN, KRILLIN, FIRST_FORM + 3), 'set_flag %d' % KRI_JOINED, 'do call 194 1']
        o += narrate("Krillin joined! Hold L and press SELECT to switch characters.") + ['stop', 'label kr_skip']
        return o
    if s != BRIEF_SET: return []
    B_ = lambda t: say(st, 'capslnut', t, 'Dr. Brief'); V = lambda t: say(st, 'vegeta1', t)
    o = ['unless_flag %d gr_skip' % VEG_JOINED, 'if_flag %d gr_done' % GRAV_DONE, 'unless_flag %d gr_other' % AS_VEGETA, 'if_flag %d gr_hint' % GRAV_OPEN]
    o += B_("Ah, Vegeta! The gravity machine is ready. One hundred times Earth's gravity, just as you asked. Please don't break it again.")
    o += B_("Bulma added a training program, too. Holograms of Goku! They hit like the real thing, she says. I don't ask how she knows.")
    o += V("Holograms of Kakarot. ...Turn it on.")
    o += ['set_flag %d' % GRAV_OPEN] + narrate("The gravity machine hums. Three holograms of Goku flicker into the room!") + ['stop']
    o += ['label gr_hint'] + B_("The holograms are still running, Vegeta! Three of them!") + ['stop']
    o += ['label gr_other'] + B_("Vegeta keeps asking about the gravity machine. Would you send him over? I think he has something to prove.") + ['stop']
    o += ['label gr_done'] + B_("The gravity machine needs a new fuse. And a new floor. And a new ceiling. Worth it, though!") + ['stop', 'label gr_skip']
    return o


def checks(st):
    """In side_check: the last hologram down makes Vegeta a Super Saiyan."""
    V = lambda t: say(st, 'vegeta1', t)
    o = ['if_flag %d pc_grav' % GRAV_DONE] + ['unless_flag %d pc_grav' % (GRAV_KILLED + i) for i in range(len(HOLOGRAMS))] + ['set_flag %d' % GRAV_DONE]
    o += V("Hah... hah... One hundred times gravity, and I'm still standing. No. Not good enough. NOT GOOD ENOUGH!")
    o += narrate("Vegeta's rage boils over... and his hair flashes gold!")
    o += V("This power... So this is what you felt, Kakarot. I am a Super Saiyan too. Now we'll see who's stronger!")
    o += ['do call %d %d 20' % (ADD_SKILL, VEGETA), 'do call 194 %d' % st.bal.quest_exp(41, True)]
    o += narrate("Vegeta learned Super Saiyan!") + ['label pc_grav']
    return o


def install(n, a, fits, r, actors, put, named, spawns, foe, BF_IDX):
    """Capsule Corp's Vegeta and his holograms. foe: log1_side's foe() for this area."""
    BB = 0x08000000
    def spot(x, y):
        for d in range(0, 200, 4):
            for ox in range(-d, d + 1, 4):
                for oy in range(-d, d + 1, 4):
                    if max(abs(ox), abs(oy)) == d and fits(a, x + ox, y + oy): return x + ox, y + oy
        raise ValueError((n, x, y))
    if n == LOOKOUT:
        x, y = spot(*PICCOLO_NPC['at']); idx = BF_IDX.get(PICCOLO_NPC['sprite']) or actors.actor(PICCOLO_NPC['sprite'], False)
        rec = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, (y << 16) | x, named['party_piccolo'], idx, 1, 0)); struct.pack_into('<I', r, rec - BB + 32, rec)
        spawns.append((POSTGAME, n, rec + 8, 0, PIC_JOINED)); spawns.append((PIC_JOINED, n, 0, idx, 0))
    if n == ROSHI_ISLAND: spawns.append((KRI_JOINED, n, 0, BF_IDX['krillin1'], 0))         # he travels with Goku now
    if n != CAPSULE: return
    x, y = spot(*VEGETA_NPC['at']); idx = BF_IDX.get(VEGETA_NPC['sprite']) or actors.actor(VEGETA_NPC['sprite'], False)
    rec = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, (y << 16) | x, named['party_vegeta'], idx, 1, 0)); struct.pack_into('<I', r, rec - BB + 32, rec)
    spawns.append((POSTGAME, n, rec + 8, 0, VEG_JOINED)); spawns.append((VEG_JOINED, n, 0, idx, 0))      # after the ending, until he joins; then gone
    for i, (hx, hy) in enumerate(HOLOGRAMS):
        foe('goku', hx, hy, 'set:%d & set:%d & clear:%d' % (GRAV_OPEN, AS_VEGETA, GRAV_KILLED + i), GRAV_KILLED + i, 6, False, 41, tint=holo_tint, look='hologram')
