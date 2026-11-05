/* In-area flight: R takes off or lands. It replaces the key reader 0x0803D4A0, which runs once per frame.
 * Flying swaps the collision pointers so the player uses the map's air mask. Landing needs walkable floor below.
 * Area loads always write the floor mask to the first pointer, so a new area cancels flying. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
/* Hook RAM is 0x03005F00-0x030061FF in IWRAM. It must stay out of the top of EWRAM: 0x0203E000-0x0203FFFF is the game's save buffer. */
#define INIT_AT ((volatile unsigned *)0x03005F00)
#define INIT_MAGIC (*(volatile unsigned *)0x030061F8)
static void ram_init(void) { if (INIT_MAGIC == 0x31474F4C) return; for (int i = 0; i < 0x300 / 4; i++) INIT_AT[i] = 0; INIT_MAGIC = 0x31474F4C; }
#define KEYS   (*(volatile u16 *)0x04000130)
#define FLOOR  (*(volatile u32 *)0x03001A4C)
#define AIR    (*(volatile u32 *)0x03001A50)
#define AREA   (*(volatile u32 *)0x03001980)
#define PLAYER (*(volatile u32 *)0x03001C34)
#define STATE  ((volatile u8 *)0x03006104)   /* 0 R held, 1 flying, 2 L held */
#define LAST   (*(volatile u32 *)0x03006108)
#define KEY_R  0x100
typedef void (*fn2)(void *, u32); typedef void (*fn0)(void);

/* Live spawn: table of {flag, area entry, record or 0, NPC to remove}, ending in flag 0. When a flag becomes set in that area, the enemy
 * record is created as the area loader would (fn(record, index), then added to the object list). Each runs once per visit. */
#define FLAGS  ((volatile u8 *)0x030010BD)
#define DONE   ((volatile u8 *)0x03006110)   /* 32 bytes, one bit per table row */
#define OBJS   ((void *)0x03001C4C)
typedef struct { u32 flag, area, record, remove, until; } spawn_t;   /* remove: NPC index to take away, 0 = none */
/* patched by tools/build_flight.py; volatile so the compiler can't fold the empty initial table */
__attribute__((section(".text.table"))) volatile const u32 spawn_ptr = 0;
typedef void *(*spawn_fn)(void *, int); typedef void (*add_fn)(void *, void *); typedef void *(*find_fn)(void *, int, int);

/* Quest-driven collision changes: when a flag is set in that area, mark a tile rectangle walkable in the live floor mask. */
typedef struct { u32 flag, area; u16 x1, y1, x2, y2; } walk_t;
__attribute__((section(".text.table"))) volatile const walk_t walk_table[16] = {{0, 0, 0, 0, 0, 0}};
#define WDONE  ((volatile u8 *)0x03006130)   /* 16 bytes */

/* NPCs stamp their 16x8 feet into the live masks, and removal leaves the stamp behind. */
static void remove_npc(void *npc) {
    int x = *(int *)((u8 *)npc + 0x1A0) >> 8, y = *(int *)((u8 *)npc + 0x1A4) >> 8;
    for (int m = 0; m < 3; m++)
        for (int ty = y >> 3; ty <= (y + 7) >> 3; ty++) for (int t = x >> 3; t <= (x + 15) >> 3; t++)
            if (t >= 0 && t < 256 && ty >= 0 && ty < 256) ((volatile u8 **)0x03001A4C)[m][ty * 32 + (t >> 3)] |= 1 << (t & 7);
    ((add_fn)0x08011945)(OBJS, npc);
}

/* Pickups stream in near the player, as BF's object list takes only 27 area objects. Table of {area, flag, x, y, record}, ending in area 0.
 * They don't block: masks are restored around the spawn, which stamps the NPC's feet. */
