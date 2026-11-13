/* Goku's skills, ported from Buu's Fury Ultimate (ultimate/src/outfit.c): the Kaioken, transformation mastery and the skill book with SELECT swapping.
 *
 * Lore gates (the owner, Nov 9): Goku starts with the Energy Blast only. King Kai teaches the Kamehameha and the Kaioken after Gregory (quest 37), he
 * becomes a Super Saiyan against Frieza (quest 67), Instant Transmission waits for Yardrat (YARDRAT_FLAG) and the Spirit Bomb for King Kai's
 * post-game secret (SPIRIT_FLAG, Nov 9). A held skill
 * that isn't earned yet is taken out of his slots (old saves and Buu's Fury's own start held all four).
 *
 * Kaioken: from a base form to its red copy (build_skills.py makes the forms and actors), a Super Saiyan class form with the red aura. Its bar
 * drains as Super Saiyan's does and it costs health as it goes; hits are 1.25x to 1.75x by its mastery. Goku's Super Saiyan forms
 * have no red copy: this game never puts the Kaioken and Super Saiyan together (the owner, Nov 9). Fully mastered, the health cost becomes a
 * cyan bar of its own that takes hits without a stagger.
 *
 * Mastery: each drain unit in a tier's form trains it; at MASTERY_L2 and MASTERY_L3 units the tier reaches Level 2 and 3 and drains slower.
 * The units live in record 1 +0x22 (Super Saiyan) and +0x23 (Kaioken): Gohan's record, never played here, and a field retail never uses, so
 * they save with the game. Goku's own +0x22 is the book's mask of known skills.
 *
 * RAM: 0x03005F80-0x03005FFF (flight.c's hook RAM, cleared with it). Addresses are retail Buu's Fury's; BFU checked each site. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;

#define RECORDS ((u8 *)0x03001560)
#define RECORD_SIZE 0x68
#define CUR (*(volatile u8 *)0x03001068)
#define FLAGS ((volatile u8 *)0x030010BD)
#define QFLAG(q) (FLAGS[(420 + (q)) >> 3] >> ((420 + (q)) & 7) & 1)
#define FLAG(f) (FLAGS[(f) >> 3] >> ((f) & 7) & 1)
#define PLAYER_OBJ (*(u8 **)0x03001C34)
#define AREA (*(volatile u32 *)0x03001980)
#define FRAMES (*(volatile u32 *)0x03000F94)
#define IN_COMBAT (*(volatile u32 *)0x03001988)
#define KEYS_NEW (*(volatile u16 *)0x03003304)
#define SOUND_MOVE 0x0831947C
#define SOUND_HIT 0x083192A8
#define FONT 0x0807012C

#define Form_Sprite ((void *(*)(const void *))0x0801713D)
#define Sprite_SetCharacter ((void (*)(void *, void *))0x0800EDF9)
#define Sprite_SetFacing ((void (*)(void *, int))0x0800ECDB)
#define Sprite_SetBehaviour ((void (*)(void *, void *))0x0800ED19)
#define PlaySound ((void (*)(void *, void *, int, int))0x0803E379)
#define Alloc ((u32 *(*)(int))0x0803D5B9)
#define MemCopy ((void (*)(void *, const void *, int))0x08049139)
#define CanAfford ((int (*)(u8 *, int))0x080134B9)
#define SS_Can ((int (*)(u8 *))0x0801A4C5)
#define SS_Use ((void (*)(u8 *, void *))0x0801A513)
#define SS3_Use ((void (*)(u8 *, void *))0x0801A5BD)
#define NewSpark ((void *(*)(int, int *, const void *, int, int, int, int))0x0802A81D)
#define ListAdd ((void (*)(void *, void *))0x0801191B)
#define ACTORS ((void *)0x03001C4C)
#define SpriteBox ((void (*)(int *, void *))0x0800FDFB)
#define VecOp ((void (*)(int *, const int *, const int *))0x08052FB5)
#define AURA_MODE (*(volatile u8 *)0x03002BB0)
#define NewText ((u32 *(*)(void *, void *, int, int, const u16 *, int, int, void *))0x08014125)
#define AddWidget ((void (*)(void *, void *))0x0800664F)
#define RemoveSkill ((void (*)(u8 *, int))0x08013ABB)
#define GetLevel ((int (*)(u8 *))0x080135D3)

/* hook RAM */
#define KK_GUARD (*(volatile u16 *)0x03005F80)      /* mastered Kaioken's bar */
#define KK_ON (*(volatile u8 *)0x03005F82)
#define EARLY (*(volatile u8 *)0x03005F83)          /* form + 1 a power-up started from, while it plays on its new figure */
#define KK_EMPTY (*(volatile u8 *)0x03005F84)       /* 1: the bar ran out, 2: powering down for it */
#define KK_DRAWN (*(volatile u8 *)0x03005F85)       /* the bar's columns on the HUD as last drawn */
#define KK_POOL (*(volatile u16 *)0x03005F86)       /* Super Saiyan's pool + 1, kept while Super Saiyan Kaioken powers down to Super Saiyan */
#define hud_widget (*(u8 * volatile *)0x03005F88)
#define XFORM (*(volatile u8 *)0x03005F8C)          /* form + 1 the next power-up ends in, or 0 */
#define XFORM_FROM (*(volatile u8 *)0x03005F8D)     /* the form it was pressed in */
#define XFORM_AT (*(volatile u16 *)0x03005F8E)      /* and when (frame counter's low half) */
#define MASTERY_TICK (*(volatile u8 *)0x03005F90)
#define WHEEL_HELD (*(volatile u8 *)0x03005F91)
#define wheel_keys ((volatile u16 *)0x03005F94)     /* 6 halfwords */

/* filled by build_skills.py (volatile: the compiler would otherwise read these placeholders' values at compile time) */
__attribute__((section(".text.table"))) volatile const u32 forms_at = 0;    /* the form table, moved to make room for the red rows */
__attribute__((section(".text.table"))) volatile const u8 kaioken_map[8][2] = {{255, 255}};
__attribute__((section(".text.table"))) volatile const u8 skill_book[8] = {255};   /* Goku's skills in book order; the mask's bits follow it */
__attribute__((section(".text.table"))) volatile const u8 kk_bar[0x500] = {1};
__attribute__((section(".text.fixed"))) const u32 kk_aura_field[9] = {1}, kk_aura_other[21] = {1};
__attribute__((section(".text.fixed"))) const int kk_vt[14] = {1};
#define form_table ((const u8 *)forms_at)

