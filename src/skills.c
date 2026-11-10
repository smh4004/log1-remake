/* Goku's skills, ported from Buu's Fury Ultimate (ultimate/src/outfit.c): the Kaioken, transformation mastery and the skill book with SELECT swapping.
 *
 * Lore gates (the owner, Nov 9): Goku starts with the Energy Blast only. King Kai teaches the Kamehameha and the Kaioken after Gregory (quest 37), he
 * becomes a Super Saiyan against Frieza (quest 67), and Instant Transmission waits for Yardrat (YARDRAT_FLAG, not reachable yet). A held skill
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
/* The player's keys (vtable 0x0804C9F0 +0x84), every frame: Kaioken's bar, the book now and then, and the quick wheel: hold L and press a
   direction to pick a skill at once (up the 1st, right the 2nd, down the 3rd, left the 4th). Not while flying, where L takes off to the world map
   (src/flight.c), nor on that map (Buu's Fury's 0:50). */
#define FLYING (*(volatile u8 *)0x03006105)
u16 *player_input(void) {
    u16 *keys = ((u16 *(*)(void))0x0804F8C9)();
    u8 *rec = rec_of(CUR);
    static const u8 pick[4] = {1, 3, 0, 2};
    int d, i;
    kk_track();
    if (CUR == 0 && (FRAMES & 63) == 0) skills_sync();
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
