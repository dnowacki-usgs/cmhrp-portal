#!/usr/bin/env python

import netCDF4 as nc4
import numpy as np
import shutil

shutil.copy('10661sc-a.nc', 'tmpout.nc')

with nc4.Dataset('tmpout.nc', 'r+') as nc:
    print(nc.variables['lat'])
    print(nc.variables['lat'][:])
    nc.variables['lat'][:] = 43.7158
    print(nc.variables['lat'])
    print(nc.variables['lat'][:])
    print(nc.latitude)
    nc.latitude = np.float32(43.7158)
    print(nc.latitude)
    print(nc.history)
    nc.history = '2019-12-19 correct lat from 42 to 43. ' + nc.history
    print(nc.history)
