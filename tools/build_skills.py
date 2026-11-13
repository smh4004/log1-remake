"""Goku's Kaioken, transformation mastery and skill book (src/skills.c), ported from Buu's Fury Ultimate (ultimate/build.py). Nothing here holds art:
the red Goku is made at build time from Buu's Fury's own frames.

    ui_text(path)          before the text build: the Kaioken's name and description
    actors(act)            before act.finish(): red copies of Goku's figures
    install(r, red)        last, after log1_start.alive(): form rows, the skill row, the code and its hooks
"""
import colorsys, os, struct, subprocess, sys, tempfile
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
from wfz import decompress_stream  # noqa: E402

B = 0x08000000
FORMS, FORM_COUNT = 0x6B82EC, 54
SKILL_ROWS, SKILL_COUNT, SKILL_REF = 0x71DAF8, 24, 0x13618
SS_SKILL, IT_SKILL, KAME_SKILL, KAIOKEN_SKILL, SPIRIT_SKILL, SOLAR_SKILL = 20, 14, 15, 24, 19, 25
GALICK_SKILL, SBC_SKILL, DISC_SKILL, SCATTER_SKILL = 26, 27, 28, 29                        # the allies' beams (log1_party): Vegeta's Galick Gun, Piccolo's Special Beam Cannon
NATIVES, JOIN_NATIVE, JOIN_OLD = 0x55098, 0xE8, 0x08003891   # party_join: a native no script calls (BFU's choice)
BEAM_PARAMS, BEAM_VT = 0x71DA68, 0x4D9F8
BLAST_VT = 0x4DC14                                         # Energy Blast's behaviour
BALL_PARAMS, BALL_VT = 0x76ACC0, 0x4D05C                 # Big Bang's: levels 1 and 2 cyan ball, level 3 gold
DISC_POWER = (1.25, 1.25, 1.3)
COMBO = os.path.join(ROOT, 'rom', 'log12.gba')            # the LoG I & II cart: LoG2 from 0x800000 (BFU's USA-cart offsets, moved to it)
L2_BEAM_ART, L2_PAL, L2_BASE = 0x6E46D8, 0x3ED01C, 0x08800000
BOOK = (7, KAME_SKILL, KAIOKEN_SKILL, SPIRIT_SKILL, SS_SKILL, SOLAR_SKILL, IT_SKILL)     # Energy Blast, Kamehameha, Kaioken, Spirit Bomb, Super Saiyan, Solar Flare, Instant Transmission
YARDRAT_FLAG = 402                                         # Instant Transmission: the Yardrat Elder teaches it (log1_yardrat.LEARNED)
SPIRIT_FLAG = 403                                          # the Spirit Bomb: King Kai's post-game secret (log1_yardrat.SPIRIT)
KK_NAME_UI = 1700
MASTERY_L2, MASTERY_L3 = 100, 250
CODE, CODE_END = 0xFC0000, 0x1000000
# Kaioken: Goku's forms -> the actor index (form +0xE less 9) its red copy is made from. 0 base, 2 with the halo (dead, quest 23-37). No Super Saiyan
# Kaioken: this game never puts the two together (the owner, Nov 9).
KAIOKEN = {0: 106, 2: 108}
KAIOKEN_TINT = 0.3
OBJ_PAL = 0x701B0 + 768
MENU_SLOTS = {2, 8, 9, 103, 193, 217, 218, 223, 224, 225, 236}   # OBJ palette entries the menus change at run time
POWER_UP_VT, AURA_FIELD, AURA_OTHER = 0x4E2B0, 0x752D28, 0x7520D4
HP_COLS, HP_BAR = 0x71CB0, 0x7137D8
KK_CYAN = {3: (0, 216, 248), 32: (0, 104, 152), 33: (0, 152, 200), 34: (72, 232, 248), 35: (152, 248, 248)}
u32 = lambda r, o: struct.unpack_from('<I', r, o)[0]


