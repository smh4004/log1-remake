"""Replace Buu's Fury's start with LoG1's: boot logos, intro movie, title picture and title song, all taken from your ROM at build time.

Screens go in as plain mode 4 pictures, and the boot code (src/boot.c) runs before Buu's Fury's start-up. Nothing from the ROMs is stored in the repo.
"""
import os, struct, subprocess, tempfile
from PIL import Image
import build_flight
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 0x08000000
LEGAL, INFOGRAMES, WEBFOOT, SPLASH, TITLE = 0x1C7B50, 0xFE4C, 0xFE58, 0x4DEDD8, 0x19BCDC   # image headers {palette, pixels, flags} in LoG1: the logo title, then the one behind Press Start
MOVIE = 0x337248                                                       # the boot movie
STORY_MOVIES = (0x4E4F44, 0x1CA168)                                    # the two played in the story, by scene 11 and scene 21
TITLE_SONG, GAME_OVER_SONG = 15, 17                                    # LoG1's song numbers: 15 plays from the intro movie through the title, 17 on its game over screen (sub_08004D5C)
BF_DEATH_TRACK = 8                                                     # the track Buu's Fury's "You have died!" script plays
BF_TITLE_TRACK, TRACK_BASE, TABLE_REF = 45, 53, 0x8F8
MENU_X, MENU_Y = (0x524A, 0x5284), ((0x5256, 88), (0x5294, 102))        # the title menu's position, moved to where LoG1 has Press Start
BF_TITLE_PICS, BF_TITLE_PAL = (0x5414, 0x1E744, 0x1E9E0), 0x5458         # the title and menu screens' picture pointers, and the title's palette, in Buu's Fury
OVERLAY_RANGES = ((0x51E8, 0x5228), (0x1E4A0, 0x1E540), (0x1E774, 0x1E810))
MENU = (1, 2, 6, 16, 24, 25, 28, 31, 62, 64, 65, 77, 78, 79, 80, 109, 110, 111, 113, 127)   # palette entries the title menu draws with, measured on Buu's Fury


def image(log1, gfx, header):
    pal, pix, _ = struct.unpack_from('<3I', log1, header)
    im = Image.open(os.path.join(gfx, 'blocks', 'gUnknown_%08X.png' % pix)); assert im.mode == 'P' and im.size == (240, 160)
    return log1[pal - B:pal - B + 512], im.tobytes()


STORY_FONT, STORY_TEXT, T_LAST = 0x15B2F0, 0x5C2E1A, 104                # LoG1's font record (palette, tiles) and opening text


def identity(r):
    """A game of its own: emulators pick a save file by the header's title and code, and Buu's Fury or any hack of it would otherwise share saves with this game.
    Slots of any other game then fail their checksum, whose start value changes here, and show as New Game, so their data is never read as this game's."""
    assert r[0x3FC5A:0x3FC5C] == b'\x01\x24'; r[0x3FC5A] = 0x4C
    r[0xA0:0xAC] = b'LEGACYGOKU1R'; r[0xAC:0xB0] = b'ZLG1'; r[0xBD] = (-sum(r[0xA0:0xBD]) - 0x19) & 0xFF


def nop(r, off, halves):
    for i in range(halves): struct.pack_into('<H', r, off + 2 * i, 0x46C0)


def title_picture(palette, pixels, bf_palette, menu):
    """The menu is drawn on the picture with Buu's Fury's colours, so those palette entries stay and the picture's own colours move to spare ones."""
    used = sorted(set(pixels)); free = [i for i in range(1, 256) if i not in used and i not in menu]; moved = {}; pal = bytearray(palette)
    for i in used:
        if i in menu or i == 0:
            if not free: raise ValueError('title palette is full')
            k = free.pop(0); moved[i] = k; pal[2 * k:2 * k + 2] = palette[2 * i:2 * i + 2]
    for i in menu: pal[2 * i:2 * i + 2] = bf_palette[2 * i:2 * i + 2]
    return bytes(pal[:2]) + bytes(pal[2:]), bytes(moved.get(p, p) for p in pixels)


