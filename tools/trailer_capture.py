"""Records the release trailer's gameplay clips with the test harness, 30 frames a second, from the game and, for its cutscenes, a test build (SCENE_TEST=1 OUT=trailer).
python3 tools/trailer_capture.py <outdir> [clip ...]. A finished clip is skipped, so a run cut short carries on. Frames stay local: they come from the ROMs."""
import json, os, shutil, struct, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_side as Z
from log1_story import NEW_GAME_SPOT
H = os.path.join(ROOT, 'out', 'harness'); ROM = os.path.join(ROOT, 'out', 'slice', 'slice.gba'); SCENE_ROM = os.path.join(ROOT, 'out', 'slice', 'trailer.gba'); ORIG = os.path.join(ROOT, 'rom', 'log1.gba')
LISTS = dict(json.load(open(os.path.join(ROOT, 'out', 'slice', 'slice.lists.json'))), **{k: v for k, v in json.load(open(os.path.join(ROOT, 'out', 'slice', 'trailer.lists.json'))).items() if k.startswith('dbgscene')}); SCENE_LISTS = json.load(open(os.path.join(ROOT, 'out', 'slice', 'trailer.lists.json'))); STATES = json.load(open(os.path.join(ROOT, 'tools', 'trailer_states.json')))
GAME, FLAGS, QF = 0x03001068, 0x030010BD, 420
OUT = os.path.abspath(sys.argv[1]); WORK = os.path.join(OUT, '_work')


class Run:
    def __init__(self, d, rom=ROM, start=None):
        self.d, self.rom, self.cur, self.n = d, rom, start, 0; os.makedirs(d, exist_ok=True)
        self.sav = os.path.join(d, 'd.sav')
        if not os.path.exists(self.sav): open(self.sav, 'wb').write(b'\xff' * 8192)
        if start and not os.path.exists(os.path.join(d, start + '.ss')): shutil.copy(os.path.join(WORK, start + '.ss'), os.path.join(d, start + '.ss'))

    def run(self, l):
        p = os.path.join(self.d, '_q.txt'); open(p, 'w').write('\n'.join((['load ' + self.cur] if self.cur else []) + l + ['save _n']) + '\n')
        subprocess.run([H, self.rom, p, self.d], capture_output=True, env=dict(os.environ, SAVEF=self.sav)); self.cur = '_n'

    def u(self, a, n=4): self.run(['dump _u %08x %x' % (a, n)]); return open(os.path.join(self.d, '_u.bin'), 'rb').read()
    def u32(self, a): return struct.unpack('<I', self.u(a))[0]
    def pl(self): return self.u32(0x03001C34)
    def pos(self, o=None): return [v >> 8 for v in struct.unpack('<2i', self.u((o or self.pl()) + 0x1A0, 8))]
    def flag(self, f): return self.u(FLAGS + (f >> 3), 1)[0] >> (f & 7) & 1
    def setf(self, f, v=1):
        a = FLAGS + (f >> 3); b = self.u(a, 1)[0]; self.run(['w8 %08x %02x' % (a, (b | 1 << (f & 7)) if v else b & ~(1 << (f & 7)))])
    def game(self, name): self.run(['w8 %08x %02x' % (GAME + i, b) for i, b in enumerate(bytes.fromhex(STATES[name]))] + ['10'])
    def warp(self, a, wait=150):
        self.run(['w8 %08x %02x' % (0x0300617C + i, b) for i, b in enumerate(struct.pack('<I', (SCENE_LISTS if self.rom == SCENE_ROM else LISTS)[str(a)]))] + [str(wait)])
    def scene(self, name): self.run(['w8 %08x %02x' % (0x0300617C + i, b) for i, b in enumerate(struct.pack('<I', LISTS[name]))] + ['4'])
    def place(self, x, y):
        p = self.pl(); self.run(['w8 %08x %02x' % (p + 0x1A0 + k, b) for k, b in enumerate(struct.pack('<2i', x << 8, y << 8))] + ['2'])
    def objs(self):
        c = self.u32(0x03001C50); return [(p, self.pos(p)) for p in struct.unpack('<%dI' % c, self.u(0x03001C54, 4 * c))]
    def enemies(self):
        c = self.u32(0x03001BB0); return struct.unpack('<%dI' % c, self.u(0x03001BB4, 4 * c)) if c else ()
    def heal(self): self.run(['w8 03001576 ff', 'w8 03001577 7f'])
    def rec(self, *steps):
        """steps: (frames, key or ''). Captures every second frame into the clip."""
        l = []
        for fr, k in steps:
            for _ in range(0, fr, 2): l += ['2 ' + k if k else '2', 'shot f%05d' % self.n]; self.n += 1
        self.run(l)


