#!/bin/bash

set -e

FILES="UFK14Aqua1571aqc-trm.nc
UFK14ArgE306aqd-trm.nc
UFK14ArgE1495aqd-trm.nc
UFK14RBR77750p-trm.nc"

for f in $FILES
do
  echo "$f"
  python other_centers.py $f
  compliance-checker -t cf -t acdd files/clean/$f
done
