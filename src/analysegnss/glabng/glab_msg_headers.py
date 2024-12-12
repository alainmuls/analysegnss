import polars as pl


HDRS_OUTPUT = {
    "OUTPUT": {
        "dtype": pl.String,
        "desc": "Fixed word indicating the data stored.",
    },
    "Year": {
        "dtype": pl.UInt16,
        "desc": "Year number (4 digits).",
    },
    "DoY": {
        "dtype": pl.UInt16,
        "desc": "Day of Year (3 digits).",
    },
    "sod": {
        "dtype": pl.Float32,
        "desc": "Seconds elapsed since the beginning of the day.",
    },
    "DT": {
        "dtype": pl.String,
        "desc": "Date and time of the message.",
    },
    "mode": {
        "dtype": pl.UInt16,
        "desc": "Processing mode indicator",
    },
    "dir": {
        "dtype": pl.UInt16,
        "desc": "Processing direction indicator",
    },
    "#SVs": {
        "dtype": pl.UInt32,
        "desc": "Number of satellites used in the navigation solution",
    },
    "#GNSSs": {
        "dtype": pl.UInt16,
        "desc": "Number of constellations used in the navigation solution",
    },
    "GNSSs": {
        "dtype": pl.String,
        "desc": "List of constellations used in the filter (separated by dashes ('-')",
    },
    "sdXYZ": {
        "dtype": pl.Float32,
        "desc": "Square root diagonal elements covariance matrix",
    },
    "X": {
        "dtype": pl.Float64,
        "desc": "X coordinate",
    },
    "Y": {
        "dtype": pl.Float64,
        "desc": "Y coordinate",
    },
    "Z": {
        "dtype": pl.Float64,
        "desc": "Z coordinate",
    },
    "delta.X": {
        "dtype": pl.Float64,
        "desc": "Receiver X position - Nominal a priori X position",
    },
    "delta.Y": {
        "dtype": pl.Float64,
        "desc": "Receiver Y position - Nominal a priori Y position",
    },
    "delta.Z": {
        "dtype": pl.Float64,
        "desc": "Receiver Z position - Nominal a priori Z position",
    },
    "sd.X": {
        "dtype": pl.Float32,
        "desc": "Receiver X formal error",
    },
    "sd.Y": {
        "dtype": pl.Float32,
        "desc": "Receiver Y formal error",
    },
    "sd.Z": {
        "dtype": pl.Float32,
        "desc": "Receiver Z formal error",
    },
    "lat": {
        "dtype": pl.Float64,
        "desc": "Receiver latitude",
    },
    "lon": {
        "dtype": pl.Float64,
        "desc": "Receiver longitude",
    },
    "ellH": {
        "dtype": pl.Float64,
        "desc": "Receiver height",
    },
    "delta.N": {
        "dtype": pl.Float64,
        "desc": "Receiver North difference in relation to nominal a priori position",
    },
    "delta.E": {
        "dtype": pl.Float64,
        "desc": "Receiver East difference in relation to nominal a priori position",
    },
    "delta.U": {
        "dtype": pl.Float64,
        "desc": "Receiver Up difference in relation to nominal a priori position",
    },
    "sd.N": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in North direction",
    },
    "sd.E": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in East direction",
    },
    "sd.U": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in Up direction",
    },
    "delta.hor": {
        "dtype": pl.Float64,
        "desc": "Receiver horizontal difference in relation to nominal a priori position",
    },
    "delta.vert": {
        "dtype": pl.Float64,
        "desc": "Receiver vertical difference in relation to nominal a priori position",
    },
    "delta.3D": {
        "dtype": pl.Float64,
        "desc": "Receiver 3D difference in relation to nominal a priori position",
    },
    "GNSSclock": {
        "dtype": pl.String,
        "desc": "Constellation used as reference clock",
    },
    "clk_off": {
        "dtype": pl.Float64,
        "desc": "Receiver clock offset",
    },
    "clk_err": {
        "dtype": pl.Float32,
        "desc": "Receiver clock formal error",
    },
    "GDOP": {
        "dtype": pl.Float32,
        "desc": "Geometric Dilution of Precision",
    },
    "PDOP": {
        "dtype": pl.Float32,
        "desc": "Positioning Dilution of Precision",
    },
    "TDOP": {
        "dtype": pl.Float32,
        "desc": "Time Dilution of Precision",
    },
    "HDOP": {
        "dtype": pl.Float32,
        "desc": "Horizontal Dilution of Precision",
    },
    "VDOP": {
        "dtype": pl.Float32,
        "desc": "Vertical Dilution of Precision",
    },
    "ZTDinc": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay (including nominal value)",
    },
    "ZTDecl": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay (excluding nominal value)",
    },
    "sd.ZTD": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay formal error",
    },
}

HDRS_SATSEL = {
    "SATSEL": {
        "dtype": pl.String,
        "desc": "Fixed word indicating the data stored.",
    },
    "Year": {
        "dtype": pl.UInt16,
        "desc": "Year number (4 digits).",
    },
    "DoY": {
        "dtype": pl.UInt16,
        "desc": "Day of Year (3 digits).",
    },
    "sod": {
        "dtype": pl.Float32,
        "desc": "Seconds elapsed since the beginning of the day.",
    },
    "DT": {
        "dtype": pl.String,
        "desc": "Date and time of the message.",
    },
    "GNSS": {
        "dtype": pl.String,
        "desc": "GNSS system",
    },
    "PRN": {
        "dtype": pl.UInt16,
        "desc": "PRN satellite identifier",
    },
    "code": {
        "dtype": pl.UInt16,
        "desc": "Error code",
    },
    "code_desc": {
        "dtype": pl.String,
        "desc": "Selected or Error code description",
    },
}

GLAB_OUTPUTS = {
    "OUTPUT": HDRS_OUTPUT,
    "SATSEL": HDRS_SATSEL,
}
