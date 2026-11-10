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
            '-DMASTERY_L2=%d' % MASTERY_L2, '-DMASTERY_L3=%d' % MASTERY_L3]
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-Os', '-ffreestanding', '-fno-builtin', '-nostdlib', '-fshort-wchar', *defs, '-c', os.path.join(ROOT, 'src', 'skills.c'), '-o', o])
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-nostdlib', '-T', ld, '-Wl,-e,player_input', o, '-lgcc', '-o', e])
    heads = subprocess.check_output(['arm-none-eabi-objdump', '-h', e]).decode()
    for l in heads.splitlines():
        p = l.split()
        if len(p) > 2 and p[1] == '.data': assert int(p[2], 16) == 0, 'skills.c has writable statics: they would sit in ROM'
    subprocess.check_call(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.text', e, b])
    sym = {l.split()[2]: int(l.split()[0], 16) for l in subprocess.check_output(['arm-none-eabi-nm', e]).decode().splitlines() if len(l.split()) == 3}
    return open(b, 'rb').read(), sym


def install(r, red, named):
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
    return {'code': len(code), 'end': hex(at), 'forms': kmap}
