#!/usr/bin/env python
"""
Station: PV_SHELF-405 File: 4054_a Variable: CS_300 Min: -1.0650293282877492e+36 Max: 3.162729106918337e+31
Station: PV_SHELF-405 File: 4054_a Variable: v_1206 Min: -1.1178265858361426e+32 Max: 5.983635668543551e+35
Station: MOBILE_BAY-382 File: 3821c1_a Variable: u_1 Min: -26586806.0 Max: 2.7130894497679724e+21
Station: MOBILE_BAY-382 File: 3821c1_a Variable: v_1 Min: -4.283303892440862e+29 Max: 4.313485700526215e+33
Station: MOBILE_BAY-382 File: 3821c1_a Variable: vdir_1 Min: -1.2158234653202842e+17 Max: 1.6325662998427337e+20
Station: MOBILE_BAY-382 File: 3821c1_a Variable: vspd_1 Min: -6.374803362139921e+29 Max: 1.36866725019794e+34
Station: MONTEREY_CAN-423 File: 4232_a Variable: north Min: -4.690559166401244e+35 Max: 9.830113441009513e+34
Station: MONTEREY_CAN-423 File: 4232_a Variable: vdir_1 Min: -1.909518192662842e+36 Max: 5.0203310340929727e+30
Station: MONTEREY_CAN-423 File: 4232_a Variable: vspd_1 Min: -1.0033746653597897e+28 Max: 9.704381217572842e+31
Station: MONTEREY_CAN-423 File: 4233_a Variable: east Min: -1.10532968388858e+36 Max: 1.656462646521778e+26
Station: MONTEREY_CAN-423 File: 4233_a Variable: north Min: -2.418328741320399e+35 Max: 6.817040671439224e+34
Station: MONTEREY_CAN-423 File: 4233_a Variable: vdir_1 Min: -5.236318961195026e+21 Max: 6.782978503670278e+34
Station: MONTEREY_CAN-423 File: 4233_a Variable: vspd_1 Min: -8.251543182248411e+33 Max: 1.42824314553705e+33
Station: MONTEREY_CAN-424 File: 4241_a Variable: north Min: -3.049452163022371e+35 Max: 9.069862827589632e+16
Station: MONTEREY_CAN-424 File: 4241_a Variable: vdir_1 Min: -5.693194362311173e+31 Max: 8.07327084757066e+28
Station: MONTEREY_CAN-424 File: 4241_a Variable: vspd_1 Min: -1.7013923064471958e+36 Max: 3.479935302350112e+20
Station: MONTEREY_CAN-424 File: 4242_a Variable: vdir_1 Min: -6.87253413639644e+36 Max: 3.535488932891934e+36
Station: MONTEREY_CAN-424 File: 4242_a Variable: vspd_1 Min: -6.679273196488045e+35 Max: 6.123183821206039e+33
"""

import urllib
import netCDF4 as nc4
import numpy as np
import shutil
nc4.default_fillvals

rooturl = 'https://stellwagen.er.usgs.gov/DATAFILES/'
files = ['PV_SHELF/4054-a.nc',
         'MOBILE_BAY/3821c1-a.cdf',
         'MONTEREY_CAN/4232-a.cdf',
         'MONTEREY_CAN/4233-a.cdf',
         'MONTEREY_CAN/4241-a.cdf',
         'MONTEREY_CAN/4242-a.cdf']

for file in files:
    filnam = file.split('/')[1]
    urllib.request.urlretrieve(rooturl + file, 'stellwagen/' + filnam)

# %%

for file in files:
    filnam = file.split('/')[1]
    shutil.copy('stellwagen/' + filnam, 'stellwagen/fix' + filnam)
    with nc4.Dataset('stellwagen/fix' + filnam, 'r+') as nc:
        print(filnam)
        for v in nc.variables:
            badminmax = False
            bads = False
            if 'time' not in nc.variables[v].dimensions:
                continue
            if 'time' in v:
                continue
            if 'vdir' in v or 'bearing' in v:
                bads = (nc.variables[v][:] < 0) | (nc.variables[v][:] > 360)
                badminmax = np.any(bads)
            elif 'vspd' in v:
                bads = (nc.variables[v][:] < 0) | (nc.variables[v][:] > 500)
                badminmax = np.any(bads)
            elif 'east' in v or 'north' in v or 'u_1' in v or 'v_1' in v:
                bads = (nc.variables[v][:] < -200) | (nc.variables[v][:] > 200)
                badminmax = np.any(bads)
            else:
                bads = (nc.variables[v][:] < -1e19) | (nc.variables[v][:] > 1e19)
                badminmax = np.any(bads)
            print(v, nc.variables[v][:].min(), nc.variables[v][:].max())
            print(np.sum(bads))
            if badminmax:
                print(np.where(bads.squeeze()))
                print(badminmax)
                nc.variables[v][np.squeeze(bads), :, :, :] = np.nan
                print(nc.history)
                nc.history = '2020-01-17 Remove erroneous min/max values in ' + v + '. ' + nc.history
                print(nc.history)

# %%
""" check our work """

import matplotlib.pyplot as plt

for file in [files[1]]:
    filnam = file.split('/')[1]
    with nc4.Dataset('stellwagen/fix' + filnam, 'r') as ncfix:
        with nc4.Dataset('stellwagen/' + filnam, 'r') as ncbad:
            for v in ncfix.variables:
                if 'time' in v:
                    continue
                if 'time' not in ncfix.variables[v].dimensions:
                    continue
                plt.figure()
                plt.plot(ncbad[v][:].squeeze())
                plt.plot(ncfix[v][:].squeeze())
                plt.title(v)
                plt.ylim(-500,500)
