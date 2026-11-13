"""The movie villains' own ki attacks: original pixel art drawn here (no ROM art), as RGBA frames.

    ATTACKS                 name -> dict(boss, title, what, frames=fn() -> {part: [RGBA frames]}, timing)
    to_indices(img, bf)     an RGBA frame -> Buu's Fury OBJ palette indices (0 = clear)
    sheet(), gif(...)       previews for the owner (effects only, no characters)

Each attack is made of parts that src/bosses.c moves about: an orb, a beam segment, a ring, a spark. All are drawn from simple shapes with a
bright core and a coloured rim, the way Buu's Fury draws its own ki.
"""
import math
import numpy as np

CLEAR = (0, 0, 0, 0)


def blank(w, h): return np.zeros((h, w, 4), np.uint8)


def ramp(cols, t):
    """t in 0..1 along a list of RGB colours."""
    t = min(max(t, 0.0), 1.0) * (len(cols) - 1); i = min(int(t), len(cols) - 2); f = t - i
    a, b = np.array(cols[i], float), np.array(cols[i + 1], float)
    return tuple(int(round(v)) for v in a + (b - a) * f)


def quant(c, levels=5):
    """Snap to a few steps, so frames stay pixel-art flat rather than smooth gradients."""
    return c


def orb(r, cols, glow=0, rim=1, noise=None, seed=0):
    """A ball of ki: cols from the hot core (white) out to the rim colour; glow adds a soft outer ring in the last colour."""
    R = r + glow; w = 2 * R + 2; img = blank(w, w); cx = cy = R + 0.5
    rng = np.random.default_rng(seed)
    for y in range(w):
        for x in range(w):
            d = math.hypot(x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5)
            if noise: d += rng.uniform(-noise, noise)
            if d <= r:
                t = d / max(r, 1)
                steps = len(cols)
                k = min(int(t * steps), steps - 1)
                img[y, x] = cols[k] + (255,)
            elif d <= R and glow:
                if (x + y) % 2 == 0 or d <= r + glow / 2: img[y, x] = cols[-1] + (255,)
    if rim:
        a = img[..., 3] > 0
        edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
        img[edge] = cols[-1] + (255,)
    return img


def ring(r, width, cols, sparks=0, phase=0, seed=0):
    """A spinning ring (Kill Driver): bright band, darker edges, a few crackling sparks round it."""
    w = int(2 * (r + width + 4) + 1); img = blank(w, w); c = w // 2; rng = np.random.default_rng(seed + phase)
    for y in range(w):
        for x in range(w):
            d = math.hypot(x - c, y - c); off = abs(d - r)
            if off <= width:
                ang = (math.atan2(y - c, x - c) + phase * math.pi / 4) % (2 * math.pi)
                bright = 0.5 + 0.5 * math.cos(ang * 3)
                k = 0 if off < width * 0.35 and bright > 0.4 else (1 if off < width * 0.7 else 2)
                img[y, x] = cols[min(k, len(cols) - 1)] + (255,)
    for s in range(sparks):
        a = rng.uniform(0, 2 * math.pi); d0 = r + width + 1
        x, y = c + d0 * math.cos(a), c + d0 * math.sin(a)
        for k in range(rng.integers(2, 5)):
            x += rng.choice([-1, 0, 1]) + math.cos(a); y += rng.choice([-1, 0, 1]) + math.sin(a)
            if 0 <= int(x) < w and 0 <= int(y) < w: img[int(y), int(x)] = cols[0] + (255,)
    return img


def beam(length, thick, cols, phase=0, taper=0):
    """A horizontal beam segment (drawn facing right): white core, coloured edges, a ripple along it."""
    h = thick + 4; img = blank(length, h); c = (h - 1) / 2
    for x in range(length):
        t = max(thick / 2 + (0.6 if thick > 3 else 0.3) * math.sin((x + phase * 3) * 0.7), 0.75)
        if taper: t *= min(1, (x + 1) / taper)
        for y in range(h):
            off = abs(y - c)
            if off <= t:
                k = 0 if off <= t * 0.35 else (1 if off <= t * 0.7 else 2)
                img[y, x] = cols[min(k, len(cols) - 1)] + (255,)
    return img


