/* In-area flight: R takes off or lands. It replaces the key reader 0x0803D4A0, which runs once per frame.
 * Flying swaps the collision pointers so the player uses the map's air mask. Landing needs walkable floor below.
 * Area loads always write the floor mask to the first pointer, so a new area cancels flying. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define KEYS   (*(volatile u16 *)0x04000130)
#define FLOOR  (*(volatile u32 *)0x03001A4C)
#define AIR    (*(volatile u32 *)0x03001A50)
#define AREA   (*(volatile u32 *)0x03001980)
#define PLAYER (*(volatile u32 *)0x03001C34)
#define STATE  ((volatile u8 *)0x0203FF04)   /* 0 R held, 1 flying */
#define LAST   (*(volatile u32 *)0x0203FF08)
#define KEY_R  0x100
typedef void (*fn2)(void *, u32); typedef void (*fn0)(void);

/* Live spawn: table of {flag, area entry, record or 0, NPC to remove}, ending in flag 0. When a flag becomes set in that area, the enemy
 * record is created as the area loader would (fn(record, index), then added to the object list). Each runs once per visit. */
#define FLAGS  ((volatile u8 *)0x030010BD)
#define DONE   ((volatile u8 *)0x0203FF10)   /* 32 bytes, one per table row */
#define OBJS   ((void *)0x03001C4C)
typedef struct { u32 flag, area, record, remove; } spawn_t;   /* remove: NPC index to take away, 0 = none */
/* patched by tools/build_flight.py; volatile so the compiler can't fold the empty initial table */
__attribute__((section(".text.table"))) volatile const spawn_t spawn_table[32] = {{0, 0, 0, 0}};
typedef void *(*spawn_fn)(void *, int); typedef void (*add_fn)(void *, void *); typedef void *(*find_fn)(void *, int, int);

/* Quest-driven collision changes: when a flag is set in that area, mark a tile rectangle walkable in the live floor mask. */
typedef struct { u32 flag, area; u16 x1, y1, x2, y2; } walk_t;
__attribute__((section(".text.table"))) volatile const walk_t walk_table[16] = {{0, 0, 0, 0, 0, 0}};
#define WDONE  ((volatile u8 *)0x0203FF30)   /* 16 bytes */

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
    for (int i = 0; i < 32 && spawn_table[i].flag; i++) {
        volatile const spawn_t *s = &spawn_table[i];
        if (new_area) DONE[i] = 0;
        if (DONE[i] || s->area != AREA) continue;
        if (!(FLAGS[s->flag >> 3] >> (s->flag & 7) & 1)) continue;
        DONE[i] = 1;
        if (s->remove) {
            void *npc = ((find_fn)0x08011C71)(OBJS, 5, ((int (*)(int))0x08000159)(s->remove));
            if (npc) {   /* NPCs stamp their 16x8 feet into the live masks, and removal leaves the stamp behind */
                int x = *(int *)((u8 *)npc + 0x1A0) >> 11, y = *(int *)((u8 *)npc + 0x1A4) >> 11;
                for (int m = 0; m < 3; m++) for (int t = x; t < x + 2; t++) if (t >= 0 && t < 256 && y >= 0 && y < 256)
                    ((volatile u8 **)0x03001A4C)[m][y * 32 + (t >> 3)] |= 1 << (t & 7);
                ((add_fn)0x08011945)(OBJS, npc);
            }
        }
        u32 *rec = (u32 *)s->record;
        if (!rec) continue;                                 /* removal only: a character who started following the player */
        void *obj = ((spawn_fn)rec[0])(rec, 0);
        ((add_fn)0x0801191B)(OBJS, obj);
    }
}

void flight_keys(u8 *st) {
    u32 k = ~(u32)KEYS & 0xFFFF;
    ((fn2)0x0804023D)(st, k);
    if (!(~*(u16 *)(st + 2) & 0xF) && st[1] && (*(u16 *)(st + 4) & 0xF)) ((fn0)0x0803FA0D)();
    int fresh = AREA != LAST;
    if (fresh) { LAST = AREA; STATE[1] = 0; }
    live_spawn(fresh);
    live_walk(fresh);
    int r = (k & KEY_R) != 0, pressed = r && !STATE[0]; STATE[0] = r;
    if (!pressed || !PLAYER) return;
    if (STATE[1]) {
        u32 p = PLAYER; int x = *(int *)(p + 0x1A0) >> 11, y = *(int *)(p + 0x1A4) >> 11;
        if (x < 0 || y < 0 || x > 255 || y > 255) return;
        if (!(((u8 *)AIR)[y * 32 + (x >> 3)] >> (x & 7) & 1)) return;   /* the real floor is here while flying */
    }
    u32 t = FLOOR; FLOOR = AIR; AIR = t; STATE[1] ^= 1;
}
