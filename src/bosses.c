/* The movie villains' own ki attacks (tools/log1_movies.py, tools/log1_bossfx.py): enemy-only moves, not player skills.
 *
 * bosses_tick() runs every frame from player_input. It looks for a villain among the live enemies (by actor record, boss_table) and, every so
 * often while Goku is in range, runs one of his attacks: it turns him to Goku, holds him in place and spawns projectiles.
 *
 * A projectile is one of Buu's Fury's effect sparks (NewSpark, the object its auras and impacts use) with a vtable of its own: its update moves
 * it, loops or holds its frames, follows or circles its owner while charging, and on touching Goku hits him through Buu's Fury's own HitObjects
 * (the Spirit Bomb's burst, aimed at the player's side) and leaves an impact spark. Frames are original art drawn by tools/log1_bossfx.py.
 *
 * The Great Ape and giant Slug stand twice Goku's height: their actors' own frames are hidden (tools/log1_actors.py) and src/flight.c's 32x64
 * sprite (BIG_OBJ, as for the story's Great Ape) draws them, walking, casting or staggering, from boss_table's poses.
 *
 * Giant Slug's third attack brings Gohan's whistle: WHISTLE_FLAG runs its scene (src/flight.c's later lists) and Slug staggers for a while.
 *
 * RAM: 0x03005F6C-0x03005F7F (flight.c's hook RAM, free between BIG_SHOWN and the Kaioken's block) and 0x03005FEC-0x03005FF7. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef signed char s8; typedef short s16;

#define PLAYER_OBJ (*(u8 **)0x03001C34)
#define FRAMES (*(volatile u32 *)0x03000F94)
#define ENEMIES ((const u32 *)0x03001BB0)
#define ACTORS ((void *)0x03001C4C)
#define SPARKS (*(void **)0x087504CC)                 /* the list a spark removes itself from */
#define Alloc ((u32 *(*)(int))0x0803D5B9)
#define NewSpark ((void *(*)(void *, int *, const void *, int, int, int, int))0x0802A81D)
#define SparkUpdate ((void (*)(void *))0x0802A8AB)
#define ListAdd ((void (*)(void *, void *))0x0801191B)
#define ListRemove ((void (*)(void *, void *))0x08011945)
#define HitObjects ((int (*)(void *, int, void *))0x08011C0D)
#define RectAt ((void (*)(void *, const void *, int *))0x08052FD5)
#define PlaySound ((void (*)(void *, void *, int, int))0x0803E379)
#define Quake ((void (*)(int, int))0x0800797D)
#define SOUND_MOVE 0x0831947C
#define SOUND_HIT 0x083192A8

/* filled by tools/build_skills.py from tools/log1_bossfx.py:
   boss_parts[k] = {frames, count, directions, bytes}: frames are 12-byte spark frames (s8 ox, oy; u8 w, h; u16 attr0, attr1; pixels), a
   directional part has count frames for each of down, up, left, right in turn.
   boss_table = {actor record, moveset, big figure or 0} rows, ending in 0. A big figure is three poses (walking, walking, casting), each 32x64
   8bpp for down, up, left and right (2 KB each). TALL (1) in its place: a boss drawn tall by his own frames (a boss-class actor's 64x64
   pieces: Cooler's final form), his shots starting as high as a big figure's. */
#define TALL ((const u8 *)1)
typedef struct { const u8 *frames; u8 count, dirs; u16 bytes; } part_t;
typedef struct { u32 record; u32 moveset; const u8 *big; } boss_t;
__attribute__((section(".text.table"))) volatile const part_t boss_parts[24] = {{0}};
__attribute__((section(".text.table"))) volatile const boss_t boss_table[12] = {{1}};
__attribute__((section(".text.fixed"))) const int proj_vt[16] = {1};
enum { P_EYE, P_SLUG_EYE, P_FLASH, P_FINGER, P_NOVA, P_NOVA_BURST, P_RING, P_CAL_CHARGE, P_CAL_WAVE, P_METEOR, P_TWIN, P_SMASHER,
       P_KI_BURST, P_VIOLET_BURST, P_NOVA_SPIN, P_SMASH_SPIN, P_MOUTH, P_SHOCK };
