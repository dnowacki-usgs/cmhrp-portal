def acdd_attrs(ds):
  # stuff for ACDD
  ds.attrs['creator_url'] = 'https://www.usgs.gov/'
  ds.attrs['publisher_url'] = 'https://www.usgs.gov/'
  ds.attrs['source'] = 'USGS'
  ds.attrs['geospatial_lat_min'] = ds['latitude'].min().values
  ds.attrs['geospatial_lat_max'] = ds['latitude'].max().values
  ds.attrs['geospatial_lon_min'] = ds['longitude'].min().values
  ds.attrs['geospatial_lon_max'] = ds['longitude'].max().values
