"""Checks the movie bosses (tools/log1_movies.py) on a built ROM, film by film (Cooler, Turles, Lord Slug): none before the ending, before
the film ahead of it is won or before its lead-in; the lead-in; the villain's arrival in his arena, his three soldiers, the area's animals
keeping away; each phase after the one before falls (Cooler's final form and Gohan's Senzu, Gohan as a Great Ape drawn big, Turles after the
fruit, giant Slug drawn big, Gohan's whistle stunning him, the dark sky while Slug is here); the reward once, and the arena quiet (and its
animals back) afterwards.

    python3 tools/movies_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM. Prints one line per check and exits 1 if any failed.
"""
import json, os, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H = os.environ.get('HARNESS') or os.path.join(ROOT, 'out', 'harness')
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_movies as M  # noqa: E402
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
        if 0x02000000 <= p < 0x02040000 and p != me and struct.unpack('<I', rd(p + 0x14, 4))[0] == 0x03001B0C:     # characters only, not effects
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



def foes():
    """Live streamed enemies (src/flight.c's slots at 0x03006180): [(obj, x, y, where it spawns)]."""
    b = rd(0x03006180, 14 * 8); out = []
    for i in range(14):
        row, p = struct.unpack_from('<2I', b, 8 * i)
        if row and 0x02000000 <= p < 0x02040000:
            hp = struct.unpack('<i', rd(p + 0x28C, 4))[0]
            if hp > 0: x, y = [v >> 8 for v in struct.unpack('<2i', rd(p + 0x1A0, 8))]; out.append((p, x, y, struct.unpack('<HH', rd(row + 6, 4))))
    return out
import map_convert as MC  # noqa: E402
from log1_areas import fits  # noqa: E402
AREA = {}
def area_map(n): return AREA.setdefault(n, MC.Area(os.path.join(ROOT, 'out', 'converted', 'log1data'), n))
def spot(n, x, y):
    """Where log1_side's foe() puts an enemy asked for at (x, y): the nearest place it fits."""
    a = area_map(n)
    for d in range(0, 200, 4):
        for ox in range(-d, d + 1, 4):
            for oy in range(-d, d + 1, 4):
                if max(abs(ox), abs(oy)) == d and fits(a, x + ox, y + oy): return x + ox, y + oy
SPOTS = {}
for f in M.FILMS:
    for ph in f['phases']: SPOTS[id(ph)] = [spot(f['area'], *at) for at in M.spots(f, ph)]
OURS = {tuple(at) for v in SPOTS.values() for at in v}
def near(f): return [q for q in f if q[3] in OURS]                  # the films' villains and soldiers, not the areas' own animals
def wildlife(): return [q for q in foes() if q[3] not in OURS]
def beat(tag, rounds=10, only=None, until=None):
    """Each live enemy of ours down to 1 HP, then punched from below until none is left. With until (a kill flag), one punch at a time until that
    flag is set: the next phase stands where this one fell, and a strong Goku would beat it with the same punches."""
    if until is not None:
        until = until if isinstance(until, list) else [until]
        for k in range(60):
            if all(flag(u) for u in until): return True
            f = [q for q in near(foes()) if only is None or q[3] in only]
            if not f: run(['20'], tag); continue
            p, x, y, _ = f[0]; mx = struct.unpack('<H', rd(REC + 0x18, 2))[0]
            run(w32(0x03001574, mx << 16) + w32(p + 0x28C, 1) + place(x, y + 20, 1) + ['2 A', '40'], tag)
        return all(flag(u) for u in until)
    for k in range(rounds):
        f = [q for q in near(foes()) if only is None or q[3] in only]
        if not f: return True
        p, x, y, _ = f[0]; mx = struct.unpack('<H', rd(REC + 0x18, 2))[0]
        run(w32(0x03001574, mx << 16) + ['80'] + w32(p + 0x28C, 1), tag); p, x, y, _ = next((q for q in near(foes()) if q[0] == p), f[0])   # full HP, back on his feet
        run(w32(p + 0x28C, 1) + place(x, y + 20, 1) + ['2 A', '15', '2 A', '15', '2 A', '60'] + ['2 A', '30'] * 4 + ['60'], tag)
    return not [q for q in near(foes()) if only is None or q[3] in only]