#define BUDGET 3072                                   /* OBJ tile bytes all live projectiles may hold */
/* Never let a spark's tile allocation fail: when it does, Buu's Fury collects sprite memory by destroying or evicting actors in the middle of
   the actor update (Goku's and the HUD's tiles included), which garbles them or crashes the next update. So nothing spawns unless the largest
   free block (0x080116FC) leaves room to spare. */
#define VramFree ((int (*)(void *))0x080116FD)
#define SPARE 1024
static int room(int bytes) { return VramFree(ACTORS) >= bytes + SPARE && ((u32 *)ACTORS)[1] < 120; }

/* the villain now fighting */
struct boss { u8 *obj; s16 pinx, piny; u16 t, cool; u8 atk, step, n, mset; s16 aux; u16 spare; };
#define BS (*(struct boss *)0x03005F6C)               /* 20 bytes */
struct boss2 { const u8 *big; u8 *shown; u16 stun; u8 tall; u8 pose; s16 lastx, lasty; };
#define B2 (*(struct boss2 *)0x03005FEC)              /* 16 bytes */
#define BIG_OBJ (*(volatile u32 *)0x03005F60)          /* src/flight.c's 32x64 figure: the object it stands on, and its frames */
#define BIG_DATA (*(volatile u32 *)0x03005F64)
#define FLAGS ((volatile u8 *)0x030010BD)
static int flag(int f) { return FLAGS[f >> 3] >> (f & 7) & 1; }
static void set_flag(int f) { FLAGS[f >> 3] |= 1 << (f & 7); }

/* a projectile: a spark (0x44 bytes) and these fields after it */
struct proj {
    u8 spark[0x48];
    int x, y;                  /* 1/16 px */
    s16 vx, vy;                /* 1/16 px a frame */
    u8 part, dir, mode, hold;  /* mode 0 flies, 1 rides above its owner (charging), 2 circles its owner; hold: stop on the last frame */
    u16 life, power;
    u8 *owner;
    s16 ox, oy;                /* ride/circle offset, or circle angle and radius */
    u8 burst, hit, size, pad;
    u16 age, pad2;
};

static int iabs(int v) { return v < 0 ? -v : v; }
static int px_(u8 *o) { return *(int *)(o + 0x1A0) >> 8; }
static int py_(u8 *o) { return *(int *)(o + 0x1A4) >> 8; }
static const s8 SIN16[16] = {0, 49, 90, 117, 127, 117, 90, 49, 0, -49, -90, -117, -127, -117, -90, -49};

static const u8 *frames_of(int part, int dir) {
    const volatile part_t *p = &boss_parts[part];
    return p->frames + (p->dirs > 1 ? dir : 0) * p->count * 12;
}
static void set_box(struct proj *q) {
    u8 *s = q->spark; const s8 *f = *(const s8 **)(s + 0x34);
    int x = q->x >> 4, y = q->y >> 4;
    *(int *)(s + 0x10) = x; *(int *)(s + 0x14) = y;
    *(int *)(s + 0x20) = x - f[0]; *(int *)(s + 0x24) = y - f[1];
    *(int *)(s + 0x28) = x - f[0] + ((const u8 *)f)[2]; *(int *)(s + 0x2C) = y - f[1] + ((const u8 *)f)[3];
}
static void burst_at(int part, int x, int y) {
    const volatile part_t *p = &boss_parts[part]; int pos[2] = {x, y};
    void *s;
    if (!room(p->bytes)) return;
    s = NewSpark(0, pos, (const void *)p->frames, p->count, 0x4000, p->bytes, 0x38);
    if (s) ListAdd(ACTORS, s);
}
static void kill(struct proj *q) { ListRemove(SPARKS, q); }

/* as Buu's Fury's own Energy Blast hits (0x0801997C): the owner's side (+0x1D0), its facing, 1024 = an ordinary hit, the blast's effect, the
   owner, and the projectile itself, which stays alive a moment after (the hit reaction looks back at it) */
static void hit_player(struct proj *q) {
    static const int RECT[4] = {-10, -10, 20, 20};
    u32 hit[16]; int pos[2], i; u8 *o = q->owner;
    for (i = 0; i < 16; i++) hit[i] = 0;
    pos[0] = q->x >> 4; pos[1] = q->y >> 4;
    *(u8 *)&hit[0] = o ? o[0x1D0] : 0; RectAt(&hit[1], RECT, pos);
    *(u8 *)&hit[5] = o ? o[0x10] : 0;
    hit[6] = q->power; hit[7] = 0x086B80A8; hit[8] = (u32)o; hit[12] = (u32)q;
    HitObjects(ACTORS, 0, hit);
}
/* A spent projectile shows a clear frame for a moment (as the Energy Blast lingers 16 frames after its hit) rather than leaving the screen:
   when Buu's Fury runs out of OBJ tiles it destroys sparks it hasn't drawn lately, and a destroyed one still in the actor list crashes the next
   update. For the same reason a projectile is removed the moment it leaves the screen. */
