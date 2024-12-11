import xarray as xr
import numpy as np
import netCDF4 as nc4
ds = xr.open_dataset('http://geoport.whoi.edu/thredds/dodsC/silt/usgs/Projects/stellwagen/CF-1.6/EUROSTRATAFORM/7031adc-a.nc')

# %%
np.__version__
nc4.__version__
with nc4.Dataset('http://geoport.whoi.edu/thredds/dodsC/silt/usgs/Projects/stellwagen/CF-1.6/EUROSTRATAFORM/7031adc-a.nc') as nc:
    # assert nc.original_folder == project
    # assert nc.original_filename == ncfile
    assert nc.MOORING == 703
    # assert nc.id == os.path.splitext(ncfile)[0]
    assert 'u_1205' in nc.variables
    assert 'latitude' in nc.variables
    assert 'longitude' in nc.variables
    assert 'z' in nc.variables
    assert nc.variables['z'].positive == 'up'

    assert np.isclose(nc.variables['longitude'][:], 13.8795)
    assert np.isclose(nc.variables['latitude'][:], 43.3331)
    # Make sure it was sorted and converted to positive "up" (from "down")
    assert np.allclose(nc.variables['z'][:],
                       np.asarray([14.204893, 13.454893, 12.704893, 11.954893, 11.204893, 10.454894,
                                   9.704894,  8.954894,  8.204894,  7.454894,  6.704894,  5.954894,
                                   5.204894,  4.454894,  3.704894,  2.954893,  2.204893,  1.4548931]) * -1)
    assert 'z' in nc.variables['u_1205'].dimensions
    assert np.allclose(nc.variables['u_1205'][0, :],
                           np.asarray([0.09832777, 0.11781799, 0.113214445, 0.1127844, 0.11278457, 0.11321489,
                                       0.11058952, 0.10837395, 0.11536535, 0.10108161, 0.09856583, 0.12186166,
                                       0.113773575, 0.12351909, 0.12192587, 0.11469815, 0.12418562, 0.08060351]))
    print(nc.variables['u_1205'][0, :])
    print('done')

assert np.allclose(ds.u_1205[0,:],
                   np.asarray([0.09832777, 0.11781799, 0.113214445, 0.1127844, 0.11278457, 0.11321489,
                   0.11058952, 0.10837395, 0.11536535, 0.10108161, 0.09856583, 0.12186166,
                   0.113773575, 0.12351909, 0.12192587, 0.11469815, 0.12418562, 0.08060351]))

assert np.allclose(nc.variables['u_1205'][0, :],
                       np.asarray([0.09832777, 0.11781799, 0.113214445, 0.1127844, 0.11278457, 0.11321489,
                                   0.11058952, 0.10837395, 0.11536535, 0.10108161, 0.09856583, 0.12186166,
                                   0.113773575, 0.12351909, 0.12192587, 0.11469815, 0.12418562, 0.08060351]))
