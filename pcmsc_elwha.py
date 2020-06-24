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
# %%
fildir = 'pcmsc/elwha_west_mooring_time_series/'

filnam =  'ELW14B9M02bl.nc'

ds = xr.load_dataset(fildir + filnam, decode_times=False)
ds = stglib.utils.epic_to_cf_time(ds)

# round time to the nearest second to avoid weird netCDF datetime64 error
ds['time'] = ds['time'].dt.round(freq='S')


ds.attrs['title'] = '{}: {}: {}'.format(ds.attrs['PROGRAM'], ds.attrs['PROJECT'], ds.attrs['EXPERIMENT'])
if 'history' not in ds.attrs:
    ds.attrs['history'] = 'Generated using pcmsc_elwhat.py'
if 'summary' not in ds.attrs:
    ds.attrs['summary'] = """First Release: Aug 2017
Revised: May 2018 (ver. 1.1)

Time-series data of velocity, pressure, turbidity, conductivity, and temperature were collected near the mouth of the Elwha River, Washington, USA, from December 2010 through October 2014, for the Department of Interior’s Elwha River Restoration project. As part of this project, the U.S. Geological Survey studied the effects of renewed sediment supplies on the coastal ecosystems before, during, and following the removal of two dams, Elwha and Glines Canyon, from the Elwha River. Removal of the dams reintroduced sediment stored in the reservoirs to the river, and the river moved much of this sediment to the coast.

Several benthic tripods were instrumented with oceanographic sensors to collect the time-series data. Initial deployment in December 2010 consisted of one tripod about 1 km east of the Elwha River mouth (Tripod A). In March of 2011, an identical tripod (Tripod B) was placed about 1 km west of the river mouth. A mooring was added to the western site in July 2012 to measure turbidity and conductivity near the surface. A third tripod was placed in deeper water (50 m) directly offshore of the river mouth in an attempt to characterize sediment gravity flows near the seafloor if they occurred (Tripod C). Exceptional sedimentation was observed near the original tripod site A during the winter of 2013-2014. As a result, the tripod was relocated further east in April 2013 and renamed Tripod D.

Please check metadata and instrument information carefully for applicable time periods of specific data, as individual instrument deployment times and duration of the time series vary.

The naming convention for the NetCDF files included in this release is a 12-character alphanumeric code (ELWYYJKLNNXX.nc) where:

ELW is a 3-digit alphabetic-code for this experiment located at the mouth of the Elwha River
YY is the 2 digit year at the time of deployment
J is the location with respect to the river mouth [A, East (December 2010 to April 2013); B, West; C, Offshore; D, East (April 2013 to March 2014)]
K is the deployment number (1-9; beginning and ending dates of each deployment are given below)
L is the instrument package type (T, tripod; M, surface mooring)
NN indicates the position of instrument on the surface mooring (01, nearest the surface; NN increases with depth)
XX denotes the instrument or data type (wh, RDInstruments ADCP current data; wv, RDInstruments ADCP derived wave parameters; nx, Falmouth Scientific NXIC CTD; aq, Aquatec Aqualogger OBS; bl, RBR, Ltd CTD; sc, SeaBird Electonics SBE16+ CT)

Some derived parameters are included in these data.

Deployment dates:
1. Dec 2010 to Mar 2011
2. Mar 2011 to Sep 2011
3. Sep 2011 to Mar 2012
4. Mar 2012 to Aug 2012
5. Aug 2012 to Jan 2013
6. Jan 2013 to Jun 2013
7. Jun 2013 to Dec 2013
8. Dec 2013 to Mar 2014
9. Mar 2014 to Oct 2014"""

if 'keywords' not in ds.attrs:
    ds.attrs['keywords'] = "oceanography, sediment transport"

ds.attrs['featureType'] = 'timeSeries'
ds = ds.squeeze()

# CF Compliance
# ds = ds.squeeze()  # don't index by latitude and longitude
# if 'aq' in filnam:
#     ds = ds.rename({'depth': 'z'})
# else:

ds['z'] = ds['depth'] - ds.attrs['initial_instrument_height']
ds['depth'].attrs['long_name'] = 'nominal water depth'
ds['depth'].attrs['units'] = 'm'
ds['z'].attrs['positive'] = 'down'
ds['z'].attrs['long_name'] = 'depth of sensor below nominal water level'


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
ds['latitude'].attrs['units'] = 'degrees_north'

# drop all vars without a standard_name
for d in ds.data_vars:
    if d not in standard_names:
        ds = ds.drop(d)

for k in standard_names:
    if k in ds:
        if 'standard_name' not in ds[k].attrs:
            ds[k].attrs['standard_name'] = standard_names[k]

ds['feature_type_instance'] = filnam.split('.')[0]
ds['feature_type_instance'].attrs['cf_role'] = 'timeseries_id'

for k in ds.data_vars:
    ds[k].attrs['coverage_content_type'] = 'physicalMeasurement'

# ADD STUFF FOR PORTAL COMPATIBILITY
# see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
ds.attrs['experiment_id'] = filnam[0:5]
ds.attrs['metadata_link'] = 'https://doi.org/10.5066/F7CR5RW8'
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

print(ds.data_vars)
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
portal.acdd_attrs(ds)
if 'CREATION_DATE' in ds.attrs:
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

Path(fildir + 'clean').mkdir(parents=True, exist_ok=True)
ds.to_netcdf(fildir + 'clean/' + filnam)

# %%
# Load all available checker classes
# check_suite = CheckSuite()
# check_suite.load_all_available_checkers()
# path = fildir + 'clean/' + filnam
# checker_names = [ 'cf:1.6']
# # checker_names = ['cf:1.6']
# return_value, errors = ComplianceChecker.run_checker(path, checker_names, 0, 'normal')
