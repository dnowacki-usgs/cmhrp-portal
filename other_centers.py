#!/usr/bin/env python

import xarray as xr
import pandas as pd
import numpy as np
import sys
# %%
if len(sys.argv) < 2:
    raise SystemExit('Please specify a filename')
else:
    filnam = sys.argv[1]

# filnam = 'UFK14ArgE1495aqd-trm.nc'
# filnam = 'UFK14ArgE306aqd-trm.nc'
# %%
fildir = 'files/'
ds = xr.open_dataset(fildir + filnam).load()
ds.close()

if filnam == 'UFK14Aqua1571aqc-trm.nc':
    site = 'Aqua'
elif filnam == 'UFK14ArgE306aqd-trm.nc':
    site = 'S1'
elif filnam == 'UFK14ArgE1495aqd-trm.nc':
    site = 'S2'
elif filnam == 'UFK14RBR77750p-trm.nc':
    site = 'RBR'

if 'title' not in ds.attrs:
    ds.attrs['title'] = ('Ocean Currents and Pressure Time Series at the '
                         'Upper Florida Keys: Crocker Reef, FL: Site {}').format(site)

if 'Conventions' not in ds.attrs:
    ds.attrs['Conventions'] = 'CF-1.6, ACDD-1.3'

standard_names = {'latitude': 'latitude',
                  'longitude': 'longitude',
                  'velocity_north': 'northward_sea_water_velocity',
                  'velocity_east': 'eastward_sea_water_velocity',
                  'velocity_up': 'upward_sea_water_velocity',
                  'sound_speed': 'speed_of_sound_in_sea_water',
                  'heading': 'platform_orientation',
                  'roll': 'platform_roll_angle',
                  'pitch': 'platform_pitch_angle',
                  'speed': 'sea_water_speed',
                  'direction': 'sea_water_to_direction',
                  'temp': 'sea_water_temperature',
                  'time': 'time',
                  'pressure': 'sea_water_pressure_due_to_sea_water',
                  'z': 'height'}

# drop SNR1, SNR2, SNR3 from AQD as the units are in non-CF dB
for k in ['SNR1', 'SNR2', 'SNR3']:
    if k in ds:
        ds = ds.drop(k)

# fix degrees C -> degree_C
if 'temp' in ds:
    if 'units' in ds['temp'].attrs:
        ds['temp'].attrs['units'] = 'degree_C'

# fix featuretype typo
if 'featureType' in ds.attrs:
    if ds.attrs['featureType'] == 'timeSeries Profile':
        ds.attrs['featureType'] = 'timeSeriesProfile'

for k in standard_names:
    if k in ds:
        if 'standard_name' not in ds[k].attrs:
            ds[k].attrs['standard_name'] = standard_names[k]

# ds.attrs['cdm_data_type'] = 'TimeSeries'
ds.attrs['cdm_timeseries_variables'] = 'feature_type_instance, latitude, longitude'

# remove sta, Z, and sensor_depth dims
if (filnam == 'UFK14ArgE306aqd-trm.nc') or (filnam == 'UFK14ArgE1495aqd-trm.nc'):
    squeezevars = ['sta', 'sensor_depth']
    ds = ds.squeeze([x for x in squeezevars if x in ds.dims])
else:
    squeezevars = ['sta', 'Z', 'sensor_depth']
    ds = ds.squeeze([x for x in squeezevars if x in ds.dims])

if filnam == 'UFK14Aqua1571aqc-trm.nc':
    ds = ds.set_coords('z')
    ds = ds.assign_coords(z=ds['z'])
elif (filnam == 'UFK14ArgE306aqd-trm.nc') or (filnam == 'UFK14ArgE1495aqd-trm.nc'):
    ds = ds.set_coords('z')
    ds = ds.assign_coords(z=ds['z'])
    ds = ds.swap_dims({'Z': 'z'})
    # sort z ascending
    ds = ds.sortby('z')

ds['z'].attrs['positive'] = 'down'
if filnam == 'UFK14Aqua1571aqc-trm.nc':
    # we lose z attrs after the expand_dims(), so make a backup and reassign
    attrs = ds['z'].attrs
    for v in ['velocity_east',
              'velocity_north',
              'velocity_up',
              'amplitude_beam1',
              'amplitude_beam2',
              'amplitude_beam3',
              'speed',
              'direction']:
        if v in ds:
            ds[v] = ds[v].expand_dims('z')
    ds['z'].attrs = attrs

# put time first
for d in ds.data_vars:
    if 'time' in ds[d].dims:
        dims = [k for k in ds[d].dims if k != 'time']
        dims.insert(0, 'time')
        dims = tuple(dims)
        ds[d] = ds[d].transpose(*dims)
    if d not in ['water_depth',
                 'feature_type_instance',
                 'z',
                 'latitude',
                 'longitude']:
        ds[d].attrs['coordinates'] = 'time z latitude longitude'

# ds.attrs['infoUrl'] = 'https://www.usgs.gov/'
# ds.attrs['institution'] = 'USGS'

# CF: Coordinate variables cannot have _FillValue
for d in ds.coords:
    ds[d].encoding['_FillValue'] = None
# no _FillValue for lat, lon just to be safe
for d in ['latitude', 'longitude']:
    ds[d].encoding['_FillValue'] = None

# CF: Add axis attr
ds['time'].attrs['axis'] = 'T'
ds['z'].attrs['axis'] = 'Z'
ds['longitude'].attrs['axis'] = 'X'
ds['latitude'].attrs['axis'] = 'Y'

# ADD STUFF FOR PORTAL COMPATIBILITY
# see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
ds.attrs['experiment_id'] = 'UFK14'
ds.attrs['metadata_link'] = 'https://doi.org/10.5066/F7VD6XBF'
if filnam == 'UFK14Aqua1571aqc-trm.nc':
    ds.attrs['MOORING'] = 'UFK14Aqua'
    ds.attrs['featureType'] = 'timeSeriesProfile'
elif filnam == 'UFK14RBR77750p-trm.nc':
    ds.attrs['MOORING'] = 'UFK14RBR'
elif filnam == 'UFK14ArgE306aqd-trm.nc':
    ds.attrs['MOORING'] = 'UFK14S1'
elif filnam == 'UFK14ArgE1495aqd-trm.nc':
    ds.attrs['MOORING'] = 'UFK14S2'
ds.attrs['id'] = filnam.split('.')[0]
ds.attrs['project'] = 'CMG_Portal'

if 'Arg' in filnam:
    # add a profile_id for erddap for Argonauts
    ds['profile_index'] = xr.DataArray(np.arange(len(ds.time)), dims='time')
    ds['profile_index'].attrs['cf_role'] = 'profile_id'
    ds['profile_index'].encoding['dtype'] = 'i4'  # don't output as long int
    ds.attrs['cdm_profile_variables'] = 'profile_index'


portal.acdd_attrs(ds)

for k in ['date_created', 'time_coverage_start', 'time_coverage_end']:
    ds.attrs[k] = pd.Timestamp(ds.attrs[k]).isoformat()
ds.attrs['time_coverage_duration'] = (
    pd.Timestamp(ds.attrs['time_coverage_end']) -
    pd.Timestamp(ds.attrs['time_coverage_start'])).isoformat()
ds.attrs['time_coverage_resolution'] = pd.Timedelta(
    ds.time.diff(dim='time').median().values).isoformat()
ds['longitude']
ds.to_netcdf(fildir + 'clean/' + filnam)