static u8 *rec_of(int c) { return RECORDS + c * RECORD_SIZE; }
#define MASTERY (rec_of(1) + 0x22)          /* [0] Super Saiyan, [1] Kaioken */
static int flags_of(int form) { return form_table[form * 24]; }
static int mapped(int form) { int i; for (i = 0; kaioken_map[i][0] != 255; i++) if (kaioken_map[i][0] == form) return kaioken_map[i][1]; return 255; }
static int is_kaioken(int form) { int i; for (i = 0; kaioken_map[i][0] != 255; i++) if (kaioken_map[i][1] == form) return 1; return 0; }

/* ---------- mastery ---------- */
static int tier_of(int skill) { return skill == SS_SKILL ? 0 : skill == KAIOKEN_SKILL ? 1 : -1; }
int mastery_level(int c, int skill) {          /* 0, 1, 2: shown as Level 1-3 */
    int t = tier_of(skill);
    if (c != 0 || t < 0) return 0;
    return MASTERY[t] >= MASTERY_L3 ? 2 : MASTERY[t] >= MASTERY_L2 ? 1 : 0;
}
static int kk_mastered(void) { return mastery_level(CUR, KAIOKEN_SKILL) == 2; }
static int form_tier(int form) {
    if (is_kaioken(form)) return 1;
    if ((flags_of(form) & 3) == 1) return 0;
    return -1;
}
static int mastery_train(u8 *rec, int every) {        /* -> 1 to skip this drain unit */
    int t = form_tier(rec[0x14]), lv;
    if (CUR != 0 || t < 0) return 0;
    MASTERY_TICK++;
    if (MASTERY_TICK % every == 0 && MASTERY[t] < 255) {
        lv = mastery_level(0, t ? KAIOKEN_SKILL : SS_SKILL);
        MASTERY[t]++;
        if (mastery_level(0, t ? KAIOKEN_SKILL : SS_SKILL) != lv) PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
    }
    lv = mastery_level(0, t ? KAIOKEN_SKILL : SS_SKILL);
    return MASTERY_TICK % 5 < lv;
}

/* ---------- the skill book ---------- */
#define KNOWN(rec) (*(u16 *)((rec) + 0x22))
#define MAX_HELD 6
static int book_at(int skill) { int i; for (i = 0; i < 8; i++) if (skill_book[i] == skill) return i; return -1; }
static int slot_of(const u8 *rec, int skill) { int i; for (i = 0; i < rec[0x0C]; i++) if (rec[0x0D + i] == skill) return i; return -1; }
static int knows(int skill) { int b = book_at(skill); return b >= 0 && KNOWN(rec_of(0)) >> b & 1; }
static void set_known(int skill, int on) {
    int b = book_at(skill);
    if (b < 0) return;
    if (on) KNOWN(rec_of(0)) |= 1 << b; else KNOWN(rec_of(0)) &= ~(1 << b);
}
static const u8 level_steps[][3] = {{14, 75, 125}, {15, 100, 150}, {255, 0, 0}};   /* Buu's Fury's level-up script: a move's Level 2 and 3 by Goku's level */
static int derived_level(int skill) {
    int lv = GetLevel(rec_of(0)), i;
    if (tier_of(skill) >= 0) return mastery_level(0, skill);
    for (i = 0; level_steps[i][0] != 255; i++)
        if (level_steps[i][0] == skill) return (lv >= level_steps[i][2]) + (lv >= level_steps[i][1]);
    return 0;
}
static void equip(u8 *rec, int at, int skill) {     /* put a skill in slot `at` (at == count: a new slot) with its level */
    int lv = derived_level(skill);
    rec[0x0D + at] = skill; rec[0x2E + 2 * at] = lv; rec[0x2F + 2 * at] = lv;
    if (at == rec[0x0C]) rec[0x0C]++;
}
static int earned(int skill) {
    if (skill == KAIOKEN_SKILL || skill == KAME_SKILL) return QFLAG(37);      /* King Kai teaches both, after Gregory */
    if (skill == SS_SKILL) return QFLAG(67);               /* against Frieza */
    if (skill == IT_SKILL) return YARDRAT_FLAG && FLAG(YARDRAT_FLAG);
    if (skill == SPIRIT_SKILL) return FLAG(SPIRIT_FLAG);                          /* King Kai's secret, after the ending: reach his planet by Instant Transmission */
    if (skill == SOLAR_SKILL) return QFLAG(71);                                   /* the Village wise man's reward, after the ending */
    return 1;
}
static void learn(int skill) {
    u8 *rec = rec_of(0);
    if (slot_of(rec, skill) >= 0) { set_known(skill, 1); return; }
    if (knows(skill)) return;
    set_known(skill, 1);
    if (rec[0x0C] < MAX_HELD) equip(rec, rec[0x0C], skill);
}
void skills_sync(void) {
    u8 *rec = rec_of(0);
    int i, s;
    for (i = rec[0x0C] - 1; i >= 0; i--) {
        s = rec[0x0D + i];
        if (!earned(s)) { set_known(s, 0); RemoveSkill(rec, s); continue; }
        set_known(s, 1);
        if (tier_of(s) >= 0) rec[0x2E + 2 * i] = rec[0x2F + 2 * i] = mastery_level(0, s);
    }
    if (rec[0x15] >= rec[0x0C]) rec[0x15] = 0;
    for (i = 0; i < 8 && skill_book[i] != 255; i++) {
        s = skill_book[i];
        if (earned(s)) learn(s); else set_known(s, 0);
    }
}
static int can_swap(void) {
    u8 *rec = rec_of(0);
    int b;
    for (b = 0; b < 8 && skill_book[b] != 255; b++) if (KNOWN(rec) >> b & 1 && slot_of(rec, skill_book[b]) < 0) return 1;
    return 0;
}
static void skills_swap(int at) {      /* the chosen slot takes the next skill Goku knows but isn't holding */
    u8 *rec = rec_of(0);
    int i, b0, cur, n = 0;
    while (n < 8 && skill_book[n] != 255) n++;
    if (at < 0 || at >= rec[0x0C] || !n) return;
    cur = rec[0x0D + at]; b0 = book_at(cur);
    for (i = 1; i <= n; i++) {
        int b = ((b0 < 0 ? -1 : b0) + i + n) % n, s = skill_book[b];
        if (!(KNOWN(rec) >> b & 1) || slot_of(rec, s) >= 0) continue;
        set_known(cur, 1);
        equip(rec, at, s);
        return;
    }
}
/* The pause menu's Skills tab (vtable 0x0804B024): SELECT swaps (slot 10, keys); opening it learns what play has earned (slot 1, setup). */
#define SkillTab_Keys ((int (*)(u8 *))0x080175FD)
#define SkillTab_Setup ((int (*)(u8 *, int, int, int))0x080171A9)
int skilltab_keys(u8 *obj) {
    if ((KEYS_NEW & 0x4) && *(int *)(obj + 0x114) == 0) {
        skills_swap(*(int *)(obj + 0x120));
        PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
        *(int *)(obj + 0x118) = rec_of(0)[0x0C];
        *(int *)(obj + 0x110) = 0;
    }
    return SkillTab_Keys(obj);
}
int skilltab_setup(u8 *obj, int a, int b, int d) {
    int c = *(int *)(obj + 0x114), r;
    if (c == 0) { skills_sync(); *(int *)(obj + 0x118) = rec_of(0)[0x0C]; }
    r = SkillTab_Setup(obj, a, b, d);
    if (c == 0)                 /* the hint, beside Select and Cancel (the game's buttons have no SELECT icon) */
        AddWidget(obj, NewText(0, obj, 0x84, 0x90, can_swap() ? (const u16 *)L"SELECT: Swap" : (const u16 *)L"Nothing to swap", 5, 0, (void *)FONT));
    return r;
}

