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


FLAG_QUEST = 700                 # quest 0: found 700, delivered 701; quest 1: 702, 703; quest 2: 704, 705; reward done 706
SENZU = 21                       # placeholder for LoG1's bean pickups: Buu's Fury's Senzu Bean


def opening_quests(sets, say):
    """LoG1 quests 0-3: find three items, give them to Roshi, then his reward. Returns scene lines placed before his normal talk."""
    out = []
    for q, entry in enumerate((11, 13, 15)):
        found, given = FLAG_QUEST + 2 * q, FLAG_QUEST + 2 * q + 1; nx = 'q%d_next' % q
        out += ['if_flag %d %s' % (given, nx), 'unless_flag %d %s' % (found, nx)]
        out += say(chain(sets[66], entry)[0]) + ['set_flag %d' % given, 'do call 128 %d' % SENZU, 'goto q_reward', 'label ' + nx]
    return out + ['goto q_normal', 'label q_reward'] + ['unless_flag %d q_done' % (FLAG_QUEST + 2 * q + 1) for q in range(3)] + \
        ['if_flag %d q_done' % (FLAG_QUEST + 6), 'set_flag %d' % (FLAG_QUEST + 6), 'do call 194 350'] + say(chain(sets[66], 20)[0]) + ['label q_done', 'stop', 'label q_normal']


FIND = {0: (0, 160, 80), 1: (0, 328, 208), 2: (1, 168, 128)}   # LoG1 quests 0-2: area, x, y


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
        def say(body):
            res = []
            for l in body:
                who = 'goku' if l['who'] == 'goku' else ('#%d' % portraits[l['who']] if portraits and l['who'] in portraits else SPEAKER.get(l['who']))
                pre = '' if who else NAME.get(l['who'], l['who'].rstrip('0123456789').title()) + ': '
                res += ['say %s %s' % (who or 'narrator', part) for part in split_line(pre + clean(l['text']))]
            return res
        if s == 66: out += ['set_flag %d' % NOOP] + opening_quests(sets, say)
        for e in sorted((x for x in seen if x), reverse=True): out.append('if_flag %d e%d_%d' % (flag(s, e), s, e))
        out.append('set_flag %d' % NOOP)
        for e, (body, nxt) in sorted(seen.items()):
            out.append('label e%d_%d' % (s, e))
            for l in body:
                who = 'goku' if l['who'] == 'goku' else ('#%d' % portraits[l['who']] if portraits and l['who'] in portraits else SPEAKER.get(l['who'])); pre = '' if who else NAME.get(l['who'], l['who'].rstrip('0123456789').title()) + ': '
                for part in split_line(pre + clean(l['text'])): out.append('say %s %s' % (who or 'narrator', part)); lines += 1
            if nxt is not None and nxt != e and nxt in seen and nxt: out.append('set_flag %d' % flag(s, nxt))
            out.append('stop')
    for q in FIND:
        out += ['list find_q%d' % q, 'set_flag %d' % NOOP, 'if_flag %d f%d_end' % (FLAG_QUEST + 2 * q, q), 'set_flag %d' % (FLAG_QUEST + 2 * q), 'narrate You found something for Master Roshi.', 'label f%d_end' % q, 'stop']
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    assert FLAG_BASE + len(flags) <= NOOP, 'too many entry flags'
    return dict(sets=len(set_ids), lines=lines, flags=len(flags))
