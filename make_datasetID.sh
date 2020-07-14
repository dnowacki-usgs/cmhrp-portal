for x in ELW*.xml; do
    echo $x;
    y="${x%.*}"
    echo $y;
    sed -i "s/datasetID=\".*\"/datasetID=\""${y}"\"/g" ${x};
done