/* ---------- transformations ---------- */
static void power_down(u8 *record, void *sprite) { if (flags_of(record[0x14]) & 2) SS3_Use(record, sprite); else SS_Use(record, sprite); }
static void power_up(void *sprite, const void *vt) {
    u32 *state = Alloc(0x10);
    if (state) { *(u8 *)&state[1] = 4; state[0] = (u32)vt; }
    Sprite_SetFacing(sprite, 10);
    Sprite_SetBehaviour(sprite, state);
}
/* Kaioken powers up on its new figure: the old one's slot 10 is Super Saiyan's (gold hair). build_skills.py makes the red figure's. */
static void power_to(u8 *record, void *sprite, int form, const void *vt) {
    XFORM = form + 1; XFORM_FROM = record[0x14]; XFORM_AT = FRAMES;
    Sprite_SetCharacter(sprite, Form_Sprite(form_table + form * 24));
    EARLY = record[0x14] + 1;
    power_up(sprite, vt);
}
int xform_target(int up, u8 *record) {                          /* sub_0801C312's new form */
    int t = XFORM;
    XFORM = 0;
    if (t && record[0x14] == XFORM_FROM && (u16)(FRAMES - XFORM_AT) < 600) return t - 1;
    return up;
}
void xform_hook(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global xform_hook\nxform_hook:\n"
        "ldrb r0, [r7, #22]\nadds r1, r4, #0\nbl xform_target\nstrb r0, [r4, #20]\nlsls r3, r0, #1\nadds r0, r3, r0\nldr r3, =0x0801C365\nbx r3\n.ltorg\n");
static int can_step(u8 *record) { return IN_COMBAT && CanAfford(record, 10); }
static int can_start(u8 *record) { return can_step(record) && *(u32 *)(record + 4) == 0; }
int ss_can(u8 *record) { return is_kaioken(record[0x14]) ? 0 : SS_Can(record); }      /* no Super Saiyan in Kaioken */
void ss_use(u8 *record, void *sprite) { XFORM = 0; SS_Use(record, sprite); }
int kaioken_can(u8 *record) {
    int form = record[0x14];
    if (is_kaioken(form)) return 1;
    if (mapped(form) == 255) return 0;
    return !(flags_of(form) & 3) && can_start(record);                 /* from a base form only: never with Super Saiyan (the owner, Nov 9) */
}
static void kk_down(u8 *record, void *sprite) {       /* out of Kaioken: to its base, or from Super Saiyan Kaioken to Super Saiyan with its pool */
    if (flags_of(form_table[record[0x14] * 24 + 0x17]) & 1) KK_POOL = *(u16 *)(record + 0x1E) + 1;
    SS_Use(record, sprite);
}
void kaioken_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_kaioken(form)) kk_down(record, sprite);
    else power_to(record, sprite, mapped(form), kk_vt);
}
/* the power-up with its aura red (the game's start, 0x0801C3EC, with the aura's frames swapped) */
void kk_start(u32 *state, void *sprite) {
    int box[4], v[2], u[2], w[2], pos[2];
    u32 *spark;
    state[2] = 0;
    ((void (*)(void *, void *))0x0800DE61)(state, sprite);
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x288, 0x40, 0);
    state[3] = 0;
    if (AURA_MODE > 1) return;
    SpriteBox(box, sprite); VecOp(v, box, box + 2);
    u[0] = v[0] >> 1; u[1] = v[1] >> 1; w[0] = 0; w[1] = AURA_MODE ? 2 : 1;
    VecOp(pos, u, w);
    if (AURA_MODE) { ListAdd(ACTORS, NewSpark(0, pos, kk_aura_other, 7, 0xC88, 1024, 0x38)); return; }
    spark = Alloc(0x48);
    if (spark) { NewSpark((int)spark, pos, kk_aura_field, 3, 0x4000, 1024, 0x38); spark[0] = 0x0804B9E0; spark[0x44 / 4] = (u32)kk_aura_field; }
    state[3] = (u32)spark;
    ListAdd(ACTORS, spark);
}

/* Fully mastered Kaioken costs no health: a bar of its own, half Goku's health, drawn cyan over the health bar, pays the cost, takes the hits
   first and stops the stagger while it lasts. When it runs out the Kaioken ends. */
