"""Port LoG1's 18 songs into Buu's Fury at build time. Both games use Webfoot's tracker engine, so the songs copy almost as they are.

LoG1 song: {-> pattern pointer list, -> order list, tempo | speed << 8}, with one global sample table and mask dictionary.
Buu's Fury song: {-> patterns, -> order, -> samples, -> dictionary, meta}, in a table at 0x3BB78C with 53 songs. The new table keeps those 53 and adds
LoG1's as tracks 53-70, so scripts and areas pick them by number. Nothing from the ROMs is stored in the repo.
"""
import struct
TRACKS, N_SONGS, SAMPLES, N_SAMPLES, DICT = 0x591F3C, 18, 0x591E4C, 20, 0x142388
BF_TABLE, BF_SONGS, BASE = 0x3BB78C, 53, 53
REFS = (0x8F8, 0x4210, 0x545C, 0x8D10)                                 # the code's pointers to Buu's Fury's song table
B = 0x08000000


def install(r, log1):
    def put(b):
        while len(r) % 4: r.append(0)
        o = len(r); r.extend(b); return B + o
    u = lambda o: struct.unpack_from('<I', log1, o)[0]
    samples = bytearray(); seen = {}
    for i in range(N_SAMPLES):
        p, rest = u(SAMPLES + 12 * i), log1[SAMPLES + 12 * i + 4:SAMPLES + 12 * i + 12]; length = struct.unpack_from('<H', rest, 4)[0]
        if p not in seen: seen[p] = put(log1[p - B:p - B + length + 4])
        samples += struct.pack('<I', seen[p]) + rest
    sp, dp = put(bytes(samples)), put(log1[DICT:DICT + 14]); table = bytearray(r[BF_TABLE:BF_TABLE + 20 * BF_SONGS]); total = 0
    for k in range(N_SONGS):
        tp, so, meta = struct.unpack_from('<III', log1, TRACKS + 12 * k); t0, s0 = tp - B, so - B; ptrs = []
        while True:
            v = u(t0 + 4 * len(ptrs))
            if not so <= v < tp: break
            ptrs.append(v)
        body = log1[s0:t0]; at = put(body); delta = at - so; lst = put(struct.pack('<%dI' % len(ptrs), *[v + delta for v in ptrs])); total += len(body)
        table += struct.pack('<5I', lst, at, sp, dp, meta)
    t = put(bytes(table))
    for ref in REFS:
        assert struct.unpack_from('<I', r, ref)[0] == B + BF_TABLE; struct.pack_into('<I', r, ref, t)
    return total + sum(0 for _ in ())