static const u8 CLEAR_TILE[64] __attribute__((aligned(4))) = {0};
static const u32 CLEAR_FRAME[3] = {0x08080404, 0x00002000, (u32)CLEAR_TILE};
#define CAMERA ((const int *)0x030019BC)            /* x0, y0, x1, y1 of the screen in the area */
static void spend(struct proj *q) {
    u8 *s = q->spark;
    q->mode = 3; q->life = 16;
    *(const u32 **)(s + 0x34) = CLEAR_FRAME; *(int *)(s + 0x3C) = 1; q->hold = 1;
}
static int on_screen(struct proj *q) {
    const u8 *s = q->spark;
    return *(const int *)(s + 0x20) < CAMERA[2] + 8 && *(const int *)(s + 0x28) > CAMERA[0] - 8 &&
           *(const int *)(s + 0x24) < CAMERA[3] + 8 && *(const int *)(s + 0x2C) > CAMERA[1] - 8;
}

/* A giant's shots start at his head, which is off the top of the screen while Goku stands close below him (and a shot off the screen is removed
   at once): they start at the screen's top edge instead. q->pad is 40 for a tall owner. */
static void keep_in_view(struct proj *q) { int top = CAMERA[1] + 10; if ((q->y >> 4) < top) q->y = top << 4; }

void proj_update(struct proj *q) {
    u8 *s = q->spark, *me = PLAYER_OBJ, *o = q->owner;
    const volatile part_t *p = &boss_parts[q->part];
    int last = *(int *)(s + 0x3C) <= 1;
    if (q->mode == 3) { set_box(q); if (!--q->life || !on_screen(q)) kill(q); return; }
    if (!(q->hold && last)) {
        if (last) { *(const u8 **)(s + 0x34) = frames_of(q->part, q->dir); *(int *)(s + 0x3C) = p->count; }     /* loop */
        SparkUpdate(s);
    }
    if (q->mode == 1 && o) { q->x = (px_(o) + q->ox) << 4; q->y = (py_(o) + q->oy) << 4; }
    else if (q->mode == 2 && o) {
        int a = (q->ox + (FRAMES & 0xFFFF) / 4) & 15;
        q->x = (px_(o) + SIN16[(a + 4) & 15] * q->oy / 128) << 4; q->y = (py_(o) - q->pad + SIN16[a] * q->oy / 256) << 4;
    } else { q->x += q->vx; q->y += q->vy; }
    if (q->mode && q->pad == 40) keep_in_view(q);
    set_box(q);
    if (q->mode == 0 && me && !q->hit) {
        int dx = (q->x >> 4) - px_(me), dy = (q->y >> 4) - (py_(me) - 12), r = 8 + q->size;
        if (iabs(dx) < r && iabs(dy) < r + 4) {
            q->hit = 1; hit_player(q);
            burst_at(q->burst, q->x >> 4, q->y >> 4);
            if (q->power >= 0x1600) Quake(0x18, 0x30);
            spend(q); return;
        }
    }
    if (!on_screen(q)) { kill(q); return; }
    if (q->life && !--q->life) { if (q->mode == 0 && q->size >= 8) burst_at(q->burst, q->x >> 4, q->y >> 4); kill(q); }
}

