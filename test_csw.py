# basically a copy-paste from https://github.com/rsignell-usgs/notebook/blob/master/CSW/usgs_pycsw.ipynb

from owslib.csw import CatalogueServiceWeb
from owslib import fes
import numpy as np
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/Users/dnowacki/Documents/cacert.pem'
# %%
# endpoint = 'http://geoport.whoi.edu/csw'
# endpoint = 'http://gamone.whoi.edu/csw'
endpoint = 'http://geoport.usgs.esipfed.org/csw'
#endpoint = 'http://data.nodc.noaa.gov/geoportal/csw'
#endpoint = 'http://data.ioos.us/csw'
#endpoint = 'https://dev-catalog.ioos.us/csw'
csw = CatalogueServiceWeb(endpoint,timeout=60)
print(csw.version)
# %%
csw.get_operation_by_name('GetRecords').constraints
# %%
try:
    csw.get_operation_by_name('GetDomain')
    csw.getdomain('apiso:ServiceType', 'property')
    print(csw.results['values'])
except:
    print('GetDomain not supported')
# %%
# val = 'Grand Bay'
val = 'reduced'
#val = 'William Jones'
filter1 = fes.PropertyIsLike(propertyname='apiso:AnyText',literal=('*%s*' % val),
                        escapeChar='\\',wildCard='*',singleChar='?')

def print_records(csw, startposition=0):
    csw.getrecords2(constraints=[ filter1 ], maxrecords=100, esn='full', startposition=startposition)
    for rec in list(csw.records.keys()):
        # print(dir(csw.records[rec]))
        print(csw.records[rec].identifier, csw.records[rec].title)
    if csw.results['nextrecord'] > 0:
        startposition = csw.results['nextrecord']
        print_records(csw, startposition=startposition)

print_records(csw)
# %%
