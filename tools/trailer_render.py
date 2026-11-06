"""Cuts the release trailer from tools/trailer_capture.py's clips to the song, in 1080p. Text and cuts follow the song's bars.
python3 tools/trailer_render.py <clips> sheet <png>                 contact sheet of every shot
python3 tools/trailer_render.py <clips> shots <workdir> [budget s]  renders shots not done yet, stopping after the time budget
python3 tools/trailer_render.py <clips> final <workdir> <song> <mp4>  joins the shots and adds the music"""
import os, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H, FPS = 1920, 1080, 30
FONT = next(p for p in ('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if os.path.exists(p))
START, BAR = 15.7, 60 / 136 * 4                                             # the full band comes in at START; 136 beats a minute, four to the bar
CHORD, SONG_END = 276.4, 285.9                                              # the song's last chord, cut straight after CUT
b = lambda n: START + n * BAR
CUT = b(32); END = CUT + SONG_END - CHORD - 1.2
ORANGE = (255, 140, 20)

# start, end, clip, first frame, view, text, text size. A clip of None is black.
SHOTS = [
    (0, 3.3, 'orig_title', 0, 'retro', 'REMEMBER THIS?', 88),
    (3.3, 7.0, 'orig_field', 138, 'retro', 'ONE HERO. ONE WORLD TO SAVE.', 88),
    (7.0, 10.5, 'orig_boot', 330, 'retro', 'THE LEGACY OF GOKU', 88),
    (10.5, 13.6, 'orig_field', 180, 'retro', "YOU THINK YOU'VE SEEN IT ALL.", 88),
    (13.6, START, None, 0, 'black', "YOU HAVEN'T.", 120),
    (b(0), b(2), 'new_boot', 200, 'full', 'REBUILT FROM THE GROUND UP', 92),
    (b(2), b(3), 'new_title', 10, 'full', "ON BUU'S FURY'S ENGINE", 92),
    (b(3), b(4), 'fight_base', 60, 'full', 'WITH ITS COMBAT', 92),
    (b(4), b(5), 'new_opening', 8, 'full', 'THE STORY YOU LOVE', 92),
    (b(5), b(6), 'ape', 396, 'full', 'EVERY CUTSCENE', 92),
    (b(6), b(7), 'roshi_talk', 34, 'fit', 'NEW PORTRAITS', 92),
    (b(7), b(8), 'lost_spirits', 40, 'full', 'EVERY MAP REPAINTED', 92),
    (b(8), b(10), 'fight_base', 120, 'full', 'REAL FIGHTS', 92),
    (b(10), b(11), 'fight_base', 190, 'full', 'REAL EXP', 92),
    (b(11), b(12), 'elder', 130, 'fit', 'REAL GEAR', 92),
    (b(12), b(14), 'beach', 0, 'full', 'THE ORIGINAL MUSIC', 92),
    (b(14), b(16), 'new_boot', 300, 'full', None, 0),
    (b(16), b(17), None, 0, 'black', 'AND FOR THE FIRST TIME', 92),
    (b(17), b(19), 'fly_area', 2, 'full', 'TAKE TO THE SKIES', 110),
    (b(19), b(21), 'fly_map', 92, 'full', 'FLY THE WHOLE WORLD', 110),
    (b(21), b(22), 'fly_namek', 20, 'full', 'ALL THE WAY...', 110),
    (b(22), b(23), 'fly_namek', 66, 'full', 'TO NAMEK', 170),
    (b(23), b(24), 'namek_walk', 0, 'full', None, 0),
    (b(24), b(26), 'ape', 566, 'fit', 'GREAT APES. FULL SIZE.', 100),
    (b(26), b(27), 'ape', 878, 'full', None, 0),
    (b(27), b(28), 'ssj', 396, 'fit', 'GOKU VS FRIEZA', 100),
    (b(28), b(29), 'butler', 30, 'fit', 'WHO LOST THE SLIPPERS?', 84),
    (b(29), b(30), 'elder', 76, 'fit', 'WHAT BUSINESS PLAN?', 84),
    (b(30), b(31), 'announcer', 20, 'fit', 'WHO ASKED FOR A REMATCH?', 84),
    (b(31), b(32), 'rematch', 70, 'full', 'NEW SIDE QUESTS. HIDDEN GEAR. OLD RIVALS.', 64),
    (CUT, END, 'new_title', 10, 'end', None, 0),
]
OUT_NOW = CUT + 2.0                                                         # the last chord's peak


def font(size): return ImageFont.truetype(FONT, size)


def text_layer(text, size, glow=ORANGE, italic=True):
    """White italic text with a black edge and a coloured glow, as a padded RGBA array."""
    while font(size).getlength(text) > W - 160: size -= 4
    f = font(size); w = int(f.getlength(text)) + 160; h = int(size * 1.6) + 80
    t = Image.new('L', (w, h), 0); ImageDraw.Draw(t).text((80, 40), text, 255, font=f)
    if italic: t = t.transform((w, h), Image.AFFINE, (1, 0.18, -0.18 * h / 2, 0, 1, 0), Image.BILINEAR)
    edge = t.filter(ImageFilter.MaxFilter(9)); g = edge.filter(ImageFilter.GaussianBlur(14))
    a = np.asarray(t, float) / 255; e = np.asarray(edge, float) / 255; gl = np.asarray(g, float) / 255 * 0.9
    rgb = np.zeros((h, w, 3)); rgb[...] = np.array(glow) * (gl > 0)[..., None]; alpha = np.maximum(gl, e)
    rgb = rgb * (1 - e[..., None]); rgb = rgb * (1 - a[..., None]) + 255 * a[..., None]; alpha = np.maximum(alpha, a)
    return rgb, alpha


def paste(frame, layer, cx, cy, scale=1.0, fade=1.0):
    rgb, alpha = layer
    if scale != 1.0:
        h, w = alpha.shape; nh, nw = int(h * scale), int(w * scale); ys = (np.arange(nh) / scale).astype(int).clip(0, h - 1); xs = (np.arange(nw) / scale).astype(int).clip(0, w - 1)
        rgb = rgb[ys][:, xs]; alpha = alpha[ys][:, xs]
    h, w = alpha.shape; x0, y0 = cx - w // 2, cy - h // 2; xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    a = alpha[ya - y0:yb - y0, xa - x0:xb - x0, None] * fade
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - a) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * a


class Clips:
    def __init__(self, d): self.d, self.c = d, {}
    def n(self, name):
        if name not in self.c: self.c[name] = len([f for f in os.listdir(os.path.join(self.d, name)) if f.startswith('f') and f.endswith('.png')])
        return self.c[name]
    def get(self, name, i): return np.asarray(Image.open(os.path.join(self.d, name, 'f%05d.png' % min(i, self.n(name) - 1))).convert('RGB'))


def zoomed(src, z, cx=0.5, cy=0.5, dx=0, dy=0):
    """Nearest-neighbour: the pixels stay crisp. z is screen pixels per game pixel."""
    sw, sh = W / z, H / z; x0 = (240 - sw) * cx + dx / z; y0 = (160 - sh) * cy + dy / z
    xs = (x0 + np.arange(W) / z).astype(int).clip(0, 239); ys = (y0 + np.arange(H) / z).astype(int).clip(0, 159); return src[ys][:, xs]


def backdrop(src):
    """The frame blown up, blurred and dimmed, behind a shot that shows the whole game screen."""
    return np.asarray(Image.fromarray(src).resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR), float) * 0.3