static int held(void) {                       /* tile bytes the live projectiles hold */
    u32 *l = (u32 *)ACTORS; int i, n = l[1], sum = 0;
    for (i = 0; i < n; i++) { struct proj *q = (struct proj *)l[2 + i]; if (q && *(const int **)q == proj_vt) sum += boss_parts[q->part].bytes; }
    return sum;
}
static struct proj *shoot(int part, int dir, int x, int y, int vx, int vy, int life, int power, int burst, int size) {
    const volatile part_t *p = &boss_parts[part];
    struct proj *q;
    int pos[2] = {x, y};
    if (held() + p->bytes > BUDGET || !room(p->bytes)) return 0;
    q = (struct proj *)Alloc(sizeof(struct proj));
    if (!q) return 0;
    NewSpark(q, pos, frames_of(part, dir), p->count, 0x4000, p->bytes, 0x38);
    *(const int **)q = proj_vt;
    q->x = x << 4; q->y = y << 4; q->vx = vx; q->vy = vy; q->part = part; q->dir = dir; q->mode = 0; q->hold = 0;
    q->life = life; q->power = power; q->owner = BS.obj; q->ox = q->oy = 0; q->burst = burst; q->hit = 0; q->size = size; q->age = 0; q->pad = B2.tall ? 40 : 14;
    if (B2.tall) keep_in_view(q);
    set_box(q);
    ListAdd(ACTORS, q);
    return q;
}

/* aim: velocity (1/16 px a frame) of the given speed toward Goku; dir4: the main direction 0 down, 1 up, 2 left, 3 right */
static int dir4(int dx, int dy) { return iabs(dx) >= iabs(dy) ? (dx < 0 ? 2 : 3) : (dy < 0 ? 1 : 0); }
static void aim(int dx, int dy, int speed, int *vx, int *vy) {
    int ax = iabs(dx), ay = iabs(dy), len = (ax > ay ? ax + ay / 2 : ay + ax / 2);
    if (len < 1) len = 1;
    *vx = dx * speed / len; *vy = dy * speed / len;
}
static const s8 DX[4] = {0, 0, -1, 1}, DY[4] = {1, -1, 0, 0};

/* attacks: each runs over BS.t frames; returns 1 when done */
enum { A_EYE, A_FLASH, A_NOVA, A_RING, A_CALAMITY, A_METEOR, A_FINGER, A_SLUG_EYE, A_TWIN, A_SMASHER, A_MOUTH, A_STOMP };
static const u8 MOVES[8][4] = {
    {A_EYE, A_FLASH, A_EYE, A_FLASH},            /* Cooler */
    {A_FLASH, A_EYE, A_NOVA, A_FLASH},           /* Cooler, final form */
    {A_RING, A_CALAMITY, A_RING, A_CALAMITY},    /* Turles */
    {A_METEOR, A_CALAMITY, A_RING, A_METEOR},    /* Turles after the fruit */
    {A_FINGER, A_SLUG_EYE, A_TWIN, A_FINGER},    /* Lord Slug */
    {A_SMASHER, A_SLUG_EYE, A_TWIN, A_FINGER},   /* Lord Slug, giant */
    {A_MOUTH, A_STOMP, A_MOUTH, A_STOMP},        /* Gohan as a Great Ape */
    {A_MOUTH, A_METEOR, A_MOUTH, A_FLASH},       /* Dodoria, in Bardock's vision */
};
static const u8 COOLDOWN[8] = {100, 80, 105, 80, 105, 85, 95, 90};

static void beam_seg(int part, int d, int x, int y, int speed, int side, int power, int burst) {
    shoot(part, d, x + DY[d] * side, y + DX[d] * side, DX[d] * speed * 16, DY[d] * speed * 16, 34, power, burst, 0);
}

