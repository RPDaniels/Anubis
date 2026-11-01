#!/bin/bash
# usage: runshots.sh game.bin actions.tcl outdir
mkdir -p $3
GAMEBIN=$1 ACTIONS=$2 OUTDIR=$3 SDL_AUDIODRIVER=dummy timeout 300 xvfb-run -a openmsx -machine C-BIOS_MSX1 -script shot.tcl 2>&1 | grep -E "DUMP|rror" | grep -v sequencer
for f in $3/*.vram; do b=${f%.vram}; python3 render.py $f $b.regs $b.png; done
