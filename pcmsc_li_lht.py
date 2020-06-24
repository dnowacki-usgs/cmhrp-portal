#!/usr/bin/env python

import xarray as xr
import pandas as pd
import numpy as np
import sys
import stglib
# import matplotlib.pyplot as plt
import portal
from compliance_checker.runner import ComplianceChecker, CheckSuite
from pathlib import Path
# %load_ext autoreload
# %autoreload 2

# %%

if len(sys.argv) < 2:
    raise SystemExit('Please specify a filename')
else:
    filnam = sys.argv[1]

fildir = './'
# fildir = 'pcmsc/DL115LWA/'

# filnam = 'NMB14M1T01awWvs-p.nc'
# filnam = 'NMB14SCW01rbrWvs-p.nc'
# filnam = 'NMB15M1T03aqd.nc'
# filnam = 'NMB15SCW01rbrWvs-p.nc'
# filnam = 'DL115LWArbr-s.nc'
# filnam = 'DL115LWAvir.nc'
# %%

ds = xr.load_dataset(fildir + filnam, decode_times=False)
ds = stglib.utils.epic_to_cf_time(ds)
print(ds.data_vars)

# round time to the nearest second to avoid weird netCDF datetime64 error
ds['time'] = ds['time'].dt.round(freq='S')
# ds.attrs['featureType'] = 'timeSeries'

ds.attrs['title'] = '{}: {}'.format(ds.attrs['PROGRAM'], ds.attrs['PROJECT'])
ds.attrs['history'] = 'Generated using pcmsc_li_lht.py'
ds.attrs['summary'] = """Water depth and turbidity time-series data were collected in Little Holland Tract (LHT) from 2015 to 2017. Depth (from pressure) was measured in high-frequency (6 or 8 Hz) bursts. Burst means represent tidal stage, and burst data can be used to determine wave height and period. The turbidity sensors were calibrated to suspended-sediment concentration measured in water samples collected on site. The calibration and fit parameters for all of the turbidity sensors used in the study are tabulated and provided with the data. Data were sequentially added to this data release as they were collected and post-processed.

Typically, each zip folder for a deployment period contains one file from an optical backscatter sensor and two files of data from a bursting pressure sensor.
---------
Data were collected from several sites in Little Holland Tract (LHT) and Liberty Island (LI), including the Liberty Island Conservation Bank (LICB), from 2015 to 2017. Table 1 (below) lists the deployment name (DLXXX) and dates for each sampling station location. Station names starting with ‘H’ are in LHT; station names starting with ‘L’ are in LI, and the station name starting with ‘W’ is in LICB. At stations with a ‘W’ as the second character of the station name, we collected water-level, wind-wave, and turbidity time-series data. At stations with a ‘V’ as the second character of the station name, we collected water-level, wind-wave, and turbidity, as well as velocity time-series data. The turbidity sensors were calibrated to suspended-sediment concentration measured in water samples collected on site (tables 2a,b) for LHT and LI. Details on instrumentation and sampling are included on the individual pages for each station (see links below). Data were sequentially added to this data release as they were retrieved and post-processed."""
ds.attrs['keywords'] = "oceanography, sediment transport"

ds.attrs['featureType'] = 'timeSeries'
ds = ds.squeeze()

# CF Compliance
# ds = ds.squeeze()  # don't index by latitude and longitude
ds = ds.rename({'depth': 'z'})
ds['z'].attrs['positive'] = 'down'
ds['z'].attrs['long_name'] = 'depth of sensor below mean water level'

ds.attrs['Conventions'] = 'CF-1.6, ACDD-1.3'

ds = ds.rename({'lon': 'longitude', 'lat': 'latitude'})

ds['longitude'].attrs['standard_name'] = 'longitude'
ds['latitude'].attrs['standard_name'] = 'latitude'
ds['longitude'].attrs['long_name'] = 'sensor longitude'
ds['latitude'].attrs['long_name'] = 'sensor latitude'

