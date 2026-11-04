"""New side content for the remake, in the series' sillier spirit: a bounty board, hidden gear and more lost spirits. All text here is original.

Bounty board (City): talk to Officer Pudding to open five bounties around the world, with EXP for each and a shirt for the last.
Hidden gear: capsules in pockets only flight reaches, each with a piece of Buu's Fury's sillier equipment. Gear drops at Goku's feet (native 143).
Lost Spirits, extended (Hell): three more spirits to walk to the attendant once Gathered Spirits is done, then a fight with Head Demon Steve.

HP and EXP are placeholders until the balancing pass. Flags 340-365.
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
from convert_log1 import split_line  # noqa: E402

OPEN, KILLED, PAID, CHEST, S_START, S_DONE, STEVE_DEAD, STEVE_PAID, STEVE_OPEN = 340, 341, 346, 351, 357, 360, 363, 364, 365
GATHERED = 420 + 30                                                    # quest 30, Gathered Spirits
EARTH_CITY, HELL = 17, 12

BOUNTIES = [
    dict(area=4, sprite='ptero1', at=(700, 420), hp=150, exp=500, name='Sir Reginald Flapsworth',
         paid=["Bounty collected: Sir Reginald Flapsworth, wanted for grand theft lunchbox.", "He drops a very small monocle. Nobody asks."]),
    dict(area=0, sprite='crab', at=(380, 250), hp=300, exp=800, name='Gus',
         paid=["Bounty collected: Gus the Unreasonably Large Crab, wanted for pinching sunbathers.", "Master Roshi is furious. Gus was the only one who ever laughed at his jokes."]),
    dict(area=5, sprite='squirrel', at=(600, 420), hp=500, exp=1200, name='Nutty Tony',
         paid=["Bounty collected: Nutty Tony, kingpin of the acorn underworld.", "Somewhere, ten thousand squirrels begin to plot."]),
    dict(area=16, sprite='wolf', at=(360, 320), hp=800, exp=2000, name='Mayor Wolfgang',
         paid=["Bounty collected: Mayor Wolfgang, elected by a very scared town.", "A recount has been called."]),
    dict(area=22, sprite='trex', at=(360, 160), hp=1500, exp=4000, name='Mrs. Fluffy', gear=38,
         paid=["Bounty collected: Mrs. Fluffy, the Mayor's lost kitten.", "In hindsight, the poster did say 'big boned'.", "She was wearing a very stylish shirt. You feel you should have it."]),
]
CHESTS = [
    dict(area=2, at=(856, 288), gear=50, text="Wool Mittens! A note says: 'Goku, wrap up warm. Love, Chi-Chi. P.S. Study.'"),
    dict(area=4, at=(440, 632), gear=14, text="A Halloween Costume! It's a very frightening Goku. You scream a little."),
    dict(area=5, at=(80, 32), gear=117, text="Rhinestone Sunglasses! You can't see a thing, but you've never looked better."),
    dict(area=9, at=(888, 40), gear=51, text="Reflective Gloves! Now your enemies can see how sorry they are."),
    dict(area=22, at=(8, 8), gear=29, text="A Rhinestone Leisure Suit! The army swears it has no idea how this got here."),
    dict(area=12, at=(392, 8), gear=36, text="A Wet Suit, here in Hell. Some demon has big plans for his day off."),
]
SPIRITS = [
    dict(sprite='spirit4', at=(700, 300), hi=["Excuse me, did I leave the stove on? I died a hundred years ago, but it's really been bothering me.", "Could you walk me to the attendant? She has a form for this."],
         end=["Stove inquiry, form 12-B. It's been on for a hundred years, sir. Your house is fine. Your neighbours have questions."]),
    dict(sprite='spirit5', at=(1000, 500), hi=["I'd like to come back as a lamp. Nothing fancy. People are nice to lamps.", "Take me to the attendant, would you? Mind the flames, I'm flammable. That's new."],
         end=["Reincarnation as a lamp... approved. Floor lamp or table lamp? Oh, take your time. You've got eternity."]),
    dict(sprite='spirit1', at=(300, 500), hi=["I'm not lost. I'm exploring. I've been exploring this rock for sixty years.", "Fine! Fine. Walk me to the attendant. But I was about to find it."],
         end=["Sixty years, and the office is right here. It has a sign, sir.", "Oh dear. That was the last of today's queue, which means Head Demon Steve will want a word. He hates it when the queue moves."]),
]
STEVE = dict(sprite='devil2', at=(528, 560), hp=1000, gear=15, paid=["Head Demon Steve: Ow! Okay! Okay! You have the good manners to punch me in the face!", "Head Demon Steve: Take this armor. It's the Dark kind. I only wear it to parties, and nobody invites me."])


def say(who, text):
    t = text.replace('{', '(').replace('}', ')')
    return ['say goku ' + p for p in split_line(t)] if who == 'goku' else ['narrate ' + p for p in split_line((who + ': ' if who else '') + t)]


class Side:
    def __init__(self, story): self.st = story

    def add_pickups(self):
        """Hidden capsules go through the same streaming as LoG1's pickups."""
        for i, c in enumerate(CHESTS):
            if c['area'] in self.st.pickups: self.st.pickups[c['area']].append(dict(x=c['at'][0], y=c['at'][1], id=21, flag=CHEST + i, list='side_chest%d' % i, side=say(None, c['text']) + ['do call 143 %d' % c['gear']]))

    def lists(self):
        ids = self.st.ids; o = ['list side_board', 'set_flag 895', 'if_flag %d b_open' % OPEN, 'set_flag %d' % OPEN]
        o += say('Officer Pudding', "Citizen! Are you here about the bounties? Excellent. I'd do it myself, but I have a note from my mum.")
        o += say('Officer Pudding', "Five dangerous criminals roam the land. Check the Forest, Kame Island, the Village, the road outside town and the Military Base.")
        o += say('goku', "Are they strong? Is there food?")
        o += say('Officer Pudding', "...One of them is a kitten. Off you go.") + ['stop', 'label b_open']
        for i, b in enumerate(BOUNTIES):
            o += ['if_flag %d b_%d' % (PAID + i, i)] + say('Officer Pudding', 'Still out there: %s. Please hurry. I have promised the press a photo.' % b['name']) + ['stop', 'label b_%d' % i]
        o += say('Officer Pudding', "All five! You've put me out of a job, citizen. I'm going to go lie down in a field.") + ['stop']
        o += ['list side_check', 'set_flag 895']
        for i, b in enumerate(BOUNTIES):
            o += ['if_flag %d sc%d' % (PAID + i, i), 'unless_flag %d sc%d' % (KILLED + i, i), 'set_flag %d' % (PAID + i)]
            for t in b['paid']: o += say(None, t)
            o += ['do call 194 %d' % b['exp']] + (['do call 143 %d' % b['gear']] if 'gear' in b else []) + ['label sc%d' % i]
        o += ['if_flag %d sc_s' % STEVE_PAID, 'unless_flag %d sc_s' % STEVE_DEAD, 'set_flag %d' % STEVE_PAID]
        for t in STEVE['paid']: o += say(None, t)
        o += ['do call 194 3000', 'do call 143 %d' % STEVE['gear'], 'label sc_s', 'stop']
        for i, s in enumerate(SPIRITS):
            o += ['list side_spirit%d' % i, 'set_flag 895', 'if_flag %d sp%d' % (S_START + i, i)]
            for t in s['hi']: o += say('Lost Spirit', t)
            o += ['set_flag %d' % (S_START + i), 'label sp%d' % i, 'stop']
        o += ['list side_deliver', 'set_flag 895']
        for i, s in enumerate(SPIRITS):
            o += ['unless_flag %d de%d' % (S_START + i, i), 'if_flag %d de%d' % (S_DONE + i, i), 'set_flag %d' % (S_DONE + i)]
            for t in s['end']: o += say('Attendant', t)
            o += ['do call 194 1000']
            if i == len(SPIRITS) - 1: o.append('set_flag %d' % STEVE_OPEN)
            o += ['label de%d' % i]
        return o + ['stop']

    def install(self, n, a, fits, r, actors, put, named, spawns, foes_out, follows, walkins, foe_i, BF_IDX, cond_code):
        """Adds this area's side content to the build's tables. Returns the next enemy index."""
        BB = 0x08000000
        def spot(x, y):
            for d in range(0, 200, 4):
                for ox in range(-d, d + 1, 4):
                    for oy in range(-d, d + 1, 4):
                        if max(abs(ox), abs(oy)) == d and fits(a, x + ox, y + oy): return x + ox, y + oy
            raise ValueError((n, x, y))
        def npc_rec(sprite, x, y, talk):
            idx = BF_IDX.get(sprite) or actors.actor(sprite, False); rec = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, (y << 16) | x, talk, idx, 1, 0)); struct.pack_into('<I', r, rec - BB + 32, rec); return rec + 8, idx
        if n == EARTH_CITY:
            x, y = spot(360, 320); rec, _ = npc_rec('cop1', x, y, named['side_board']); self.board_rec = rec
        for i, b in enumerate(BOUNTIES):
            if b['area'] != n: continue
            x, y = spot(*b['at']); death = put(__import__('scenes').assemble('call 29 %d; call 29 893' % (KILLED + i), {}) + b'\x11'); row = actors.row(b['sprite'], death, True, b['hp'])
            cond = put(cond_code('set:%d & clear:%d' % (OPEN, KILLED + i)) + b'\x11')
            foes_out.append((n, foe_i, x, y, put(struct.pack('<8I', 0x0800FD55, cond, row, (y << 16) | x, actors.actor(b['sprite'], True), 0x080555A0, 1, 0x080716EC)))); foe_i += 1
        if n == HELL:
            for i, s in enumerate(SPIRITS):
                x, y = spot(*s['at']); rec, idx = npc_rec(s['sprite'], x, y, named['side_spirit%d' % i])
                spawns.append((GATHERED, n, rec, 0, S_START + i)); spawns.append((S_START + i, n, 0, idx, 0))
                rf = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, 0, named['no_talk'], idx, 1, 0)); struct.pack_into('<I', r, rf - BB + 32, rf); follows.append((S_START + i, S_DONE + i, rf + 8))
            walkins.append((n, 40, 672, 112, 744, named['side_deliver']))
            x, y = spot(*STEVE['at']); death = put(__import__('scenes').assemble('call 29 %d; call 29 893' % STEVE_DEAD, {}) + b'\x11'); row = actors.row(STEVE['sprite'], death, True, STEVE['hp'])
            spawns.append((STEVE_OPEN, n, put(struct.pack('<8I', 0x0800FD55, 0, row, (y << 16) | x, actors.actor(STEVE['sprite'], True), 0x080555A0, 1, 0x080716EC)), 0, STEVE_DEAD))
        return foe_i