def install(r, log1, L, menu):
    import bios, log1_music                                            # bios: log1-decomp's tools/assets, on the path from slice_build
    gfx = os.path.join(L, 'assets', 'gfx')

    def put(b):
        while len(r) % 4: r.append(0)
        o = len(r); r.extend(b); return B + o

    # Title song
    table = struct.unpack_from('<I', r, TABLE_REF)[0] - B
    r[table + 20 * BF_TITLE_TRACK:table + 20 * BF_TITLE_TRACK + 20] = r[table + 20 * (TRACK_BASE + TITLE_SONG):table + 20 * (TRACK_BASE + TITLE_SONG) + 20]
    r[table + 20 * BF_DEATH_TRACK:table + 20 * BF_DEATH_TRACK + 20] = r[table + 20 * (TRACK_BASE + GAME_OVER_SONG):table + 20 * (TRACK_BASE + GAME_OVER_SONG) + 20]
    # Title picture
    pal, pix = image(log1, gfx, TITLE); bf_pal = bytes(r[0x5652C:0x5652C + 512]); pal, pix = title_picture(pal, pix, bf_pal, menu)
    pic = put(struct.pack('<II', 0, len(pix)) + pix); struct.pack_into('<I', r, BF_TITLE_PAL, put(pal))
    for lit in BF_TITLE_PICS:
        assert struct.unpack_from('<I', r, lit)[0] == 0x083BE3D4; struct.pack_into('<I', r, lit, pic)
    for start, end in OVERLAY_RANGES:                                  # the calls that draw Buu's Fury's characters and menu art over the picture
        n = 0
        for o in range(start, end, 2):
            h, l = struct.unpack_from('<HH', r, o)
            if h >> 11 == 0x1E and l >> 11 == 0x1F:
                off = (h & 0x7FF) << 12 | (l & 0x7FF) << 1
                if o + 4 + (off - 0x800000 if off & 0x400000 else off) == 0x3F9D4: nop(r, o, 2); n += 1
        assert n == 1, hex(start)
    # Boot screens and movie
    rows = bytearray()
    for head, hold in ((LEGAL, 150), (INFOGRAMES, 150), (WEBFOOT, 150)):
        p, x = image(log1, gfx, head); rows += struct.pack('<III', put(p), put(x), hold)
    rows += bytes(12); screens = put(bytes(rows))
    p, x = image(log1, gfx, SPLASH); splash = put(struct.pack('<III', put(p), put(x), 180))
    for o in MENU_X: r[o] = 75
    for o, y in MENU_Y: r[o] = y
    size = struct.unpack_from('<I', log1, MOVIE)[0]; assert struct.unpack_from('<H', log1, MOVIE + 4)[0] == 0xAF11; movie = put(log1[MOVIE:MOVIE + size])
    mv = [put(log1[o:o + struct.unpack_from('<I', log1, o)[0]]) for o in STORY_MOVIES]
    # The opening after New Game: LoG1's story text, font and palette
    f = struct.unpack_from('<II', log1, STORY_FONT); assert f[1] - B == STORY_FONT + 12
    font = bios.unpack(log1, f[1] - B)[0]; assert len(font) >= (T_LAST + 1) * 32
    e_ = log1.index(b'\0', STORY_TEXT); story = [put(font[:(T_LAST + 1) * 32]), put(log1[f[0] - B:f[0] - B + 32]), put(log1[STORY_TEXT:e_ + 1])]
    # Boot code
    while len(r) % 4: r.append(0)
    at = len(r); d = tempfile.mkdtemp(); o, e, b = (os.path.join(d, n) for n in ('b.o', 'b.elf', 'b.bin'))
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-Os', '-ffreestanding', '-nostdlib', '-DSCREENS=0x%X' % screens, '-DMOVIE=0x%X' % movie, '-DSTORY_FONT=0x%X' % story[0], '-DSTORY_PAL=0x%X' % story[1], '-DSTORY_TEXT=0x%X' % story[2], '-DSFX_BASE=%d' % log1_music.SFX_BASE, '-DSPLASH=0x%X' % splash, '-DTITLE_SONG=0x%X' % (B + table + 20 * BF_TITLE_TRACK), '-c', os.path.join(ROOT, 'src', 'boot.c'), '-o', o])
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-nostdlib', '-Wl,-Ttext=0x%X' % (B + at), '-Wl,-e,boot_entry', o, '-lgcc', '-o', e])
    subprocess.check_call(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.text', e, b]); r.extend(open(b, 'rb').read())
    entry = int(next(l.split()[0] for l in subprocess.check_output(['arm-none-eabi-nm', e]).decode().splitlines() if l.endswith('boot_entry')), 16)
    play = int(next(l.split()[0] for l in subprocess.check_output(['arm-none-eabi-nm', e]).decode().splitlines() if l.endswith('play_movie')), 16) | 1
    pstory = int(next(l.split()[0] for l in subprocess.check_output(['arm-none-eabi-nm', e]).decode().splitlines() if l.endswith('play_story')), 16) | 1
    build_flight.EXTRA[:] = ['-DPLAY_STORY=0x%X' % pstory, '-DPLAY_MOVIE=0x%X' % play, '-DMOVIE_A=0x%X' % mv[0], '-DMOVIE_B=0x%X' % mv[1]]
    # main: skip Buu's Fury's first logo, and run this in place of the rest of them
    nop(r, 0x41A6, 5)
    struct.pack_into('<HHHI', r, 0x41D2, 0x4B01, 0x4718, 0x46C0, entry | 1)
    return len(pix), size
