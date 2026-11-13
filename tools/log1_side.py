"""New side content for the remake, in the series' sillier spirit: a bounty board, hidden gear and more lost spirits. All text here is original.

Bounty board (City): talk to Officer Pudding to open five bounties around the world, with EXP for each and a shirt for the last.
Hidden gear: capsules in pockets only flight reaches, each with a piece of Buu's Fury's sillier equipment. Gear goes straight into the equipment list (native 0x93).
Lost Spirits, extended (Hell): three more spirits to walk to the attendant once Gathered Spirits is done, then a fight with Head Demon Steve.

HP and EXP come from log1_balance, a bit above each area's level. Flags 340-365.
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'vendor', 'gero-tools', 'tools')]
from convert_log1 import split_line  # noqa: E402

OPEN, KILLED, PAID, CHEST, S_START, S_DONE, STEVE_DEAD, STEVE_PAID, STEVE_OPEN = 340, 341, 346, 351, 357, 360, 363, 364, 365
GATHERED = 420 + 30                                                    # quest 30, Gathered Spirits
EARTH_CITY, HELL = 17, 12

BOUNTIES = [
    dict(area=4, sprite='ptero1', at=(700, 420), name='Sir Reginald Flapsworth',
         paid=["Bounty collected: Sir Reginald Flapsworth, wanted for grand theft lunchbox.", "He drops a very small monocle. Nobody asks."]),
    dict(area=0, sprite='crab', at=(380, 250), name='Gus',
         paid=["Bounty collected: Gus the Unreasonably Large Crab, wanted for pinching sunbathers.", "Master Roshi is furious. Gus was the only one who ever laughed at his jokes."]),
    dict(area=5, sprite='squirrel', at=(600, 420), name='Nutty Tony',
         paid=["Bounty collected: Nutty Tony, kingpin of the acorn underworld.", "Somewhere, ten thousand squirrels begin to plot."]),
    dict(area=16, sprite='wolf', at=(360, 320), name='Mayor Wolfgang',
         paid=["Bounty collected: Mayor Wolfgang, elected by a very scared town.", "A recount has been called."]),
    dict(area=22, sprite='trex', at=(360, 160), name='Mrs. Fluffy', gear=38, extra=4,
         paid=["Bounty collected: Mrs. Fluffy, the Mayor's lost kitten.", "In hindsight, the poster did say 'big boned'.", "She was wearing a very stylish shirt. You feel you should have it."]),
]
CHESTS = [
    dict(area=2, at=(904, 408), gear=50, text="Wool Mittens! A note says: 'Goku, wrap up warm. Love, Chi-Chi. P.S. Study.'"),
    dict(area=4, at=(240, 712), gear=14, text="A Halloween Costume! It's a very frightening Goku. You scream a little."),
    dict(area=5, at=(136, 32), gear=117, text="Rhinestone Sunglasses! You can't see a thing, but you've never looked better."),
    dict(area=9, at=(792, 312), gear=51, text="Reflective Gloves! Now your enemies can see how sorry they are."),
    dict(area=22, at=(104, 152), gear=29, text="A Rhinestone Leisure Suit! The army swears it has no idea how this got here."),
    dict(area=12, at=(992, 144), gear=36, text="A Wet Suit, here in Hell. Some demon has big plans for his day off."),
]
SPIRITS = [
    dict(sprite='spirit4', at=(700, 300), hi=["Excuse me, did I leave the stove on? I died a hundred years ago, but it's really been bothering me.", "Could you walk me to the attendant? She has a form for this."],
         end=["Stove inquiry, form 12-B. It's been on for a hundred years, sir. Your house is fine. Your neighbours have questions."]),
    dict(sprite='spirit5', at=(1000, 500), hi=["I'd like to come back as a lamp. Nothing fancy. People are nice to lamps.", "Take me to the attendant, would you? Mind the flames, I'm flammable. That's new."],
         end=["Reincarnation as a lamp... approved. Floor lamp or table lamp? Oh, take your time. You've got eternity."]),
    dict(sprite='spirit1', at=(300, 500), hi=["I'm not lost. I'm exploring. I've been exploring this rock for sixty years.", "Fine! Fine. Walk me to the attendant. But I was about to find it."],
         end=["Sixty years, and the office is right here. It has a sign, sir.", "Oh dear. That was the last of today's queue, which means Head Demon Steve will want a word. He hates it when the queue moves."]),
]
STEVE = dict(sprite='devil2', at=(528, 560), gear=15, paid=["Head Demon Steve: Ow! Okay! Okay! You have the good manners to punch me in the face!", "Head Demon Steve: Take this armor. It's the Dark kind. I only wear it to parties, and nobody invites me."])

# Later additions. Flags 366-394.
QF = 420
BUTLER_OPEN, SLIPPER, BUTLER_PAID = 366, 367, 370
BUTLER = dict(area=11, sprite='snake', at=(300, 890), after=QF + 26, gear=54)
SLIPPERS = [((230, 1100), "A very small slipper. Snakes don't have feet. You decide not to ask."), ((200, 1300), "Another slipper, monogrammed 'P.S.' and slightly chewed."),
            ((220, 700), "The last slipper. It smells of perfume and regret.")]
COACH_OPEN, COACH_KILLED, COACH_PAID = 371, 372, 375
COACH = dict(area=13, sprite='crab', at=(120, 300), after=QF + 35, gear=52, foes=[(200, 280), (300, 340), (420, 300)], enemy='devil1')
ELITE_KILLED, ELITE_PAID = 376, 379
ELITES = [dict(area=24, sprite='hench7', at=(640, 420), gear=None, paid="Sergeant Second-to-Last falls over. He had one job, and it was mostly standing."),
          dict(area=28, sprite='hench8', at=(500, 300), gear=None, paid="Lieutenant Quite-Important drops his clipboard. It lists his own name, circled."),
          dict(area=31, sprite='hench6', at=(420, 300), gear=57, paid="Major Actually-Pretty-Good gives you his favourite gear. He says it's for your trouble. He seems relieved.")]
AFTER_ELITES = QF + 52
ELDER_PAID = 382
ELDER = dict(area=24, sprite='oldman', at=(300, 500), after=QF + 53)
RM_KILLED, RM_PAID, RM_OPEN = 383, 387, 391
ANNOUNCER = dict(area=0, sprite='wiseman', at=(292, 186), after=QF + 68)
REMATCHES = [dict(sprite='raditz', at=(380, 200), name='Raditz', extra=0, line="Raditz: I came back to apologise. No, wait. To fight. It was to fight."),
             dict(sprite='nappa', at=(380, 200), name='Nappa', extra=3, line="Nappa: Vegeta says I have to do this before I can have dessert."),
             dict(sprite='vegeta2', at=(380, 200), name='Vegeta', extra=6, line="Vegeta: This changes nothing, Kakarot. I'm only here for the exercise."),
             dict(sprite='frieza4', at=(380, 200), name='Frieza', extra=9, gear=45, line="Frieza: You have five minutes. I've booked the island until two.")]


def say(who, text):
    t = text.replace('{', '(').replace('}', ')')
    return ['say goku ' + p for p in split_line(t)] if who == 'goku' else ['narrate ' + p for p in split_line((who + ': ' if who else '') + t)]


class Side:
    def __init__(self, story): self.st = story

    def add_pickups(self):
        """Hidden capsules go through the same streaming as LoG1's pickups."""
        for i, c in enumerate(CHESTS):
            if c['area'] in self.st.pickups: self.st.pickups[c['area']].append(dict(x=c['at'][0], y=c['at'][1], id=21, flag=CHEST + i, list='pk_side%d' % i, side=say(None, c['text']) + ['do call 147 %d' % c['gear']]))

    def lists(self):
        ids = self.st.ids; o = ['list side_board', 'set_flag 895', 'if_flag %d b_open' % OPEN, 'set_flag %d' % OPEN]
        o += say('Officer Pudding', "Citizen! Are you here about the bounties? Excellent. I'd do it myself, but I have a note from my mum.")
        o += say('Officer Pudding', "Five dangerous criminals roam the land. Check the Forest, Kame Island, the Village, the road outside town and the Military Base.")
        o += say('goku', "Are they strong? Is there food?")
        o += say('Officer Pudding', "...One of them is a kitten. Off you go.") + ['stop', 'label b_open']
        for i, b in enumerate(BOUNTIES):
            o += ['if_flag %d b_%d' % (PAID + i, i)] + say('Officer Pudding', 'Still out there: %s. Please hurry. I have promised the press a photo.' % b['name']) + ['stop', 'label b_%d' % i]
        o += say('Officer Pudding', "All five! You've put me out of a job, citizen. I'm going to go lie down in a field.") + ['stop']
        o += self.more_lists()
        o += ['list side_check', 'set_flag 895']
        for i, b in enumerate(BOUNTIES):
            o += ['if_flag %d sc%d' % (PAID + i, i), 'unless_flag %d sc%d' % (KILLED + i, i), 'set_flag %d' % (PAID + i)]
            for t in b['paid']: o += say(None, t)
            o += ['do call 194 %d' % self.st.bal.quest_exp(b['area'], True)] + (['do call 147 %d' % b['gear']] if 'gear' in b else []) + ['label sc%d' % i]
        o += self.more_checks() + __import__('log1_party').checks(self.st) + __import__('log1_movies').checks(self.st)
        o += ['if_flag %d sc_s' % STEVE_PAID, 'unless_flag %d sc_s' % STEVE_DEAD, 'set_flag %d' % STEVE_PAID]
        for t in STEVE['paid']: o += say(None, t)
        o += ['do call 194 %d' % self.st.bal.quest_exp(HELL, True), 'do call 147 %d' % STEVE['gear'], 'label sc_s', 'stop']
        for i, s in enumerate(SPIRITS):
            o += ['list side_spirit%d' % i, 'set_flag 895', 'if_flag %d sp%d' % (S_START + i, i)]
            for t in s['hi']: o += say('Lost Spirit', t)
            o += ['set_flag %d' % (S_START + i), 'label sp%d' % i, 'stop']
        o += ['list side_deliver', 'set_flag 895']
        for i, s in enumerate(SPIRITS):
            o += ['unless_flag %d de%d' % (S_START + i, i), 'if_flag %d de%d' % (S_DONE + i, i), 'set_flag %d' % (S_DONE + i)]
            for t in s['end']: o += say('Attendant', t)
            o += ['do call 194 %d' % self.st.bal.quest_exp(HELL)]
            if i == len(SPIRITS) - 1: o.append('set_flag %d' % STEVE_OPEN)
            o += ['label de%d' % i]
        return o + ['stop']

    def more_lists(self):
        o = ['list side_butler', 'set_flag 895']
        o += ['if_flag %d bu_paid' % BUTLER_PAID, 'if_flag %d bu_open' % BUTLER_OPEN, 'set_flag %d' % BUTLER_OPEN]
        o += say('Snake Butler', "Excuse me, sir. Her Highness has mislaid her slippers somewhere along Snake Way. Three of them.")
        o += say('goku', "Why does a snake need slippers?") + say('Snake Butler', "I have worked here four hundred years, sir, and I have learned not to ask.") + ['stop', 'label bu_open']
        for i in range(len(SLIPPERS)): o += ['unless_flag %d bu_wait' % (SLIPPER + i)]
        o += ['set_flag %d' % BUTLER_PAID] + say('Snake Butler', "All three! Her Highness will be thrilled, or at least less terrifying. Please accept these. They were a gift she didn't care for.")
        o += ['do call 194 %d' % self.st.bal.quest_exp(BUTLER['area'], True), 'do call 147 %d' % BUTLER['gear'], 'stop', 'label bu_wait']
        o += say('Snake Butler', "Still searching, sir? Do mind the edge. It's a long way down, and it's mostly paperwork.") + ['stop', 'label bu_paid']
        o += say('Snake Butler', "Her Highness has now lost a hat. I shall tell her you've retired.") + ['stop']
        for i, (_, t) in enumerate(SLIPPERS):
            o += ['list side_slip%d' % i, 'set_flag 895', 'unless_flag %d sl%d' % (BUTLER_OPEN, i), 'if_flag %d sl%d' % (SLIPPER + i, i), 'set_flag %d' % (SLIPPER + i)] + say(None, t) + ['label sl%d' % i, 'stop']
        o += ['list side_coach', 'set_flag 895', 'if_flag %d co_paid' % COACH_PAID, 'if_flag %d co_open' % COACH_OPEN, 'set_flag %d' % COACH_OPEN]
        o += say('Coach Crab', "You! Stop slouching. This planet's gravity is ten times Earth's, and you're still walking like you're on holiday.")
        o += say('Coach Crab', "Three of my Gravity Ghosts are loose. Catch them. It builds character. I've got loads, and look at me.") + say('goku', "You're a crab.") + say('Coach Crab', "Exactly.") + ['stop', 'label co_open']
        o += say('Coach Crab', "Still ghosts out there! And pick your knees up, sideways is the only way to walk!") + ['stop', 'label co_paid']
        o += say('Coach Crab', "You've graduated. Your diploma is that you may now leave.") + ['stop']
        o += ['list side_elder', 'set_flag 895', 'if_flag %d el_paid' % ELDER_PAID, 'set_flag %d' % ELDER_PAID]
        o += say('Village Elder', "Those saplings you saved have sprouted! We've got a shop now. It sells saplings. It's not a good business plan, but we are very proud.")
        o += say('Village Elder', "Here. Take these for your trouble. We grew them ourselves, somehow.") + ['do call 194 %d' % self.st.bal.quest_exp(ELDER['area'], True), 'do call 128 11', 'do call 128 11', 'do call 128 11', 'stop', 'label el_paid']
        o += say('Village Elder', "Business is terrible! Isn't it wonderful? We've never had a business before.") + ['stop']
        o += ['list side_announcer', 'set_flag 895']
        for i, m in enumerate(REMATCHES):
            o += ['if_flag %d rm%d' % (RM_KILLED + i, i), 'if_flag %d rw%d' % (RM_OPEN + i, i), 'set_flag %d' % (RM_OPEN + i)]
            o += say('Announcer', "Welcome to the Kame Island Invitational! Today's challenger, back by no popular demand: %s! Over on the beach, please." % m['name']) + say(None, m['line']) + ['stop', 'label rw%d' % i]
            o += say('Announcer', "Your opponent's waiting on the beach, and I'm paid by the hour, so take your time.") + ['stop', 'label rm%d' % i]
        o += say('Announcer', "That's everyone! The tournament is over, and I've just been told the prize was exposure. Thanks for coming!") + ['stop']
        return o

    def more_checks(self):
        o = ['if_flag %d sc_co' % COACH_PAID] + ['unless_flag %d sc_co' % (COACH_KILLED + i) for i in range(len(COACH['foes']))] + ['set_flag %d' % COACH_PAID]
        o += say('Coach Crab', "Ha! That's the last ghost! Here, take these weights. I can't lift them, on account of being a crab.") + ['do call 194 %d' % self.st.bal.quest_exp(COACH['area'], True), 'do call 147 %d' % COACH['gear'], 'label sc_co']
        for i, e in enumerate(ELITES):
            o += ['if_flag %d sc_e%d' % (ELITE_PAID + i, i), 'unless_flag %d sc_e%d' % (ELITE_KILLED + i, i), 'set_flag %d' % (ELITE_PAID + i)] + say(None, e['paid']) + ['do call 194 %d' % self.st.bal.quest_exp(e['area'], True)] + (['do call 147 %d' % e['gear']] if e['gear'] else []) + ['label sc_e%d' % i]
        for i, m in enumerate(REMATCHES):
            o += ['if_flag %d sc_r%d' % (RM_PAID + i, i), 'unless_flag %d sc_r%d' % (RM_KILLED + i, i), 'set_flag %d' % (RM_PAID + i)] + say('Announcer', "And %s is down! Talk to me when you're ready for the next one." % m['name']) + ['do call 194 %d' % self.st.bal.quest_exp(41, True)] + (['do call 147 %d' % m['gear']] if m.get('gear') else []) + ['label sc_r%d' % i]
        return o

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
            x, y = spot(*b['at']); death = put(__import__('scenes').assemble('call 29 %d; call 29 893' % (KILLED + i), {}) + b'\x11'); row = actors.row(b['sprite'], death, True, None, n, True, b.get('extra', 0))
            cond = put(cond_code('set:%d & clear:%d' % (OPEN, KILLED + i)) + b'\x11')
            foes_out.append((n, foe_i, x, y, put(struct.pack('<8I', 0x0800FD55, cond, row, (y << 16) | x, actors.actor(b['sprite'], True), 0x080555A0, 1, 0x080716EC)))); foe_i += 1
        if n == HELL:
            for i, s in enumerate(SPIRITS):
                x, y = spot(*s['at']); rec, idx = npc_rec(s['sprite'], x, y, named['side_spirit%d' % i])
                spawns.append((GATHERED, n, rec, 0, S_START + i)); spawns.append((S_START + i, n, 0, idx, 0))
                rf = put(struct.pack('<9I', 0x0800A223, 0x32, 0x08017DA3, 0x20002, 0, named['no_talk'], idx, 1, 0)); struct.pack_into('<I', r, rf - BB + 32, rf); follows.append((S_START + i, S_DONE + i, rf + 8))
            walkins.append((n, 40, 672, 112, 744, named['side_deliver']))
            x, y = spot(*STEVE['at']); death = put(__import__('scenes').assemble('call 29 %d; call 29 893' % STEVE_DEAD, {}) + b'\x11'); row = actors.row(STEVE['sprite'], death, True, None, n, True, 3)
            spawns.append((STEVE_OPEN, n, put(struct.pack('<8I', 0x0800FD55, 0, row, (y << 16) | x, actors.actor(STEVE['sprite'], True), 0x080555A0, 1, 0x080716EC)), 0, STEVE_DEAD))
        def foe(sprite, x, y, cond, kill, extra=0, boss=True, level_area=None, tint=None, look=None):
            nonlocal foe_i
            x, y = spot(x, y); death = put(__import__('scenes').assemble('call 29 %d; call 29 893' % kill, {}) + b'\x11'); row = actors.row(sprite, death, True, None, level_area if level_area is not None else n, boss, extra)
            foes_out.append((n, foe_i, x, y, put(struct.pack('<8I', 0x0800FD55, put(cond_code(cond) + b'\x11'), row, (y << 16) | x, actors.actor(sprite, True, tint, look), 0x080555A0, 1, 0x080716EC)))); foe_i += 1
        def npc(d, talk):
            x, y = spot(*d['at']); rec, _ = npc_rec(d['sprite'], x, y, named[talk]); spawns.append((d['after'], n, rec, 0, 0))
        if n == BUTLER['area']:
            npc(BUTLER, 'side_butler')
            for i, (at, _) in enumerate(SLIPPERS):
                x, y = spot(*at); walkins.append((n, x - 12, y - 12, x + 28, y + 20, named['side_slip%d' % i]))
        if n == COACH['area']:
            npc(COACH, 'side_coach')
            for i, at in enumerate(COACH['foes']): foe(COACH['enemy'], at[0], at[1], 'set:%d & clear:%d' % (COACH_OPEN, COACH_KILLED + i), COACH_KILLED + i, 2, False)
        for i, e in enumerate(ELITES):
            if e['area'] == n: foe(e['sprite'], e['at'][0], e['at'][1], 'set:%d & clear:%d' % (AFTER_ELITES, ELITE_KILLED + i), ELITE_KILLED + i, 4, True)
        if n == ELDER['area']: npc(ELDER, 'side_elder')
        __import__('log1_party').install(n, a, fits, r, actors, put, named, spawns, foe, BF_IDX)
        __import__('log1_movies').install(n, a, fits, r, actors, put, named, spawns, foe, walkins, BF_IDX)
        if n == ANNOUNCER['area']:
            npc(ANNOUNCER, 'side_announcer')
            for i, m in enumerate(REMATCHES): foe(m['sprite'], m['at'][0], m['at'][1], 'set:%d & clear:%d' % (RM_OPEN + i, RM_KILLED + i), RM_KILLED + i, m['extra'], True, 41)
        return foe_i