static int attack(u8 *me) {
    u8 *o = BS.obj; int t = BS.t, x = px_(o), y = py_(o) - (B2.tall ? 44 : 14), dx = px_(me) - x, dy = (py_(me) - 12) - y, vx, vy, d = BS.step;
    struct proj *q;
    if (t == 0) { BS.step = d = dir4(dx, dy); o[0x10] = d; PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0); }    /* he turns to Goku (Sprite_SetFacing's slot change uploads a whole animation into an enemy's 1 KB of tiles: never) */
    switch (BS.atk) {
    case A_EYE: case A_SLUG_EYE:                    /* a glint, then two thin beams from the eyes */
        if (t >= 18 && t < 42 && !(t & 3)) beam_seg(BS.atk == A_EYE ? P_EYE : P_SLUG_EYE, d, x + DX[d] * 18, y - 4 + DY[d] * 8, 6, 0, 0x300, P_KI_BURST);
        return t >= 48;
    case A_FINGER:                                  /* a needle of gold */
        if (t >= 14 && t < 34 && !(t & 3)) beam_seg(P_FINGER, d, x + DX[d] * 20, y + DY[d] * 8, 8, 0, 0x340, P_KI_BURST);
        return t >= 36;
    case A_FLASH:                                   /* three bolts from the finger */
        if (t == 10 || t == 28 || t == 46) { int dd = dir4(dx, dy); shoot(P_FLASH, dd, x + DX[dd] * 16, y + DY[dd] * 10, DX[dd] * 80, DY[dd] * 80, 60, 0x500, P_KI_BURST, 2); }
        return t >= 56;
    case A_RING:                                    /* Kill Driver: a crackling ring, thrown */
        if (t == 16) { aim(dx, dy, 40, &vx, &vy); shoot(P_RING, 0, x, y, vx, vy, 150, 0x700, P_VIOLET_BURST, 6); }
        return t >= 26;
    case A_CALAMITY:                                /* a dark ball behind the neck, then a wide wave */
        if (t == 0) { q = shoot(P_CAL_CHARGE, 0, x, y - 10, 0, 0, 60, 0, P_VIOLET_BURST, 0); if (q) { q->mode = 1; q->ox = -2; q->oy = -24; q->hold = 1; } }
        if (t == 60) PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 4, 0x40, 0);
        if (t >= 60 && t < 84 && !(t & 3)) beam_seg(P_CAL_WAVE, d, x + DX[d] * 20, y + DY[d] * 10, 8, 0, 0x800, P_VIOLET_BURST);
        return t >= 96;
    case A_METEOR:                                  /* a fan of small violet blasts */
        if (t >= 20 && t <= 52 && !(t & 7)) {
            int k = (t - 20) / 8 - 2, ax = dx - dy * k / 4, ay = dy + dx * k / 4;
            aim(ax, ay, 64, &vx, &vy); shoot(P_METEOR, dir4(vx, vy), x, y, vx, vy, 70, 0x2C0, P_VIOLET_BURST, 0);
        }
        return t >= 60;
    case A_TWIN:                                    /* two suns circle him, then fly at Goku one after the other */
        if (t == 0) for (d = 0; d < 2; d++) { q = shoot(P_TWIN, 0, x, y, 0, 0, 0, 0x600, P_KI_BURST, 4); if (q) { q->mode = 2; q->ox = d * 8; q->oy = 20; BS.aux = 0; } }
        return t >= 8;
    case A_NOVA: case A_SMASHER: {                  /* a sun grown over his head, then hurled */
        int big = BS.atk == A_NOVA ? P_NOVA : P_SMASHER;
        if (t == 0) { q = shoot(big, 0, x, y - 22, 0, 0, 0, BS.atk == A_NOVA ? 0x1800 : 0x1600, P_NOVA_BURST, 14); if (q) { q->mode = 1; q->ox = 0; q->oy = B2.tall ? -68 : -36; q->hold = 1; *(int *)(q->spark + 0x40) = 0x0888; } }
        return t >= 8;
    }
    case A_MOUTH:                                   /* a roar, then a thick blast from the mouth */
        if (t == 0) Quake(0x10, 0x20);
        if (t >= 24 && t < 52 && !(t & 3)) beam_seg(P_MOUTH, d, x + DX[d] * 14, y + 4 + DY[d] * 10, 7, 0, 0x480, P_KI_BURST);
        return t >= 60;
    case A_STOMP:                                   /* he pounds the ground: shockwaves run out every way */
        if (t == 20) { Quake(0x20, 0x30); PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 4, 0x40, 0); }
        if (t == 20 || t == 34) for (d = 0; d < 4; d++) shoot(P_SHOCK, d, px_(o) + DX[d] * 16, py_(o) - 8 + DY[d] * 8, DX[d] * 72, DY[d] * 72, 60, 0x380, P_KI_BURST, 4);
        return t >= 44;
    }
    return 1;
}

/* launch the riding or circling projectiles of the current owner: suns after their growth, twin stars after their circling */
static void launch(u8 *me) {
    u32 *l = (u32 *)ACTORS; int i, n = l[1];
    for (i = 0; i < n; i++) {
        struct proj *q = (struct proj *)l[2 + i];
        int vx, vy, dx, dy, speed, when;
        if (!q || *(const int **)q != proj_vt || q->owner != BS.obj || !q->mode || !q->power) continue;
        if (q->part == P_TWIN) { when = 100 + q->ox * 3; speed = 48; }
        else { when = 130; speed = q->part == P_NOVA ? 22 : 26; }
        if (++q->age < when) continue;
        dx = px_(me) - (q->x >> 4); dy = (py_(me) - 12) - (q->y >> 4);
        aim(dx, dy, speed, &vx, &vy);
        q->mode = 0; q->vx = vx; q->vy = vy; q->life = q->part == P_TWIN ? 90 : 160;
        if (q->part == P_NOVA || q->part == P_SMASHER) {                   /* grown: thrown, churning */
            q->part = q->part == P_NOVA ? P_NOVA_SPIN : P_SMASH_SPIN; q->hold = 0;
            *(const u8 **)(q->spark + 0x34) = frames_of(q->part, 0); *(int *)(q->spark + 0x3C) = boss_parts[q->part].count; *(int *)(q->spark + 0x40) = 0x2000;
        }
        PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 4, 0x40, 0);
    }
}

