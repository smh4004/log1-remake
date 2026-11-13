"""Checks the Earth Dragon Ball hunt (tools/log1_dragonballs.py) on a built ROM: no balls before the radar, Bulma's radar and its readout, each
ball's pickup, the summon, Shenron's wish picker, each wish, and the balls scattering for the next hunt.

    python3 tools/dragonball_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM. Prints one line per check and exits 1 if any failed.
"""
import json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_dragonballs as DB  # noqa: E402
ROM, D = sys.argv[1:3]; os.makedirs(D, exist_ok=True); LISTS = json.load(open(ROM[:-4] + '.lists.json'))
BLANK = os.path.join(D, 'blank.sav'); open(BLANK, 'wb').write(b'\xff' * 8192); os.environ['SAVEF'] = BLANK
FLAGS, REC, CUR = 0x030010BD, 0x03001560, 0x03001068
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
def rec(c): r = rd(REC + 0x68 * c, 0x68); return dict(bits=r[0], form=r[0x14], skills=list(r[0xD:0xD + r[0xC]]), ep=struct.unpack_from('<h', r, 0x1A)[0])
def who(): return rd(CUR, 1)[0]
def player(): return struct.unpack('<I', rd(0x03001C34, 4))[0]
def pos(): return [v >> 8 for v in struct.unpack('<2i', rd(player() + 0x1A0, 8))]
def place(x, y, d=1): p = player(); return ['w8 %08x %02x' % (p + 0x1A0 + i, b) for i, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + w8(p + 0x10, d)
def npcs():
    b = rd(0x03001C4C, 0x80); out = []; me = player()
    for i in range(31):
        p = struct.unpack_from('<I', b, 4 + 4 * i)[0]
        if 0x02000000 <= p < 0x02040000 and p != me:
            x, y = [v >> 8 for v in struct.unpack('<2i', rd(p + 0x1A0, 8))]
            if 0 < x < 4096 and 0 < y < 4096: out.append((x, y))
    return out
def near(at, pts): return min(pts, key=lambda p: abs(p[0] - at[0]) + abs(p[1] - at[1]))
def talk(x, y, tag):
    L = place(x, y + 18) + ['4', '2 A', '40']
    for i in range(30): L += ['2 A', '25']
    run(L, tag); run(w8(player() + 0x10, 0) + ['2 A', '30'] * 8 + ['200'], tag)        # then face away, so the last presses close the box and don't talk again
def switch(rights, tag): run(['10 L', '2 L+SELECT', '10 L', '60'] + ['4 RIGHT', '60'] * rights + ['4 A', '300'], tag)
def moves():
    """Walks somewhere: tries each direction from where it stands."""
    p0, base = pos(), cur[0]
    for d in ('LEFT', 'RIGHT', 'DOWN', 'UP'):
        cur[0] = base; run(['20 ' + d, '10'], '_mv')
        if pos() != p0: cur[0] = base; return True
    cur[0] = base; return False
def fire(c, slot, tag):
    """Hold B with the slot's move, then let go: true when the move spent EP and nothing crashed."""
    ep = rec(c)['ep']; run(w8(REC + 0x68 * c + 0x15, slot) + ['4', '40 B', '8'], tag); spent = rec(c)['ep'] < ep
    run(['20', 'shot ' + tag, '200'], tag)
    return spent and player() >> 24 == 2
def check(name, ok, got=''):
    print('%s  %s%s' % ('ok  ' if ok else 'FAIL', name, '' if ok else '  (got %s)' % (got,)))
    if not ok: fails.append(name)



SP = DB.spots(os.path.join(ROOT, 'out', 'converted', 'log1data')); SPB = DB.spots(os.path.join(ROOT, 'out', 'converted', 'log1data'), SP)
ITEMS = 0x0300106A
def item(i): return rd(ITEMS + i, 1)[0]
def warp(n, tag): run(w32(0x0300617C, LISTS[str(n)]) + ['300'] + ['2 A', '30'] * 14 + ['200'], tag)
def grab(k, tag, more=True, b=False):
    """Walk onto ball k (of the second set with b) from each side in turn until its pickup runs."""
    base = cur[0]; x, y = (SPB if b else SP)[DB.AREAS[k]]; f = (DB.DB_BALL_B if b else DB.DB_BALL) + k
    for (dx, dy, d, key) in ((0, 30, 1, 'UP'), (0, -24, 0, 'DOWN'), (30, 0, 2, 'LEFT'), (-30, 0, 3, 'RIGHT')):
        cur[0] = base; run(place(x + dx, y + dy, d) + ['10', '20 ' + key, '30'], tag)
        if flag(f):
            if more: run(['2 A', '30'] * 6 + ['100'], tag)
            return True
    cur[0] = base; return False
def pick_menu(): return rd(0x03005F30, 2)


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
check('no Dragon Balls during the story (no radar)', all(flag(DB.DB_BALL + k) for k in range(7)) and not flag(DB.DB_RADAR))
run(setf(DB.POSTGAME), 'post'); warp(DB.AREAS[1], 'early'); check('no ball shows before the radar, even after the ending', len(npcs()) == len([q for q in npcs()]) and all(flag(DB.DB_BALL + k) for k in range(7)))
cur[0] = 'post'; talk(320, 192, 'radar')
check('Bulma gives the Dragon Radar after the ending', flag(DB.DB_RADAR) == 1 and not any(flag(DB.DB_BALL + k) for k in range(7)))
talk(320, 192, 'reading'); check('her radar reading leaves Goku free to move', player() >> 24 == 2)
base = 'reading'
for k, n in enumerate(DB.AREAS[:6]):
    cur[0] = base; warp(n, 'a%d' % k)
    ok = grab(k, 'g%d' % k); check('ball %d (%s) picked up: Buu\'s Fury\'s Dragon Ball %d item' % (k + 1, DB.NAMES[n], k + 1), ok and item(DB.ITEM + k) == 1, (SP[n], pos(), flag(DB.DB_BALL + k)))
    base = cur[0]
check('six balls: no summon yet', not flag(DB.DB_SUMMON) and pick_menu()[0] == 0)
def to_picker(tag):
    """Press A through the summon until Shenron's picker is up (A in the picker would choose)."""
    for _ in range(25):
        if pick_menu()[0] == 1: return
        run(['2 A', '40'], tag)
warp(DB.AREAS[6], 'a6'); ok = grab(6, 'g6', more=False); to_picker('sum'); run(['20', 'shot summon'], 'sum')
check('the seventh ball summons Shenron and his wish picker opens', ok and pick_menu()[0] == 1, (ok, pick_menu()))
run(['2 B', '30'], 'sumb'); check('B doesn\'t close Shenron\'s picker', pick_menu()[0] == 1)
r0 = rd(REC + 0x28, 3)
run(['2 A', '30'] + ['2 A', '40'] * 18 + ['200'], 'wished')
r1 = rd(REC + 0x28, 3)
check('"Make me stronger": strength, power and endurance +5', [b - a for a, b in zip(r0, r1)] == [5, 5, 5], (list(r0), list(r1)))
check('the balls scatter to new spots: the second set is out, the items are gone', not any(flag(DB.DB_BALL_B + k) for k in range(7)) and all(flag(DB.DB_BALL + k) for k in range(7)) and not any(item(DB.ITEM + k) for k in range(7)) and flag(DB.DB_WISHED) == 1)
check('the second set is somewhere else in each area', all(abs(SP[n][0] - SPB[n][0]) + abs(SP[n][1] - SPB[n][1]) >= 240 for n in DB.AREAS), (SP, SPB))
# a second hunt, straight to the last ball: the rare-gear wish (the picker's 4th row)
L = []
for k in range(6):
    f = DB.DB_BALL_B + k; L += ['w8 %08x 01' % (ITEMS + DB.ITEM + k)]
by = {}
for k in range(6): f = DB.DB_BALL_B + k; by[f >> 3] = by.get(f >> 3, rd(FLAGS + (f >> 3), 1)[0]) | 1 << (f & 7)
run(L + ['w8 %08x %02x' % (FLAGS + a, v) for a, v in by.items()], 'six')
check('six of the second hunt\'s balls (set by hand)', [flag(DB.DB_BALL_B + k) for k in range(7)] == [1] * 6 + [0], [flag(DB.DB_BALL_B + k) for k in range(7)])
warp(DB.AREAS[5], 'b5'); warp(DB.AREAS[6], 'b6'); ok = grab(6, 'h6', more=False, b=True); to_picker('sum2')
check('the second hunt\'s seventh ball, at its new spot, summons Shenron again', ok and pick_menu()[0] == 1)
gear0 = rd(0x03001068, 0x8A8)
run(['2 RIGHT', '10', '2 RIGHT', '10', '2 RIGHT', '10', '2 A', '30'] + ['2 A', '40'] * 18 + ['200'], 'gear')
check('"Rare gear": the Dragon Armor first', flag(DB.DB_GEAR) == 1, [flag(DB.DB_GEAR + i) for i in range(4)])
check('and the balls scatter back to the first spots', not any(flag(DB.DB_BALL + k) for k in range(7)) and all(flag(DB.DB_BALL_B + k) for k in range(7)))
run(['4 START', '120', '4 B', '200'] * 2, 'menus'); check('the pause menu still opens and closes', player() >> 24 == 2)
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
