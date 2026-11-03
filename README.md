# Legacy of Goku 1 remake on the Buu's Fury engine

A personal, non-commercial ROM hack: Legacy of Goku's story and map layouts on Buu's Fury's engine, art, combat, EXP, equipment and UI.
The output is a `.bps` patch.

**Never add to this repo:** ROMs, or anything extracted from them (text, sprites, maps, portraits, screenshots). You supply the ROMs and the build reads them.

## Quick start
`./setup.sh <Buu's Fury> <Legacy of Goku> <LoG I & II combo> <Legacy of Goku II>` installs the tools, fetches the decomps, checks your ROMs and builds `out/slice/slice.gba`.

## Manual setup
```sh
git clone --recursive https://github.com/smh4004/log1-remake && cd log1-remake
sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi libmgba-dev libpng-dev zlib1g-dev
pip install --break-system-packages capstone numpy pillow unicorn
gcc -O2 vendor/gero-tools/tools/harness.c -o vendor/gero-tools/tools/harness -lmgba -lpng -lz
python3 tools/romcheck.py <Buu's Fury> <Legacy of Goku> <LoG I & II combo>
python3 build.py
vendor/gero-tools/tools/harness out/log1_remake.gba tools/routes/boot.txt out/boot
```
`romcheck.py` needs a clean Buu's Fury; its header explains how to rebuild one from a patched dump.

## Measuring LoG1
Needs extracted `log1-decomp` and `buusfury-decomp` checkouts. On a fresh `log1-decomp` clone, first run:
```sh
mkdir -p .analysis && python3 tools/bfdis/lz.py baserom.gba .analysis/lz_blocks.json 0xFE40 0x7A6418
```
Then `make extract` in both, and:
```sh
python3 tools/measure_log1.py <log1-decomp> <buusfury-decomp> rom/log1.gba
```
Results are summarised in `docs/m1_measurements.md`.