def burst(r, cols, phase, seed=0):
    """An explosion: a flash, then a ring of fire breaking up."""
    w = 2 * r + 2; img = blank(w, w); c = w / 2; rng = np.random.default_rng(seed)
    rr = r * (0.35 + 0.65 * phase / 3)
    for y in range(w):
        for x in range(w):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) + rng.uniform(-1.5, 1.5)
            if phase == 0 and d <= rr: img[y, x] = cols[0] + (255,)
            elif phase > 0 and rr * (0.45 + 0.15 * phase) <= d <= rr:
                if phase == 3 and rng.random() < 0.45: continue
                k = 0 if d < rr * 0.8 else 1 if phase < 2 else 2
                img[y, x] = cols[min(k + (phase > 1), len(cols) - 1)] + (255,)
            elif phase == 1 and d < rr * 0.45: img[y, x] = cols[0] + (255,)
    return img


def bolt(length, cols, phase):
    """Death Flash: a short white-hot bolt with a tapering tail."""
    img = blank(length, 9)
    for x in range(length):
        t = x / length; th = 0.5 + 3.5 * t
        for y in range(9):
            off = abs(y - 4)
            if off <= th:
                k = 0 if off <= th * 0.4 else (1 if off <= th * 0.75 else 2)
                if x < length * 0.3 and (x + phase) % 2: continue
                img[y, x] = cols[min(k, len(cols) - 1)] + (255,)
    return img


# ki colours, hot core first
WHITE = (255, 255, 255)
RED = [WHITE, (255, 150, 170), (230, 40, 70), (130, 10, 40)]
YELLOW = [WHITE, (255, 250, 170), (255, 210, 60), (200, 120, 20)]
NOVA = [(255, 255, 230), (255, 230, 140), (255, 170, 60), (240, 100, 30), (200, 40, 20), (120, 20, 20)]
VIOLET = [WHITE, (230, 200, 255), (170, 100, 240), (90, 40, 160)]
PURPLE_DARK = [(240, 220, 255), (180, 110, 240), (110, 50, 190), (50, 20, 90)]
SLUG = [WHITE, (255, 240, 180), (250, 190, 70), (190, 110, 30)]
GREENISH = [WHITE, (220, 255, 200), (140, 230, 90), (50, 140, 40)]


def twin_beam(length, gap, cols, phase):
    """Two thin parallel beams in one segment (the Darkness Eye Beam): white cores, coloured edges, a faint glow between flickers."""
    h = gap + 6; img = blank(length, h)
    for x in range(length):
        for k, yc in enumerate((2, 2 + gap)):
            wob = 1 if (x + phase * 5 + k * 3) % 11 == 0 else 0
            img[yc, x] = cols[0] + (255,)
            for yy in (yc - 1, yc + 1):
                if 0 <= yy < h: img[yy, x] = cols[2 - wob] + (255,)
        if (x + phase) % 4 == 0:
            for yy in range(4, 2 + gap - 1): img[yy, x] = cols[3] + (255,)
    return img


def comet(r, tail, cols, phase=0):
    """A ball with a tapering tail behind it (drawn moving right)."""
    w = tail + 2 * r + 2; h = 2 * r + 3; img = blank(w, h); cy = h / 2
    for x in range(w):
        for y in range(h):
            dxh = x - (tail + r); d = math.hypot(dxh, y + 0.5 - cy)
            if d <= r:
                k = 0 if d <= r * 0.45 else (1 if d <= r * 0.8 else 2)
                img[y, x] = cols[k] + (255,)
            elif x < tail + r:
                th = r * (x / (tail + r)) ** 1.3
                if abs(y + 0.5 - cy) <= th and (x + phase * 2) % 3:
                    img[y, x] = cols[2 if abs(y + 0.5 - cy) <= th * 0.5 else 3] + (255,)
    return img


