#!/bin/bash

for x in "$@"; do
    echo "$x";
    y="${x%.*}"
    echo "$y";
    sed -i "s/datasetID=\".*\"/datasetID=\""${y}"\"/g" ${x};
done
