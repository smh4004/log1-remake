#!/bin/sh
# Test harness with a real save file: the Gero tools harness, plus SAVEF=<file> to load one as an emulator does. Writes out/harness.
set -e
mkdir -p out
sed 's/mCoreLoadFile(c,argv\[1\]); c->reset(c);/mCoreLoadFile(c,argv[1]); if(getenv("SAVEF"))c->loadSave(c,VFileOpen(getenv("SAVEF"),O_RDWR)); c->reset(c);/' vendor/gero-tools/tools/harness.c > out/harness.c
grep -q SAVEF out/harness.c
sed -i '1i #include <stdlib.h>\n#include <fcntl.h>' out/harness.c
gcc -O2 out/harness.c -o out/harness -lmgba -lpng -lz
