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

void flight_keys(u8 *st) {
    u32 k = ~(u32)KEYS & 0xFFFF;
    ((fn2)0x0804023D)(st, k);
    if (!(~*(u16 *)(st + 2) & 0xF) && st[1] && (*(u16 *)(st + 4) & 0xF)) ((fn0)0x0803FA0D)();
    if (AREA != LAST) { LAST = AREA; STATE[1] = 0; }
    int r = (k & KEY_R) != 0, pressed = r && !STATE[0]; STATE[0] = r;
    if (!pressed || !PLAYER) return;
    if (STATE[1]) {
        u32 p = PLAYER; int x = *(int *)(p + 0x1A0) >> 11, y = *(int *)(p + 0x1A4) >> 11;
        if (x < 0 || y < 0 || x > 255 || y > 255) return;
        if (!(((u8 *)AIR)[y * 32 + (x >> 3)] >> (x & 7) & 1)) return;   /* the real floor is here while flying */
    }
    u32 t = FLOOR; FLOOR = AIR; AIR = t; STATE[1] ^= 1;
}
