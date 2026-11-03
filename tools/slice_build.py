"""M4 slice build: new game starts on LoG1's area 0. Reads your ROMs and extracted assets; writes out/slice only.

    python3 tools/slice_build.py <log1-decomp>
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
import map_convert as C, mapkit, scenes  # noqa: E402


def main():
    L = sys.argv[1]; r = bytearray(open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()); r += b'\xff' * (0x1000000 - len(r))
    a = C.Area(L, 0); m, st = C.convert(r, a, 'recolour', []); an, dur = C.anim_tiles(r, a); C.reduce_tiles(r, m, 860, [b for b, _ in an])
    P = m.write(r, C.TEMPLATE); C.add_anim(r, P, an, dur); mapkit.link_area(r, 1, 1, P)
    struct.pack_into('<I', r, mapkit.area_entry(r, 1, 1) + 4, 0)     # no BF NPCs here
    end = len(r); r += bytes(0x10000)
    sc = [scenes.parse(os.path.join(ROOT, 'src', 'scenes', 'opening.scene'))]
    scenes.compile_all(r, sc, {}, {'narrator': 0}, end)
    while len(r) % 0x10000: r.append(0xFF)
    os.makedirs(os.path.join(ROOT, 'out', 'slice'), exist_ok=True); open(os.path.join(ROOT, 'out', 'slice', 'slice.gba'), 'wb').write(r); print('tiles', st['tiles'], 'rom', len(r))


if __name__ == '__main__':
    main()