static void kk_pool_back(u8 *rec) {     /* the power-down empties the pool (retail goes to base): back in Super Saiyan, it has what it had */
    if (KK_POOL && !is_kaioken(rec[0x14]) && (flags_of(rec[0x14]) & 1)) { *(u16 *)(rec + 0x1E) = KK_POOL - 1; KK_POOL = 0; }
}
static void kk_begin(const u8 *rec) {
    if (KK_ON) return;
    KK_ON = 1; KK_EMPTY = 0; KK_GUARD = *(const short *)(rec + 0x18) / 2;
}
static void kk_track(void) {
    u8 *rec = rec_of(CUR), *me = PLAYER_OBJ;
    int form = rec[0x14], max = *(short *)(rec + 0x18), cols;
    if (EARLY) {                                   /* a power-up cut short leaves the new figure on the old form: put the old one back */
        u32 *state = me ? *(u32 **)(me + 0x14) : 0;
        if (!me || (u16)(FRAMES - XFORM_AT) >= 600) EARLY = 0;
        else if (!state || state[0] != (u32)kk_vt) {
            if (form == EARLY - 1) Sprite_SetCharacter(me, Form_Sprite(form_table + form * 24));
            EARLY = 0;
        }
    }
    if (!is_kaioken(form)) {
        kk_pool_back(rec);
        if (!(flags_of(form) & 1)) KK_POOL = 0;
        KK_ON = 0; KK_GUARD = 0; KK_EMPTY = 0; KK_DRAWN = 0; hud_widget = 0; return;
    }
    if (kk_mastered()) kk_begin(rec);
    if (KK_EMPTY == 1 && me) { KK_EMPTY = 2; kk_down(rec, me); }
    cols = max > 0 ? KK_GUARD * 41 / max : 0;
    if (cols != KK_DRAWN && hud_widget) *(u32 *)(hud_widget + 0x1C) = 0xFFFFFFFF;     /* the HUD redraws when its cached bar lengths differ */
}
/* Super Saiyan's drain (sub_0800E3E6) is about to take a unit from the pool (+0x1E): 1 skips the unit */
int ss_tick(u8 *rec) {
    if (rec != rec_of(CUR)) return 0;
    kk_pool_back(rec);
    if (is_kaioken(rec[0x14])) {
        short *hp = (short *)(rec + 0x16), cost = *(short *)(rec + 0x18) / 150;
        if (cost < 1) cost = 1;
        if (kk_mastered()) {
            kk_begin(rec);
            if (KK_GUARD > cost) KK_GUARD -= cost;
            else { KK_GUARD = 0; if (!KK_EMPTY) KK_EMPTY = 1; }
        }
        else if (*hp > cost + 1) *hp -= cost;
        else *(u16 *)(rec + 0x1E) = 0;
    }
    return mastery_train(rec, 10);
}
void ss_drain_hook(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global ss_drain_hook\nss_drain_hook:\n"
        "push {r0}\nbl ss_tick\nadds r3, r0, #0\npop {r0}\nadds r1, r0, #0\nadds r1, #30\nldrh r2, [r1]\n"
        "cmp r3, #0\nbne 1f\ncmp r2, #0\nldr r3, =0x0800E435\nbx r3\n1:\nldr r3, =0x0800E467\nbx r3\n.ltorg\n");
/* The HUD (0x0800B99C) has drawn its bars into buf; before it goes to VRAM, mastered Kaioken paints its bar over the health bar. */
#define HP_COLS ((const u32 *)0x08071CB0)
void skills_hud(const u8 *widget, u8 *buf) {
    const u8 *rec = rec_of(CUR);
    int max = *(const short *)(rec + 0x18), cols = 0, c, k;
    if (KK_ON && max > 0) {
        hud_widget = (u8 *)widget;
        cols = KK_GUARD * 41 / max;
        if (cols > 41) cols = 41;
        for (c = 0; c < cols; c++) for (k = 0; k < 3; k++) { u32 o = HP_COLS[c * 4 + k]; buf[o] = kk_bar[o]; }
    }
    KK_DRAWN = cols;
    MemCopy((u8 *)0x06010000 + *(const u16 *)(widget + 12) * 32, buf, 0x500);
}
/* Damage: hit[1] is the attack's scale (1024 = normal); hit[3] the attacker, whose stats are at +0x1B0; team 1 is the player's side. */
void combat_orig(void *defender, int *hit);
__asm__(".syntax unified\n.thumb\n.thumb_func\ncombat_orig:\npush {r4, r5, r6, r7, lr}\nadds r6, r0, #0\nadds r4, r1, #0\nadds r1, #8\nldr r3, =0x0800E9E1\nbx r3\n.ltorg\n");
void combat_hook(void *defender, int *hit) {
    int scale = hit[1], form = rec_of(CUR)[0x14];
    u16 *stats = hit[3] ? (u16 *)((u8 *)hit[3] + 0x1B0) : 0, strength = stats ? stats[0] : 0, power = stats ? stats[1] : 0;
    int mine = hit[3] && *((u8 *)hit[3] + 0x1D0) == 1;
    if (mine && is_kaioken(form)) {
        /* 1.25x, 1.5x, 1.75x by mastery, from Goku's own stats: the row is Super Saiyan's class, which adds 5 to Strength and Power (taken off
           again). Super Saiyan Kaioken, down to Super Saiyan, keeps Super Saiyan's +5. */
        hit[1] = scale + (scale >> 2) * (1 + mastery_level(CUR, KAIOKEN_SKILL));
        if (!(flags_of(form_table[form * 24 + 0x17]) & 1) && strength > 5 && power > 5) { stats[0] = strength - 5; stats[1] = power - 5; }
    }
    combat_orig(defender, hit);
    if (defender == PLAYER_OBJ && KK_ON && KK_GUARD && is_kaioken(form) && hit[6] > 0) {     /* hit[6]: the damage (1/1024ths) */
        int dmg = (hit[6] + 0x3FF) >> 10;
        if (dmg < KK_GUARD) { KK_GUARD -= dmg; hit[6] = 0; }
        else { hit[6] -= KK_GUARD << 10; KK_GUARD = 0; if (!KK_EMPTY) KK_EMPTY = 1; }
    }
    hit[1] = scale;
    if (stats) { stats[0] = strength; stats[1] = power; }
}
/* Instant Transmission (Yardrat, post-game). Near an enemy it is Buu's Fury's own move; anywhere else it costs nothing and opens src/flight.c's
   picker of the places Goku has been. */
#define IT_Can ((int (*)(u8 *))0x0801A217)
#define IT_Use ((void (*)(u8 *, void *))0x0801A23B)
#define IT_PENDING (*(volatile u8 *)0x03005F93)
static int foe_near(void) {
    const u32 *l = (const u32 *)0x03001BB0; u8 *me = PLAYER_OBJ;
    int i, n = l[0], px, py;
    if (!me) return 0;
    px = *(int *)(me + 0x1A0) >> 8; py = *(int *)(me + 0x1A4) >> 8;
    for (i = 0; i < n && i < 32; i++) {
        const u8 *e = (const u8 *)l[1 + i]; int dx, dy;
        if (!e) continue;
        dx = (*(const int *)(e + 0x1A0) >> 8) - px; dy = (*(const int *)(e + 0x1A4) >> 8) - py;
        if (dx > -160 && dx < 160 && dy > -120 && dy < 120) return 1;
    }
    return 0;
}
int it_can(u8 *record) { return foe_near() ? IT_Can(record) : 1; }
void it_use(u8 *record, void *sprite) { if (foe_near()) IT_Use(record, sprite); else IT_PENDING = 1; }

