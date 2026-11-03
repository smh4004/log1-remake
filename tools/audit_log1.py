"""M2 audit: LoG1 sprite sets -> Buu's Fury actor IDs (from scouter names), LoG2 portrait speakers, or LoG1's own sprites.

    python3 tools/audit_log1.py <log1-decomp> <buusfury-decomp> <log2-decomp>

Sprite IDs come only from BF's scouter table, which ties a name to a character ID. Text mentions don't count.
Writes out/audit.json (names and IDs only) and prints a summary.
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BF = {'bubbles': 'Bubbles', 'bulma': 'Bulma', 'chaitzu': 'Chiaotzu', 'chichi': 'Chi-Chi', 'dende': 'Dende', 'gohan1': 'Gohan', 'gohan2': 'Gohan', 'gohan3': 'Gohan',
      'goku': 'Goku', 'gokumallet': 'Goku', 'ssgoku': 'Goku', 'gregory': 'Gregory', 'kingkai': 'King Kai', 'kingyema': 'King Yemma', 'korrin': 'Korin', 'krillin1': 'Krillin', 'krillin2': 'Krillin',
      'piccolo': 'Piccolo', 'popo': 'Mr. Popo', 'puar': 'Puar', 'roshi': 'Master Roshi', 'tien': 'Tien', 'vegeta1': 'Vegeta', 'vegeta2': 'Vegeta', 'vegeta3': 'Vegeta', 'yamcha': 'Yamcha',
      'assist1': "Yemma's Assistant", 'assist2': "Yemma's Assistant", 'assist3': "Yemma's Assistant", 'robber1': 'Thug', 'robber2': 'Thug', 'robber3': 'Thug'}
SPEAK = {'frieza1': 'FRIEZA', 'frieza2': 'FRIEZA', 'frieza3': 'FRIEZA', 'frieza4': 'FRIEZA', 'dende': 'DENDE', 'gohan1': 'GOHAN', 'gohan2': 'GOHAN', 'gohan3': 'GOHAN', 'goku': 'GOKU', 'ssgoku': 'GOKU', 'gokumallet': 'GOKU',
         'piccolo': 'PICCOLO', 'krillin1': 'KRILLIN', 'krillin2': 'KRILLIN', 'bulma': 'BULMA', 'chichi': 'CHI', 'yamcha': 'YAMCHA', 'tien': 'TIEN', 'vegeta1': 'VEGETA', 'vegeta2': 'VEGETA', 'vegeta3': 'VEGETA', 'roshi': 'ROSHI', 'kingkai': 'KING KAI', 'popo': 'POPO', 'korrin': 'KORIN'}


def main():
    log1, bf, log2 = sys.argv[1:4]
    L = [l for l in csv.reader(open(bf + '/assets/tables/scouter.csv')) if l and not l[0].startswith('#')]
    sc = defaultdict(set)
    for r in L[1:]: sc[dict(zip(L[0], r))['_name_text'].strip()].add(int(dict(zip(L[0], r))['character']))
    sp = open(log2 + '/assets/scripts/SPEAKERS.txt', errors='ignore').read().upper()
    rep = json.load(open(ROOT + '/out/converted/report.json'))
    rows = []
    for n in [l.split()[1] for l in open(log1 + '/assets/areas/SPRITES.txt')]:
        name = BF.get(n); ids = sorted(sc.get(name, [])) if name else []
        rows.append(dict(sprite=n, source='buus_fury' if ids else 'log1', bf_name=name if ids else None, bf_ids=ids, log2_portrait=bool(SPEAK.get(n) and SPEAK[n] in sp),
                         placed=rep['enemy_sprites'].get(n, 0) + rep['npc_sprites'].get(n, 0), lines=rep['speakers'].get(n, 0)))
    json.dump(rows, open(ROOT + '/out/audit.json', 'w'), indent=1)
    print(Counter(r['source'] for r in rows))
    print('BF:', ' '.join('%s=%s' % (r['sprite'], r['bf_ids'][:4]) for r in rows if r['source'] == 'buus_fury'))
    print('LOG1:', ' '.join(r['sprite'] for r in rows if r['source'] == 'log1'))
    print('speakers without BF or LoG2 portrait route:', sum(1 for r in rows if r['lines'] and r['source'] == 'log1' and not r['log2_portrait']), 'lines', sum(r['lines'] for r in rows if r['source'] == 'log1' and not r['log2_portrait']))
    print('LoG2 portrait hits:', [r['sprite'] for r in rows if r['log2_portrait']])


if __name__ == '__main__':
    main()
