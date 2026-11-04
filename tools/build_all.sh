#!/bin/bash
# Builds the game from your own ROM dumps, run from the repo root: tools/build_all.sh <folder holding the dumps>
# The dumps are recognised by checksum, so their file names don't matter. windows/build_game.bat runs this on Windows.
# ROMs and everything extracted from them stay in rom/, deps/ and out/, which git ignores. The result is out/slice/slice.gba.
set -e
DIR=$1
[ -d "$DIR" ] || { echo "Usage: tools/build_all.sh <folder holding the ROM dumps>"; exit 1; }
BF= L1= COMBO= L2=
for f in "$DIR"/*.gba "$DIR"/*.GBA; do
    [ -f "$f" ] || continue
    case $(sha1sum "$f" | cut -d' ' -f1) in
        f1c4b07554d2a3b1ad2f325307051e775ce68087|e65738e9d67688309f09811a54f495523ec9aada) BF=$f ;;
        a3c8c76742f11fc6a3f6e3fcca20992458cac0b5) L1=$f ;;
        f02d179accbeb9b68bcaef8720eb0ae426dde6ee) COMBO=$f ;;
        18e0715dec419f3501c301511530d2edcd590f8b) L2=$f ;;
        *) echo "Ignoring $(basename "$f"): not one of the four dumps this build needs." ;;
    esac
done
missing=
[ -n "$BF" ] || missing="$missing\n  Dragon Ball Z: Buu's Fury (USA)"
[ -n "$L1" ] || missing="$missing\n  Dragon Ball Z: The Legacy of Goku (USA), stand-alone"
[ -n "$COMBO" ] || missing="$missing\n  Dragon Ball Z: The Legacy of Goku I & II combo cart"
[ -n "$L2" ] || missing="$missing\n  Dragon Ball Z: The Legacy of Goku II (USA), stand-alone"
if [ -n "$missing" ]; then printf "Couldn't find a matching .gba for:$missing\nThese must be unmodified, unzipped USA dumps in: %s\n" "$DIR"; exit 1; fi

export PYTHONPATH="$PWD/tools/winfix${PYTHONPATH:+:$PYTHONPATH}" PYTHONUTF8=1
step() { echo; echo "=== $1"; }
step "Getting the tools and decomps"
git submodule update --init
mkdir -p deps
for r in buusfury-decomp log1-decomp log2-decomp; do
    [ -d deps/$r/.git ] || { rm -rf deps/$r; git -c core.autocrlf=false clone --depth 1 https://github.com/smh4004/$r deps/$r; }
done
step "Building Buu's Fury"
cp "$BF" deps/buusfury-decomp/baserom.gba; (cd deps/buusfury-decomp && make -j4 && make compare && make extract)
step "Building Legacy of Goku"
cp "$L1" deps/log1-decomp/baserom.gba; (cd deps/log1-decomp && make -j4 && make compare && mkdir -p .analysis && python3 tools/bfdis/lz.py baserom.gba .analysis/lz_blocks.json 0xFE40 0x7A6418 && make extract)
step "Building Legacy of Goku II"
cp "$L2" deps/log2-decomp/baserom.gba; (cd deps/log2-decomp && make -j4 && make compare && make extract)
step "Building the game"
python3 tools/romcheck.py deps/buusfury-decomp/buusfury.gba "$L1" "$COMBO" "$L2"
python3 tools/slice_build.py deps
echo; echo "Done: out/slice/slice.gba"
