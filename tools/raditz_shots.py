"""Capture full-frame screenshots of the Raditz test from your own build. Writes PNGs to out/raditz/shots.

    python3 tools/raditz_test.py <log1-decomp> && python3 tools/raditz_shots.py
"""
import os, struct, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, 'out', 'raditz', 'shots'); os.makedirs(D, exist_ok=True)


def le(a, v): return ['w8 %08x %02x' % (a + i, x) for i, x in enumerate(struct.pack('<i', v << 8))]


lines = open(os.path.join(ROOT, 'tools', 'routes', 'bf_boot_to_field.txt')).read().splitlines()
lines += le(0x0202F2E0, 448) + le(0x0202F2E4, 152) + le(0x0202E4C8, 418) + le(0x0202E4CC, 152)
lines += ['2', '10 RIGHT', '10', 'shot 1_before_talk', '4 A', '30', 'shot 2_enemy_appears', '40 RIGHT', 'shot 3_chase']
for i in range(3): lines += ['4 A', '8']
lines += ['shot 4_attack', '60 RIGHT', 'shot 5_later']
p = os.path.join(D, 'route.txt'); open(p, 'w').write('\n'.join(lines) + '\n')
subprocess.run([os.path.join(ROOT, 'vendor', 'gero-tools', 'tools', 'harness'), os.path.join(ROOT, 'out', 'raditz', 'test.gba'), p, D], check=True)
print('screenshots in', D)
