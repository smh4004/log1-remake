"""M4: turn LoG1 conversation sets into Buu's Fury talk lists. Text is read from extracted assets at build time; the scene
file goes to out/ only.

Each set gets `talk_setNN`. LoG1 keeps a next-entry value per set. Here each reachable entry above 0 has a flag, and the last
one set wins. Portrait ids come from log1_portraits. Speakers without one use the narrator box with their name in front of the line.
"""
import glob, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from convert_log1 import chain, conversations, split_line  # noqa: E402

FLAG_BASE, NOOP = 620, 895
# speaker ids from Gero's RE notes; 2 is the first party slot. Others are marked "likely" there and need checking in game.
SPEAKER = dict(goku='goku', krillin1='#82', krillin2='#82', piccolo='#104', tien='#127', kingkai='#87')
NAME = dict(roshi='Master Roshi', bulma='Bulma', gohan1='Gohan', gohan2='Gohan', gohan3='Gohan', turtle='Turtle', chichi='Chi-Chi')


def clean(t): return t.replace('{', '(').replace('}', ')').strip()


def generate(log1, set_ids, path, portraits=None):
    sets = conversations(log1); flags = {}; out = []; lines = 0
    def flag(s, e):
        k = (s, e)
        if k not in flags: flags[k] = FLAG_BASE + len(flags)
        return flags[k]
    for s in set_ids:
        L = sets[s]; todo = [0]; seen = {}
        while todo:
            e = todo.pop()
            if e in seen or e not in L: continue
            body, nxt = chain(L, e); seen[e] = (body, nxt)
            if nxt is not None: todo.append(nxt)
        out.append('list talk_set%02d' % s)
        for e in sorted((x for x in seen if x), reverse=True): out.append('if_flag %d e%d_%d' % (flag(s, e), s, e))
        out.append('set_flag %d' % NOOP)
        for e, (body, nxt) in sorted(seen.items()):
            out.append('label e%d_%d' % (s, e))
            for l in body:
                who = 'goku' if l['who'] == 'goku' else ('#%d' % portraits[l['who']] if portraits and l['who'] in portraits else SPEAKER.get(l['who'])); pre = '' if who else NAME.get(l['who'], l['who'].rstrip('0123456789').title()) + ': '
                for part in split_line(pre + clean(l['text'])): out.append('say %s %s' % (who or 'narrator', part)); lines += 1
            if nxt is not None and nxt != e and nxt in seen and nxt: out.append('set_flag %d' % flag(s, nxt))
            out.append('stop')
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    assert FLAG_BASE + len(flags) <= NOOP, 'too many entry flags'
    return dict(sets=len(set_ids), lines=lines, flags=len(flags))