static int boss_moveset(u8 *o) {
    u32 rec = *(u32 *)(o + 0x58); int i;
    for (i = 0; i < 12 && boss_table[i].record; i++) if (boss_table[i].record == rec) return (int)boss_table[i].moveset;
    return -1;
}

/* the big figure: walking poses while he moves, the casting pose while he attacks */
static void big_figure(u8 *o) {
    int pose = 0, x = px_(o), y = py_(o);
    if (BS.atk != 0xFF && !B2.stun) pose = 2;
    else if (x != B2.lastx || y != B2.lasty) pose = (FRAMES >> 3) & 1;
    B2.lastx = x; B2.lasty = y;
    BIG_OBJ = (u32)o; BIG_DATA = (u32)B2.big + pose * 8192; B2.shown = o;
}
static void let_go(void) { if (B2.shown && BIG_OBJ == (u32)B2.shown) BIG_OBJ = 0; B2.shown = 0; }

void bosses_tick(void) {
    u8 *me = PLAYER_OBJ, *o = 0; int i, n, m = -1;
    if (!me) { BS.obj = 0; let_go(); return; }
    n = ENEMIES[0];
    for (i = 0; i < n && i < 32; i++) {
        u8 *e = (u8 *)ENEMIES[1 + i];
        if (e && *(int *)(e + 0x28C) > 0 && (m = boss_moveset(e)) >= 0) { o = e; break; }
    }
    if (!o) { BS.obj = 0; let_go(); return; }
    if (o != BS.obj || m != BS.mset) {                /* a new villain (the next phase can take the last one's memory: tell them by moveset) */
        let_go(); BS.obj = o; BS.t = 0; BS.cool = 90; BS.atk = 0xFF; BS.n = 0; BS.mset = m; B2.stun = 0; B2.big = 0;
        for (i = 0; i < 12 && boss_table[i].record; i++) if (boss_table[i].record == *(u32 *)(o + 0x58)) B2.big = boss_table[i].big;
        B2.tall = B2.big != 0; B2.lastx = px_(o); B2.lasty = py_(o);
    }
    if (B2.big && B2.big != TALL) big_figure(o);
    launch(me);
    if (B2.stun) {                                     /* Gohan's whistle: he staggers, clutching his head */
        B2.stun--;
        *(int *)(o + 0x1A0) = (BS.pinx + ((FRAMES >> 2) & 1)) << 8; *(int *)(o + 0x1A4) = BS.piny << 8;
        return;
    }
    if (BS.atk != 0xFF) {
        *(int *)(o + 0x1A0) = BS.pinx << 8; *(int *)(o + 0x1A4) = BS.piny << 8;    /* he holds still while he casts */
        if (attack(me)) { BS.atk = 0xFF; BS.cool = COOLDOWN[BS.mset]; }
        else BS.t++;
        return;
    }
    if (BS.cool) { BS.cool--; return; }
    {
        int dx = px_(me) - px_(o), dy = py_(me) - py_(o);
        if (iabs(dx) > 170 || iabs(dy) > 110) return;
    }
    if (BS.mset == 5 && BS.n >= 3 && !flag(WHISTLE_DONE) && !flag(WHISTLE_FLAG)) {     /* giant Slug: Gohan whistles */
        set_flag(WHISTLE_FLAG); B2.stun = 300; BS.pinx = px_(o); BS.piny = py_(o); BS.cool = 40; return;
    }
    BS.atk = MOVES[BS.mset][BS.n++ & 3]; BS.t = 0; BS.pinx = px_(o); BS.piny = py_(o);
    if (attack(me)) BS.atk = 0xFF; else BS.t = 1;
}
