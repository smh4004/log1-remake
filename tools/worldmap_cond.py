"""Flag conditions as bytecode, the same format as Gero's worldmap.py, without importing it (it needs a generated palette file)."""
import scenes


def cond_code(spec):
    """'set:N & clear:M' -> bytecode leaving 1/0."""
    out = b''
    for i, t in enumerate(spec.split('&')):
        k, f = t.strip().split(':')
        out += scenes.assemble('call %d %d' % (27 if k == 'set' else 28, int(f)), {})
        if i: out += b'\x04'
    return out