def sun(r, cols, phase, flare=0, seed=0):
    """A churning ball (Supernova, Big Smasher): a hot core, rings of colour that wobble with the phase, and flares licking off the rim."""
    R = r + flare + 1; w = 2 * R + 1; img = blank(w, w); c = R; rng = np.random.default_rng(seed + phase * 13)
    for y in range(w):
        for x in range(w):
            dx, dy = x - c, y - c; d = math.hypot(dx, dy); a = math.atan2(dy, dx)
            wob = 0.9 * math.sin(a * 5 + phase * 1.7) + 0.6 * math.sin(a * 3 - phase)
            if d <= r + wob * 0.5:
                t = (d + wob * 0.7) / max(r, 1)
                k = min(int(max(t, 0) * len(cols)), len(cols) - 1)
                img[y, x] = cols[k] + (255,)
            elif flare and d <= r + flare and (math.sin(a * 7 + phase * 2.3) > 0.55 or rng.random() < 0.05):
                img[y, x] = cols[-2] + (255,)
    a = img[..., 3] > 0
    edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    img[edge] = cols[-1] + (255,)
    return img


def ellipse_ring(rx, ry, cols, phase, arcs=4, seed=0):
    """Kill Driver: a ring seen at a slant, its bright side turning, with arcs of lightning jumping off it."""
    w, h = 2 * rx + 7, 2 * ry + 9; img = blank(w, h); cx, cy = w // 2, h // 2; rng = np.random.default_rng(seed + phase)
    for k in range(360):
        a = math.radians(k); x = cx + rx * math.cos(a); y = cy + ry * math.sin(a)
        bright = math.cos(a - phase * math.pi / 2)
        col = cols[0] if bright > 0.5 else cols[1] if bright > -0.2 else cols[2]
        for t in (-1, 0, 1):
            xx, yy = int(round(x)), int(round(y + t * (1 if bright > -0.2 else 0)))
            if 0 <= xx < w and 0 <= yy < h: img[yy, xx] = (cols[0] if t == 0 and bright > 0.5 else col) + (255,)
    for n in range(arcs):
        a = rng.uniform(0, 2 * math.pi); x = cx + rx * math.cos(a); y = cy + ry * math.sin(a)
        for k in range(int(rng.integers(3, 6))):
            x += math.cos(a) * 1.2 + rng.choice([-1, 0, 1]) * 0.8; y += math.sin(a) * 1.2 + rng.choice([-1, 0, 1]) * 0.8
            if 0 <= int(x) < w and 0 <= int(y) < h: img[int(y), int(x)] = (cols[0] if k % 2 else cols[1]) + (255,)
    return img


def fireball(r, cols, phase, seed=0):
    """An impact: a white flash, a fireball, then a ring of smoke breaking up."""
    w = 2 * r + 2; img = blank(w, w); c = w / 2; rng = np.random.default_rng(seed + phase)
    for y in range(w):
        for x in range(w):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) + rng.uniform(-1.2, 1.2)
            if phase == 0:
                if d <= r * 0.45: img[y, x] = cols[0] + (255,)
                elif d <= r * 0.55 and (x + y) % 2: img[y, x] = cols[1] + (255,)
            elif phase == 1:
                if d <= r * 0.35: img[y, x] = cols[0] + (255,)
                elif d <= r * 0.7: img[y, x] = cols[1] + (255,)
                elif d <= r * 0.8: img[y, x] = cols[2] + (255,)
            elif phase == 2:
                if d <= r * 0.4: img[y, x] = cols[1] + (255,)
                elif d <= r * 0.75: img[y, x] = cols[2] + (255,)
                elif d <= r * 0.9 and rng.random() < 0.7: img[y, x] = cols[3] + (255,)
            else:
                if r * 0.55 <= d <= r and rng.random() < 0.4: img[y, x] = cols[3] + (255,)
                elif d <= r * 0.3 and rng.random() < 0.3: img[y, x] = cols[2] + (255,)
    return img