typedef struct { u32 area; u16 flag, x, y; u32 rec; } pick_t;
__attribute__((section(".text.table"))) volatile const u32 pick_ptr = 0;
typedef struct { const pick_t *row; void *obj; } slot_t;
#define SLOTS  ((slot_t *)0x03006140)         /* MAX_SLOTS entries */
#define MAX_SLOTS 6
#define TICK   (*(volatile u8 *)0x03006170)
#define OBJ_N  (*(volatile u32 *)0x03001C50)
#define MASKS  ((u8 *volatile *)0x03001A4C)

static void spawn_pick(const pick_t *p, slot_t *s) {
    int x0 = p->x >> 3, x1 = (p->x + 15) >> 3, y0 = p->y >> 3, y1 = (p->y + 7) >> 3; u8 save[3][2][2];
    for (int m = 0; m < 3; m++) for (int y = 0; y < 2; y++) for (int b = 0; b < 2; b++) save[m][y][b] = MASKS[m][(y0 + y) * 32 + (x0 >> 3) + b];
    u32 *rec = (u32 *)p->rec; void *obj = ((spawn_fn)rec[0])(rec, 0); ((add_fn)0x0801191B)(OBJS, obj);
    for (int m = 0; m < 3; m++) for (int y = 0; y < 2; y++) for (int b = 0; b < 2; b++) MASKS[m][(y0 + y) * 32 + (x0 >> 3) + b] = save[m][y][b];
    s->row = p; s->obj = obj; (void)x1; (void)y1;
}

/* Bit 15 of flag: shown once the flag is set (a placed bridge stone or sapling) rather than until then. */
static int pick_gone(const pick_t *p) {
    u32 f = p->flag & 0x7FFF; int set = FLAGS[f >> 3] >> (f & 7) & 1; return p->flag & 0x8000 ? !set : set;
}

static void live_pick(int new_area) {
    slot_t *S = SLOTS;
    if (new_area) { for (int i = 0; i < MAX_SLOTS; i++) S[i].row = 0; return; }
    if (!PLAYER || (TICK++ & 7)) return;
    int px = *(int *)(PLAYER + 0x1A0) >> 8, py = *(int *)(PLAYER + 0x1A4) >> 8;
    for (int i = 0; i < MAX_SLOTS; i++) {
        const pick_t *p = S[i].row;
        if (!p) continue;
        int dx = p->x - px, dy = p->y - py;
        if (pick_gone(p) || dx > 200 || dx < -200 || dy > 160 || dy < -160) { ((add_fn)0x08011945)(OBJS, S[i].obj); S[i].row = 0; }
    }
    for (const pick_t *p = (const pick_t *)pick_ptr; p && p->area; p++) {
        if (p->area != AREA || pick_gone(p)) continue;
        int dx = p->x - px, dy = p->y - py, free_ = -1, have = 0;
        if (dx > 160 || dx < -160 || dy > 120 || dy < -120) continue;
        for (int i = 0; i < MAX_SLOTS; i++) { if (S[i].row == p) have = 1; else if (!S[i].row) free_ = i; }
        if (!have && free_ >= 0 && OBJ_N < 29) spawn_pick(p, &S[free_]);
    }
}

/* Enemies stream too, so an area keeps all of LoG1's enemies with no more than ESLOTS alive: table of {area, index in area, x, y, record},
 * ending in area 0. One that leaves the object list has died and stays dead for this visit (DEAD holds one bit per index). */
__attribute__((section(".text.table"))) volatile const u32 foe_ptr = 0;
typedef struct { const pick_t *row; void *obj; } fslot_t;
#define FOES   ((fslot_t *)0x03006180)
#define ESLOTS 14
#define DEAD   ((volatile u8 *)0x030061F0)    /* 8 bytes */
#define OBJ_AT ((void *volatile *)0x03001C54)
typedef int (*cond_fn)(u32);
#define COND_FN 0x08004785

static int listed(void *o) { for (u32 i = 0; i < OBJ_N; i++) if (OBJ_AT[i] == o) return 1; return 0; }