def ui_text(path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('[ui:%d]\n= Spirit Bomb\n\n' % (KK_NAME_UI + 2))
        f.write('[ui:%d]\n= Press the B Button to raise a Spirit Bomb, then throw it the way you face. It hits everything nearby very hard. Costs half your EP.\n\n' % (KK_NAME_UI + 3))
        f.write('[ui:%d]\n= Solar Flare\n\n' % (KK_NAME_UI + 4))
        f.write('[ui:%d]\n= Press the B Button to flash a blinding light: every ordinary enemy on screen is stunned for a few seconds. Bosses are not fooled.\n\n' % (KK_NAME_UI + 5))
        f.write('[ui:%d]\n= Galick Gun\n\n' % (KK_NAME_UI + 6))
        f.write('[ui:%d]\n= Press the B Button and hold it to charge, then release to fire Vegeta\'s violet beam.\n\n' % (KK_NAME_UI + 7))
        f.write('[ui:%d]\n= Special Beam Cannon\n\n' % (KK_NAME_UI + 8))
        f.write('[ui:%d]\n= Press the B Button and hold it to charge, then release to fire a thin, piercing beam from two fingers.\n\n' % (KK_NAME_UI + 9))
        f.write('[ui:%d]\n= Destructo Disc\n\n' % (KK_NAME_UI + 10))
        f.write('[ui:%d]\n= Hold the B Button to form a spinning disc of energy, then let go to throw it. It cuts through almost anything.\n\n' % (KK_NAME_UI + 11))
        f.write('[ui:%d]\n= Scatter Shot\n\n' % (KK_NAME_UI + 12))
        f.write('[ui:%d]\n= Press the B Button to fire five ki blasts at once, fanned out in front of you. Costs three Energy Blasts\' worth of EP.\n\n' % (KK_NAME_UI + 13))
        f.write('[ui:%d]\n= Kaioken\n\n' % KK_NAME_UI)
        f.write('[ui:%d]\n= Press the B Button for the Kaioken: attacks hit 1.25x as hard, up to 1.75x as you master it, but it wears on your health. Not with Super Saiyan. Press it again to change back.\n\n' % (KK_NAME_UI + 1))


def palette(r):
    pal = np.frombuffer(bytes(r[OBJ_PAL:OBJ_PAL + 768]), np.uint8).reshape(256, 3)
    usable = np.array([i for i in range(1, 256) if i not in MENU_SLOTS]); p = pal[usable].astype(int); cache = {}
    def ch(v): return np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
    def one(q):
        q = np.asarray(q, dtype=int); k = tuple(int(v) for v in q)
        if k not in cache: cache[k] = int(usable[(((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)).argmin()])
        return cache[k]
    return pal, one


def kaioken_remap(pal, one):
    def colour(v):
        if v == 0: return 0
        r, g, b = (int(c) for c in pal[v])
        if max(r, g, b) < 48: return v
        a = KAIOKEN_TINT
        return one(np.array((r * (1 - a) + 248 * a, g * (1 - a) * 0.75, b * (1 - a) * 0.75)))
    return bytes(colour(v) for v in range(256))


def shifted(pal, one, hue):
    def colour(v):
        if v == 0: return 0
        h, s, b = colorsys.rgb_to_hsv(*(pal[v] / 255.0))
        if s < 0.12: return v
        return one((np.array(colorsys.hsv_to_rgb(hue, s, b)) * 255).astype(int))
    return bytes(colour(v) for v in range(256))


def tinted_actor(ins, rom, rec_at, remap):
    """A copy of an actor with every frame's pixels through remap. Tiles are stored raw. (BFU lib/sprites.py)"""
    n = u32(rom, rec_at) & 0xFF; rec = bytearray(rom[rec_at:rec_at + 0x54 + 4 * n])
    done, frames, anims = {}, {}, {}
    def tile(tp, w, h):
        if tp not in done:
            o = tp - B; t, size = u32(rom, o), u32(rom, o + 4)
            raw = rom[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(rom, o + 8, size)[0])
            data = bytes(raw[:w * h]).translate(remap)
            done[tp] = ins.put(struct.pack('<II', 0, len(data)) + data)
        return done[tp]
    def frame(fp):
        if fp not in frames:
            o = fp - B; k = u32(rom, o); body = bytearray(rom[o:o + 4 + 16 * k])
            for j in range(k):
                w, h = body[4 + 16 * j + 2], body[4 + 16 * j + 3]
                struct.pack_into('<I', body, 4 + 16 * j + 12, tile(u32(rom, o + 4 + 16 * j + 12), w, h))
            frames[fp] = ins.put(bytes(body))
        return frames[fp]
    for s in range(n):
        ap = u32(rom, rec_at + 0x54 + 4 * s)
        if not ap: continue
        if ap not in anims:
            o = ap - B; k = u32(rom, o)
            ptrs = [frame(u32(rom, o + 4 + 4 * j)) if u32(rom, o + 4 + 4 * j) else 0 for j in range(4 * k)]
            anims[ap] = ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs))
        struct.pack_into('<I', rec, 0x54 + 4 * s, anims[ap])
    return rec


