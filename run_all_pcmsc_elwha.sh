#!/bin/bash

# set -e

STARTDIR="$(pwd)"
for p in $(find pcmsc/elwha*/EL* -name "*.nc")
do
    echo "$p"
    DIR="$(dirname "$p")"
    FILE="$(basename "$p")"
    cd "$DIR" || exit
    python ../../pcmsc_elwha.py "$FILE"
    compliance-checker --test=cf:1.6 clean/"$FILE"
    # compliance-checker --test=acdd clean/"$FILE"
    cd "$STARTDIR" || exit
done
