"""Check your ROM dumps and put clean copies in rom/.

    python3 tools/romcheck.py <dump> [<dump> ...]

Needed: Buu's Fury (USA) and the stand-alone Legacy of Goku (USA), plus the LoG I & II combo cart for LoG2 sprites.
Some Buu's Fury dumps differ in 10 code bytes at 0x8B66 (SHA-1 e65738e9...). Rebuild the clean ROM with buusfury-decomp:
    cp <dump> baserom.gba && make && make compare     # buusfury.gba is the clean ROM; pass that here
"""
import hashlib, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN = {
    'f1c4b07554d2a3b1ad2f325307051e775ce68087': ('bf.gba', "Buu's Fury (USA), clean"),
    'a3c8c76742f11fc6a3f6e3fcca20992458cac0b5': ('log1.gba', 'Legacy of Goku (USA), stand-alone'),
    'f02d179accbeb9b68bcaef8720eb0ae426dde6ee': ('log12.gba', 'Legacy of Goku I & II combo cart'),
    '18e0715dec419f3501c301511530d2edcd590f8b': ('log2.gba', 'Legacy of Goku II (USA), stand-alone'),
    'e65738e9d67688309f09811a54f495523ec9aada': (None, "Buu's Fury, 10-byte patched dump: rebuild it first (see above)"),
}
os.makedirs(os.path.join(ROOT, 'rom'), exist_ok=True)
for p in sys.argv[1:]:
    h = hashlib.sha1(open(p, 'rb').read()).hexdigest()
    name, what = KNOWN.get(h, (None, 'unknown dump (SHA-1 %s)' % h))
    print('%s: %s' % (os.path.basename(p), what))
    if name:
        shutil.copy(p, os.path.join(ROOT, 'rom', name)); print('  -> rom/%s' % name)