def start_state(rom, name):
    """A new game, past the opening, saved for every clip to start from."""
    d = os.path.join(WORK, 'boot_' + name); s = os.path.join(WORK, name + '.ss')
    if os.path.exists(s): return
    r = Run(d, rom); r.run(['3000', '8 START', '180', '8 START', '180', '8 START', '120', '8 A', '120', '8 A', '200'])
    for _ in range(80):
        if r.pl() and r.pos()[:2] == list(NEW_GAME_SPOT) and r.flag(959): break
        r.run(['8 A', '50'])
    assert r.pos()[:2] == list(NEW_GAME_SPOT), r.pos(); r.run(['60', 'save start']); shutil.copy(os.path.join(d, 'start.ss'), s)


def toward(r, tx, ty, frames=10, reach=26):
    """Runs at a target for a moment; True when close. Returns the key used."""
    x, y = r.pos(); dx, dy = tx - x, ty - y
    if abs(dx) <= reach and abs(dy) <= 8: return True
    return False if r.rec((frames, ('RIGHT' if dx > 0 else 'LEFT') if abs(dx) > abs(dy) else ('DOWN' if dy > 0 else 'UP'))) else False


def fight(r, frames, heal=True):
    """Fights the nearest enemy for about `frames`, stepping beside them whenever they get away, so the clip is all action. A punches, B fires a ki blast."""
    done = 0
    while done < frames:
        E = r.enemies()
        if not E: r.rec((20, '')); done += 20; continue
        x, y = r.pos(); e = min(E, key=lambda o: sum(abs(a - b) for a, b in zip(r.pos(o), (x, y)))); ex, ey = r.pos(e)
        if heal: r.heal()
        if abs(ex - x) > 44 or abs(ey - y) > 18: r.place(ex - 22, ey); x = ex - 22
        k = 'RIGHT' if ex > x else 'LEFT'
        r.rec((2, k), (6, 'A'), (8, ''), (6, 'A'), (8, ''), (6, 'A'), (10, ''), (6, 'B'), (16, '')); done += 68


def talk(r, x, y, presses, step=30):
    r.place(x, y + 12); r.run(['6 UP'])
    r.rec(*[s for _ in range(presses) for s in ((2, 'A'), (step, ''))])


def near(r, at):
    return min(r.objs(), key=lambda q: abs(q[1][0] - at[0]) + abs(q[1][1] - at[1]))[1]


def orig_boot(r):
    r.run(['240']); r.rec((1320, ''))                                                             # logos and movie
def orig_title(r):
    r.run(['3000']); r.rec((150, ''))
def orig_field(r):
    r.run(['3290', '8 START', '60', '8 START', '90']); r.rec(*[s for _ in range(6) for s in ((4, 'A'), (40, ''))])
    r.run(['4 A', '40'] * 30 + ['200']); r.rec((60, 'DOWN'), (40, 'LEFT'), (60, 'RIGHT'), (30, 'UP'))
def new_boot(r):
    r.run(['300']); r.rec((1300, ''))
def new_title(r):
    r.run(['3000', '8 START', '150']); r.rec((90, '')); r.rec((8, 'START'), (120, ''))
def new_opening(r):
    r.run(['3000', '8 START', '180', '8 START', '180', '8 START', '120', '8 A', '120', '8 A', '60']); r.rec((180, '')); r.rec((8, 'A'), (150, ''))
def beach(r):
    r.rec((50, 'RIGHT'), (10, ''), (40, 'LEFT'), (30, 'UP'), (40, 'DOWN'))
def roshi_talk(r):
    r.warp(0); o = near(r, (248, 240)); talk(r, o[0], o[1], 5)