static void live_foes(int new_area) {
    fslot_t *S = FOES;
    if (new_area) { for (int i = 0; i < ESLOTS; i++) S[i].row = 0; for (int i = 0; i < 8; i++) DEAD[i] = 0; return; }
    if (!PLAYER || (TICK & 7) != 5) return;
    int px = *(int *)(PLAYER + 0x1A0) >> 8, py = *(int *)(PLAYER + 0x1A4) >> 8;
    for (int i = 0; i < ESLOTS; i++) {
        const pick_t *p = S[i].row;
        if (!p) continue;
        if (!listed(S[i].obj)) { DEAD[p->flag >> 3] |= 1 << (p->flag & 7); S[i].row = 0; continue; }
        int dx = (*(int *)((u8 *)S[i].obj + 0x1A0) >> 8) - px, dy = (*(int *)((u8 *)S[i].obj + 0x1A4) >> 8) - py;
        if (dx > 240 || dx < -240 || dy > 190 || dy < -190) { ((add_fn)0x08011945)(OBJS, S[i].obj); S[i].row = 0; }
    }
    for (const pick_t *p = (const pick_t *)foe_ptr; p && p->area; p++) {
        if (p->area != AREA || DEAD[p->flag >> 3] >> (p->flag & 7) & 1) continue;
        int dx = p->x - px, dy = p->y - py, free_ = -1, have = 0;
        if (dx > 190 || dx < -190 || dy > 150 || dy < -150) continue;
        for (int i = 0; i < ESLOTS; i++) { if (S[i].row == p) have = 1; else if (!S[i].row) free_ = i; }
        if (have || free_ < 0 || OBJ_N >= 27) continue;
        u32 *rec = (u32 *)p->rec;
        if (rec[1] && !((cond_fn)COND_FN)(rec[1])) continue;
        void *o = ((spawn_fn)rec[0])(rec, p->flag); ((add_fn)0x0801191B)(OBJS, o); S[free_].row = p; S[free_].obj = o;
    }
}

/* LoG1's hurting ground: table of {area, rect, damage per second, mode}, ending in area 0. Mode 1 zones spare a flying player. Never kills: HP stops at 1. */
typedef struct { u32 area; short x1, y1, x2, y2; u16 dmg, mode; } hurt_t;
__attribute__((section(".text.table"))) volatile const u32 zone_ptr = 0;
#define HP (*(volatile int *)0x03001574)
#define SECOND (*(volatile u8 *)0x03006171)

static void live_hurt(void) {
    if (!PLAYER || ++SECOND < 60) return;
    SECOND = 0;
    int px = *(int *)(PLAYER + 0x1A0) >> 8, py = *(int *)(PLAYER + 0x1A4) >> 8;
    for (const hurt_t *z = (const hurt_t *)zone_ptr; z && z->area; z++) {
        if (z->area != AREA || px < z->x1 || px >= z->x2 || py < z->y1 || py >= z->y2 || (z->mode == 1 && STATE[1])) continue;
        int v = HP - ((int)z->dmg << 16); HP = v < (1 << 16) ? (1 << 16) : v; return;
    }
}

/* A story enemy's death script sets flag 893. This runs quest_check as an exit zone would (sub_080073F0): the script reads +0x10 and +0x14 of its zone object. */
__attribute__((section(".text.table"))) volatile const u32 check_ptr = 0;
#define PENDING 893
#define DEBUG_LIST (*(volatile u32 *)0x0300617C)   /* the test bot writes a list pointer here to warp; nothing in the game does */
static void live_pending(void) {
    if (!PLAYER || !(FLAGS[PENDING >> 3] >> (PENDING & 7) & 1)) return;
    FLAGS[PENDING >> 3] &= ~(1 << (PENDING & 7));
    u32 zone[6] = {0, 0, 0, 0, 0, check_ptr};
    ((fn2)0x080073F1)(zone, PLAYER);
}

