"""One-command build. M0: no content yet, so it passes clean Buu's Fury through the patch pipeline.

    python3 build.py        # rom/bf.gba -> out/log1_remake.gba + out/log1_remake.bps (empty patch until content exists)
"""
import hashlib, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'vendor', 'gero-tools', 'tools'))
import bps  # noqa: E402

BF_SHA1 = 'f1c4b07554d2a3b1ad2f325307051e775ce68087'


def main():
    clean = open(os.path.join(ROOT, 'rom', 'bf.gba'), 'rb').read()
    if hashlib.sha1(clean).hexdigest() != BF_SHA1:
        sys.exit('rom/bf.gba is not clean Buu\'s Fury (USA); run tools/romcheck.py')
    rom = bytearray(clean)
    # content steps go here as the milestones land
    out = bytes(rom)
    patch = bps.make(clean, out, meta=b'LoG1 remake on Buu\'s Fury (personal ROM hack)')
    assert bps.apply(clean, patch) == out, 'patch round-trip failed'
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
    open(os.path.join(ROOT, 'out', 'log1_remake.gba'), 'wb').write(out)
    open(os.path.join(ROOT, 'out', 'log1_remake.bps'), 'wb').write(patch)
    print('out/log1_remake.gba', len(out), 'bytes; patch', len(patch), 'bytes')


if __name__ == '__main__':
    main()
