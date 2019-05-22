#!/usr/bin/env python

import xarray as xr
import pandas as pd
import numpy as np
import sys
import stglib
# import matplotlib.pyplot as plt
import portal
# %load_ext autoreload
# %autoreload 2
# %%

if len(sys.argv) < 2:
    raise SystemExit('Please specify a filename')
else:
    filnam = sys.argv[1]

fildir = 'pcmsc/NMBTimeSeriesData/'

# filnam = 'NMB14M1T01awWvs-p.nc'
# filnam = 'NMB14SCW01rbrWvs-p.nc'
# filnam = 'NMB15M1T03aqd.nc'
# filnam = 'NMB15SCW01rbrWvs-p.nc'

# %%

ds = xr.open_dataset(fildir + filnam, decode_times=False, decode_coords=False).load()
ds.close()
ds = stglib.utils.epic_to_cf_time(ds)
print(filnam)
if filnam == 'NMB14M1T01awWvs-p.nc':
    # some bad data at the ends of the file...
    ds = ds.sel(time=slice('2014-11-10 17:30', '2015-04-09 21:00'))
    # round time to the nearest second to avoid weird netCDF datetime64 error
    ds['time'] = ds['time'].dt.round(freq='S')
    ds.attrs['featureType'] = 'timeSeries'
elif filnam == 'NMB14SCW01rbrWvs-p.nc':
    ds['time'] = ds['time'].dt.round(freq='S')
    ds.attrs['featureType'] = 'timeSeries'
elif filnam == 'NMB15SCW01rbrWvs-p.nc':
    ds['time'] = ds['time'].dt.round(freq='S')
    ds.attrs['featureType'] = 'timeSeries'
elif filnam == 'NMB15M1T03aqd.nc':
    ds['time'] = ds['time'].dt.round(freq='S')
    ds.attrs['featureType'] = 'timeSeriesProfile'
    # these are empty strings
    ds['u_1205'].attrs.pop('valid_range')
    ds['v_1206'].attrs.pop('valid_range')
    ds['w_1204'].attrs.pop('valid_range')

ds.attrs['title'] = (f'Time-Series data on currents, waves and sediment '
                      'transport off Santa Cruz, CA, 2014-2015: Site {}'
                      ).format(ds.attrs['Site'])

# CF Compliance
ds = ds.squeeze()  # don't index by latitude and longitude
ds['z'] = ds['depth'] - ds.attrs['initial_instrument_height']
ds['z'].attrs['positive'] = 'down'

ds.attrs['Conventions'] = 'CF-1.6, ACDD-1.3'

standard_names = {'wh_4061': 'sea_surface_wave_significant_height',
                  'Tz': 'sea_surface_wave_mean_period',
                  'wp_peak': 'sea_surface_wave_period_at_variance_spectral_density_maximum',
                  'Hmean': 'sea_surface_wave_mean_height',
                  'H10': 'sea_surface_wave_mean_height_of_highest_tenth',
                  'u_1205': 'eastward_sea_water_velocity',
                  'v_1206': 'northward_sea_water_velocity',
                  'w_1204': 'upward_sea_water_velocity',
                  'P_4023': 'sea_water_pressure_due_to_sea_water',
                  'Trb1_980': 'sea_water_turbidity',
                  'Ptch_1216': 'platform_pitch_angle',
                  'Roll_1217': 'platform_roll_angle',
                  'Hdg_1215': 'platform_orientation',
                  'z': 'height'}

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
ds['longitude'].attrs['axis'] = 'X'
ds['latitude'].attrs['axis'] = 'Y'

# drop all vars without a standard_name
for d in ds.data_vars:
    if d not in standard_names:
        ds = ds.drop(d)

for k in standard_names:
    if k in ds:
        if 'standard_name' not in ds[k].attrs:
            ds[k].attrs['standard_name'] = standard_names[k]

ds['time'].encoding['dtype'] = 'i4'
ds['time'].attrs['standard_name'] = 'time'

ds['feature_type_instance'] = filnam.split('.')[0]
ds['feature_type_instance'].attrs['cf_role'] = 'timeseries_id'

# ADD STUFF FOR PORTAL COMPATIBILITY
# see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
ds.attrs['experiment_id'] = filnam[0:5]
ds.attrs['metadata_link'] = 'https://doi.org/10.5066/F71C1W36'
# already have MOORING
ds.attrs['id'] = filnam.split('.')[0]
ds.attrs['datasetID'] = filnam.split('.')[0]
ds.attrs['project'] = 'CMG_Portal'

# ERDDAP
ds.attrs['cdm_timeseries_variables'] = 'feature_type_instance, latitude, longitude'

# for d in ds:
#     print(d)
#     if 'coordinates' in ds[d].attrs:
#         print(d, 'has coords')
#         ds[d].attrs.pop('coordinates')
# for d in ds.data_vars:
#     if d not in ['water_depth',
#                  'feature_type_instance',
#                  'z',
#                  'latitude',
#                  'longitude']:
#         ds[d].attrs['coordinates'] = 'time z latitude longitude'

# ACDD stuff
portal.acdd_attrs(ds)
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

ds.to_netcdf(fildir + 'clean/' + filnam)
