"""Checks the post-game allies (tools/log1_party.py) on a built ROM: who waits where and when, joining, L + SELECT's Switch Character screen,
moving and fighting as each ally, Vegeta's gravity room and Super Saiyan, and the status page.

    python3 tools/party_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM. Prints one line per check and exits 1 if any failed.
"""
import json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_party as P  # noqa: E402
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


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
run(['2 L+SELECT', '60'], 'alone'); check('L + SELECT does nothing with no one in the party (no scouter, no save)', who() == 0 and player() >> 24 == 2 and moves())
cur[0] = 'new'; run(w32(0x0300617C, LISTS['20']) + ['300'], 'cc_early'); check('Capsule Corp: no Vegeta before the ending', len(npcs()) == 1, npcs())
cur[0] = 'new'; run(setf(P.POSTGAME), 'post')
# Krillin, at Kame House
run(['20'], 'post2'); k = near((280, 240), npcs()); talk(*k, 'kr'); r = rec(P.KRILLIN)
check('Krillin joins at Kame House', flag(P.KRI_JOINED) and r['bits'] & 1 and r['skills'] == [7, 28, 15, 25], r)
check('and leaves the island with Goku', k not in npcs(), npcs())
# Piccolo, at the Lookout
run(w32(0x0300617C, LISTS['15']) + ['300'], 'lk'); p_ = near(P.PICCOLO_NPC['at'], npcs()); talk(*p_, 'pc'); r = rec(P.PICCOLO)
check('Piccolo joins at the Lookout', flag(P.PIC_JOINED) and r['bits'] & 1 and r['skills'] == [7, 29, 8, 27], r)
# Vegeta, at Capsule Corp
run(w32(0x0300617C, LISTS['20']) + ['300'], 'cc'); v = near(P.VEGETA_NPC['at'], npcs()); talk(*v, 'vg'); r = rec(P.VEGETA)
check('Vegeta joins at Capsule Corp, in his armour (LoG1 colours)', flag(P.VEG_JOINED) and r['bits'] & 1 and r['skills'] == [7, 26, 2] and r['form'] == P.FIRST_FORM, r)
check('Vegeta leaves the lab once he has joined', v not in npcs(), npcs())
talk(120, 112, 'brief0'); check('Dr. Brief keeps the gravity machine for Vegeta', not flag(P.GRAV_OPEN))
# Switch Character: Goku, Piccolo, Krillin, Vegeta (record order)
for k, (c, name) in enumerate(((P.PICCOLO, 'Piccolo'), (P.KRILLIN, 'Krillin'), (P.VEGETA, 'Vegeta'))):
    cur[0] = 'brief0'; switch(k + 1, 'as%d' % c)
    check('L + SELECT: switch to %s, who walks' % name, who() == c and moves(), (who(), pos()))
cur[0] = 'as%d' % P.VEGETA; run(['2 START', '90', 'shot status', '4 B', '60'], 'st'); check('the status page opens as Vegeta', player() >> 24 == 2 and who() == P.VEGETA)
for c, slot, name in ((P.VEGETA, 1, 'Galick Gun'), (P.VEGETA, 2, 'Big Bang'), (P.PICCOLO, 3, 'Special Beam Cannon'), (P.PICCOLO, 2, 'Energy Punch'), (P.PICCOLO, 1, 'Scatter Shot'), (P.KRILLIN, 1, 'Destructo Disc'), (P.KRILLIN, 2, 'Kamehameha')):
    cur[0] = 'as%d' % c; check('%s fires' % name, fire(c, slot, name.replace(' ', '_')))
# the gravity room
cur[0] = 'as%d' % P.VEGETA; talk(120, 112, 'brief'); check('as Vegeta, Dr. Brief opens the gravity room', flag(P.GRAV_OPEN) == 1)
holo = [q for q in npcs() if q != (120, 112)]; check('three holograms of Goku', len(holo) == 3, holo)
b = rd(0x03001C4C, 0x80); me = player(); L = []
for i in range(31):
    p = struct.unpack_from('<I', b, 4 + 4 * i)[0]
    if 0x02000000 <= p < 0x02040000 and p != me: L += w32(p + 0x28C, 1)
run(L + ['20'], 'weak')
for k in range(4):
    left = [q for q in npcs() if q != (120, 112)]
    if not left: break
    x, y = near(pos(), left); run(place(x, y + 20, 1) + ['2 A', '15', '2 A', '15', '2 A', '60'], 'hit%d' % k)
run(['2 A', '40'] * 30 + ['200'], 'graved')          # his lines, the level-ups, the new move
check('beating them makes Vegeta a Super Saiyan', flag(P.GRAV_DONE) == 1 and 20 in rec(P.VEGETA)['skills'], rec(P.VEGETA))
run(w8(REC + 0x68 * P.VEGETA + 0x15, rec(P.VEGETA)['skills'].index(20)) + ['4', '3 B', '200'], 'ssv')
check('Super Saiyan Vegeta (the armoured recolour)', rec(P.VEGETA)['form'] == P.FIRST_FORM + 1, rec(P.VEGETA)['form'])
run(['4 START', '120', '4 B', '200'] * 3, 'menus'); check('the pause menu opens and closes three times as Vegeta', player() >> 24 == 2)
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