def crescent(w, h, cols, phase, seed=0):
    """A shockwave along the ground (drawn moving right): a crescent of dust and ki, breaking up at its tips."""
    img = blank(w, h); rng = np.random.default_rng(seed + phase); cx, cy = -h * 0.05, (h - 1) / 2; R = w - 1 - cx
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, (y - cy) * 1.0); ang = abs(math.atan2(y - cy, x - cx))
            th = (8 - 1.6 * phase) * max(0.25, 1 - ang / 1.3)
            off = R - d + rng.uniform(-0.8, 0.8)
            if 0 <= off <= th and ang < 1.25 - 0.1 * phase and (phase < 2 or rng.random() < 0.8):
                k = 0 if off <= th * 0.3 else (1 if off <= th * 0.6 else 2 if off <= th * 0.85 else 3)
                img[y, x] = cols[min(k, len(cols) - 1)] + (255,)
    return img


APE = [WHITE, (255, 236, 200), (255, 170, 120), (210, 80, 60)]
DUST = [(255, 244, 210), (230, 200, 140), (180, 140, 90), (120, 90, 60)]


def frames():
    """{part name: [RGBA frames]} for every attack's parts. All fit 32x32, so a few at once stay within Buu's Fury's sprite memory."""
    f = {}
    f['eye_beam'] = [twin_beam(32, 4, RED, p) for p in range(2)]
    f['slug_eye_beam'] = [twin_beam(32, 4, YELLOW, p) for p in range(2)]
    f['death_flash'] = [comet(3, 20, [WHITE, (255, 250, 200), (255, 220, 80), (220, 140, 30)], p) for p in range(2)]
    f['finger_beam'] = [beam(32, 2, SLUG, p) for p in range(2)]
    f['supernova'] = [sun(r, NOVA, r, flare=0 if r < 9 else 1, seed=r) for r in (3, 5, 7, 9, 11, 13)]                 # growing over his head
    f['supernova_spin'] = [sun(13, NOVA, p, flare=1, seed=9) for p in range(7, 10)]                                    # thrown, churning
    f['nova_burst'] = [fireball(15, [(255, 255, 230), (255, 190, 80), (230, 80, 30), (110, 40, 30)], k, seed=3) for k in range(4)]
    f['kill_driver'] = [ellipse_ring(10, 6, VIOLET, p, seed=7) for p in range(4)]
    f['calamity_charge'] = [sun(r, PURPLE_DARK, r, flare=1 if r > 4 else 0, seed=r) for r in (2, 4, 6, 8)] + [sun(8, PURPLE_DARK, p, flare=1, seed=5) for p in range(9, 11)]
    f['calamity_wave'] = [beam(32, 9, [WHITE] + VIOLET[1:], p) for p in range(3)]
    f['meteor_shot'] = [comet(3, 8, VIOLET, p) for p in range(2)]
    f['twin_star'] = [sun(6, SLUG, p, flare=1, seed=p) for p in range(3)]
    f['big_smasher'] = [sun(r, SLUG + [(120, 60, 20)], r, flare=1, seed=r) for r in (5, 8, 11, 13)]
    f['big_smasher_spin'] = [sun(13, SLUG + [(120, 60, 20)], p, flare=1, seed=4) for p in range(7, 10)]
    f['ki_burst'] = [fireball(12, YELLOW, k, seed=1) for k in range(4)]
    f['violet_burst'] = [fireball(12, VIOLET, k, seed=2) for k in range(4)]
    f['mouth_blast'] = [beam(32, 10, APE, p) for p in range(3)]
    f['shockwave'] = [crescent(18, 30, DUST, p, seed=6) for p in range(3)]
    return f


