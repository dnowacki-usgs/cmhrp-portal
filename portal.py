def acdd_attrs(ds):
    # stuff for ACDD
    ds.attrs['creator_url'] = 'https://www.usgs.gov/'
    ds.attrs['publisher_url'] = 'https://www.usgs.gov/'
    ds.attrs['source'] = 'USGS'
    ds.attrs['geospatial_lat_min'] = ds['latitude'].min().values
    ds.attrs['geospatial_lat_max'] = ds['latitude'].max().values
    ds.attrs['geospatial_lon_min'] = ds['longitude'].min().values
    ds.attrs['geospatial_lon_max'] = ds['longitude'].max().values

    return ds

standard_names = {'P_1': 'sea_water_pressure',
                  'Tz': 'sea_surface_wave_mean_period',
                  'wp_peak': 'sea_surface_wave_period_at_variance_spectral_density_maximum',
                  'Hmean': 'sea_surface_wave_mean_height',
                  'H10': 'sea_surface_wave_mean_height_of_highest_tenth',
                  'u_1205': 'eastward_sea_water_velocity',
                  'v_1206': 'northward_sea_water_velocity',
                  'w_1204': 'upward_sea_water_velocity',
                  'P_4023': 'sea_water_pressure_due_to_sea_water',
                  'T_28': 'sea_water_temperature',
                  'C_51': 'sea_water_electrical_conductivity',
                  'S_41': 'sea_water_salinity',
                  'Trb1_980': 'sea_water_turbidity',
                  'Trb_980': 'sea_water_turbidity',
                  'SED_981': 'mass_concentration_of_suspended_matter_in_sea_water',
                  'Ptch_1216': 'platform_pitch_angle',
                  'Roll_1217': 'platform_roll_angle',
                  'Hdg_1215': 'platform_orientation',
                  'SDP_850': 'sea_water_pressure',
                  'z': 'height'}

long_names = {'burst': 'Burst number'}

cell_methods = {'SDP_850': 'time: standard_deviation'}

def assign_standard_names(ds):
    # drop all vars without a standard_name
    for d in ds.data_vars:
        if (d not in standard_names) and (d not in long_names):
            ds = ds.drop(d)

    for k in standard_names:
        if k in ds:
            if 'standard_name' not in ds[k].attrs:
                ds[k].attrs['standard_name'] = standard_names[k]
    for k in cell_methods:
        if k in ds:
            if 'cell_methods' not in ds[k].attrs:
                ds[k].attrs['cell_methods'] = cell_methods[k]

    if 'T_28' in ds:
        if ds['T_28'].attrs['units'] == 'C':
            ds['T_28'].attrs['units'] = 'degree_C'

    if 'burst' in ds:
        if ds['burst'].attrs['units'] == 'none':
            ds['burst'].attrs['units'] = '1'

    return ds