def go(area, tag): run(['2 B', '30'] * 4 + w32(0x0300617C, LISTS[str(area)]) + ['300'] + ['2 A', '30'] * 10 + ['2 B', '30'] * 4 + ['100'], tag)
def approach(f, rect=None, area=None):
    """A short clear walk into the arena (or rect) from just outside one of its edges, nearest the middle of that edge: (x, y, facing, key)."""
    (x0, y0, x1, y1) = rect or M.arena(f); a = area_map(area if area is not None else f['area']); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    best = []
    for t in range(-90, 91, 4):
        for sx, sy, d, key, ix, iy in ((cx + t, y1 + 12, 1, 'UP', 0, -1), (cx + t, y0 - 20, 0, 'DOWN', 0, 1), (x0 - 24, cy + t, 3, 'RIGHT', 1, 0), (x1 + 12, cy + t, 2, 'LEFT', -1, 0)):
            if all(fits(a, sx + ix * k, sy + iy * k) for k in range(0, 40, 4)): best.append((abs(t), sx, sy, d, key))
    if not best: raise ValueError(f['key'])
    return min(best)[1:]
def enter(f, tag):
    """Into the film's area, then walks into its arena from just outside it."""
    x, y, d, key = approach(f)
    go(f['area'], tag); run(place(x, y, d) + ['10', '40 ' + key, '30'] + ['2 A', '30'] * 26 + ['200'], tag)
def lead(f, tag):
    """Into the lead-in's area and a few steps about (or into its rect), then through its lines."""
    if 'lead_rect' in f:
        x, y, d, key = approach(f, f['lead_rect'], f['lead_area'])
        go(f['lead_area'], tag); run(place(x, y, d) + ['10', '40 ' + key, '60'], tag); text_done(tag); run(['200'], tag); text_done(tag); return
    go(f['lead_area'], tag); moves(); run(['20 LEFT', '20 RIGHT', '30'] + ['2 A', '30'] * 16 + ['200'], tag)
def stats(): return list(rd(REC + 0x28, 3))
def area_no(): return rd(struct.unpack('<I', rd(0x03001980, 4))[0] + 1, 1)[0] - 1
def text_done(tag, tries=40, safe=None):
    """Through any open text: A only while Goku can't take a step (a strong Goku's stray punches would beat the next phase). safe: a spot
    away from the fight to stand on while pressing it (a hit knocks him down, and he can't step then either)."""
    for i in range(tries):
        a = pos(); run(['6 DOWN', '4'], tag)
        if pos() != a: run(['6 UP', '4'], tag); return True
        run(['6 LEFT', '4'], tag)
        if pos() != a: run(['6 RIGHT', '4'], tag); return True
        run((place(*safe) if safe else []) + ['2 A', '30'], tag)
    return False
def senzu(): return rd(0x0300106A + 11, 1)[0]                      # Buu's Fury's item counts (tools/dragonball_test.py's ITEMS)
BIG_OBJ = 0x03005F60
def big(): return struct.unpack('<I', rd(BIG_OBJ, 4))[0]
def sparks():
    """Live boss projectiles (src/bosses.c's proj_vt) in the actor list."""
    b = rd(0x03001C4C, 0x200); n = struct.unpack_from('<I', b, 4)[0]; ew = rd(0x02000000, 0x40000)
    ps = [struct.unpack_from('<I', b, 8 + 4 * i)[0] for i in range(min(n, 120))]
    return sum(1 for p in ps if 0x02000000 <= p < 0x0203FFFC and struct.unpack_from('<I', ew, p - 0x02000000)[0] == SYM['proj_vt'])