ATTACKS = [
    dict(boss='Cooler', name='Darkness Eye Beam', parts=['eye_beam', 'ki_burst'],
         what='Two thin red beams from his eyes, fired straight at Goku after a short glint. Fast, light damage, hard to dodge up close.'),
    dict(boss='Cooler', name='Death Flash', parts=['death_flash', 'ki_burst'],
         what='A white-hot bolt from his finger, three in a row with a beat between. Medium damage each.'),
    dict(boss='Cooler (final form)', name='Supernova', parts=['supernova', 'nova_burst'],
         what='He raises a hand and an orange-red sun grows over his head for two seconds, then he hurls it, churning, at Goku, and it bursts wide. '
              'Very heavy damage; get clear while it grows. Only in his final form, every fourth attack.'),
    dict(boss='Great Ape Gohan', name='Mouth Blast', parts=['mouth_blast', 'ki_burst'],
         what='The Great Ape roars, then a thick white-hot blast pours from his mouth the way he faces.'),
    dict(boss='Great Ape Gohan', name='Stomp', parts=['shockwave'],
         what='He pounds the ground: the screen shakes and shockwaves of dust run out along the ground in all four directions.'),
    dict(boss='Turles', name='Kill Driver', parts=['kill_driver', 'violet_burst'],
         what='A spinning ring of violet ki crackling with sparks, thrown straight at Goku. It keeps going until it hits something or leaves the screen.'),
    dict(boss='Turles', name='Calamity Blaster', parts=['calamity_charge', 'calamity_wave', 'violet_burst'],
         what='Hands behind his neck, a dark violet ball charges for a second, then a white-and-violet wave fires the way he faces. Heavy damage, wide.'),
    dict(boss='Turles (after the fruit)', name='Meteor Burst', parts=['meteor_shot', 'violet_burst'],
         what='Powered by the fruit, he fires a fan of five small violet blasts, one after another, spread around Goku. Each is light; together they hurt.'),
    dict(boss='Lord Slug', name='Finger Beam', parts=['finger_beam', 'ki_burst'],
         what='A needle-thin golden beam, quick and precise.'),
    dict(boss='Lord Slug', name='Darkness Eye Beam', parts=['slug_eye_beam', 'ki_burst'],
         what='Like Cooler\'s but gold: two lines from his eyes.'),
    dict(boss='Lord Slug', name='Darkness Twin Star', parts=['twin_star', 'ki_burst'],
         what='Two golden spheres circle him for a few seconds, then fly at Goku one after the other.'),
    dict(boss='Lord Slug (giant form)', name='Big Smasher', parts=['big_smasher', 'nova_burst'],
         what='A golden sun grows over the giant\'s head, then he throws it, churning. Very heavy damage and a wide burst.'),
    dict(boss='Dodoria', name='Mouth Blast', key='Mouth Blast (Dodoria)', parts=['mouth_blast', 'ki_burst'],
         what="In Bardock's vision. He opens his jaws wide and a thick blast pours out the way he faces."),
    dict(boss='Dodoria', name='Meteor Burst', parts=['meteor_shot', 'violet_burst'],
         what='A fan of five small blasts, one after another, spread around Bardock.'),
    dict(boss='Dodoria', name='Death Flash', parts=['death_flash', 'ki_burst'],
         what='Three quick bolts from his finger, straight along the way he faces.'),
]


def to_indices(img, bf):
    """RGBA -> Buu's Fury OBJ palette indices by nearest colour (Lab), 0 where clear."""
    import mapkit, sys, os
    from room_test import lab
    obj = mapkit.palette(bf)[256:]; P = lab(obj[1:])
    out = np.zeros(img.shape[:2], np.uint8); m = img[..., 3] > 0
    if m.any():
        cols = img[m][:, :3]; uq, inv = np.unique(cols, axis=0, return_inverse=True)
        idx = 1 + ((lab(uq.astype(np.uint8))[:, None] - P[None]) ** 2).sum(2).argmin(1)
        out[m] = idx[inv.ravel()]
    return out