/* Someone following the player: table of {start flag, end flag, record}, ending in flag 0. They trail the player by TRAIL frames, in every area. */
typedef struct { u32 start, end, rec; } follow_t;
__attribute__((section(".text.table"))) volatile const u32 follow_ptr = 0;
#define FOLLOW (*(void *volatile *)0x03006174)
#define FROW   (*(const follow_t *volatile *)0x03006178)
#define TRAIL_AT ((volatile int *)0x03006000)         /* 32 x,y pairs */
#define TRAIL  (*(volatile u8 *)0x03006172)
static void live_follow(int new_area) {
    if (new_area) { FOLLOW = 0; FROW = 0; TRAIL = 0; return; }
    if (!PLAYER) return;
    const follow_t *want = 0;
    for (const follow_t *f = (const follow_t *)follow_ptr; f && f->start; f++)
        if (FLAGS[f->start >> 3] >> (f->start & 7) & 1 && !(FLAGS[f->end >> 3] >> (f->end & 7) & 1)) { want = f; break; }
    if (FROW != want) {
        if (FOLLOW) ((add_fn)0x08011945)(OBJS, FOLLOW);
        FOLLOW = 0; FROW = want;
        if (want && OBJ_N < 28) {
            u8 save[3][4];
            for (int m = 0; m < 3; m++) for (int b = 0; b < 4; b++) save[m][b] = MASKS[m][b];
            u32 *rec = (u32 *)want->rec; void *o = ((spawn_fn)rec[0])(rec, 0); ((add_fn)0x0801191B)(OBJS, o); FOLLOW = o;
            for (int m = 0; m < 3; m++) for (int b = 0; b < 4; b++) MASKS[m][b] = save[m][b];
            int x = *(int *)(PLAYER + 0x1A0), y = *(int *)(PLAYER + 0x1A4);
            for (int i = 0; i < 32; i++) { TRAIL_AT[i * 2] = x; TRAIL_AT[i * 2 + 1] = y; }
        }
    }
    if (!FOLLOW) return;
    int t = TRAIL; TRAIL = (t + 1) & 31;
    *(int *)((u8 *)FOLLOW + 0x1A0) = TRAIL_AT[t * 2]; *(int *)((u8 *)FOLLOW + 0x1A4) = TRAIL_AT[t * 2 + 1];
    TRAIL_AT[t * 2] = *(int *)(PLAYER + 0x1A0); TRAIL_AT[t * 2 + 1] = *(int *)(PLAYER + 0x1A4);
}

/* Walk-in zones beyond what BF's exit list holds (a full list crashes area loads): table of {area, rect, step list} grouped by area, ending in area 0.
 * A list runs when the player steps into its rectangle, as an exit zone's would. Up to 128 rows per area. */
typedef struct { u32 area; u16 x0, y0, x1, y1; u32 list; } zone_t;
__attribute__((section(".text.table"))) volatile const u32 walkin_ptr = 0;
#define ZFIRST (*(const zone_t *volatile *)0x03005F00)
#define ZINSIDE ((volatile u8 *)0x03005F04)      /* 16 bytes */
#define ZBUSY  (*(volatile u8 *)0x03005F14)
static void live_zones(int new_area) {
    const zone_t *z = ZFIRST;
    if (new_area) {
        ZFIRST = 0; for (int i = 0; i < 16; i++) ZINSIDE[i] = 0;
        for (z = (const zone_t *)walkin_ptr; z && z->area; z++) if (z->area == AREA) { ZFIRST = z; break; }
        return;
    }
    if (!z || !PLAYER || ZBUSY) return;
    int px = *(int *)(PLAYER + 0x1A0) >> 8, py = *(int *)(PLAYER + 0x1A4) >> 8;
    for (int i = 0; i < 128 && z->area == AREA; i++, z++) {
        int in = px >= z->x0 && px < z->x1 && py >= z->y0 && py < z->y1, was = ZINSIDE[i >> 3] >> (i & 7) & 1;
        if (in == was) continue;
        ZINSIDE[i >> 3] ^= 1 << (i & 7);
        if (in) { u32 zone[6] = {0, 0, 0, 0, 0, z->list}; ZBUSY = 1; ((fn2)0x080073F1)(zone, PLAYER); ZBUSY = 0; return; }
    }
}

