import subprocess

import numpy as np


def check_compliance_system(f, test):
    return subprocess.run(["compliance-checker", "-t", test, f], capture_output=True)


def acdd_attrs(ds):
    # stuff for ACDD
    ds.attrs["creator_url"] = "https://www.usgs.gov/"
    ds.attrs["publisher_url"] = "https://www.usgs.gov/"
    ds.attrs["source"] = "USGS"
    ds.attrs["geospatial_lat_min"] = ds["latitude"].min().values
    ds.attrs["geospatial_lat_max"] = ds["latitude"].max().values
    ds.attrs["geospatial_lon_min"] = ds["longitude"].min().values
    ds.attrs["geospatial_lon_max"] = ds["longitude"].max().values

    return ds


standard_names = {
    "P_1": "sea_water_pressure",
    "P_1294": "sea_water_pressure",
    "SDP_850": "sea_water_pressure",
    "P_4023": "sea_water_pressure_due_to_sea_water",
    "u_1205": "eastward_sea_water_velocity",
    "v_1206": "northward_sea_water_velocity",
    "w_1204": "upward_sea_water_velocity",
    "u_1205min": "eastward_sea_water_velocity",
    "v_1206min": "northward_sea_water_velocity",
    "w_1204min": "upward_sea_water_velocity",
    "u_1205max": "eastward_sea_water_velocity",
    "v_1206max": "northward_sea_water_velocity",
    "w_1204max": "upward_sea_water_velocity",
    "USTD_4097": "eastward_sea_water_velocity",
    "VSTD_4098": "northward_sea_water_velocity",
    "WSTD_4099": "upward_sea_water_velocity",
    "T_28": "sea_water_temperature",
    "Tx_1211": "sea_water_temperature",
    "C_50": "sea_water_electrical_conductivity",
    "C_51": "sea_water_electrical_conductivity",
    "S_41": "sea_water_salinity",
    "ST_70": "sea_water_sigma_t",
    "SV_80": "speed_of_sound_in_sea_water",
    "Trb2_980": "sea_water_turbidity",
    "Trb1_980": "sea_water_turbidity",
    "Trb_980": "sea_water_turbidity",
    "SED_981": "mass_concentration_of_suspended_matter_in_sea_water",
    "SED1_981": "mass_concentration_of_suspended_matter_in_sea_water",
    "Sed_981": "mass_concentration_of_suspended_matter_in_sea_water",
    "Ptch_1216": "platform_pitch_angle",
    "Roll_1217": "platform_roll_angle",
    "Hdg_1215": "platform_orientation",
    "wh_4061": "sea_surface_wave_significant_height",
    "mwh_4064": "sea_surface_wave_maximum_height",
    "wp_4060": "sea_surface_wave_mean_period",
    "hght_18": "sea_surface_height",
    "Tz": "sea_surface_wave_mean_period",
    "wp_peak": "sea_surface_wave_period_at_variance_spectral_density_maximum",
    "Hmean": "sea_surface_wave_mean_height",
    "H10": "sea_surface_wave_mean_height_of_highest_tenth",
    "wvdir": "sea_surface_wave_from_direction",
    "z": "height",
}

# long_names = {'burst': 'Burst number',
#               'Werr_1201': 'ADCP error velocity (difference between the two estimates of vertical velocity)',
#               'PGd_1203': 'Percent good pings'}

cell_methods = {
    "SDP_850": "time: standard_deviation",
    "u_1205min": "time: minimum",
    "v_1206min": "time: minimum",
    "w_1204min": "time: minimum",
    "u_1205max": "time: maximum",
    "v_1206max": "time: maximum",
    "w_1204max": "time: maximum",
    "USTD_4097": "time: standard_deviation",
    "VSTD_4098": "time: standard_deviation",
    "WSTD_4099": "time: standard_deviation",
}


def assign_standard_names(ds):
    # drop all vars without a standard_name
    for d in ds.data_vars:
        if (d not in standard_names) and ("long_name" not in ds[d].attrs):
            ds = ds.drop(d)

    # drop time2
    if "time2" in ds:
        ds = ds.drop("time2")

    for k in standard_names:
        if k in ds:
            if "standard_name" not in ds[k].attrs:
                ds[k].attrs["standard_name"] = standard_names[k]
    for k in cell_methods:
        if k in ds:
            if "cell_methods" not in ds[k].attrs:
                ds[k].attrs["cell_methods"] = cell_methods[k]

    if "T_28" in ds:
        if ds["T_28"].attrs["units"] == "C":
            ds["T_28"].attrs["units"] = "degree_C"

    if "Tx_1211" in ds:
        if (
            (ds["Tx_1211"].attrs["units"] == "C")
            or (ds["Tx_1211"].attrs["units"] == "degrees.C")
            or (ds["Tx_1211"].attrs["units"] == "Deg. C")
            or (ds["Tx_1211"].attrs["units"] == "degrees C")
        ):
            ds["Tx_1211"].attrs["units"] = "degree_C"

    if "latitude" in ds:
        ds["latitude"].attrs["standard_name"] = "latitude"
        ds["latitude"].attrs["long_name"] = "sensor latitude"
        ds["latitude"].attrs["units"] = "degrees_north"

    if "longitude" in ds:
        ds["longitude"].attrs["standard_name"] = "longitude"
        ds["longitude"].attrs["long_name"] = "sensor longitude"
        ds["longitude"].attrs["units"] = "degrees_east"

    if "burst" in ds:
        if "units" in ds["burst"].attrs:
            if ds["burst"].attrs["units"] == "none":
                ds["burst"].attrs["units"] = "1"
        else:
            ds["burst"].attrs["units"] = "1"

    if "P_1" in ds:
        if ds["P_1"].attrs["units"] == "DB":
            ds["P_1"].attrs["units"] = "dbar"

    if "P_1294" in ds:
        if ds["P_1294"].attrs["units"].lower() == "deca-pascals":
            ds["P_1294"].attrs["units"] = "dekapascals"

    if "C_50" in ds:
        if ds["C_50"].attrs["units"] == "mmho/cm":
            # mho is an "unaccepted special name for an SI unit"
            ds["C_50"].attrs["units"] = "mS cm-1"

    # rename attributes with a '.' in them (causes CF warning)
    for k in list(
        ds.attrs
    ):  # needs to be list; can't have keys changing during iteration
        if "." in k:
            ds.attrs[k.replace(".", "_")] = ds.attrs.pop(k)

    return ds


def ensure_attr_dtype(ds):
    for k in ds:
        for a in ds[k].attrs:
            if isinstance(ds[k].attrs[a], np.ndarray) or isinstance(
                ds[k].attrs[a], np.float64
            ):
                if ds[k].attrs[a].dtype != ds[k].dtype:
                    # this typically happens on valid_range being a different type than its variable
                    # so promote dtype of valid_range attr to be the same as its var
                    ds[k].attrs[a] = ds[k].attrs[a].astype(ds[k].dtype)

    return ds


def ensure_valid_range(ds):
    # mostly happens when valid_range is a space character
    # remove it if so
    for k in ds:
        if ("valid_range" in ds[k].attrs) and (ds[k].attrs["valid_range"] == " "):
            ds[k].attrs.pop("valid_range")

    return ds