/* The player's keys (vtable 0x0804C9F0 +0x84), every frame: Kaioken's bar, the book now and then, and the quick wheel: hold L and press a
   direction to pick a skill at once (up the 1st, right the 2nd, down the 3rd, left the 4th). Not while flying, where L takes off to the world map
   (src/flight.c), nor on that map (Buu's Fury's 0:50). */
#define FLYING (*(volatile u8 *)0x03006105)
/* The Dragon Ball hunt (tools/log1_dragonballs.py) asks for these by flag, since a scene list can't change a record or the inventory itself. */
#define SETF(f) (FLAGS[(f) >> 3] |= 1 << ((f) & 7))
#define CLRF(f) (FLAGS[(f) >> 3] &= ~(1 << ((f) & 7)))
static void dragon_balls(void) {
    int i, out = FLAG(DB_ROUND) ? DB_BALL_B : DB_BALL, away = out == DB_BALL ? DB_BALL_B : DB_BALL;
    u8 *r;
    for (i = 0; i < 7; i++) {
        SETF(away + i);                                                         /* the set that isn't out never shows */
        if (!FLAG(DB_RADAR)) SETF(out + i);                                     /* and with no radar yet, neither does the other */
    }
    if (FLAG(DB_SCATTER)) {                                                     /* after a wish: the balls fly apart, to the other set's spots */
        CLRF(DB_SCATTER);
        if (FLAG(DB_ROUND)) CLRF(DB_ROUND); else SETF(DB_ROUND);
        for (i = 0; i < 7; i++) { CLRF(away + i); SETF(out + i); *(u8 *)(0x0300106A + 16 + i) = 0; }
    }
    if (FLAG(DB_POWER)) {                                                       /* "Make me stronger": +5 strength, power and endurance */
        CLRF(DB_POWER); r = rec_of(CUR);
        for (i = 0; i < 3; i++) r[0x28 + i] = r[0x28 + i] > 250 ? 255 : r[0x28 + i] + 5;
    }
    if (FLAG(DB_MASTERY)) { CLRF(DB_MASTERY); MASTERY[0] = MASTERY[1] = MASTERY_L3; }  /* Kaioken and Super Saiyan at Level 3 */
}

void bosses_tick(void);
/* Bardock's vision (tools/log1_bardock.py): on Planet Vegeta (area 70) Goku is Bardock, a form of his own record; anywhere else he is himself again. */
static void bardock_tick(void) {
    u8 *rec = rec_of(0), *me = PLAYER_OBJ;
    int in = AREA && *(u8 *)AREA == 26 && *(u8 *)(AREA + 1) == BARDOCK_MAP;
    if (CUR != 0 || !me) return;
    if (in && rec[0x14] != BARDOCK_FORM) { rec[0x14] = BARDOCK_FORM; Sprite_SetCharacter(me, Form_Sprite(form_table + BARDOCK_FORM * 24)); }
    else if (!in && rec[0x14] == BARDOCK_FORM) { rec[0x14] = 0; Sprite_SetCharacter(me, Form_Sprite(form_table)); }
}
u16 *player_input(void) {
    u16 *keys = ((u16 *(*)(void))0x0804F8C9)();
    u8 *rec = rec_of(CUR);
    static const u8 pick[4] = {1, 3, 0, 2};
    int d, i;
    kk_track();
    if (CUR == 4) FLAGS[AS_VEGETA >> 3] |= 1 << (AS_VEGETA & 7); else FLAGS[AS_VEGETA >> 3] &= ~(1 << (AS_VEGETA & 7));     /* the gravity room's holograms are for Vegeta */
    dragon_balls();
    rec_of(0)[0] |= 1;      /* Goku is in the party: the pause menu lists party members (record +0 bit 0) and, with none, reads a stale entry and crashes */
    if (CUR == 0 && (FRAMES & 63) == 0) skills_sync();
    bardock_tick();
    bosses_tick();                                     /* the movie villains' attacks (src/bosses.c) */
    if (!(keys[1] & 0x200) || FLYING || (AREA && *(u16 *)AREA == (0 | 50 << 8))) return keys;
    d = keys[2] & 0xF0;
    if (d) {
        for (i = 0; i < 4; i++) if (d & (0x10 << i)) break;
        if (pick[i] < rec[0x0C] && rec[0x15] != pick[i]) { rec[0x15] = pick[i]; PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0); }
    }
    for (i = 0; i < 6; i++) wheel_keys[i] = keys[i];
    wheel_keys[1] &= ~0xF0; wheel_keys[2] &= ~0xF0;
    return (u16 *)wheel_keys;
}

/* ---------- the Spirit Bomb and the Solar Flare (Buu's Fury Ultimate's, ported) ----------
   Spirit Bomb (King Kai, quest 37; Buu's Fury's unused skill row 19): Goku holds his arms up while the orb grows over his head, then it flies the
   way he faces and bursts, hitting everything nearby hard. It runs from an effect slot (EFFECTS[3]), which the game updates every frame; the
   movement states call spirit_tick so Goku holds his pose. The orb is Buu's Fury's own Spirit Bomb, the glowing disc of its ending (the owner,
   Nov 9: "use the actual spirit bomb sprites", not BFU's drawn orb).
   Solar Flare (the Village wise man, quest 71, after the ending): a white flash while Goku holds a pose; every ordinary enemy on screen is stunned
   (the game's own dizzy state, its timer set longer). Bosses aren't fooled. */
