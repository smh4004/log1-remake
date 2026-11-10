"""Checks src/skills.c on a built ROM: lore gates, the Kaioken, its mastery and bar, Super Saiyan kept apart from it, the Skills page and level-ups.

    python3 tools/skills_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM (slice_build writes it). Prints one line per check and exits 1 if any failed.
"""
import json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
ROM, D = sys.argv[1:3]; os.makedirs(D, exist_ok=True); LISTS = json.load(open(ROM[:-4] + '.lists.json'))
BLANK = os.path.join(D, 'blank.sav'); open(BLANK, 'wb').write(b'\xff' * 8192); os.environ['SAVEF'] = BLANK
FLAGS, REC, SEL = 0x030010BD, 0x03001560, 0x03001575
MASTERY = REC + 0x68 + 0x22                    # record 1 +0x22: Super Saiyan, +0x23: Kaioken
KK_GUARD = 0x03005F80
cur = [None]; fails = []


def run(lines, save=None):
    p = os.path.join(D, '_r.txt'); open(p, 'w').write('\n'.join((['load ' + cur[0]] if cur[0] else []) + lines + (['save ' + save] if save else [])) + '\n')
    subprocess.run([H, ROM, p, D], capture_output=True)
    if save: cur[0] = save


def rd(a, n): run(['dump _d %08x %x' % (a, n)]); return open(os.path.join(D, '_d.bin'), 'rb').read()
def w8(a, v): return ['w8 %08x %02x' % (a, v)]
def w32(a, v): return ['w8 %08x %02x' % (a + i, b) for i, b in enumerate(struct.pack('<I', v))]
def setq(q): f = 420 + q; return w8(FLAGS + (f >> 3), rd(FLAGS + (f >> 3), 1)[0] | 1 << (f & 7))
def rec():
    r = rd(REC, 0x68)
    return dict(skills=list(r[0xD:0xD + r[0xC]]), form=r[0x14], hp=struct.unpack_from('<h', r, 0x16)[0], levels=[r[0x2E + 2 * i] for i in range(r[0xC])])
def player(): return struct.unpack('<I', rd(0x03001C34, 4))[0]
def check(name, ok, got=''):
    print('%s  %s%s' % ('ok  ' if ok else 'FAIL', name, '' if ok else '  (got %s)' % (got,)))
    if not ok: fails.append(name)
def press(skill, frames=300):
    s = rec()['skills']
    return w8(SEL, s.index(skill)) + ['4', '3 B', str(frames)] if skill in s else [str(frames)]
def cool():
    for _ in range(8):
        if rd(REC + 4, 4) == bytes(4): return
        run(['300'], cur[0])


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
check('new game: Energy Blast only', rec()['skills'] == [7], rec()['skills'])
run(setq(37), 'q37'); run(['140'], 'kk')
check('King Kai (quest 37): Kamehameha, Kaioken and Spirit Bomb', rec()['skills'] == [7, 15, 24, 19], rec()['skills'])
check('no Super Saiyan before Frieza', 20 not in rec()['skills'])
check('no Instant Transmission (Yardrat)', 14 not in rec()['skills'])
run(['10 L', '3 L+RIGHT', '10 L', '20'], 'wheel'); a = rd(SEL, 1)[0]; run(['10 L', '3 L+DOWN', '10 L', '20'], 'wheel2'); b = rd(SEL, 1)[0]
check('quick pick: L+Right the 2nd skill, L+Down the 3rd', (a, b) == (1, 2), (a, b))
hp0 = rec()['hp']; run(press(24, 600), 'on'); r = rec()
check('Kaioken: red form', r['form'] == 54, r['form'])
check('Kaioken: costs health', r['hp'] < hp0, (hp0, r['hp']))
check('Kaioken: trains mastery', rd(MASTERY + 1, 1)[0] > 0)
run(press(20, 200), 'on2')
check('no Super Saiyan in Kaioken', rec()['form'] == 54, rec()['form'])
run(press(24, 200), 'off'); check('Kaioken off', rec()['form'] == 0, rec()['form'])
run(setq(67), 'q67'); run(['140'], 'ss0'); check('Frieza (quest 67): Super Saiyan', 20 in rec()['skills'], rec()['skills'])
cool(); run(press(20, 300), 'ss'); check('Super Saiyan', rec()['form'] == 3, rec()['form'])
run(w8(MASTERY + 1, 250) + ['100'] + press(24, 300), 'ss2'); check('no Kaioken in Super Saiyan, even mastered', rec()['form'] == 3, rec()['form'])
run(press(20, 200), 'ss3'); cool(); hp0 = rec()['hp']
run(press(24, 600), 'kkm'); r = rec()
check('mastered Kaioken: on', r['form'] == 54, r['form'])
check('mastered Kaioken: no health cost', r['hp'] >= hp0, (hp0, r['hp']))
check('mastered Kaioken: its bar', struct.unpack('<H', rd(KK_GUARD, 2))[0] > 0)
check('mastery shown as Level 3', r['levels'][r['skills'].index(24)] == 2, r['levels'])
run(press(24, 200) + ['2 START', '60', '2 DOWN', '40', 'shot skills', '2 SELECT', '30', '2 B', '30', '2 B', '60'], 'menu')
check('Skills page opens and closes', player() >> 24 == 2, hex(player()))
cur[0] = 'kkm'; run(setq(68), 'end'); run(setq(71), 'q71'); run(w8(0x030010BD + (402 >> 3), rd(0x030010BD + (402 >> 3), 1)[0] | 1 << (402 & 7)) + ['200'], 'all')     # after the ending: Solar Flare (quest 71) and Instant Transmission (Yardrat)
r = rec(); known = struct.unpack('<H', rd(REC + 0x22, 2))[0]
check('seven moves: six held, one waiting in the book', len(r['skills']) == 6 and bin(known).count('1') == 7, (r['skills'], hex(known)))
held = r['skills'][:]; run(['2 START', '60', '2 DOWN', '40', '2 SELECT', '30', '2 B', '30', '2 B', '60'], 'swap')
check('SELECT on the Skills page swaps in the waiting move', sorted(rec()['skills']) != sorted(held) and len(rec()['skills']) == 6, (held, rec()['skills']))
cur[0] = 'kkm'; run(w32(0x0300617C, LISTS['x41']) + ['600'], 'lv'); run(['2 A'] * 40 + ['600'], 'lv2')
check('level-ups with held-back moves (no assert)', player() >> 24 == 2 and rec()['skills'][:3] == [7, 15, 24], (hex(player()), rec()['skills']))
run(['shot after_levels'])
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