def actors(act):
    """Red copies of Goku's figures. Returns {source actor index: new form actor value (index + 9)}. Their slot 10 (the power-up) is cut so the
    hair never turns gold: from base, the crouch and the shout, then his stance; from Super Saiyan, its first ten frames, then the stance."""
    r = act.r; pal, one = palette(r); red = kaioken_remap(pal, one); out = {}
    for src in sorted(set(KAIOKEN.values())):
        rec = tinted_actor(act.ins, r, act.table[src] - B, red)
        def frame(slot, k):
            a = u32(rec, 0x54 + 4 * slot) - B; assert k < u32(r, a), 'slot %d has no frame %d' % (slot, k)
            return bytes(r[a + 4 + 16 * k:a + 4 + 16 * k + 16])
        assert rec[0] > 10 and u32(r, u32(rec, 0x54 + 40) - B) == 11, 'actor %d: slot 10 is not an 11-frame power-up' % src
        frames = [frame(10, 0)] + [frame(10, 1)] * 9 + [frame(0, 0)] if src in (106, 108) else [frame(10, k) for k in range(10)] + [frame(0, 0)]
        struct.pack_into('<I', rec, 0x54 + 40, act.ins.put(struct.pack('<I', 11) + b''.join(frames)))
        if not u32(rec, 0x54 + 44):        # changing back plays slot 11; the base figures have none, and an empty one draws junk over other sprites' tiles
            struct.pack_into('<I', rec, 0x54 + 44, u32(rec, 0x54))
        out[src] = len(act.table) + 9; act.table.append(act.ins.put(bytes(rec)))
    return out


def thumb_bl(at, to):
    off = to - (at + 4)
    return struct.pack('<HH', 0xF000 | (off >> 12) & 0x7FF, 0xF800 | (off >> 1) & 0x7FF)


