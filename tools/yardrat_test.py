"""Checks Yardrat and Instant Transmission on a built ROM: the world map landing (post-game only), the Elder's test, learning the move, its picker and
flying back out.

    python3 tools/yardrat_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM. Prints one line per check and exits 1 if any failed.
"""
import json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_yardrat as Y  # noqa: E402
ROM, D = sys.argv[1:3]; os.makedirs(D, exist_ok=True); LISTS = json.load(open(ROM[:-4] + '.lists.json'))
BLANK = os.path.join(D, 'blank.sav'); open(BLANK, 'wb').write(b'\xff' * 8192); os.environ['SAVEF'] = BLANK
FLAGS, REC, SEL = 0x030010BD, 0x03001560, 0x03001575

cur = [None]; fails = []


def run(lines, save=None):
    p = os.path.join(D, '_r.txt'); open(p, 'w').write('\n'.join((['load ' + cur[0]] if cur[0] else []) + lines + (['save ' + save] if save else [])) + '\n')
    subprocess.run([H, ROM, p, D], capture_output=True)
    if save: cur[0] = save


def rd(a, n): run(['dump _d %08x %x' % (a, n)]); return open(os.path.join(D, '_d.bin'), 'rb').read()
def w8(a, v): return ['w8 %08x %02x' % (a, v)]
def w32(a, v): return ['w8 %08x %02x' % (a + i, b) for i, b in enumerate(struct.pack('<I', v))]
def flag(f): return rd(FLAGS + (f >> 3), 1)[0] >> (f & 7) & 1
def setf(f): return w8(FLAGS + (f >> 3), rd(FLAGS + (f >> 3), 1)[0] | 1 << (f & 7))
def area(): a = struct.unpack('<I', rd(0x03001980, 4))[0]; w, n = rd(a, 2); return w, n
def player(): return struct.unpack('<I', rd(0x03001C34, 4))[0]
def pos(): return [v >> 8 for v in struct.unpack('<2i', rd(player() + 0x1A0, 8))]
def place(x, y, d=1): P = player(); return ['w8 %08x %02x' % (P + 0x1A0 + i, b) for i, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + w8(P + 0x10, d)
def skills(): r = rd(REC, 0x68); return list(r[0xD:0xD + r[0xC]])
def npcs():
    """(x, y) of each character object but the player."""
    b = rd(0x03001C4C, 0x80); out = []; me = player()
    for i in range(31):
        p = struct.unpack_from('<I', b, 4 + 4 * i)[0]
        if 0x02000000 <= p < 0x02040000 and p != me:
            x, y = [v >> 8 for v in struct.unpack('<2i', rd(p + 0x1A0, 8))]
            if x > 0: out.append((x, y))
    return out
def talk(x, y, tag):
    L = place(x, y + 18) + ['4', '2 A', '40']
    for i in range(25): L += ['2 A', '25']
    run(L + ['60'], tag)
def near(pt, pts, d=12): return any(abs(pt[0] - q[0]) <= d and abs(pt[1] - q[1]) <= d for q in pts)
def check(name, ok, got=''):
    print('%s  %s%s' % ('ok  ' if ok else 'FAIL', name, '' if ok else '  (got %s)' % (got,)))
    if not ok: fails.append(name)


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
run(w32(0x0300617C, LISTS['dbgscene_yardrat_map']) + ['200', '60 B', '300'], 'early')
check('Yardrat closed before the ending', area() == (0, 50), area())
cur[0] = 'new'; run(setf(Y.POSTGAME), 'post'); run(w32(0x0300617C, LISTS['dbgscene_yardrat_map']) + ['200', '60 B', '300'], 'land')
check('Yardrat open after the ending (hold B under it)', area() == (26, Y.AREA + 1), area())
cur[0] = 'land'; run(['4 START', '120', '4 B', '200'] * 3, 'menus')
check('the pause menu opens and closes three times (Yardrat)', player() >> 24 == 2 and area() == (26, Y.AREA + 1), (hex(player()), area()))
cur[0] = 'land'
people = npcs()
check('the Elder and three apprentices', len(people) == 4, people)
elder = min(people, key=lambda p: abs(p[0] - Y.ELDER['at'][0]) + abs(p[1] - Y.ELDER['at'][1]))
talk(*elder, 'met'); check('the Elder sets the test', flag(Y.MET) == 1)
for k in range(3):
    a = [p for p in npcs() if p != elder]; s = min(a, key=lambda p: abs(p[0] - Y.STUDENTS[k]['a'][0]) + abs(p[1] - Y.STUDENTS[k]['a'][1]))
    talk(*s, 'a%d' % k); run(['30'], 'a%dw' % k)
    check('apprentice %d blinks away' % (k + 1), flag(Y.BLINK + k) == 1 and not near(s, npcs(), 4), npcs())
for k in range(3):
    b = [p for p in npcs() if p != elder]; s = min(b, key=lambda p: abs(p[0] - Y.STUDENTS[k]['b'][0]) + abs(p[1] - Y.STUDENTS[k]['b'][1]))
    talk(*s, 'b%d' % k); check('apprentice %d caught' % (k + 1), flag(Y.CAUGHT + k) == 1)
run(['30'], 'caught'); check('caught apprentices leave', len(npcs()) == 1, npcs())
talk(*elder, 'taught'); run(['2 A', '30'] * 12 + ['300'], 'taught2')      # the lesson's EXP can level Goku up more than once
check('the Elder teaches Instant Transmission', flag(Y.LEARNED) == 1 and 14 in skills(), skills())
run(w8(SEL, skills().index(14)) + ['4', '3 B', '20', 'shot picker'], 'pick')
check('the picker opens', rd(0x03005F30, 1)[0] == 1)
names = [n for _, n in Y.PLACES]; seen = []
for i in range(4):
    seen.append(rd(0x03005F31, 1)[0]); run(['2 RIGHT', '10'], 'pick%d' % i)
check('it offers only places Goku has visited (Roshi\'s Island, Yardrat)', sorted(set(names[i] for i in seen)) == ["Roshi's Island", 'Yardrat'], [names[i] for i in seen])
while names[rd(0x03005F31, 1)[0]] != "Roshi's Island": run(['2 RIGHT', '10'], 'pickr')
run(['2 A', '240'], 'went'); check("A goes there (Roshi's Island)", area() == (26, 1), area())
run(['2 R', '40', '2 L', '300'], 'up'); check('flying up from Earth still reaches the map', area() == (0, 50), area())
cur[0] = 'taught2'; run(['2 R', '40', '2 L', '300'], 'out'); check('flying up from Yardrat reaches the map (not straight back in)', area() == (0, 50), area())
# King Kai's secret: after the ending, Instant Transmission reaches his planet (once visited in the story) and he teaches the Spirit Bomb
cur[0] = 'taught2'; run(setf(Y.VISIT + Y.KING_KAI), 'kkv')
check('no Spirit Bomb before King Kai\'s secret', 19 not in skills(), skills())
run(w8(SEL, skills().index(14)) + ['4', '3 B', '20'], 'kkpick')
while names[rd(0x03005F31, 1)[0]] != "King Kai's Planet": run(['2 RIGHT', '10'], 'kkpick')
run(['2 A', '540'], 'kkwent'); check("Instant Transmission reaches King Kai's Planet", area() == (26, Y.KING_KAI + 1), area())
kk = min(npcs(), key=lambda p: abs(p[0] - 248) + abs(p[1] - 192))
talk(*kk, 'kktalk'); run(['2 A', '30'] * 20 + ['300'] + ['2 A', '60'] * 6 + ['300'], 'kktaught')     # the EXP may level him up
check('King Kai teaches the Spirit Bomb', flag(Y.SPIRIT) == 1 and 19 in skills(), (flag(Y.SPIRIT), skills()))
run(w8(SEL, skills().index(14)) + ['4', '3 B', '20'], 'kkhome')
while names[rd(0x03005F31, 1)[0]] != "Roshi's Island": run(['2 RIGHT', '10'], 'kkhome')
run(['2 A', '540'], 'kkhome2'); check("Instant Transmission takes him home from King Kai's Planet", area() == (26, 1), area())
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
