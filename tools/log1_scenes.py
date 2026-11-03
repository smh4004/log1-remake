"""Read LoG1's cutscene table (0x0815A778: {u32 count, u32 -> list of command pointers}). Writes out/converted/scenes.json.

Each command starts with a function pointer, which the player calls with the scene state (sub_0800C42E).
Commands are listed by function address, with arguments kept as raw bytes until each function is named.

    python3 tools/log1_scenes.py
"""
import json, os, struct
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE, N = 0x15A778, 22
d = open(os.path.join(ROOT, 'rom', 'log1.gba'), 'rb').read(); u = lambda o: struct.unpack_from('<I', d, o)[0]; M = 0x1FFFFFF
scenes = []; fns = Counter()
for i in range(N):
    n, p = u(TABLE + 8 * i), u(TABLE + 8 * i + 4) & M
    ptrs = [u(p + 4 * k) & M for k in range(n)]; order = sorted(set(ptrs)); cmds = []
    for q in ptrs:
        nxt = min([x for x in order if x > q], default=q + 16); size = min(nxt - q, 32)
        f = u(q); fns[f] += 1; cmds.append(dict(fn='%08X' % f, raw=d[q + 4:q + size].hex()))
    scenes.append(dict(scene=i, commands=cmds))
os.makedirs(os.path.join(ROOT, 'out', 'converted'), exist_ok=True)
json.dump(scenes, open(os.path.join(ROOT, 'out', 'converted', 'scenes.json'), 'w'), indent=1)
print('scenes', len(scenes), 'commands', sum(len(s['commands']) for s in scenes), 'functions', len(fns))
for f, c in fns.most_common(): print('%08X' % f, c)