def compile_code(at):
    d = tempfile.mkdtemp(); c, o, e, b, ld = (os.path.join(d, n) for n in ('s.c', 's.o', 's.elf', 's.bin', 's.ld'))
    open(ld, 'w').write('SECTIONS { . = 0x%X; .text : { *(.text*) *(.rodata*) } .data : { *(.data*) *(.bss*) *(COMMON) } /DISCARD/ : { *(.comment) *(.ARM.attributes) } }\n' % (B + at))
    defs = ['-DSS_SKILL=%d' % SS_SKILL, '-DIT_SKILL=%d' % IT_SKILL, '-DKAME_SKILL=%d' % KAME_SKILL, '-DKAIOKEN_SKILL=%d' % KAIOKEN_SKILL, '-DSPIRIT_SKILL=%d' % SPIRIT_SKILL, '-DSOLAR_SKILL=%d' % SOLAR_SKILL, '-DYARDRAT_FLAG=%d' % YARDRAT_FLAG, '-DSPIRIT_FLAG=%d' % SPIRIT_FLAG,
            '-DMASTERY_L2=%d' % MASTERY_L2, '-DAS_VEGETA=%d' % __import__('log1_party').AS_VEGETA, *['-D%s=%d' % kv for kv in __import__('log1_dragonballs').C_FLAGS.items()], '-DMASTERY_L3=%d' % MASTERY_L3]
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-Os', '-ffreestanding', '-fno-builtin', '-nostdlib', '-fshort-wchar', *defs, '-c', os.path.join(ROOT, 'src', 'skills.c'), '-o', o])
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-nostdlib', '-T', ld, '-Wl,-e,player_input', o, '-lgcc', '-o', e])
    heads = subprocess.check_output(['arm-none-eabi-objdump', '-h', e]).decode()
    for l in heads.splitlines():
        p = l.split()
        if len(p) > 2 and p[1] == '.data': assert int(p[2], 16) == 0, 'skills.c has writable statics: they would sit in ROM'
    subprocess.check_call(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.text', e, b])
    sym = {l.split()[2]: int(l.split()[0], 16) for l in subprocess.check_output(['arm-none-eabi-nm', e]).decode().splitlines() if len(l.split()) == 3}
    open(os.path.join(ROOT, 'out', 'skills.syms'), 'w').write(''.join('%08x %s\n' % (v, k) for k, v in sorted(sym.items(), key=lambda kv: kv[1])))     # for debugging
    return open(b, 'rb').read(), sym


def install(r, red, named, party=None):
    """red: actors()'s result. Call last: it moves the form table, which log1_start.alive() edits in place."""
    assert set(r[CODE:CODE_END]) <= {0xFF}, 'skills code space is in use'
    clean_rows = bytes(r[SKILL_ROWS:SKILL_ROWS + 24 * SKILL_COUNT]); pal, one = palette(r)
    code, sym = compile_code(CODE); at = (CODE + len(code) + 3) & ~3
    r[CODE:CODE + len(code)] = code
    def put(data):
        nonlocal at
        at = (at + 3) & ~3; o = at; r[o:o + len(data)] = data; at += len(data); assert at <= CODE_END, 'skills space full'
        return B + o
    def fill(name, data):
        o = sym[name] - B; r[o:o + len(data)] = data
    # form rows: the four red ones after Buu's Fury's 54
    rows = bytearray(r[FORMS:FORMS + 24 * FORM_COUNT]); kmap = []
    for base, src in KAIOKEN.items():
        row = bytearray(rows[24 * base:24 * base + 24])
        struct.pack_into('<H', row, 0, 0x51); struct.pack_into('<I', row, 8, 0x03001B78)     # Super Saiyan class, with its behaviour object
        struct.pack_into('<H', row, 0x0E, red[src]); row[0x16] = 255; row[0x17] = base
        kmap.append((base, FORM_COUNT + len(kmap))); rows += row
    party_forms = {}
    if party:
        import log1_party
        more, party_forms = log1_party.form_rows(rows, len(rows) // 24, party); rows += more
    new_forms = put(bytes(rows)); n = 0
    for o in range(0, 0x80000, 4):
        if u32(r, o) == B + FORMS: struct.pack_into('<I', r, o, new_forms); n += 1
    assert n == 37, 'form table: expected 37 code references, found %d' % n
    fill('forms_at', struct.pack('<I', new_forms))
    fill('kaioken_map', bytes(v for p in kmap for v in p) + b'\xff\xff')
    fill('skill_book', bytes(BOOK) + b'\xff' * (8 - len(BOOK)))
    # mastered Kaioken's bar: the health bar's columns in cyan
    offs = [u32(r, HP_COLS + 16 * c + 4 * k) for c in range(41) for k in range(3)]
    assert all(0x200 <= o < 0x500 for o in offs), 'HP bar column table changed'
    img = r[HP_BAR:HP_BAR + 0x300]; assert {img[o - 0x200] for o in offs} <= set(KK_CYAN), 'HP bar colours changed'
    bar = bytearray(0x500)
    for o in offs: bar[o] = one(np.array(KK_CYAN[img[o - 0x200]]))
    fill('kk_bar', bytes(bar))
    # the red aura and the power-up state that shows it
    aura = shifted(pal, one, 4 / 360)
    for name, src, count in (('kk_aura_field', AURA_FIELD, 3), ('kk_aura_other', AURA_OTHER, 7)):
        out = bytearray(r[src:src + 12 * count])
        for k in range(0, 12 * count, 12):
            t = u32(out, k + 8) - B; struct.pack_into('<I', out, k + 8, put(bytes(r[t:t + out[k + 2] * out[k + 3]]).translate(aura)))
        fill(name, bytes(out))
    vt = sym['kk_vt'] - B
    for k in range(14):
        fn = (sym['kk_start'] | 1) if k == 0 else B + POWER_UP_VT + struct.unpack_from('<i', r, POWER_UP_VT + 4 * k)[0]
        struct.pack_into('<i', r, vt + 4 * k, fn - (B + vt))
    # the skill table, moved to add the Kaioken's row (Super Saiyan's with red icons); Super Saiyan's own row checks for the Kaioken and shows its mastery
    assert u32(r, SKILL_REF) == B + SKILL_ROWS, 'skill table reference moved'
    table = bytearray(clean_rows)
    s20 = SKILL_ROWS + 24 * SS_SKILL
    assert struct.unpack_from('<II', r, s20 + 16) == (0x0801A4C5, 0x0801A513), 'Super Saiyan skill row changed'
    struct.pack_into('<II', table, 24 * SS_SKILL + 16, sym['ss_can'] | 1, sym['ss_use'] | 1); table[24 * SS_SKILL] = 2
    assert struct.unpack_from('<II', r, SKILL_ROWS + 24 * IT_SKILL + 16) == (0x0801A217, 0x0801A23B), 'Instant Transmission skill row changed'
    struct.pack_into('<II', table, 24 * IT_SKILL + 16, sym['it_can'] | 1, sym['it_use'] | 1)        # away from enemies: the travel menu
    row = bytearray(clean_rows[24 * SS_SKILL:24 * SS_SKILL + 24]); row[0] = 2
    reds = shifted(pal, one, 0)
    def recolour(icon):
        a = np.zeros((16, 32), np.uint8)
        for t in range(8): a[t // 4 * 8:t // 4 * 8 + 8, t % 4 * 8:t % 4 * 8 + 8] = np.frombuffer(bytes(icon[t * 64:t * 64 + 64]), np.uint8).reshape(8, 8)
        w = a[2:11, 2:20]; a[2:11, 2:20] = np.frombuffer(reds, np.uint8)[w]
        return b''.join(a[t // 4 * 8:t // 4 * 8 + 8, t % 4 * 8:t % 4 * 8 + 8].tobytes() for t in range(8))
    struct.pack_into('<II', row, 4, *[put(recolour(r[p - B:p - B + 0x200])) for p in struct.unpack_from('<II', row, 4)])
    struct.pack_into('<HHII', row, 12, KK_NAME_UI, KK_NAME_UI + 1, sym['kaioken_can'] | 1, sym['kaioken_use'] | 1)
    assert len(table) == 24 * KAIOKEN_SKILL
    table += row
    # Spirit Bomb: Buu's Fury's unused row 19, with the Kamehameha's icons and no level. Solar Flare: Burning Attack's row (4) with pale icons, no level.
    assert struct.unpack_from('<II', clean_rows, 24 * SPIRIT_SKILL + 16) == (0x08019D25, 0x08019D29), 'skill row 19 is in use'
    sb = bytearray(clean_rows[24 * KAME_SKILL:24 * KAME_SKILL + 24]); sb[0] = 0xFF
    struct.pack_into('<HHII', sb, 12, KK_NAME_UI + 2, KK_NAME_UI + 3, sym['spirit_usable'] | 1, sym['spirit_use'] | 1); table[24 * SPIRIT_SKILL:24 * SPIRIT_SKILL + 24] = sb
    pale = bytes(0 if v == 0 else one(np.array([min(255, int(c) + 90) for c in pal[v]])) for v in range(256))
    sf = bytearray(clean_rows[24 * 4:24 * 5]); sf[0] = 0xFF
    def recolour_with(icon, remap):
        a = np.zeros((16, 32), np.uint8)
        for t in range(8): a[t // 4 * 8:t // 4 * 8 + 8, t % 4 * 8:t % 4 * 8 + 8] = np.frombuffer(bytes(icon[t * 64:t * 64 + 64]), np.uint8).reshape(8, 8)
        w = a[2:11, 2:20]; a[2:11, 2:20] = np.frombuffer(remap, np.uint8)[w]
        return b''.join(a[t // 4 * 8:t // 4 * 8 + 8, t % 4 * 8:t % 4 * 8 + 8].tobytes() for t in range(8))
    struct.pack_into('<II', sf, 4, *[put(recolour_with(r[p - B:p - B + 0x200], pale)) for p in struct.unpack_from('<II', sf, 4)])
    struct.pack_into('<HHII', sf, 12, KK_NAME_UI + 4, KK_NAME_UI + 5, sym['solar_can'] | 1, sym['solar_use'] | 1)
    assert len(table) == 24 * SOLAR_SKILL
    table += sf
    assert len(table) == 24 * GALICK_SKILL
    table += beam_rows(r, pal, one, put, fill, sym, clean_rows)
    assert len(table) == 24 * DISC_SKILL
    table += disc_row(r, pal, one, put, fill, sym, clean_rows)
    assert len(table) == 24 * SCATTER_SKILL
    table += scatter_row(r, pal, one, put, sym, clean_rows)
    # the effect slot's methods (0 delete, 2 update every frame)
    vt = sym['spirit_vt'] - B
    for k, name in enumerate(('spirit_destroyed', 'spirit_nop', 'spirit_update', 'spirit_nop', 'spirit_nop', 'spirit_nop')):
        struct.pack_into('<i', r, vt + 4 * k, (sym[name] | 1) - (B + vt))
    struct.pack_into('<I', r, SKILL_REF, put(bytes(table)))
    # hooks
    def site(at_, want, new):
        assert r[at_:at_ + len(want) // 2].hex() == want, 'hook site 0x%X changed: %s' % (at_, r[at_:at_ + len(want) // 2].hex())
        r[at_:at_ + len(new)] = new
    jump = lambda name: bytes.fromhex('004b1847') + struct.pack('<I', sym[name] | 1)
    site(0x1C35C, 'b87d207543001818', jump('xform_hook'))           # a power-up's end: Kaioken chooses its form
    site(0xE42C, '011c1e310a88002a', jump('ss_drain_hook'))         # Super Saiyan's drain: Kaioken's health cost and mastery
    site(0xE9D8, 'f0b5061c0c1c0831', jump('combat_hook'))           # damage: Kaioken's multiplier and the mastered bar's guard
    site(0xBCAE, 'a08971490522400140181202291c3df03cfa',            # the HUD's copy to VRAM: skills_hud(widget, buffer) paints the bar and copies
         bytes.fromhex('201c291c024b') + thumb_bl(0xBCAE + 6, 0x46AA6) + bytes.fromhex('02e0c046') + struct.pack('<I', sym['skills_hud'] | 1))
    # Buu's Fury's level-up script asks the level of moves Goku may not hold yet here (sub_08013BCC asserts on a missing one): a missing move is level 0
    site(0x13BEE, 'ff228e320023', bytes.fromhex('002010bdc046'))
    for vt_, want, name in ((0x4C384, 0x08012D8B, 'state_a'), (0x4BEF0, 0x08012DEF, 'state_b'), (0x4C790, 0x08013023, 'state_c'), (0x4C3A8, 0x080131BB, 'state_d')):
        assert B + vt_ + struct.unpack_from('<i', r, vt_ + 8)[0] == want, 'state vtable changed at 0x%X' % vt_     # the movement states: Spirit Bomb and Solar Flare poses
        struct.pack_into('<i', r, vt_ + 8, (sym[name] | 1) - (B + vt_))
    for vt_, slot, want, name in ((0x4C9F0, 0x84, 0x0804F8C9, 'player_input'), (0x4B024, 4, 0x080171A9, 'skilltab_setup'), (0x4B024, 40, 0x080175FD, 'skilltab_keys')):
        assert B + vt_ + struct.unpack_from('<i', r, vt_ + slot)[0] == want, 'vtable changed at 0x%X' % (vt_ + slot)
        struct.pack_into('<i', r, vt_ + slot, (sym[name] | 1) - (B + vt_))
    # party_join, the allies' native, and their moves
    assert u32(r, NATIVES + 4 * JOIN_NATIVE) == JOIN_OLD, 'native 0x%X changed' % JOIN_NATIVE
    struct.pack_into('<I', r, NATIVES + 4 * JOIN_NATIVE, sym['party_join'] | 1)
    if party:
        import log1_party
        fill('party_skills', b''.join(bytes([len(m)] + list(m) + [0] * (7 - len(m))) for m in (log1_party.SKILLS.get(c, ()) for c in range(8))))
        fill('party_lean', b''.join(bytes(log1_party.LEAN.get(c, (100, 100, 100))) for c in range(8)))
    return {'code': len(code), 'end': hex(at), 'forms': kmap, 'party': party_forms}


def scatter_row(r, pal, one, put, sym, clean_rows):
    """Scatter Shot: Energy Blast's row and behaviour, its update swapped for scatter_update (five shots), its icons green."""
    vt = sym['scatter_vt'] - B
    for k in range(9):
        fn = (sym['scatter_update'] | 1) if k == 1 else B + BLAST_VT + struct.unpack_from('<i', r, BLAST_VT + 4 * k)[0]
        struct.pack_into('<i', r, vt + 4 * k, fn - (B + vt))
    row = bytearray(clean_rows[24 * 7:24 * 8])
    green = bytes(0 if v == 0 else one(np.array((int(min(pal[v]) * 0.5), int(max(pal[v])), int(min(pal[v]) * 0.6)))) for v in range(256))
    struct.pack_into('<II', row, 4, *[put(bytes(r[p - B:p - B + 0x200]).translate(green)) for p in struct.unpack_from('<II', row, 4)])
    struct.pack_into('<HH', row, 12, KK_NAME_UI + 12, KK_NAME_UI + 13)
    struct.pack_into('<I', row, 20, sym['scatter_use'] | 1)
    return bytes(row)


def disc_row(r, pal, one, put, fill, sym, clean_rows):
    """Destructo Disc: Big Bang's ball animations redrawn as a flat, spinning golden disc the size each ball frame was, with Big Bang's code (BFU's
    Eraser Cannon way). The art is drawn here, not taken from anything."""
    gold = [one(np.array(c)) for c in ((120, 72, 0), (232, 168, 0), (248, 216, 40), (248, 248, 160), (255, 255, 255))]
    copies = {}
    def disc(tiles, w, h, spin):
        o = tiles - B; px = np.frombuffer(bytes(r[o:o + w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
        ys, xs = np.nonzero(px)
        rad = (max(xs.max() - xs.min(), ys.max() - ys.min()) + 1) / 2 if len(xs) else w / 4
        a, b = min(w / 2 - 0.5, rad * 1.15), max(1.5, rad * 0.4)
        img = np.zeros((h, w), np.uint8); cy, cx = (h - 1) / 2, (w - 1) / 2
        for y in range(h):
            for x in range(w):
                d = ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2
                if d > 1: continue
                ang = (np.degrees(np.arctan2((y - cy) / b, (x - cx) / a)) + spin) % 90
                img[y, x] = gold[0] if d > 0.82 else gold[4] if d < 0.12 else gold[3] if ang < 18 else gold[2] if d < 0.5 else gold[1]
        return img.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).tobytes()
    def ball(rec):
        out = bytearray(r[rec:rec + 480])
        for k in range(0, 480, 12):
            head, _, tiles = struct.unpack_from('<III', out, k)
            if tiles:
                w, h = head >> 16 & 255, head >> 24 & 255
                if tiles not in copies: copies[tiles] = put(disc(tiles, w, h, 30 * len(copies)))
                struct.pack_into('<I', out, k + 8, copies[tiles])
        return put(bytes(out))
    balls, params = {}, bytearray()
    for i in range(3):
        a, b_, rec, strength = struct.unpack_from('<4I', r, BALL_PARAMS + 16 * i)
        balls.setdefault(rec, ball(rec - B))
        params += struct.pack('<4I', a, b_, balls[rec], int(strength * DISC_POWER[i]))
    fill('disc_params', bytes(params))
    vt = sym['disc_vt'] - B
    for k in range(9):
        fn = (sym['disc_start'] | 1) if k == 0 else B + BALL_VT + struct.unpack_from('<i', r, BALL_VT + 4 * k)[0]
        struct.pack_into('<i', r, vt + 4 * k, fn - (B + vt))
    row = bytearray(clean_rows[24 * 2:24 * 3])         # Big Bang's row, golden icons
    tint = bytes(0 if v == 0 else one(np.array((max(pal[v]), int(max(pal[v]) * 0.8), int(min(pal[v]) * 0.3)))) for v in range(256))
    struct.pack_into('<II', row, 4, *[put(bytes(r[p - B:p - B + 0x200]).translate(tint)) for p in struct.unpack_from('<II', row, 4)])
    struct.pack_into('<HH', row, 12, KK_NAME_UI + 10, KK_NAME_UI + 11)
    struct.pack_into('<I', row, 20, sym['disc_use'] | 1)
    return bytes(row)


def beam_rows(r, pal, one, put, fill, sym, clean_rows):
    """Galick Gun and Special Beam Cannon (BFU's add_eraser): copies of the Kamehameha's frame records, each {header, attributes, tile data} rows,
    recoloured; the Special Beam Cannon's beam itself is LoG2's own art. Returns their two skill rows."""
    rows = b''
    def frames(o, count, remap, copies):
        out = bytearray(r[o:o + 12 * count])
        for k in range(0, 12 * count, 12):
            tiles = u32(out, k + 8)
            if not 0x08700000 <= tiles < 0x08800000: continue
            if tiles not in copies:
                t = tiles - B; copies[tiles] = put(bytes(r[t:t + out[k + 2] * out[k + 3]]).translate(remap))
            struct.pack_into('<I', out, k + 8, copies[tiles])
        return put(bytes(out))
    def remap_of(tint): return bytes(0 if v == 0 else one(np.array(tint.get(v, tuple(pal[v])), dtype=int)) for v in range(256))
    # Galick Gun: the Kamehameha in violet. Special Beam Cannon: BFU's tint (pale yellow core, gold, purple rim).
    GALICK = {2: (248, 232, 255), 30: (248, 232, 255), 29: (232, 184, 255), 76: (208, 136, 255), 28: (208, 136, 255), 5: (208, 136, 255), 195: (176, 80, 248), 27: (176, 80, 248), 110: (176, 80, 248),
              75: (120, 32, 200), 109: (120, 32, 200), 74: (80, 16, 152), 4: (80, 16, 152)}
    SBC = {2: (248, 248, 216), 30: (248, 248, 216), 29: (248, 248, 144), 76: (248, 248, 72), 28: (248, 248, 72), 5: (248, 248, 72), 195: (248, 208, 0), 27: (248, 208, 0), 110: (248, 208, 0),
           75: (168, 48, 224), 109: (168, 48, 224), 74: (112, 24, 168), 4: (112, 24, 168)}
    for name, tint, ui in (('galick', GALICK, KK_NAME_UI + 6), ('sbc', SBC, KK_NAME_UI + 8)):
        remap = remap_of(tint); copies = {}
        head = frames(u32(r, BEAM_PARAMS + 12) - B, 64, remap, copies)
        if name == 'sbc':        # LoG2's beam: 7 rows a facing (muzzle 2, body 3, tip 2) laid into BF's 16-row facings (muzzle 0-1, body 3-5 and spare 6, tip 7-8 and 10-11)
            l2 = open(COMBO, 'rb').read()[0x800000:]; L2_ART = L2_BEAM_ART
            l2pal = np.frombuffer(l2[L2_PAL:L2_PAL + 768], np.uint8).reshape(256, 3).astype(int)
            l2map = bytes(0 if v == 0 else one(l2pal[v]) for v in range(256)); l2tiles = {}
            record = bytearray(r[head - B:head - B + 768])
            for facing in range(4):
                for bf, row in ((0, 0), (1, 1), (3, 2), (4, 3), (5, 4), (7, 5), (8, 6), (10, 5), (11, 6)):
                    hdr, attr, tiles = struct.unpack_from('<III', l2, L2_ART + 12 * (facing * 7 + row))
                    if tiles not in l2tiles:
                        t = tiles - L2_BASE; l2tiles[tiles] = put(l2[t:t + 256].translate(l2map))
                    struct.pack_into('<III', record, 12 * (facing * 16 + bf), hdr, attr, l2tiles[tiles])
                struct.pack_into('<I', record, 12 * (facing * 16 + 6) + 8, u32(record, 12 * (facing * 16 + 5) + 8))
            head = put(bytes(record))
        shape, params = {}, bytearray()
        for i in range(3):
            a, strength, body, _ = struct.unpack_from('<4I', r, BEAM_PARAMS + 16 * i)
            shape.setdefault(body, frames(body - B, 9, remap, copies))
            params += struct.pack('<4I', a, strength, shape[body], head)
        fill(name + '_params', bytes(params))
        vt = sym[name + '_vt'] - B
        for k in range(9):
            fn = (sym[name + '_start'] | 1) if k == 0 else B + BEAM_VT + struct.unpack_from('<i', r, BEAM_VT + 4 * k)[0]
            struct.pack_into('<i', r, vt + 4 * k, fn - (B + vt))
        row = bytearray(clean_rows[24 * KAME_SKILL:24 * KAME_SKILL + 24])
        struct.pack_into('<II', row, 4, *[put(bytes(r[p - B:p - B + 0x200]).translate(remap)) for p in struct.unpack_from('<II', row, 4)])
        struct.pack_into('<HH', row, 12, ui, ui + 1)
        struct.pack_into('<I', row, 20, sym[name + '_use'] | 1)
        rows += bytes(row)
    return rows
