"""Balance: a Buu's Fury level for each LoG1 area, with enemy stats read off Buu's Fury's own enemies at that level and EXP scaled to its curve.

Levels here are Buu's Fury's stored value minus 50. The game shows the stored value, so level 1 reads LVL 51. Numbers come from your Buu's Fury data at build time. Tune STAGE and the factors below.
"""
import csv, json, os
import numpy as np
BOSS_HP, BOSS_DMG, KILL_EXP, QUEST_EXP = 5.0, 1.15, 0.5, 0.45
START = dict(level=51, hp=90, ep=60, str=18, pow=18, end=16, spd=50)    # replaces Goku's Buu's Fury start
STAGE = {0: 2, 1: 2, 2: 3, 3: 15, 4: 5, 5: 7, 6: 7, 7: 7, 8: 7, 9: 10, 10: 10, 11: 12, 12: 15, 13: 16, 14: 16, 15: 18, 16: 19, 17: 20, 18: 20, 19: 20, 20: 20, 21: 20, 22: 22, 23: 25,
         24: 28, 25: 28, 26: 28, 27: 28, 28: 30, 30: 33, 31: 38, 32: 40, 33: 40, 34: 41, 35: 41, 36: 43, 37: 43, 38: 43, 39: 43, 40: 46, 41: 50}
for _k in range(42, 54): STAGE[_k] = 33


class Balance:
    def __init__(self, bf_decomp):
        T = bf_decomp + '/assets/tables/'; R = [e for e in csv.DictReader(l for l in open(T + 'enemies.csv') if not l.startswith('#')) if e['_names']]
        self.exp = [int(e['exp']) for e in csv.DictReader(l for l in open(T + 'exp.csv') if not l.startswith('#'))]
        P = np.array([[int(e['level_plus_50']) - 50, int(e['hp']), int(e['exp']), int(e['str']), int(e['pow']), int(e['end'])] for e in R if 40 <= int(e['hp']) < 8000 and int(e['exp']) > 0 and int(e['level_plus_50']) > 50], float)
        self.P = P
        def fit(y, log=False):
            yy = np.log(y) if log else y; c = np.polyfit(P[:, 0], yy, 2); return (lambda L: float(np.exp(np.polyval(c, L)))) if log else (lambda L: float(np.polyval(c, L)))
        self.f_hp, self.f_exp = fit(P[:, 1], True), fit(P[:, 2], True); atk = np.maximum(P[:, 3], P[:, 4]); self.f_atk, self.f_end = fit(atk), fit(P[:, 5])

    def enemy(self, area, boss=False, extra=0):
        """(level + 50, hp, exp, str, pow, end) for an enemy in this area."""
        L = STAGE[area] + extra + (2 if boss else 0); hp, ex = self.f_hp(L), self.f_exp(L); a, e = max(4, self.f_atk(L)), max(4, self.f_end(L))
        if L < 12: hp = 18 + 18 * L; ex *= (L / 12) ** 2           # Buu's Fury has no enemies this weak, so the curve is drawn in by hand
        ex *= 1 + L / 30
        if boss: hp *= min(BOSS_HP, 2.5 + L / 12); a *= (0.8 if L < 20 else BOSS_DMG); ex *= 6     # early bosses ease in; the first difficulty run died at every one up to Burter
        return int(L + 50), int(max(12, hp)), int(ex * KILL_EXP), int(a), int(a), int(e)

    def quest_exp(self, area, boss=False):
        """A quest reward: part of the way to the next level at this stage, more for a boss."""
        L = STAGE.get(area, 10); gap = self.exp[min(L + 2, len(self.exp) - 1)] - self.exp[L + 1]; return int(gap * (1.3 if boss else QUEST_EXP) * (1 + L / 25))

    def simulate(self, log1):
        """Expected level through the story, killing each area's enemies once on the way through."""
        names = json.load(open(log1 + '/assets/story/quests.json'))['quests']; xp = 0; out = []; seen = set()
        def level(x):
            k = 0
            while k + 1 < len(self.exp) and self.exp[k + 1] <= x: k += 1
            return k
        for n, area in ((0, 0), (2, 2), (4, 4), (5, 5), (9, 9), (11, 11), (12, 12), (13, 13), (15, 15), (17, 17), (22, 22), (23, 23), (24, 24), (28, 28), (50, 50), (30, 30), (31, 31), (34, 34), (40, 40), (41, 41)):
            a = json.load(open(log1 + '/assets/areas/area%02d.json' % n)); foes = [s for s in a['actors'] if s['kind'] == 2]
            xp += sum(self.enemy(n)[2] for _ in foes) * .7
            qs = [x for x in names if any(t.get('area') == n for t in x['tasks']) and any(b['type'] == 'give_exp' for b in x['actions'])]
            xp += sum(self.quest_exp(n, any(t['type'] in ('activate', 'defeat') for t in x['tasks'])) for x in qs)
            out.append((n, STAGE[n], level(xp)))
        return out
