#!/bin/bash

set -e

FILES="NMB14M1T01awWvs-p.nc
NMB14SCW01rbrWvs-p.nc
NMB15M1T03aqd.nc
NMB15SCW01rbrWvs-p.nc"

for f in $FILES
do
  echo "$f"
  python pcmsc_nmb.py $f
  compliance-checker -t cf pcmsc/NMBTimeSeriesData/clean/$f
done