def lost_spirits(r):                                                                               # story-state walk on Snake Way, halo on
    r.setf(QF + 23); r.warp(11); r.rec((80, 'UP'), (40, 'RIGHT'), (60, 'UP'))
def fight_base(r):
    r.game('q52'); r.warp(34); fight(r, 420)
def fly_area(r):
    r.game('q52'); r.warp(0); r.rec((2, 'R'), (30, ''), (50, 'RIGHT'), (40, 'UP'), (40, 'LEFT'))
def fly_map(r):
    r.game('q52'); r.warp(0); r.run(['2 R', '30']); r.rec((2, 'L'), (160, '')); r.rec((90, 'UP'), (30, 'RIGHT'), (90, 'UP'), (30, 'LEFT'), (120, 'UP'))
def fly_namek(r):
    r.game('q52'); r.setf(824); r.warp(0); r.run(['2 R', '30', '2 L', '200']); r.place(3216, 800); r.run(['30'])
    r.rec((300, 'UP'))
    r.rec((150, ''))
def namek_walk(r):
    r.game('q52'); r.warp(24); r.rec((60, 'DOWN'), (50, 'RIGHT'), (50, 'DOWN'), (60, 'LEFT'))
def ape(r):
    r.game('q52'); r.setf(QF + 52, 0); r.warp(23); r.scene('dbgscene_12'); r.rec(*[s for _ in range(170) for s in ((2, 'A'), (24, ''))])
def ssj(r):
    r.game('q67'); r.setf(QF + 67, 0); r.warp(40); r.scene('dbgscene_20'); r.rec(*[s for _ in range(50) for s in ((2, 'A'), (24, ''))])
def frieza(r):
    r.game('q67'); r.setf(QF + 68, 0); r.warp(41); r.place(760, 120); r.run(['60']); fight(r, 360)
def announcer(r):
    r.game('post'); r.setf(Z.RM_OPEN, 0); r.warp(2); r.warp(0); talk(r, 304, 194, 8)
def rematch(r):
    r.game('post'); r.setf(Z.RM_KILLED, 0); r.setf(Z.RM_OPEN, 0); r.warp(2); r.warp(0); r.place(304, 206); r.run(['6 UP'] + ['2 A', '40'] * 8 + ['60']); fight(r, 300)
def butler(r):
    r.game('q52'); r.warp(11); o = near(r, Z.BUTLER['at']); talk(r, o[0], o[1], 6)
def elder(r):
    r.game('q52'); r.setf(QF + 53); r.setf(Z.ELDER_PAID, 0); r.warp(24); o = near(r, Z.ELDER['at']); talk(r, o[0], o[1], 10)
def bounty(r):
    b = Z.BOUNTIES[0]; r.game('q52'); r.warp(b['area']); fight(r, 240)


CLIPS = dict(new_boot=new_boot, new_title=new_title, new_opening=new_opening, beach=beach, roshi_talk=roshi_talk, fly_area=fly_area, fly_map=fly_map, fly_namek=fly_namek, namek_walk=namek_walk, ape=ape, ssj=ssj,
             fight_base=fight_base, frieza=frieza, lost_spirits=lost_spirits, announcer=announcer, rematch=rematch, butler=butler, elder=elder, bounty=bounty)
ORIGS = dict(orig_boot=orig_boot, orig_title=orig_title, orig_field=orig_field)
os.makedirs(WORK, exist_ok=True); start_state(ROM, 'start'); start_state(SCENE_ROM, 'start_scene'); SCENES = ('ape', 'ssj')
for name in sys.argv[2:] or list(ORIGS) + list(CLIPS):
    d = os.path.join(OUT, name)
    if os.path.exists(os.path.join(d, 'done')): continue
    shutil.rmtree(d, ignore_errors=True); o = name in ORIGS
    r = Run(d, ORIG if o else SCENE_ROM if name in SCENES else ROM, None if o or name in ('new_boot', 'new_title', 'new_opening') else 'start_scene' if name in SCENES else 'start')
    (ORIGS if o else CLIPS)[name](r); open(os.path.join(d, 'done'), 'w').close(); print(name, r.n, flush=True)