BAND = np.clip(1.25 - np.maximum(0, np.arange(H) - H * 0.6) / (H * 0.4) * 1.0, 0.35, 1)[:, None, None]; BAND = np.minimum(BAND, 1)


def render(sh, k, n, clips, layers):
    t0, t1, clip, first, view, text, size = sh; p = k / max(1, n - 1)
    src = clips.get(clip, first + k) if clip else None; f = np.zeros((H, W, 3))
    shake = max(0, 6 - k) * 3; dx, dy = (shake * (-1) ** k, shake * (-1) ** (k // 2)) if view in ('full', 'fit') else (0, 0)
    if view == 'full': f = zoomed(src, 8 + 0.35 * p, 0.5, 0.5, dx, dy).astype(float)
    elif view == 'fit':
        f = backdrop(src); z = 6.75; im = zoomed(src, z, 0.5, 0.5); x0 = (W - int(240 * z)) // 2; f[:, x0:W - x0] = im[:, x0:W - x0]; f = np.roll(f, (dy, dx), (0, 1))
    elif view == 'retro':                                                   # how it looked: small, soft, on an old screen
        z = 5; ih, iw = 160 * z, 240 * z; y0, x0 = (H - ih) // 2, (W - iw) // 2
        im = src[(np.arange(ih) // z)][:, (np.arange(iw) // z)].astype(float); g = im.mean(2, keepdims=True); im = im * 0.7 + g * 0.3
        im[np.arange(ih) % z >= z - 2] *= 0.55; f[y0:y0 + ih, x0:x0 + iw] = im
    elif view == 'end':
        f = backdrop(src) * 0.8 * min(1, k / 12 + 0.3)
        tn = (t0 + k / FPS) - OUT_NOW
        paste(f, layers['end1'], W // 2, 330); paste(f, layers['end2'], W // 2, 480)
        if tn >= 0:
            s = 1 + max(0, 0.7 - tn * 7); paste(f, layers['out'], W // 2, 720, s)
            if tn < 0.25: f = f + (255 - f) * (1 - tn / 0.25)
        paste(f, layers['legal'], W // 2, 1010, 1.0, min(1, k / 30))
        if t0 + k / FPS > END - 1.2: f = f * max(0, (END - (t0 + k / FPS)) / 1.2)
    if text:
        s = 1 + max(0, 0.45 - k * 0.09) if view != 'retro' else 1.0; fade = 1 if view != 'retro' else min(1, k / 8, (n - k) / 8)
        if view == 'full': f = f * BAND                                    # a shadow for the words to sit on
        paste(f, layers[text], W // 2, H // 2 if view == 'black' else 120 if view == 'fit' else H - 150 if view == 'retro' else H - 180, s, fade)
    if view != 'retro' and k < 5: f = f + (255 - f) * (1 - k / 5) * (0.9 if t0 >= START else 0)            # each cut lands with a white flash
    if view == 'retro': fd = min(1, k / 8, (n - k) / 6); f = f * fd
    if view == 'black': f = f * min(1, (n - k) / 4)
    return np.clip(f, 0, 255).astype(np.uint8)


def layers_for():
    L = {s[5]: text_layer(s[5], s[6]) for s in SHOTS if s[5]}
    L['end1'] = text_layer('LEGACY OF GOKU', 130, ORANGE); L['end2'] = text_layer('REMAKE', 90, (40, 120, 255)); L['out'] = text_layer('OUT NOW', 190, (255, 60, 20))
    f = font(30); w = int(f.getlength(LEGAL)) + 40; t = Image.new('L', (w, 70), 0); ImageDraw.Draw(t).text((20, 15), LEGAL, 200, font=f); a = np.asarray(t, float) / 255; L['legal'] = (np.full((70, w, 3), 255.0), a)
    return L


LEGAL = 'A fan project. Not affiliated with or endorsed by the rights holders.'
FF = os.environ.get('FFMPEG', 'ffmpeg')
d, mode = sys.argv[1], sys.argv[2]; clips = Clips(d)
if mode == 'sheet':
    L = layers_for(); cols = 6; rows = (len(SHOTS) + cols - 1) // cols; S = Image.new('RGB', (320 * cols, 180 * rows))
    for i, sh in enumerate(SHOTS):
        n = round(sh[1] * FPS) - round(sh[0] * FPS); k = min(n - 1, int(os.environ.get('AT', n // 2)))
        S.paste(Image.fromarray(render(sh, k, n, clips, L)).resize((320, 180)), ((i % cols) * 320, (i // cols) * 180))
    S.save(sys.argv[3])
elif mode == 'shots':
    work = sys.argv[3]; os.makedirs(work, exist_ok=True); budget = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9; t_ = time.time(); L = layers_for()
    for i, sh in enumerate(SHOTS):
        out = os.path.join(work, 's%02d.mp4' % i)
        if os.path.exists(out): continue
        if time.time() - t_ > budget: print('stopped at', i); sys.exit(0)
        n = round(sh[1] * FPS) - round(sh[0] * FPS); tmp = out + '.tmp.mp4'
        p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
        for k in range(n): p.stdin.write(render(sh, k, n, clips, L).tobytes())
        p.stdin.close(); p.wait(); os.replace(tmp, out); print(i, n, round(time.time() - t_), flush=True)
    print('all shots done')
elif mode == 'final':
    work, song, mp4 = sys.argv[3:6]; lst = os.path.join(work, 'list.txt'); open(lst, 'w').write(''.join("file 's%02d.mp4'\n" % i for i in range(len(SHOTS))))
    a = '[0:a]atrim=0:%.3f,asetpts=PTS-STARTPTS[a];[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS[c];[a][c]acrossfade=d=0.08[m];[m]afade=t=out:st=%.3f:d=1.2,aresample=48000[o]' % (CUT + 0.08, CHORD, CHORD + END - CUT, END - 1.2)
    subprocess.check_call([FF, '-v', 'error', '-y', '-i', song, '-f', 'concat', '-safe', '0', '-i', lst, '-filter_complex', a, '-map', '1:v', '-map', '[o]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', mp4])
    print('done', mp4)
