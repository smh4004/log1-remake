#!/bin/sh
# One-time setup and slice build on Debian/Ubuntu or WSL. Run from the repo root, with your own ROM dumps:
#   ./setup.sh <Buu's Fury dump> <Legacy of Goku dump> <LoG I & II combo dump> <Legacy of Goku II dump>
# ROMs and everything extracted from them stay in rom/, deps/ and out/, which git ignores. The result is out/slice/slice.gba.
set -e
[ $# -eq 4 ] || { sed -n 2,3p "$0"; exit 1; }
BF=$(realpath "$1"); L1=$(realpath "$2"); COMBO=$(realpath "$3"); L2=$(realpath "$4")
git submodule update --init
sudo apt-get install -y git make python3 python3-pip gcc gcc-arm-none-eabi binutils-arm-none-eabi libmgba-dev libpng-dev zlib1g-dev
pip install --break-system-packages capstone numpy pillow unicorn scipy
gcc -O2 vendor/gero-tools/tools/harness.c -o vendor/gero-tools/tools/harness -lmgba -lpng -lz
mkdir -p deps
for r in buusfury-decomp log1-decomp log2-decomp; do [ -d deps/$r ] || git clone --depth 1 https://github.com/smh4004/$r deps/$r; done
cp "$BF" deps/buusfury-decomp/baserom.gba; (cd deps/buusfury-decomp && make -j4 && make compare && make extract)
cp "$L1" deps/log1-decomp/baserom.gba; (cd deps/log1-decomp && make -j4 && make compare && mkdir -p .analysis && python3 tools/bfdis/lz.py baserom.gba .analysis/lz_blocks.json 0xFE40 0x7A6418 && make extract)
cp "$L2" deps/log2-decomp/baserom.gba; (cd deps/log2-decomp && make -j4 && make compare && make extract)
python3 tools/romcheck.py deps/buusfury-decomp/buusfury.gba "$L1" "$COMBO" "$L2"
python3 tools/slice_build.py deps
echo "Done: out/slice/slice.gba"