#define Spend ((void (*)(void *, int))0x08013599)
#define NativeDisc ((void (*)(int *))0x08003B95)
#define NativeAlpha ((void (*)(int *))0x08000959)
#define NativeFlash ((void (*)(int *))0x08001305)
#define SetEffect ((void (*)(void *, int, void *))0x0800927F)
#define EFFECTS (*(u32 **)(*(u32 *)0x08003C44 + 0x10))
#define ALPHA_MIRROR (*(u8 **)0x08009900)
#define RectAt ((void (*)(void *, const void *, int *))0x08052FD5)
#define HitObjects ((int (*)(void *, int, void *))0x08011C0D)
#define Quake ((void (*)(int, int))0x0800797D)
#define CALL_V(obj, off) ((u32 (*)(void *, ...))(*(u32 *)(obj) + *(int *)(*(u32 *)(obj) + (off))))
#define BLDCNT (*(volatile u16 *)0x04000050)
#define BLDY (*(volatile u16 *)0x04000054)
#define BOMB_INDEX 255
#define BOMB_PAL ((volatile u16 *)0x05000000)[BOMB_INDEX]
struct spirit { u16 frame; u16 phase; int x, y, r; void *old, *old3; u32 ticker[2]; u8 eva, evb; u16 backdrop; u8 dir, speed; u16 travelled; u8 disc; };
#define SB (*(struct spirit *)0x03005FA0)              /* 44 bytes */
#define BOMB_OLD (*(volatile u16 *)0x03005FE4)
#define SOLAR_POSE (*(volatile u8 *)0x03005FE6)
#define SOLAR_AT (*(volatile u32 *)0x03005FE8)
#define GROW_FRAMES 90
#define WINDUP_FRAMES 10
#define THROW_HOLD 22
#define THROW_DISTANCE 130
#define THROW_SIDE 100
#define THROW_UP 60
#define BURST_FRAMES 24
#define SPIRIT_POWER 0x8000
#define FLASH_PHASE 11
static const int BURST_RECT[4] = {-100, -80, 200, 160};
static const u8 flash_levels[46] = {6, 12, 16, 16, 16, 16, 10, 4, 0, 8, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 15, 14, 14, 13, 12, 12, 11, 10, 10, 9, 8, 8, 7, 6, 6, 5, 4, 4, 3, 2, 2, 1, 0};
__attribute__((section(".text.fixed"))) const int spirit_vt[6] = {1};

static int has_slot(void *player, int slot) {
    u8 *actor = (u8 *)*(u32 *)((u8 *)player + 0x58);
    return (*(u32 *)actor & 0xFF) > (u32)slot && *(u32 *)(actor + 0x54 + slot * 4) != 0;
}
static void play_slot(void *player, int slot) {
    Sprite_SetFacing(player, slot);
    *(u32 *)((u8 *)player + 0x4C) = 0; *((u8 *)player + 0x11) = 0; *(u16 *)((u8 *)player + 0x12) = 0;
}
#define SLOT_ARMS_UP 12
#define SLOT_THROW 18
static void slot_pose(void *player, int slot) {
    u8 *actor = (u8 *)*(u32 *)((u8 *)player + 0x58);
    if (!has_slot(player, slot)) return;
    if (*(u32 *)((u8 *)player + 0x50) == *(u32 *)(actor + 0x54 + slot * 4)) return;
    play_slot(player, slot);
}
static int spirit_cost(u8 *rec) { int c = *(u16 *)(rec + 0x1C) / 2; return c < 30 ? 30 : c; }
int spirit_usable(u8 *rec) { return IN_COMBAT && !SB.phase && !SOLAR_POSE && CanAfford(rec, spirit_cost(rec)); }

