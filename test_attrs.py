import xarray as xr

filnams = ['UFK14Aqua1571aqc-trm.nc',
           # 'UFK14ArgE1495aqd-trm.nc',
           # 'UFK14ArgE306aqd-trm.nc',
           # 'UFK14RBR77750p-trm.nc']
           ]

urlbase = 'http://geoport.whoi.edu/thredds/dodsC/sand/usgs/users/dnowacki/doi-F7VD6XBF/'
# %%

ds['velocity_up'].attrs
for filnam in filnams:
    print(filnam)
    ds = xr.open_dataset(urlbase + filnam, decode_cf=False).load()
    ds.close()
    # with xr.open_dataset(urlbase + filnam) as ds:
    for v in ['experiment_id', 'MOORING', 'metadata_link', 'id']:
        print(v, ds.attrs[v])

    for dv in ds.data_vars:
        for v in ['coordinates', 'standard_name', 'units']:
            if v in ds[dv].attrs:
                print(dv, v, ds[dv].attrs[v])
            else:
                print(dv, v, 'NOT PRESENT')
