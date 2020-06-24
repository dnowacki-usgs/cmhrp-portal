#!/bin/bash

# set -e

STARTDIR="$(pwd)"
for p in $(find pcmsc/DL*/DL* -name "*rbr-s.nc")
# for p in "pcmsc/DL107LWA/DL107LWArbr-s.nc"
do
    echo "$p"
    DIR="$(dirname "$p")"
    FILE="$(basename "$p")"
    cd "$DIR" || exit
    python ../../pcmsc_li_lht.py "$FILE"
    compliance-checker --test=cf:1.6 clean/"$FILE"
    # compliance-checker --test=acdd clean/"$FILE"
    cd "$STARTDIR" || exit
done