static void spirit_draw(void) {
    if (!SB.disc) {
        int st[3] = {2, 100, 15};
        SB.disc = 1; SB.old = (void *)EFFECTS[0]; EFFECTS[0] = 0;
        SB.eva = ALPHA_MIRROR[2]; SB.evb = ALPHA_MIRROR[3]; SB.backdrop = BOMB_PAL;
        NativeAlpha(st);
    }
    {
        int st[5] = {4, SB.x, SB.y, SB.r, BOMB_INDEX};
        NativeDisc(st); BOMB_PAL = 0x7F80;
    }
}
static void impact(int step) {
    if (step == 0) BOMB_OLD = BLDCNT;
    if (step < 3 || (step >= 6 && step < 9)) { BLDCNT = 0x00BF; BLDY = 16; }
    else if (step < 6) { BLDCNT = 0x00FF; BLDY = 16; }
    else { BLDCNT = BOMB_OLD; BLDY = 0; }
}
static void spirit_end(void) {
    if (SB.disc) { SetEffect(EFFECTS, 0, SB.old); ALPHA_MIRROR[2] = SB.eva; ALPHA_MIRROR[3] = SB.evb; SB.disc = 2; }
    SB.phase = 4; SB.frame = 0;
}
static void spirit_done(void) {
    if (SB.disc == 2) BOMB_PAL = SB.backdrop;
    SB.disc = 0; SB.phase = 0; EFFECTS[3] = (u32)SB.old3;
    { int st[6] = {5, 5, 200, 200, 255, 10}; NativeFlash(st); }
}
static void spirit_start_ticker(void) { SB.old3 = (void *)EFFECTS[3]; SB.ticker[0] = (u32)spirit_vt; EFFECTS[3] = (u32)SB.ticker; }
void spirit_use(u8 *rec, void *player) {
    int *p = (int *)player;
    Spend(rec, spirit_cost(rec));
    SB.disc = 0; SB.x = p[0x68] >> 8; SB.y = (p[0x69] >> 8) - 58; SB.r = 4; SB.frame = 0; SB.phase = 1;
    spirit_start_ticker();
    PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
    spirit_draw();
}
static void spirit_burst(void *player) {
    u32 hit[16]; int pos[2], i;
    for (i = 0; i < 16; i++) hit[i] = 0;
    pos[0] = SB.x; pos[1] = SB.y;
    *(u8 *)&hit[0] = 1; RectAt(&hit[1], BURST_RECT, pos); *(u8 *)&hit[5] = *((u8 *)player + 0x10);
    hit[6] = SPIRIT_POWER; hit[7] = 0x086B8098; hit[8] = (u32)player; hit[12] = (u32)player;
    HitObjects(ACTORS, 0, hit);
    Quake(0x20, 0x4B);
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 12, 0x40, 0);
}
void spirit_nop(void) {}
void spirit_update(void) {
    void *player = PLAYER_OBJ;
    SB.frame++;
    if (!player) return;
    if (SB.phase == 1) {
        if (SB.r < 48 && SB.frame % 2 == 0) SB.r++;
        spirit_draw();
        if (SB.frame >= GROW_FRAMES) { SB.phase = 2; SB.frame = 0; SB.dir = *((u8 *)player + 0x10); SB.speed = 0; SB.travelled = 0; }
    } else if (SB.phase == 2) {
        if (SB.frame <= WINDUP_FRAMES) SB.y -= 1;
        else {
            if (SB.speed < 7 && SB.frame % 3 == 0) SB.speed++;
            if (SB.dir == 0) SB.y += SB.speed; else if (SB.dir == 1) SB.y -= SB.speed; else if (SB.dir == 2) SB.x -= SB.speed; else SB.x += SB.speed;
            SB.travelled += SB.speed;
        }
        spirit_draw();
        if (SB.travelled >= (SB.dir == 1 ? THROW_UP : SB.dir == 0 ? THROW_DISTANCE : THROW_SIDE)) { spirit_burst(player); SB.phase = 3; SB.frame = 0; }
    } else if (SB.phase == 3) {
        if (SB.frame > BURST_FRAMES - 10) SB.r -= 8; else if (SB.r < 96) SB.r += 4;
        spirit_draw();
        if (SB.frame <= 10) impact(SB.frame - 1);
        if (SB.frame % 6 == 0) spirit_burst(player);
        if (SB.frame >= BURST_FRAMES) spirit_end();
    } else if (SB.phase == 4) {
        if (SB.frame >= 2) spirit_done();
    } else if (SB.phase == FLASH_PHASE) {
        if (SB.frame > (int)sizeof flash_levels) { BLDCNT = BOMB_OLD; BLDY = 0; SB.phase = 0; EFFECTS[3] = (u32)SB.old3; }
        else { BLDCNT = 0x00BF; BLDY = flash_levels[SB.frame - 1]; }
    }
}
void spirit_destroyed(void) {           /* a new area clears every effect, this one included */
    if (SB.phase == FLASH_PHASE) { BLDCNT = BOMB_OLD; BLDY = 0; }
    SB.phase = 0; SB.disc = 0;
}
/* Solar Flare */
#define SOLAR_COST 40
#define SOLAR_STUN 150
#define SOLAR_POSE_FRAMES 30
#define SOLAR_REST 360
#define ENEMY_COUNT (*(volatile int *)0x03001BB0)
#define ENEMY_LIST ((u8 **)0x03001BB4)
#define VIEW ((volatile int *)0x030019BC)
#define STUN_DESC 0x0870F51C
static int stunned(u8 *e) {
    int depth = *(int *)(e + 0x23C);
    return depth >= 1 && depth <= 5 && *(u32 *)(e + 0x240 + 8 * (depth - 1) + 4) == STUN_DESC;
}
static void stun(u8 *e, int frames) {
    int depth; u32 *top, *timer;
    if (!stunned(e)) {
        depth = *(int *)(e + 0x23C);
        if (depth < 1 || depth >= 5) return;
        CALL_V(e, 0x6C)(e, 1);
        if (!stunned(e)) return;
    }
    depth = *(int *)(e + 0x23C);
    top = *(u32 **)(e + 0x240 + 8 * (depth - 1));
    if (!top || top[2] < 2) return;
    timer = (u32 *)top[4];
    if (timer && timer[1] < (u32)frames) timer[1] = frames;
}
static int boss(u8 *e) { const u8 *row = *(const u8 **)(e + 0x224); return !row || *(const u32 *)(row + 0x14) != 0x08708920; }
int solar_can(u8 *record) { return IN_COMBAT && !SB.phase && !SOLAR_POSE && (!SOLAR_AT || FRAMES - SOLAR_AT >= SOLAR_REST) && CanAfford(record, SOLAR_COST); }
void solar_use(u8 *record, void *player) {
    int i, n = ENEMY_COUNT, x, y;
    (void)player;
    Spend(record, SOLAR_COST);
    SOLAR_AT = FRAMES; SB.phase = FLASH_PHASE; SB.frame = 0; BOMB_OLD = BLDCNT;
    spirit_start_ticker();
    SOLAR_POSE = SOLAR_POSE_FRAMES;
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x288, 0x40, 0);
    if (n > 32) n = 32;
    for (i = 0; i < n; i++) {
        u8 *e = ENEMY_LIST[i];
        if (!e || *(int *)(e + 0x28C) <= 0 || !*(u8 *)(e + 0x1CC) || *(u8 *)(e + 0x1D0) != 0 || boss(e)) continue;
        x = *(int *)(e + 0x1A0) >> 8; y = *(int *)(e + 0x1A4) >> 8;
        if (x < VIEW[0] - 16 || x > VIEW[2] + 16 || y < VIEW[1] - 16 || y > VIEW[3] + 32) continue;
        stun(e, SOLAR_STUN);
    }
}
static int solar_tick(void *player) {
    if (!SOLAR_POSE) return 0;
    if (--SOLAR_POSE == 0) { slot_pose(player, 0); return 0; }
    if (has_slot(player, 13)) slot_pose(player, 13); else slot_pose(player, SLOT_ARMS_UP);
    return 1;
}
/* the movement states (each vtable +8): while the bomb is raised or the flare held, Goku keeps his pose and doesn't move */
static int spirit_tick(void *player) {
    if (solar_tick(player)) return 1;
    if (SB.phase == 1) { slot_pose(player, SLOT_ARMS_UP); return 1; }
    if (SB.phase == 2) {
        if (SB.frame <= WINDUP_FRAMES) { slot_pose(player, SLOT_ARMS_UP); return 1; }
        if (SB.frame <= WINDUP_FRAMES + THROW_HOLD) { slot_pose(player, SLOT_THROW); return 1; }
        if (SB.frame == WINDUP_FRAMES + THROW_HOLD + 1) slot_pose(player, 0);
    }
    return 0;
}
typedef void (*state_fn)(void *, void *, int, int);
#define WRAP(name, addr) void name(void *s, void *p, int a, int b) { if (spirit_tick(p)) return; ((state_fn)(addr))(s, p, a, b); }
WRAP(state_a, 0x08012D8B)
WRAP(state_b, 0x08012DEF)
WRAP(state_c, 0x08013023)
WRAP(state_d, 0x080131BB)

/* ---------- post-game allies (tools/log1_party.py) ---------- */
/* Script native party_join(character, form), BFU's party_join: the first time someone joins, they start level with whoever is playing (EXP, max HP
   and EP, and stats leaning their own way), with their own moves. Later calls change nothing. */
