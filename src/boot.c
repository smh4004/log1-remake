/* Boot sequence from LoG1: legal screen, publisher and developer logos, the intro movie with its song, then the title logo. It runs once
   from Buu's Fury's main function, in place of its own logos, so it polls the display itself while the sound interrupts keep running. Screens and movie are copied from your ROM at build time (tools/log1_start.py). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef signed char s8;
#define DISPCNT (*(volatile u16 *)0x04000000)
#define VCOUNT  (*(volatile u16 *)0x04000006)
#define BG2PA   (*(volatile u16 *)0x04000020)
#define BG2PB   (*(volatile u16 *)0x04000022)
#define BG2PC   (*(volatile u16 *)0x04000024)
#define BG2PD   (*(volatile u16 *)0x04000026)
#define BG2X    (*(volatile u32 *)0x04000028)
#define BG2Y    (*(volatile u32 *)0x0400002C)
#define BLDCNT  (*(volatile u16 *)0x04000050)
#define BLDY    (*(volatile u16 *)0x04000054)
#define KEYS    (*(volatile u16 *)0x04000130)
#define PAL     ((volatile u16 *)0x05000000)
#define VRAM    ((volatile u16 *)0x06000000)
#define W 120
#define H 80
typedef struct { const u16 *pal; const u16 *pix; u32 hold; } screen_t;
typedef void (*fn0)(void);
static const screen_t *const screens = (const screen_t *)SCREENS;

static void vsync(void) { while (VCOUNT >= 160); while (VCOUNT < 160); }
static int skip(void) { return (~KEYS & 9) != 0; }                    /* A or START */
static void wait_release(void) { while (skip()) vsync(); }
static void dma16(volatile void *d, const void *s, u32 n) {
    *(volatile u32 *)0x040000D4 = (u32)s; *(volatile u32 *)0x040000D8 = (u32)d; *(volatile u32 *)0x040000DC = n | 0x80000000;
    while (*(volatile u32 *)0x040000DC & 0x80000000);
}
static void fade(int from, int to) {
    int s = from < to ? 1 : -1;
    for (int y = from; y != to + s; y += s) { BLDY = y; vsync(); }
}
static void show(const screen_t *p) {
    BLDCNT = 0xC4; BLDY = 16; dma16(PAL, p->pal, 256); dma16(VRAM, p->pix, 240 * 160 / 2);
    fade(16, 0);
    for (u32 i = 0; i < p->hold && !skip(); i++) vsync();
    wait_release(); fade(0, 16);
}
static u32 rd16(const u8 *p) { return p[0] | p[1] << 8; }
static u32 rd32(const u8 *p) { return rd16(p) | rd16(p + 2) << 16; }
static void colours(const u8 *p, int shift) {
    int packets = rd16(p), at = 0; p += 2;
    while (packets--) {
        at += *p++; int n = *p++; if (!n) n = 256;
        while (n-- && at < 256) { int r = p[0] << shift, g = p[1] << shift, b = p[2] << shift; PAL[at++] = (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10; p += 3; }
    }
}
/* The picture is 120x80 in a mode 4 page, zoomed 2x. VRAM takes 16-bit writes only, so each pixel updates its halfword. */
#define PUT(o, v) do { u32 o_ = (o); volatile u16 *q_ = VRAM + (o_ >> 1); *q_ = o_ & 1 ? (*q_ & 0xFF) | (v) << 8 : (*q_ & 0xFF00) | (v); } while (0)
static void chunk(int type, const u8 *p) {
    if (type == 4) colours(p, 0);
    else if (type == 11) colours(p, 2);
    else if (type == 13) { for (int y = 0; y < H; y++) for (int x = 0; x < W / 2; x++) VRAM[y * 120 + x] = 0; }
    else if (type == 16) { for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) PUT(y * 240 + x, *p++); }
    else if (type == 15) {
        for (int y = 0; y < H; y++) {
            u32 d = y * 240, e = d + W; p++;
            while (d < e) { int n = (s8)*p++; if (n >= 0) { int v = *p++; while (n--) { PUT(d, v); d++; } } else { while (n++) { PUT(d, *p); d++; p++; } } }
        }
    } else if (type == 12) {
        int y = rd16(p), lines = rd16(p + 2); p += 4;
        while (lines--) {
            u32 d = y++ * 240; int packets = *p++;
            while (packets--) { d += *p++; int n = (s8)*p++; if (n >= 0) { while (n--) { PUT(d, *p); d++; p++; } } else { int v = *p++; while (n++) { PUT(d, v); d++; } } }
        }
    } else if (type == 7) {
        int lines = rd16(p), y = 0; p += 2;
        while (lines > 0) {
            int w = (short)rd16(p); p += 2;
            if ((w & 0xC000) == 0xC000) { y -= w; continue; }
            if (w & 0x8000) { PUT(y * 240 + W - 1, w & 0xFF); continue; }
            u32 d = y * 240; lines--;
            while (w--) {
                d += *p++; int n = (s8)*p++;
                if (n >= 0) { while (n--) { PUT(d, p[0]); PUT(d + 1, p[1]); d += 2; p += 2; } }
                else { while (n++) { PUT(d, p[0]); PUT(d + 1, p[1]); d += 2; } p += 2; }
            }
            y++;
        }
    }
}
static void movie(const u8 *f) {
    int frames = rd16(f + 6); const u8 *p = f + 128;
    int wait = rd32(f + 16) * 6 / 7; if (wait < 1) wait = 1;
    chunk(13, p);
    BLDY = 0; BLDCNT = 0;
    for (int n = 0; n < frames && !skip(); n++) {
        u32 size = rd32(p); int kind = rd16(p + 4);
        if (kind == 0xF1FA) {
            int count = rd16(p + 6); const u8 *q = p + 16;
            while (count--) { chunk(rd16(q + 4), q + 6); q += rd32(q); }
        }
        p += size;
        for (int w = 0; w < wait; w++) vsync();
    }
    wait_release();
}
/* A movie in the middle of the story: the scene loads a map or picture straight afterwards, which redraws everything. */
void play_movie(const u8 *f) {
    u16 keep = BLDCNT;
    DISPCNT = 0x80; BG2PA = 0x80; BG2PB = 0; BG2PC = 0; BG2PD = 0x80; BG2X = 0; BG2Y = 0; DISPCNT = 0x0404;
    movie(f);
    DISPCNT = 0x80; BG2PA = 0x100; BG2PD = 0x100; BLDCNT = keep;
    for (int y = 0; y < H; y++) for (int x = 0; x < W / 2; x++) VRAM[y * 120 + x] = 0;
}
typedef void (*song_fn)(void *, const void *);
static void song(const void *s) { ((song_fn)0x0803F111)(**(void ***)0x0800420C, s); }
void log1_boot(void) {
    *(volatile u8 *)0x030038A9 = 0;                                     /* main has already started the title song, but the logos are silent in LoG1 */
    DISPCNT = 0x80; BG2PA = 0x100; BG2PB = 0; BG2PC = 0; BG2PD = 0x100; BG2X = 0; BG2Y = 0;
    BLDCNT = 0xC4; BLDY = 16; DISPCNT = 0x0404;
    for (const screen_t *p = screens; p->pal; p++) show(p);
    BG2PA = 0x80; BG2PD = 0x80;
    song((const void *)TITLE_SONG);                                     /* LoG1's title song starts with the movie and runs on through the title. Buu's Fury's title sees it already playing, so it doesn't restart */
    movie((const u8 *)MOVIE);
    BG2PA = 0x100; BG2PD = 0x100; show((const screen_t *)SPLASH);
    DISPCNT = 0x80; BLDCNT = 0; BLDY = 0;
}
__attribute__((naked)) void boot_entry(void) {
    __asm__("bl log1_boot\n ldr r0, =0x080041DD\n bx r0\n .ltorg");    /* back into main, after its own logos */
}
