"""M4 slice build: new game starts on LoG1's area 0. Reads your ROMs and extracted assets; writes out/slice only.

    python3 tools/slice_build.py <log1-decomp>
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import log1_areas, scenes  # noqa: E402


def main():
    L = sys.argv[1]; r = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); r += b'\xff' * (0x1000000 - len(r))
    tab, skipped = log1_areas.build(r, L, [0, 1]); print('skipped NPCs', skipped)
    end = len(r); r += bytes(0x10000)
    sc = [scenes.parse(os.path.join(ROOT, 'src', 'scenes', 'opening.scene'))]
    scenes.compile_all(r, sc, {}, {'narrator': 0}, end)
    while len(r) % 0x10000: r.append(0xFF)
    os.makedirs(os.path.join(ROOT, 'out', 'slice'), exist_ok=True); open(os.path.join(ROOT, 'out', 'slice', 'slice.gba'), 'wb').write(r); print('rom', len(r))


if __name__ == '__main__':
    main()
