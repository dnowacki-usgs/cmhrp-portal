#!/usr/bin/env python

import sys
import glob

doi = sys.argv[1]

fn = glob.glob('*.nc')

filnams = [f[:-3] for f in fn]

with open('edout.sh', 'w') as f:
    for filnam in filnams:
        cmd1 = 'bash GenerateDatasetsXml.sh EDDTableFromMultidimNcFiles /sand/usgs/users/dnowacki/doi-{}/ {}.nc "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""'.format(doi, filnam)
        cmd2 = 'cp /erddapData/logs/GenerateDatasetsXml.out /erddapData/logs/{}.xml'.format(filnam)
        f.write(cmd1 + '\n')
        f.write(cmd2 + '\n')