__attribute__((section(".text.table"))) volatile const u8 party_skills[8][8] = {{0}};      /* per character: count, then moves */
__attribute__((section(".text.table"))) volatile const u8 party_lean[8][3] = {{0}};        /* strength, power, endurance, in % of the player's */
#define R16(r, o) (*(u16 *)((r) + (o)))
#define EXP(r) (*(u32 *)((r) + 0x24))
static int scaled(int v, int pct) { v = v * pct / 100; return v > 255 ? 255 : v; }
void party_join(int *sp) {
    int n = *sp, form = sp[n], c = sp[n - 1], i, v;
    u8 *r = rec_of(c), *cur = rec_of(CUR);
    *sp = n - 2;
    if (c < 1 || c > 7 || (r[0] & 1)) return;
    r[0] |= 1;
    r[0x14] = form;
    if (EXP(cur) > EXP(r)) EXP(r) = EXP(cur);
    if (R16(cur, 0x18) > R16(r, 0x18)) R16(r, 0x18) = R16(cur, 0x18);
    if (R16(cur, 0x1C) > R16(r, 0x1C)) R16(r, 0x1C) = R16(cur, 0x1C);
    R16(r, 0x16) = R16(r, 0x18); R16(r, 0x1A) = R16(r, 0x1C);
    for (i = 0; i < 3; i++) { v = scaled(cur[0x28 + i], party_lean[c][i]); if (v > r[0x28 + i]) r[0x28 + i] = v; }
    if (cur[0x2B] > r[0x2B]) r[0x2B] = cur[0x2B];
    r[0x0C] = party_skills[c][0];
    for (i = 0; i < party_skills[c][0]; i++) { r[0x0D + i] = party_skills[c][1 + i]; r[0x2E + 2 * i] = r[0x2F + 2 * i] = 0; }
    r[0x15] = 0;
}

/* Galick Gun and Special Beam Cannon: the Kamehameha's code with their own frames (BFU's beam_start). Its start makes the charging ball from its
   parameter table, so this runs it, then points the ball at the same entry of the move's own table. */
#define Kamehameha_Start ((void (*)(u32 *, void *))0x0801BDD5)
__attribute__((section(".text.table"))) volatile const u32 galick_params[12] = {1}, sbc_params[12] = {1};
__attribute__((section(".text.fixed"))) const int galick_vt[9] = {1}, sbc_vt[9] = {1};
static void beam_start(u32 *self, void *player, const volatile u32 *params) {
    u32 *beam;
    Kamehameha_Start(self, player);
    beam = (u32 *)self[2];
    if (beam) {                                /* the charging ball's frames, and its first frame already copied to VRAM */
        const volatile u32 *mine = &params[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
static void beam_use(u8 *record, void *sprite, const int *vt) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}
void galick_start(u32 *self, void *player) { beam_start(self, player, galick_params); }
void sbc_start(u32 *self, void *player) { beam_start(self, player, sbc_params); }
void galick_use(u8 *record, void *sprite) { beam_use(record, sprite, galick_vt); }
void sbc_use(u8 *record, void *sprite) { beam_use(record, sprite, sbc_vt); }

/* Destructo Disc: Big Bang's code with its own frames and strength (BFU's Eraser Cannon). Big Bang's start makes the ball from its parameter table,
   so this runs it, then points the ball at the same entry of the move's table (the last word of an entry scales the damage). */
#define BigBang_Start ((void (*)(u32 *, void *))0x0801A7C1)
__attribute__((section(".text.table"))) volatile const u32 disc_params[12] = {1};
__attribute__((section(".text.fixed"))) const int disc_vt[9] = {1};
void disc_start(u32 *self, void *player) {
    u32 *ball;
    BigBang_Start(self, player);
    ball = (u32 *)self[1];
    if (ball) {
        const volatile u32 *mine = &disc_params[self[2] * 4];
        u32 *old = (u32 *)ball[0x4C / 4];
        int shift = (int)mine[2] - (int)old[2];
        ball[0x4C / 4] = (u32)mine;
        ball[0x50 / 4] += shift;
        ball[0x18 / 4] += shift;
    }
}
void disc_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x14);
    if (b) { b[0] = (u32)disc_vt; b[2] = level; b[3] = 0; b[4] = 0; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}

/* Scatter Shot (Piccolo, from LoG2): Energy Blast's behaviour with its own update. Where the Energy Blast fires one shot, this fires five, fanned
   out across 60 degrees in front of him; each shot is Buu's Fury's own Energy Blast projectile (sub_080197B4), its velocity (+0x40, +0x44) turned. */
#define SpawnPoint ((void (*)(int *, void *))0x0800FF45)
#define NewShot ((u8 *(*)(void *, int *, void *, int))0x080197B5)
__attribute__((section(".text.fixed"))) const int scatter_vt[9] = {1};
static const short spread[5][3] = {{222, -128, -2}, {247, -66, -1}, {256, 0, 0}, {247, 66, 1}, {222, 128, 2}};    /* cos, sin (x256), side step: -30..30 degrees */

void scatter_update(u8 *self, u8 *player) {
    u16 t = ++*(u16 *)(player + 0x12);
    int pos[2], at[2], i, vx, vy, px, py;
    u8 *s;
    if (t == 0x10) {
        player[0x11] = 1;
        SpawnPoint(pos, player);
        for (i = 0; i < 5; i++) {
            s = NewShot(0, pos, player, 1);
            if (!s) break;
            vx = *(int *)(s + 0x40); vy = *(int *)(s + 0x44);
            px = -vy / 32; py = vx / 32;                                 /* 24 px across the facing (speed 768 = 3 px a frame): closer shots clash and stop */
            at[0] = pos[0] + px * spread[i][2] + vx / 48; at[1] = pos[1] + py * spread[i][2] + vy / 48;     /* and 16 px ahead: only the newest shot ignores its owner, so the rest start clear of him */
            *(int *)(s + 0x20) = at[0] << 8; *(int *)(s + 0x24) = at[1] << 8;
            *(int *)(s + 0x40) = (vx * spread[i][0] - vy * spread[i][1]) >> 8;
            *(int *)(s + 0x44) = (vx * spread[i][1] + vy * spread[i][0]) >> 8;
            ListAdd(ACTORS, s);
        }
    }
    else if (t >= 0x28) {
        int *vt = *(int **)player;
        ((void (*)(void *, int))((u8 *)vt + vt[0x28 / 4]))(player, 0);
    }
}
void scatter_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b;
    Spend(record, *(short *)(record + 0x1C) * 3 / 20 + 1);        /* 15% of max EP: three Energy Blasts' worth for five shots */
    b = Alloc(0xC);
    if (b) { b[0] = (u32)scatter_vt; *(u8 *)(b + 1) = 0; b[2] = level; }
    Sprite_SetFacing(sprite, 3);
    Sprite_SetBehaviour(sprite, b);
}
