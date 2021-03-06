import os
import sys
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd
import stglib
import xarray as xr

import portal


def add_title_history(ds, doi, title, summary):
    if "id" in ds.attrs:
        titletxt = title + " - " + ds.attrs["id"]
    else:
        titletxt = title

    if "title" not in ds.attrs:
        ds.attrs["title"] = titletxt
    else:
        ds.attrs["title"] = titletxt + "; Original title: " + ds.attrs["title"]

    if "history" in ds.attrs and (len(ds.attrs["history"]) > 0):
        histtext = ds.attrs["history"]
    else:
        histtext = ""

    ds.attrs["history"] = (
        "Imported from ScienceBase data release and converted to CF using process_"
        + doi
        + ".ipynb; "
        + histtext
    )

    if "summary" not in ds.attrs:
        ds.attrs["summary"] = summary
    else:
        ds.attrs["summary"] = summary + "; Original summary: " + ds.attrs["summary"]

    if "keywords" not in ds.attrs:
        ds.attrs["keywords"] = "oceanography, sediment transport"

    return ds


def spcmsc_assign(ds):
    for var in ds.data_vars:
        if "QF_" not in var:
            print(var)
            if np.issubdtype(ds[var].dtype, np.integer):
                ds[var] = ds[var].astype(float)
        
        if "QF_" in var:
            ds[var].attrs["long_name"] = "A numeric value that indicates the quality of the reported data"
            ds[var].attrs["comment"] = "Flag 1 = QC has been performed and element appears to be correct, Flag 2 = QC has been performed and element appears to be probably good with other elements, Flag 3 = QC has been performed and element appears to be probably bad, Flag 4 = QC has been performed and element appears to be bad, Flag 5 = the value has been modified as a result of QC, Flag 9 = The value of the element is missing."
            
            if ds[var].dtype == object:
                ds[var].encoding['dtype'] = 'S1'

                
    for var, qf in zip(['TW_C',  'PRESS_dbar', 'SALINITY',    'pHT',    'CO2ppm', 'PRESIRGA_mbar', 'OXYGEN_mg_L', 'PAR_microEinsteins'],
                       ['QF_TW', 'QF_PRESS',   'QF_SALINITY', 'QF_pHT', 'QF_CO2', 'QF_PRESIRGA',   'QF_OXYGEN',   'QF_PAR']):
        if ds[qf].dtype == int:
            ds[var][ds[qf] != 1] = np.nan
        elif ds[qf].dtype == object:
            goods = []
            for x in ds[qf].values:
                if '1' in x:
                    goods.append(True)
                else:
                    goods.append(False)
            goods = np.array(goods)
            ds[var][~goods] = np.nan
            
    ds["PRESIRGA_mbar"].attrs["long_name"] = "pressure in the sampling chamber of the infrared gas analyzer of the CO2 sensor"
    ds["PRESIRGA_mbar"].attrs["units"] = "mbar"
    ds["CO2ppm"].attrs["long_name"] = "concentration of CO2 in parts per million by volume."
    ds["CO2ppm"].attrs["units"] = "ppm"
    ds["PAR_microEinsteins"].attrs["long_name"] = "concentration of photosynthetically available radiation"
    ds["PAR_microEinsteins"].attrs["units"] = "microEinsteins"
    
    return ds