SYM = {l.split()[-1]: int(l.split()[0], 16) for l in open(os.path.join(ROOT, 'out', 'skills.syms')) if len(l.split()) >= 2}


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
F0 = M.FILMS[0]
enter(F0, 'early'); check('no Cooler before the ending', not flag(F0['met']) and not near(foes()), near(foes()))
cur[0] = 'new'; run(setf(M.POSTGAME) + ['w8 %08x e7' % (REC + 0x18), 'w8 %08x 03' % (REC + 0x19)] + w32(0x03001574, 999 << 16) + ['w8 %08x c8' % (REC + 0x28 + i) for i in range(3)], 'post')   # a post-game Goku: 999 HP, strong
enter(F0, 'nolead'); check('no Cooler before Chi-Chi tells Goku where Gohan went', not flag(F0['met']) and not near(foes()), near(foes()))
for k, f in enumerate(M.FILMS):
    if os.environ.get('ONLY') and f['key'] != os.environ['ONLY']: continue                 # ONLY=bardock: one film (one with no film before it)
    villain = f['phases'][-1]['foes'][0]['name']
    if k and f['gate']:
        cur[0] = 'post'; lead(f, 'gl%d' % k)
        check('%s\'s lead-in waits until %s is beaten' % (villain, M.FILMS[k - 1]['phases'][-1]['foes'][0]['name']), not flag(f['lead']), flag(f['lead']))
        cur[0] = 'won%d' % (k - 1)
    else: cur[0] = 'post'
    s0 = stats(); sz0 = senzu()
    lead(f, 'lead%d' % k); check('%s\'s lead-in plays in area %d' % (villain, f['lead_area']), flag(f['lead']) == 1)
    if 'lead_effects' in f:                                                  # the vision: the lead-in takes Goku there, and he lands in it
        cur[0] = 'lead%d' % k; run(['20'], 'land%d' % k); check('Goku is Bardock on Planet Vegeta', rec(0)['form'] == 60, rec(0))
    else: enter(f, 'land%d' % k)
    check('%s arrives as Goku walks into his arena' % villain, flag(f['met']) == 1)
    if f.get('arrive_effects'): check('the sky over the Earth goes dark', flag(M.SKY_DARK) == 1)
    run(place(f['centre'][0], f['centre'][1] + 50) + ['60', 'shot %s_crew' % f['key']], 'land%d' % k)
    crew = {tuple(at) for at in SPOTS[id(f['phases'][0])]}
    c = near(foes()); check('%s\'s three soldiers' % villain, len(c) == 3 and {q[3] for q in c} == crew, c)
    check('the animals keep away while %s is here' % villain, not wildlife(), wildlife())
    run(['2 START', '90', '4 B', '100'], 'menu'); check('the pause menu works with them about', player() >> 24 == 2)
    cur[0] = 'land%d' % k; ok = beat('sq%d' % k, only=crew, until=f['phases'][0]['kills'])
    check('%s\'s soldiers fall' % villain, ok and all(flag(x) for x in f['phases'][0]['kills']), [flag(x) for x in f['phases'][0]['kills']])
    for i, ph in enumerate(f['phases'][1:], 1):
        s = ph['foes'][0]; tag = '%s%d' % (f['key'], i)
        text_done(tag, safe=approach(f)[:2]); run(place(f['centre'][0], f['centre'][1] + 50) + ['120', 'shot ' + tag], tag); b = near(foes())
        check('%s: %s (%s)' % (f['key'], s['name'], s['look']), flag(ph['said']) == 1 and len(b) == 1 and not flag(ph['kills'][0]), (flag(ph['said']), b))
        if s['look'] == 'cooler2': check('Gohan brings Goku a Senzu Bean', senzu() == sz0 + 1, (sz0, senzu()))
        if 'big' in s: check('%s is drawn big' % s['name'], b and big() == b[0][0], (hex(big()), b))
        bx, by = (b[0][1], b[0][2]) if b else f['centre']; seen = []
        run(place(bx, by + 50) + ['60'], tag + 'a')                           # close enough that he's on screen: his shots vanish off it
        for r_ in range(8): run(w32(0x03001574, 999 << 16) + place(bx, by + 50) + ['2 A', '28', 'shot %s_atk%d' % (tag, r_)], tag + 'a'); seen.append(sparks())
        check('%s attacks (his own moves) and nothing breaks' % s['name'], player() >> 24 == 2 and near(foes()) and max(seen) > 0, seen)
        if s['look'] == 'slug2':
            L = []
            for r_ in range(10): L += w32(0x03001574, 999 << 16) + ['120']
            run(L + ['shot slug_whistle'], 'whistle'); text_done('whistle')
            check('Gohan\'s whistle after giant Slug\'s third attack', flag(M.WHISTLE_DONE) == 1, flag(M.WHISTLE_DONE))
        ok = beat('b%s' % tag, until=ph['kills'][0]); text_done('b%s' % tag, safe=approach(f)[:2]); run(['60'], 'b%s' % tag)
        check('%s falls' % s['name'], ok and flag(ph['kills'][0]) == 1 and (not ('big' in s) or big() == 0), (ok, flag(ph['kills'][0]), hex(big())))
    run(['60'], 'won%d' % k); text_done('won%d' % k); run(['300'] + (place(*approach(f)[:3]) if 'end_effects' not in f or f['key'] != 'bardock' else []) + ['30'], 'won%d' % k)
    if f['key'] == 'bardock': check('Goku wakes at the Crash Site, himself again', rec(0)['form'] == 0 and area_no() == 9, (rec(0), area_no()))     # off the spot the test punched from, which can be inside a tree
    check('%s beaten: his reward, once, and Goku free to go' % villain, moves() and flag(f['paid']) == 1, flag(f['paid']))
    if f['reward'].get('fruit'): check('the fruit of the Tree of Might: +5 to each stat', all(b >= min(255, a + 5) for a, b in zip(s0, stats())), (s0, stats()))
    if f.get('arrive_effects'): check('and the sky clears', flag(M.SKY_DARK) == 0)
    go(5 if f['area'] != 5 else 2, 'away%d' % k); go(f['area'], 'back%d' % k); run(place(*f['centre']) + ['100'], 'back%d' % k)
    check('%s\'s arena is quiet afterwards' % villain, not near(foes()) and player() >> 24 == 2, near(foes()))
    check('and its animals come back', len(wildlife()) > 0 or f['area'] in (23, M.VISION), wildlife())

print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
