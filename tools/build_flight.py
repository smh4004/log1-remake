"""Compile src/flight.c and install it: a bx-pc veneer at 0x0803D4A0 jumps to the code at ROM offset CODE."""
import os, struct, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY, CODE = 0x3D4A0, 0xBF0000


def install(rom, spawns=(), walks=(), picks=(), foes=()):
    """spawns: up to 32 (flag, area entry bus address, record bus address, NPC index to remove or 0) rows for live_spawn."""
    assert len(spawns) <= 32 and len(walks) <= 16
    d = tempfile.mkdtemp(); o, e, b = (os.path.join(d, n) for n in ('f.o', 'f.elf', 'f.bin'))
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-Os', '-ffreestanding', '-nostdlib', '-c', os.path.join(ROOT, 'src', 'flight.c'), '-o', o])
    subprocess.check_call(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-nostdlib', '-Wl,-Ttext=0x%X' % (0x08000000 + CODE), '-Wl,-e,flight_keys', o, '-lgcc', '-o', e])
    subprocess.check_call(['arm-none-eabi-objcopy', '-O', 'binary', '-j', '.text', e, b])
    code = open(b, 'rb').read(); assert len(code) < 0x1000
    if len(rom) < CODE + 0x1000: rom += b'\xff' * (0x1000000 - len(rom))
    rom[CODE:CODE + len(code)] = code
    syms = subprocess.check_output(['arm-none-eabi-nm', e]).decode()
    entry = int(next(l.split()[0] for l in syms.splitlines() if l.endswith('flight_keys')), 16)
    rom[ENTRY:ENTRY + 16] = struct.pack('<HHIII', 0x4778, 0x46C0, 0xE59FC000, 0xE12FFF1C, entry | 1)
    tab = int(next(l.split()[0] for l in syms.splitlines() if l.endswith('spawn_table')), 16) - 0x08000000
    for i, row in enumerate(spawns): struct.pack_into('<4I', rom, tab + 16 * i, *row)
    wt = int(next(l.split()[0] for l in syms.splitlines() if l.endswith('walk_table')), 16) - 0x08000000
    for i, row in enumerate(walks): struct.pack_into('<2I4H', rom, wt + 16 * i, *row)
    pt = int(next(l.split()[0] for l in syms.splitlines() if l.endswith('pick_ptr')), 16) - 0x08000000
    at = CODE + 0x1000
    pack = lambda L: b''.join(struct.pack('<IHHHxxI', a, f_, x, y, rec) for a, f_, x, y, rec in L) + bytes(16)
    tb, tf = pack(picks), pack(foes); assert at + len(tb) + len(tf) < 0xBF8000
    rom[at:at + len(tb)] = tb; struct.pack_into('<I', rom, pt, 0x08000000 + at)
    pf = int(next(l.split()[0] for l in syms.splitlines() if l.endswith('foe_ptr')), 16) - 0x08000000; rom[at + len(tb):at + len(tb) + len(tf)] = tf; struct.pack_into('<I', rom, pf, 0x08000000 + at + len(tb))
    return len(code)


if __name__ == '__main__':
    r = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); print(install(r), 'bytes')
    open(sys.argv[1], 'wb').write(r)