static void live_walk(int new_area) {
    for (int i = 0; i < 16 && walk_table[i].flag; i++) {
        volatile const walk_t *w = &walk_table[i];
        if (new_area) WDONE[i] = 0;
        if (WDONE[i] || w->area != AREA || !(FLAGS[w->flag >> 3] >> (w->flag & 7) & 1)) continue;
        WDONE[i] = 1;
        u8 *m = (u8 *)(STATE[1] ? AIR : FLOOR);
        for (int y = w->y1; y < w->y2; y++) for (int x = w->x1; x < w->x2; x++) m[y * 32 + (x >> 3)] |= 1 << (x & 7);
    }
}

static void live_spawn(int new_area) {
    if (new_area) for (int i = 0; i < 32; i++) DONE[i] = 0;
    int i = 0;
    for (const spawn_t *s = (const spawn_t *)spawn_ptr; s && s->flag; s++, i++) {
        if (DONE[i >> 3] >> (i & 7) & 1 || s->area != AREA) continue;
        if (!(FLAGS[s->flag >> 3] >> (s->flag & 7) & 1)) continue;
        DONE[i >> 3] |= 1 << (i & 7);
        if (s->remove) {
            void *npc = ((find_fn)0x08011C71)(OBJS, 5, ((int (*)(int))0x08000159)(s->remove));
            if (npc) remove_npc(npc);
        }
        u32 *rec = (u32 *)s->record;
        if (!rec) continue;                                 /* removal only: a character who started following the player */
        if (s->until && FLAGS[s->until >> 3] >> (s->until & 7) & 1) continue;   /* a beaten boss stays beaten on later visits */
        void *obj = ((spawn_fn)rec[0])(rec, 0);
        ((add_fn)0x0801191B)(OBJS, obj);
    }
}

/* World map: rows of {area, take-off list}. L while flying takes off from an Earth area. Each area sets a visited flag, which opens its landing spot. */
__attribute__((section(".text.table"))) volatile const u32 fly_ptr = 0;
typedef struct { u32 area, list; } fly_t;
#define WORLD_ID 26
#define VISIT 800
static void live_world(u32 k, int fresh) {
    if (!AREA || *(u8 *)AREA != WORLD_ID) return;
    if (fresh) { int f = VISIT + *(u8 *)(AREA + 1) - 1; FLAGS[f >> 3] |= 1 << (f & 7); }
    int l = (k & 0x200) != 0, pressed = l && !STATE[2]; STATE[2] = l;
    if (!pressed || !STATE[1] || !PLAYER) return;
    for (const fly_t *f = (const fly_t *)fly_ptr; f && f->area; f++)
        if (f->area == AREA) { u32 zone[6] = {0, 0, 0, 0, 0, f->list}; STATE[1] = 0; { u32 t = FLOOR; FLOOR = AIR; AIR = t; } ((fn2)0x080073F1)(zone, PLAYER); return; }
}

/* The draw pass (sub_0801157E) rebuilt here so the world map's HUD can add to it: copy the OAM shadow to OAM, then draw each listed object's VRAM.
 * On the map, each visited place gets a marker on the minimap. */