def convert(f, doi, title, summary, experiment_id=None, MOORING=None):
    csv = False
    if f[-4:] == '.csv':
        csv = True
        df = pd.read_csv(f)
        df['time'] = pd.DatetimeIndex(df['DATETAG EST'] + ' ' + df['TIMETAG EST']) + pd.Timedelta('5h') # EST to UTC
        df.set_index('time', inplace=True)
        ds = df.to_xarray()
        ds['longitude'] = xr.DataArray([ds['Longitude'][0]], dims='longitude')
        ds['latitude'] = xr.DataArray([ds['Latitude'][0]], dims='latitude')
        ds = ds.drop(['Longitude', 'Latitude'])
        for k in ds:
            ds = ds.rename({k: k.replace(' ', '_').replace('(', '').replace(')', '').replace('/','_')})
    else:
        try:
            ds = xr.load_dataset(f, decode_times=False)
            ds = stglib.utils.epic_to_cf_time(ds)
        except:
            # deal with 2D time (burst) data sets
            with netCDF4.Dataset(f, "r+") as nc:
                time = nc["time"][:]
            # xarray won't open a dataset with vars and coords of the same name
            ds = xr.open_dataset(f, decode_times=False, drop_variables="time")
            # assign time to be the first of the burst
            ds["time"] = xr.DataArray(
                stglib.utils.epic_to_datetime(time[:, 0], ds.time2[:, 0].values),
                dims="time",
            )

    dvorig = ds.data_vars

    # round time to the nearest second to avoid weird netCDF datetime64 error
    ds["time"] = ds["time"].dt.round(freq="S")

    ds = ds.squeeze()
    if "depth" in ds:  # depth not in waves files usually
        ds = ds.rename({"depth": "z"})
        if "positive" not in ds["z"].attrs:
            ds["z"].attrs["positive"] = "down"
        if "long_name" not in ds["z"].attrs:
            ds["z"].attrs["long_name"] = "depth of sensor below mean water level"

    ds.attrs["Conventions"] = "CF-1.6, ACDD-1.3"

    if "lon" in ds and "lat" in ds and "longitude" not in ds and "latitude" not in ds:
        ds = ds.rename({"lon": "longitude", "lat": "latitude"})
    elif "latitude" not in ds and "longitude" not in ds:
        ds["longitude"] = xr.DataArray([ds.attrs["longitude"]], dims="longitude")
        ds["latitude"] = xr.DataArray([ds.attrs["latitude"]], dims="latitude")

    for d in ds.coords:
        ds[d].encoding["_FillValue"] = None
    # no _FillValue for lat, lon just to be safe
    for d in ["latitude", "longitude"]:
        ds[d].encoding["_FillValue"] = None

    # CF: Add axis attr
    ds["time"].attrs["axis"] = "T"
    if "z" in ds:
        if "axis" not in ds["z"].attrs:
            ds["z"].attrs["axis"] = "Z"
        if "units" not in ds["z"].attrs:
            ds["z"].attrs["units"] = "m"
    ds["longitude"].attrs["axis"] = "X"
    ds["latitude"].attrs["axis"] = "Y"
    
    if csv:
        print(ds)
        ds = spcmsc_assign(ds)

    ds = portal.assign_standard_names(ds)

    ds["feature_type_instance"] = os.path.split(f)[1].split(".")[0]
    ds["feature_type_instance"].attrs["cf_role"] = "timeseries_id"

    for k in ds.data_vars:
        ds[k].attrs["coverage_content_type"] = "physicalMeasurement"

    # ADD STUFF FOR PORTAL COMPATIBILITY
    # see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
    if csv:
        ds.attrs["experiment_id"] = experiment_id
        if "MOORING" not in ds.attrs:
            ds.attrs["MOORING"] = MOORING
    else:
        ds.attrs["experiment_id"] = os.path.split(f)[1][0:5]
    ds.attrs["metadata_link"] = "https://doi.org/10.5066/" + doi
    # already have MOORING
    ds.attrs["id"] = os.path.split(f)[1].split(".")[0]
    ds.attrs["datasetID"] = os.path.split(f)[1].split(".")[0]
    ds.attrs["project"] = "CMG_Portal"
    ds = add_title_history(ds, doi, title, summary)

    # ERDDAP
    ds.attrs["cdm_timeseries_variables"] = "feature_type_instance, latitude, longitude"

    def remove_problematic_attrs(ds):
        for variable in ds.variables.values():
            if "coordinates" in variable.attrs:
                del variable.attrs["coordinates"]

    remove_problematic_attrs(ds)

    for d in ds.data_vars:
        if d not in [
            "water_depth",
            "feature_type_instance",
            "z",
            "latitude",
            "longitude",
        ]:
            if "z" in ds[d].coords:
                ds[d].attrs["coordinates"] = "time z latitude longitude"
            else:
                ds[d].attrs["coordinates"] = "time latitude longitude"

    # CF Compliance Stuff
    ds = portal.ensure_attr_dtype(ds)
    # ACDD stuff
    ds = portal.acdd_attrs(ds)
    # Ensure valid_range is valid
    ds = portal.ensure_valid_range(ds)
    if "CREATION_DATE" in ds.attrs:
        ds.attrs["date_created"] = pd.Timestamp(ds.attrs["CREATION_DATE"]).isoformat()
    else:
        ds.attrs["date_created"] = pd.Timestamp.now(tz="utc").isoformat()
    ds.attrs["time_coverage_start"] = pd.Timestamp(ds["time"][0].values).isoformat()
    ds.attrs["time_coverage_end"] = pd.Timestamp(ds["time"][-1].values).isoformat()
    ds.attrs["time_coverage_duration"] = (
        pd.Timestamp(ds.attrs["time_coverage_end"])
        - pd.Timestamp(ds.attrs["time_coverage_start"])
    ).isoformat()
    ds.attrs["time_coverage_resolution"] = pd.Timedelta(
        ds.time.diff(dim="time").median().values
    ).isoformat()
    ds.attrs["standard_name_vocabulary"] = "CF Standard Name Table v66"
    ds.attrs["naming_authority"] = "gov.usgs.cmgp"
    ds.attrs["institution"] = "USGS Coastal and Marine Geology Program"

    if len(ds.dims) == 1:
        ds.attrs["featureType"] = "timeSeries"
    elif len(ds.dims) == 2:
        ds.attrs["featureType"] = "timeSeriesProfile"
        ds["profile_index"] = xr.DataArray(range(len(ds["time"])), dims="time")
        ds["profile_index"].attrs["cf_role"] = "profile_id"
        ds["profile_index"].encoding["dtype"] = "i4"
    
    ds["time"].attrs["long_name"] = "time of measurement"
    ds["time"].encoding["dtype"] = "i4"
    ds["time"].attrs["standard_name"] = "time"

    # check for 0-length attributes (this causes problems with ERDDAP) and set to an empty string
    for k in ds.attrs:
        if isinstance(ds.attrs[k], np.ndarray) and not ds.attrs[k].size:
            ds.attrs[k] = ""

    dvfinal = ds.data_vars
    Path(os.path.split(f)[0] + "/clean").mkdir(parents=True, exist_ok=True)
    if f[-4:] == '.csv':
        ds.to_netcdf(os.path.split(f)[0] + "/clean/" + os.path.split(f)[1][:-4] + '.nc')
    else:
        ds.to_netcdf(os.path.split(f)[0] + "/clean/" + os.path.split(f)[1])

    return os.path.split(f)[1], "difference in data_vars:", (set(dvorig) ^ set(dvfinal))
