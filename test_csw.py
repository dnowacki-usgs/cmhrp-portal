# basically a copy-paste from https://github.com/rsignell-usgs/notebook/blob/master/CSW/usgs_pycsw.ipynb

from owslib.csw import CatalogueServiceWeb
from owslib import fes
import numpy as np
# %%
# endpoint = 'http://geoport.whoi.edu/csw'
endpoint = 'http://gamone.whoi.edu/csw'
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
val = 'Florida'
#val = 'William Jones'
filter1 = fes.PropertyIsLike(propertyname='apiso:AnyText',literal=('*%s*' % val),
                        escapeChar='\\',wildCard='*',singleChar='?')
# %%

# csw.results
csw.getrecords2(constraints=[ filter1 ],maxrecords=100,esn='full')
print(len(csw.records.keys()))
for rec in list(csw.records.keys()):
    print(csw.records[rec].identifier)
