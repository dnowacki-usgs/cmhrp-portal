#!/usr/bin/env python

import os
from urllib.request import urlretrieve
from zipfile import ZipFile

# url = 'https://coastal.er.usgs.gov/data-release/doi-F7VD6XBF/data/UFK14Aqua1571aqc-trm.zip'
# filnam = 'UFK14Aqua1571aqc-trm.nc'

# url = 'https://coastal.er.usgs.gov/data-release/doi-F7VD6XBF/data/UFK14RBR77750p-trm.zip'
# filnam = 'UFK14RBR77750p-trm.nc'

# url = 'https://coastal.er.usgs.gov/data-release/doi-F7VD6XBF/data/UFK14ArgE306E1495aqd-trm.zip'
# filnam = 'UFK14ArgE306aqd-trm.nc'
# filnam = 'UFK14ArgE1495aqd-trm.nc'

# Unviewable with ncdump OR xarray
# url = 'https://coastal.er.usgs.gov/data-release/doi-F7VD6XBF/data/UFK14RDI3734wh-trm.zip'
# filnam = 'UFK14RDI3734wh-trm.nc'

fildir = '/Users/dnowacki/projects/cmhrp-portal/files/'

localfile = fildir + url.split('/')[-1]

if not os.path.exists(localfile):
    urlretrieve(url, localfile)
    with ZipFile(localfile, 'r') as zipObj:
        zipObj.extractall(fildir.split('/')[-2])