__attribute__((section(".text.table"))) volatile const u32 art_ptr = 0, mark_ptr = 0;
typedef struct { u16 flag; u8 x, y; } mark_t;
#define OAM ((volatile u16 *)0x03003498)
#define MARK_TILE 100                       /* the map allocates OBJ tiles down from the top of VRAM, so low tiles stay free */
#define MARK_FIRST 118
void flight_draw(int list) {
    int map = AREA && *(u8 *)AREA == 0 && *(u8 *)(AREA + 1) == 50;
    if (map) {
        int e = MARK_FIRST;
        for (const mark_t *m = (const mark_t *)mark_ptr; m && m->flag && e < 128; m++) {
            if (!(FLAGS[m->flag >> 3] >> (m->flag & 7) & 1)) continue;
            OAM[e * 4] = m->y | 0x2000; OAM[e * 4 + 1] = m->x; OAM[e * 4 + 2] = MARK_TILE; e++;
        }
    }
    ((void (*)(void *))0x0803DA63)((void *)OAM);       /* copies the shadow to OAM */
    int *p = (int *)(list + 0x208); int n = *p;
    while (n > 0) { int *o = (int *)p[n]; n--; int v = *o; ((void (*)(void *))(v + *(int *)(v + 0x14)))(o); }
    *p = 0;
    if (!map) return;
    const u32 *a = (const u32 *)art_ptr; volatile u32 *d = (volatile u32 *)(0x06010000 + MARK_TILE * 32);
    for (int i = 0; i < 16; i++) d[i] = a[i];
}

/* Story pictures are areas of their own: the player and HUD are hidden there, and put back where they were afterwards. */
#define PIC_SAVE 896
#define PIC_BACK 897
#define PIC_FIRST 55                                                   /* the first picture's area number */
#define PX (*(volatile int *)0x03005F18)
#define PY (*(volatile int *)0x03005F1C)
#define DISPCNT (*(volatile u16 *)0x04000000)
static void live_pictures(void) {
    if (!PLAYER) return;
    if (FLAGS[PIC_SAVE >> 3] >> (PIC_SAVE & 7) & 1) { FLAGS[PIC_SAVE >> 3] &= ~(1 << (PIC_SAVE & 7)); PX = *(int *)(PLAYER + 0x1A0); PY = *(int *)(PLAYER + 0x1A4); }
    if (FLAGS[PIC_BACK >> 3] >> (PIC_BACK & 7) & 1) { FLAGS[PIC_BACK >> 3] &= ~(1 << (PIC_BACK & 7)); *(int *)(PLAYER + 0x1A0) = PX; *(int *)(PLAYER + 0x1A4) = PY; }
    if (AREA && *(u8 *)AREA == 26 && *(u8 *)(AREA + 1) >= PIC_FIRST) DISPCNT &= ~0x1000;
}

void flight_keys(u8 *st) {
    ram_init();
    live_pictures();
    u32 k = ~(u32)KEYS & 0xFFFF;
    ((fn2)0x0804023D)(st, k);
    if (!(~*(u16 *)(st + 2) & 0xF) && st[1] && (*(u16 *)(st + 4) & 0xF)) ((fn0)0x0803FA0D)();
    int fresh = AREA != LAST;
    if (fresh) { LAST = AREA; STATE[1] = 0; }
    live_spawn(fresh);
    live_walk(fresh);
    live_pick(fresh);
    live_foes(fresh);
    live_hurt();
    live_zones(fresh);
    live_pending();
    live_follow(fresh);
    if (DEBUG_LIST && PLAYER) { u32 zone[6] = {0, 0, 0, 0, 0, DEBUG_LIST}; DEBUG_LIST = 0; ((fn2)0x080073F1)(zone, PLAYER); }
    live_world(k, fresh);
    int r = (k & KEY_R) != 0, pressed = r && !STATE[0]; STATE[0] = r;
    if (!pressed || !PLAYER || !AREA || *(u8 *)AREA != WORLD_ID) return;
    if (STATE[1]) {
        u32 p = PLAYER; int x = *(int *)(p + 0x1A0) >> 11, y = *(int *)(p + 0x1A4) >> 11;
        if (x < 0 || y < 0 || x > 255 || y > 255) return;
        if (!(((u8 *)AIR)[y * 32 + (x >> 3)] >> (x & 7) & 1)) return;   /* the real floor is here while flying */
    }
    u32 t = FLOOR; FLOOR = AIR; AIR = t; STATE[1] ^= 1;
}
