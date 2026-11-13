"""Checks Expanded Namek (tools/log1_namek.py) on a built ROM: the walk east from the landing village through the Namek Highlands to Elder
Moori's Village and back, a house's door both ways, Moori's two requests (six stragglers, three lost children), their rewards, and Porunga's
three wishes.

    python3 tools/namek_test.py <rom> <dir>

<rom>.lists.json must sit beside the ROM. Prints one line per check and exits 1 if any failed.
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
head = open(os.path.join(ROOT, 'tools', 'movies_test.py')).read()
exec(head[:head.index("run(open(os.path.join(ROOT, 'tools', 'routes'")])         # the movie test's helpers: run, rd, flags, place, go, beat, text_done...
import log1_namek as N  # noqa: E402
ITEMS = 0x0300106A


def walk_into(area, rect, tag):
    """From just inside the map next to an edge rectangle, walk into it."""
    x0, y0, x1, y1 = rect; a = area_map(area); y = (y0 + y1) // 2
    if x0 == 0: x, key = x1 + 20, 'LEFT'
    else: x, key = x0 - 24, 'RIGHT'
    for dy in range(0, 60, 4):
        for yy in (y - dy, y + dy):
            if fits(a, x, yy): run(place(x, yy, 2 if key == 'LEFT' else 3) + ['10', '40 ' + key, '200'], tag); return
    raise ValueError((area, rect))


def people():
    """Characters standing in the area: [(obj, x, y)] (as npcs(), with their objects)."""
    b = rd(0x03001C4C, 0x80); out = []; me = player()
    for i in range(31):
        p = struct.unpack_from('<I', b, 4 + 4 * i)[0]
        if 0x02000000 <= p < 0x02040000 and p != me and struct.unpack('<I', rd(p + 0x14, 4))[0] == 0x03001B0C:
            x, y = [v >> 8 for v in struct.unpack('<2i', rd(p + 0x1A0, 8))]
            if 0 < x < 4096 and 0 < y < 4096: out.append((p, x, y))
    return out


def talk_near(at, tag):
    """Talks to whoever stands nearest the spot."""
    p = people(); assert p, 'nobody here'
    _, x, y = min(p, key=lambda q: abs(q[1] - at[0]) + abs(q[2] - at[1]))
    talk(x, y, tag); text_done(tag)
    return x, y


def senzu(): return rd(ITEMS + 11, 1)[0]


run(open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().split('\n') + ['140'], 'new')
cur[0] = 'new'; run(setf(M.POSTGAME) + ['w8 %08x e7' % (REC + 0x18), 'w8 %08x 03' % (REC + 0x19)] + w32(0x03001574, 999 << 16) + ['w8 %08x c8' % (REC + 0x28 + i) for i in range(3)], 'post')
import map_convert as MC  # noqa: E402
for (fa, fs, fr), (ta, ts, tr) in N.PATHS:
    N.EDGES[(fa, fs)] = N.edge(area_map(fa), fits, fs, *fr); N.EDGES[(ta, ts)] = N.edge(area_map(ta), fits, ts, *tr)

go(N.LANDING, 'land'); moves(); text_done('land'); check('the Namekians point Goku east', flag(N.HINT) == 1)
walk_into(N.LANDING, N.EDGES[(N.LANDING, 'east')][0], 'hl'); check('east of the landing village: the Namek Highlands', area_no() == N.HIGHLANDS, area_no())
check('the highlands have their creatures', len(foes()) > 0, foes())
walk_into(N.HIGHLANDS, N.EDGES[(N.HIGHLANDS, 'east')][0], 'vil'); check("past them: Elder Moori's Village", area_no() == N.VILLAGE, area_no())
cur[0] = 'vil'; run(['30'], 'vil2'); walk_into(N.VILLAGE, N.EDGES[(N.VILLAGE, 'west')][0], 'back'); check('and back west into the highlands', area_no() == N.HIGHLANDS, area_no())

cur[0] = 'vil2'; mx, my = talk_near(N.MOORI['at'], 'moori'); check('Moori asks for help', flag(N.MET) == 1 and flag(N.Q1_OPEN) == 1, (flag(N.MET), flag(N.Q1_OPEN)))
# a house, both ways (the first of the village's doors: LoG1's area 31 door into 32)
cur[0] = 'moori'; run(place(852, 256, 1) + ['10', '30 UP', '200'], 'house'); check('a house door opens into it', area_no() == N.HOUSE_A, area_no())
run(['20', '40 DOWN', '200'], 'house2'); check('and out again', area_no() == N.VILLAGE, area_no())

cur[0] = 'moori'; walk_into(N.VILLAGE, N.EDGES[(N.VILLAGE, 'west')][0], 'hl2')
for s, squad in enumerate(N.SQUADS):                                      # each squad: go near it, then punch its soldiers down
    x, y = squad[0]; a_ = area_map(N.HIGHLANDS)
    near_ = next(((x + dx, y + dy) for d in range(0, 120, 8) for dx in (-d, 0, d) for dy in (-d, 0, d) if fits(a_, x + dx, y + dy)), (x, y))
    run(place(*near_) + ['60'], 'sq%d' % s)
    for k in range(20):
        if all(flag(N.STRAGGLER + 2 * s + j) for j in range(2)): break
        f = [q for q in foes() if any(abs(q[3][0] - sx) < 60 and abs(q[3][1] - sy) < 60 for sx, sy in squad)]
        if not f: run(['30'], 'sq%d' % s); continue
        p, fx, fy, _ = f[0]
        run(w32(0x03001574, 999 << 16) + w32(p + 0x28C, 1) + place(fx, fy + 20, 1) + ['2 A', '40'], 'sq%d' % s)
    text_done('sq%d' % s)
check("Frieza's six stragglers fall", all(flag(N.STRAGGLER + i) for i in range(6)), [flag(N.STRAGGLER + i) for i in range(6)])
check('and the last one is noted', flag(N.SAID_DONE) == 1)
for i, k in enumerate(N.KIDS):
    talk_near(k['at'], 'kid%d' % i); check('%s is found and sent home' % k['name'], flag(N.FOUND + i) == 1, flag(N.FOUND + i))
check('nothing broke out there', player() >> 24 == 2)

walk_into(N.HIGHLANDS, N.EDGES[(N.HIGHLANDS, 'east')][0], 'vil3'); run(['60'], 'vil3')
home = [p for p in people() if any(abs(p[1] - hx) < 24 and abs(p[2] - hy) < 24 for hx, hy in N.HOME)]
check('the children are home', len(home) >= 3, home)
sz = senzu(); st0 = stats(); talk_near((mx, my), 'pay1'); check('Moori pays for the stragglers: Saiyan Boots', flag(N.Q1_PAID) == 1)
talk_near((mx, my), 'pay2'); check('and for the children: three Senzu Beans', flag(N.Q2_PAID) == 1 and senzu() == sz + 3, (flag(N.Q2_PAID), sz, senzu()))
talk_near((mx, my), 'pg')
L = []
for i in range(60): L += ['2 A', '30']
run(L + ['300'], 'pg'); text_done('pg')
check("Porunga's three wishes (the first choice each time: +5 stats)", flag(N.PG_DONE) == 1 and all(b >= min(255, a + 15) for a, b in zip(st0, stats())), (flag(N.PG_DONE), st0, stats()))
check('and the sky clears', flag(N.DB_DARK) == 0)
check('and Goku is free to go', moves() and player() >> 24 == 2)
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
