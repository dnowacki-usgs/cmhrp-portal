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
    if "title" not in ds.attrs:
        ds.attrs["title"] = title
    else:
        ds.attrs["title"] = title + "; Original title: " + ds.attrs["title"]

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
        ds.attrs["summary"] = """"""
    else:
        ds.attrs["summary"] = summary + "; Original summary: " + ds.attrs["summary"]

    ds.attrs["keywords"] = "oceanography, sediment transport"

    return ds


def convert(f, doi, title, summary):
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
    ds = add_title_history(ds, doi, title, summary)

    ds = ds.squeeze()
    if "depth" in ds:  # depth not in waves files usually
        ds = ds.rename({"depth": "z"})
        ds["z"].attrs["positive"] = "down"
        ds["z"].attrs["long_name"] = "depth of sensor below mean water level"

    ds.attrs["Conventions"] = "CF-1.6, ACDD-1.3"

    if "lon" in ds and "lat" in ds and "longitude" not in ds and "latitude" not in ds:
        ds = ds.rename({"lon": "longitude", "lat": "latitude"})
    else:
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
        ds["z"].attrs["axis"] = "Z"
        ds["z"].attrs["units"] = "m"
    ds["longitude"].attrs["axis"] = "X"
    ds["latitude"].attrs["axis"] = "Y"

    ds = portal.assign_standard_names(ds)

    ds["feature_type_instance"] = os.path.split(f)[1].split(".")[0]
    ds["feature_type_instance"].attrs["cf_role"] = "timeseries_id"

    for k in ds.data_vars:
        ds[k].attrs["coverage_content_type"] = "physicalMeasurement"

    # ADD STUFF FOR PORTAL COMPATIBILITY
    # see https://github.com/USGS-CMG/usgs-cmg-portal/issues/289
    ds.attrs["experiment_id"] = os.path.split(f)[1][0:5]
    ds.attrs["metadata_link"] = "https://doi.org/10.5066/" + doi
    # already have MOORING
    ds.attrs["id"] = os.path.split(f)[1].split(".")[0]
    ds.attrs["datasetID"] = os.path.split(f)[1].split(".")[0]
    ds.attrs["project"] = "CMG_Portal"

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

    ds["time"].attrs["long_name"] = "time of measurement"
    ds["time"].encoding["dtype"] = "i4"
    ds["time"].attrs["standard_name"] = "time"

    if len(ds.dims) == 1:
        ds.attrs["featureType"] = "timeSeries"
    elif len(ds.dims) == 2:
        ds.attrs["featureType"] = "timeSeriesProfile"

    # check for 0-length attributes (this causes problems with ERDDAP) and set to an empty string
    for k in ds.attrs:
        if isinstance(ds.attrs[k], np.ndarray) and not ds.attrs[k].size:
            ds.attrs[k] = ""

    dvfinal = ds.data_vars
    Path(os.path.split(f)[0] + "/clean").mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(os.path.split(f)[0] + "/clean/" + os.path.split(f)[1])

    return os.path.split(f)[1], "difference in data_vars:", (set(dvorig) ^ set(dvfinal))
