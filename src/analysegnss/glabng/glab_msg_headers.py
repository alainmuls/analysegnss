import polars as pl


HDRS_OUTPUT = {
    "OUTPUT": {
        "dtype": pl.String,
        "desc": "Fixed word indicating the data stored.",
        "keep": False,
    },
    "Year": {
        "dtype": pl.UInt16,
        "desc": "Year number (4 digits).",
        "keep": True,
    },
    "DOY": {
        "dtype": pl.UInt16,
        "desc": "Day of Year (3 digits).",
        "keep": True,
    },
    "SOD": {
        "dtype": pl.Float32,
        "desc": "Seconds elapsed since the beginning of the day.",
        "keep": True,
    },
    "time": {
        "dtype": pl.String,
        "desc": "Date and time of the message.",
        "keep": False,
    },
    "mode": {
        "dtype": pl.UInt16,
        "desc": "Processing mode indicator",
        "keep": True,
    },
    "dir": {
        "dtype": pl.UInt16,
        "desc": "Processing direction indicator",
        "keep": True,
    },
    "#SVs": {
        "dtype": pl.UInt32,
        "desc": "Number of satellites used in the navigation solution",
        "keep": True,
    },
    "#GNSSs": {
        "dtype": pl.UInt16,
        "desc": "Number of constellations used in the navigation solution",
        "keep": True,
    },
    "GNSSs": {
        "dtype": pl.String,
        "desc": "List of constellations used in the filter (separated by dashes ('-')",
        "keep": True,
    },
    "sdXYZ": {
        "dtype": pl.Float32,
        "desc": "Square root diagonal elements covariance matrix",
        "keep": True,
    },
    "X": {
        "dtype": pl.Float64,
        "desc": "X coordinate",
        "keep": False,
    },
    "Y": {
        "dtype": pl.Float64,
        "desc": "Y coordinate",
        "keep": False,
    },
    "Z": {
        "dtype": pl.Float64,
        "desc": "Z coordinate",
        "keep": False,
    },
    "delta.X": {
        "dtype": pl.Float64,
        "desc": "Receiver X position - Nominal a priori X position",
        "keep": False,
    },
    "delta.Y": {
        "dtype": pl.Float64,
        "desc": "Receiver Y position - Nominal a priori Y position",
        "keep": False,
    },
    "delta.Z": {
        "dtype": pl.Float64,
        "desc": "Receiver Z position - Nominal a priori Z position",
        "keep": False,
    },
    "sd.X": {
        "dtype": pl.Float32,
        "desc": "Receiver X formal error",
        "keep": False,
    },
    "sd.Y": {
        "dtype": pl.Float32,
        "desc": "Receiver Y formal error",
        "keep": False,
    },
    "sd.Z": {
        "dtype": pl.Float32,
        "desc": "Receiver Z formal error",
        "keep": False,
    },
    "lat": {
        "dtype": pl.Float64,
        "desc": "Receiver latitude",
        "keep": True,
    },
    "lon": {
        "dtype": pl.Float64,
        "desc": "Receiver longitude",
        "keep": True,
    },
    "ellH": {
        "dtype": pl.Float64,
        "desc": "Receiver height",
        "keep": True,
    },
    "delta.N": {
        "dtype": pl.Float64,
        "desc": "Receiver North difference in relation to nominal a priori position",
        "keep": True,
    },
    "delta.E": {
        "dtype": pl.Float64,
        "desc": "Receiver East difference in relation to nominal a priori position",
        "keep": True,
    },
    "delta.U": {
        "dtype": pl.Float64,
        "desc": "Receiver Up difference in relation to nominal a priori position",
        "keep": True,
    },
    "sd.N": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in North direction",
        "keep": True,
    },
    "sd.E": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in East direction",
        "keep": True,
    },
    "sd.U": {
        "dtype": pl.Float32,
        "desc": "Receiver formal error in Up direction",
        "keep": True,
    },
    "delta.hor": {
        "dtype": pl.Float64,
        "desc": "Receiver horizontal difference in relation to nominal a priori position",
        "keep": False,
    },
    "delta.vert": {
        "dtype": pl.Float64,
        "desc": "Receiver vertical difference in relation to nominal a priori position",
        "keep": False,
    },
    "delta.3D": {
        "dtype": pl.Float64,
        "desc": "Receiver 3D difference in relation to nominal a priori position",
        "keep": False,
    },
    "GNSSclock": {
        "dtype": pl.String,
        "desc": "Constellation used as reference clock",
        "keep": True,
    },
    "clk_off": {
        "dtype": pl.Float64,
        "desc": "Receiver clock offset",
        "keep": True,
    },
    "clk_err": {
        "dtype": pl.Float32,
        "desc": "Receiver clock formal error",
        "keep": True,
    },
    "GDOP": {
        "dtype": pl.Float32,
        "desc": "Geometric Dilution of Precision",
        "keep": True,
    },
    "PDOP": {
        "dtype": pl.Float32,
        "desc": "Positioning Dilution of Precision",
        "keep": True,
    },
    "TDOP": {
        "dtype": pl.Float32,
        "desc": "Time Dilution of Precision",
        "keep": True,
    },
    "HDOP": {
        "dtype": pl.Float32,
        "desc": "Horizontal Dilution of Precision",
        "keep": True,
    },
    "VDOP": {
        "dtype": pl.Float32,
        "desc": "Vertical Dilution of Precision",
        "keep": True,
    },
    "ZTDinc": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay (including nominal value)",
        "keep": True,
    },
    "ZTDecl": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay (excluding nominal value)",
        "keep": True,
    },
    "sd.ZTD": {
        "dtype": pl.Float32,
        "desc": "Zenith Tropospheric Delay formal error",
        "keep": True,
    },
}

HDRS_SATSEL = {
    "SATSEL": {
        "dtype": pl.String,
        "desc": "Fixed word indicating the data stored.",
        "keep": True,
    },
    "Year": {
        "dtype": pl.UInt16,
        "desc": "Year number (4 digits).",
        "keep": True,
    },
    "DoY": {
        "dtype": pl.UInt16,
        "desc": "Day of Year (3 digits).",
        "keep": True,
    },
    "sod": {
        "dtype": pl.Float32,
        "desc": "Seconds elapsed since the beginning of the day.",
        "keep": True,
    },
    "DT": {
        "dtype": pl.String,
        "desc": "Date and time of the message.",
        "keep": True,
    },
    "GNSS": {
        "dtype": pl.String,
        "desc": "GNSS system",
        "keep": True,
    },
    "PRN": {
        "dtype": pl.UInt16,
        "desc": "PRN satellite identifier",
        "keep": True,
    },
    "code": {
        "dtype": pl.UInt16,
        "desc": "Error code",
        "keep": True,
    },
    "code_desc": {
        "dtype": pl.String,
        "desc": "Selected or Error code description",
        "keep": True,
    },
}

GLAB_OUTPUTS = {
    "OUTPUT": HDRS_OUTPUT,
    "SATSEL": HDRS_SATSEL,
}