def in_game_colours(img, bf):
    """The frame as the game will show it: each colour snapped to Buu's Fury's OBJ palette."""
    import mapkit
    ind = to_indices(img, bf); pal = mapkit.palette(bf)[256:]
    out = np.zeros_like(img); m = ind > 0
    out[m, :3] = pal[ind[m]]; out[m, 3] = 255
    return out


# ---------- into the ROM (tools/build_skills.py fills src/bosses.c's boss_parts) ----------
# (part, directional): the order of src/bosses.c's P_ names. A directional part is drawn facing right; the build turns it to face down, up, left
# and right in turn.
PARTS = [('eye_beam', 1), ('slug_eye_beam', 1), ('death_flash', 1), ('finger_beam', 1), ('supernova', 0), ('nova_burst', 0), ('kill_driver', 0),
         ('calamity_charge', 0), ('calamity_wave', 1), ('meteor_shot', 1), ('twin_star', 0), ('big_smasher', 0), ('ki_burst', 0), ('violet_burst', 0),
         ('supernova_spin', 0), ('big_smasher_spin', 0), ('mouth_blast', 1), ('shockwave', 1)]
# OBJ shapes the GBA can show: (shape, size) -> (w, h)
SHAPES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
          (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
MENU_SLOTS = {2, 8, 9, 103, 193, 217, 218, 223, 224, 225, 236, 255}      # OBJ colours the menus (and the Spirit Bomb's disc) rewrite


def fit_shape(w, h):
    best = None
    for (sh, sz), (W, H) in SHAPES.items():
        if W >= w and H >= h and (best is None or W * H < best[2][0] * best[2][1]): best = (sh, sz, (W, H))
    return best


def obj_indices(img, bf):
    import mapkit
    from room_test import lab
    obj = mapkit.palette(bf)[256:]; usable = [i for i in range(1, 256) if i not in MENU_SLOTS]; P = lab(obj[usable])
    out = np.zeros(img.shape[:2], np.uint8); m = img[..., 3] > 0
    if m.any():
        uq, inv = np.unique(img[m][:, :3], axis=0, return_inverse=True)
        idx = np.array(usable)[((lab(uq.astype(np.uint8))[:, None] - P[None]) ** 2).sum(2).argmin(1)]
        out[m] = idx[inv.ravel()]
    return out


def turned(img, d):
    """A right-facing frame turned to face d: 0 down, 1 up, 2 left, 3 right."""
    return {0: np.rot90(img, -1), 1: np.rot90(img, 1), 2: img[:, ::-1], 3: img}[d].copy()


def rom_parts(bf, put):
    """[(frames bus address, count, directions, bytes)] in PARTS order; each frame is a spark frame (12 bytes) with its 8bpp tiles."""
    import struct
    fr = frames(); out = []
    for name, directional in PARTS:
        imgs = fr[name]; dirs = 4 if directional else 1
        W = max(max(i.shape[1], i.shape[0]) if directional else i.shape[1] for i in imgs)
        H = max(max(i.shape[1], i.shape[0]) if directional else i.shape[0] for i in imgs)
        entries = b''; most = 0
        for d in range(dirs):
            for im in imgs:
                im = turned(im, d) if directional else im
                h, w = im.shape[:2]; sh, sz, (OW, OH) = fit_shape(w, h)
                canvas = np.zeros((OH, OW, 4), np.uint8); y0, x0 = (OH - h) // 2, (OW - w) // 2; canvas[y0:y0 + h, x0:x0 + w] = im
                ind = obj_indices(canvas, bf)
                tiles = b''.join(ind[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(OH // 8) for tx in range(OW // 8))
                most = max(most, len(tiles))
                entries += struct.pack('<bbBBHHI', OW // 2, OH // 2, OW, OH, (sh << 14) | 0x2000, sz << 14, put(tiles))
        out.append((put(entries), len(imgs), dirs, most))
    return out
