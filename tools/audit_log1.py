"""M2 first pass: which LoG1 sprite sets have a named counterpart in Buu's Fury or LoG2. Writes out/audit.json + prints a text table.

    python3 tools/audit_log1.py <log1-decomp> <buusfury-decomp> <log2-decomp>

Evidence is name matches in each game's enemy and scouter tables and text. A match needs its actor ID confirmed by eye in M2.
"""
import csv, json, os, re, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS = {'bubbles': 'bubbles', 'bulma': 'bulma', 'burter': 'burter', 'chaitzu': 'chiaotzu|chaotzu|chaozu', 'chichi': 'chi-?chi', 'dende': 'dende',
    'frieza1': 'frieza|freeza', 'frieza2': 'frieza|freeza', 'frieza3': 'frieza|freeza', 'frieza4': 'frieza|freeza', 'ginyu': 'ginyu', 'gohan1': 'gohan', 'gohan2': 'gohan', 'gohan3': 'gohan',
    'goku': 'goku', 'gokumallet': 'goku', 'ssgoku': 'goku', 'gregory': 'gregory', 'guru': 'guru', 'jeice': 'jeice|jheese', 'kami': 'kami\\b', 'kingkai': 'king kai', 'kingyema': 'yemma|yema', 'korrin': 'korin|karin',
    'krillin1': 'krillin|kuririn', 'krillin2': 'krillin|kuririn', 'nail': 'nail\\b', 'nappa': 'nappa', 'oozaru1': 'oozaru|great ape', 'oozaru2': 'oozaru|great ape', 'piccolo': 'piccolo', 'popo': 'popo',
    'puar': 'puar', 'raditz': 'raditz', 'recoome': 'recoome|recoom', 'roshi': 'roshi', 'snkqueen': 'princess snake|snake princess', 'tien': 'tien', 'vegeta1': 'vegeta', 'vegeta2': 'vegeta', 'vegeta3': 'vegeta', 'yamcha': 'yamcha',
    'turtle': 'turtle', 'wolf': 'wolf', 'snake': 'snake', 'crab': 'crab', 'squirrel': 'squirrel', 'trex': 't-?rex|dinosaur|tyrann', 'trex2': 't-?rex|dinosaur|tyrann', 'ptero1': 'ptero', 'ptero2': 'ptero', 'ptero3': 'ptero',
    'kitty': 'cat\\b|kitty', 'capslnut': 'capsule', 'namekian1': 'namek', 'namekian2': 'namek', 'namekian3': 'namek', 'namekian4': 'namek', 'namekboy': 'namek', 'chief': 'chief', 'wiseman': 'wise|elder', 'oldman': 'old man'}
GENERIC = re.compile(r'^(armyguy|assist|boy|citizen|cop|devil|doctor|father|girl|hench|mother|nurse|robber|spirit)')


def text(g):
    out = ''
    for p in ('tables/enemies.csv', 'tables/scouter.csv', 'tables/spawns.csv'):
        f = os.path.join(g, 'assets', p)
        if os.path.exists(f): out += open(f, errors='ignore').read() + '\n'
    f = os.path.join(g, 'assets', 'text', 'ui_strings.txt')
    if os.path.exists(f): out += open(f, errors='ignore').read()
    return out.lower()


def main():
    log1, bf, log2 = sys.argv[1:4]; bt, lt = text(bf), text(log2)
    rep = json.load(open(ROOT + '/out/converted/report.json'))
    names = [l.split()[1] for l in open(log1 + '/assets/areas/SPRITES.txt')]
    rows = []
    for n in names:
        use = rep['enemy_sprites'].get(n, 0) + rep['npc_sprites'].get(n, 0); sp = rep['speakers'].get(n, 0)
        t = TERMS.get(n); b = bool(t and re.search(t, bt)); l = bool(t and re.search(t, lt))
        st = 'named' if b or l else 'generic' if GENERIC.match(n) else 'unmatched'
        rows.append(dict(sprite=n, placed=use, lines=sp, bf=b, log2=l, status=st))
    json.dump(rows, open(ROOT + '/out/audit.json', 'w'), indent=1)
    print(Counter(r['status'] for r in rows))
    for s in ('named', 'generic', 'unmatched'):
        print(s.upper()); print('  '.join('%s[%s%s]' % (r['sprite'], 'B' if r['bf'] else '', 'L' if r['log2'] else '') for r in rows if r['status'] == s))
    print('only LoG2:', [r['sprite'] for r in rows if r['log2'] and not r['bf']])


if __name__ == '__main__':
    main()