for d in ds.coords:
    ds[d].encoding['_FillValue'] = None
# no _FillValue for lat, lon just to be safe
for d in ['latitude', 'longitude']:
    ds[d].encoding['_FillValue'] = None

# CF: Add axis attr
ds['time'].attrs['axis'] = 'T'
if 'z' in ds:
    ds['z'].attrs['axis'] = 'Z'
    ds['z'].attrs['units'] = 'm'
ds['longitude'].attrs['axis'] = 'X'
ds['latitude'].attrs['axis'] = 'Y'

ds = portal.assign_standard_names(ds)


ds['feature_type_instance'] = filnam.split('.')[0]
ds['feature_type_instance'].attrs['cf_role'] = 'timeseries_id'

for k in ds.data_vars:
    ds[k].attrs['coverage_content_type'] = 'physicalMeasurement'

# ADD STUFF FOR PORTAL COMPATIBILITY
# see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
ds.attrs['experiment_id'] = filnam[0:5]
ds.attrs['metadata_link'] = 'https://doi.org/10.5066/F73R0R07'
# already have MOORING
ds.attrs['id'] = filnam.split('.')[0]
ds.attrs['datasetID'] = filnam.split('.')[0]
ds.attrs['project'] = 'CMG_Portal'

# ERDDAP
ds.attrs['cdm_timeseries_variables'] = 'feature_type_instance, latitude, longitude'

def remove_problematic_attrs(ds):
    for variable in ds.variables.values():
        if 'coordinates' in variable.attrs:
            del variable.attrs['coordinates']

remove_problematic_attrs(ds)

for d in ds.data_vars:
    if d not in ['water_depth',
                 'feature_type_instance',
                 'z',
                 'latitude',
                 'longitude']:
        if 'z' in ds[d].coords:
            ds[d].attrs['coordinates'] = 'time z latitude longitude'
        else:
            ds[d].attrs['coordinates'] = 'time latitude longitude'

# ACDD stuff
ds = portal.acdd_attrs(ds)
ds.attrs['date_created'] = pd.Timestamp(ds.attrs['CREATION_DATE']).isoformat()
ds.attrs['time_coverage_start'] = pd.Timestamp(ds['time'][0].values).isoformat()
ds.attrs['time_coverage_end'] = pd.Timestamp(ds['time'][-1].values).isoformat()
ds.attrs['time_coverage_duration'] = (
    pd.Timestamp(ds.attrs['time_coverage_end']) -
    pd.Timestamp(ds.attrs['time_coverage_start'])).isoformat()
ds.attrs['time_coverage_resolution'] = pd.Timedelta(
    ds.time.diff(dim='time').median().values).isoformat()
ds.attrs['standard_name_vocabulary'] = 'CF Standard Name Table v66'
ds.attrs['naming_authority'] = 'gov.usgs.cmgp'
ds.attrs['institution'] = 'USGS Coastal and Marine Geology Program'

ds['time'].attrs['long_name'] = 'time of measurement'
ds['time'].encoding['dtype'] = 'i4'
ds['time'].attrs['standard_name'] = 'time'

# check for 0-length attributes (this causes problems with ERDDAP) and set to an empty string
for k in ds.attrs:
    if isinstance(ds.attrs[k], np.ndarray) and not ds.attrs[k].size:
        print(ds.attrs[k])
        print (k, ds.attrs[k].dtype, ds.attrs[k].size)
        print(ds.attrs[k])
        ds.attrs[k] = ''

print(ds.data_vars)
Path(fildir + 'clean').mkdir(parents=True, exist_ok=True)
ds.to_netcdf(fildir + 'clean/' + filnam)

# %%
# Load all available checker classes
# check_suite = CheckSuite()
# check_suite.load_all_available_checkers()
# path = fildir + 'clean/' + filnam
# checker_names = ['acdd', 'cf:1.6']
# # checker_names = ['cf:1.6']
# return_value, errors = ComplianceChecker.run_checker(path, checker_names, 0, 'normal')
