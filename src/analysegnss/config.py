import os

from polars import Config
from rich.console import Console

# console to use when an operation lasts some time to inform user
rich_console = Console()

# general constants for printing polars dataframes
Config.set_tbl_cols(-1)
Config.set_float_precision(5)
Config.set_tbl_cell_numeric_alignment("RIGHT")

# Get the directory of the config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the geoid file
GEOID_PATH = os.path.join(BASE_DIR, "gnss", "geoids", "egm2008-1.pgm")

# Constants
# Earth's gravitational constant
RE_GLO = 6378136.0  # type: ignore # radius of earth (m)            ref [2]
GM_GPS = 3.986005e14  # type: ignore # gravitational constant         ref [1]
GM_GLO = 3.9860044e14  # type: ignore # gravitational constant         ref [2]
GM_GAL = 3.986004418e14  # type: ignore # earth gravitational constant   ref [7]
GM_BDS = 3.986004418e14  # type: ignore # earth gravitational constant   ref [9]

J2_GLO = 1.0826257e-3  # 2nd zonal harmonic of geopot   ref [2]

# Earth's rotation rate
OMGE_GPS = 7.2921151467e-5  # Earth's rotation rate rad/sOMGE_GLO = 7.292115e-5  # earth angular velocity (rad/s) ref [2]
OMGE_GAL = 7.2921151467e-5  # earth angular velocity (rad/s) ref [7]
OMGE_BDS = 7.292115e-5  # earth angular velocity (rad/s) ref [9]

# Timing constants
GPS_BDS_WEEK_DIFF = 1356  # week difference between GPS and BDS time
SECS_IN_WEEK = 604800  # seconds in a week

# speed of light
C84 = 299792458  # Speed of light m/s

# Error codes
ERROR_CODES = {
    "E_SUCCESS": 0,
    "E_FILE_NOT_EXIST": 1,
    "E_FILE_EMPTY": 2,
    "E_NOT_IN_PATH": 3,
    "E_UNKNOWN_OPTION": 4,
    "E_TIME_PASSED": 5,
    "E_WRONG_OPTION": 6,
    "E_SIGNALTYPE_MISMATCH": 7,
    "E_DIR_NOT_EXIST": 8,
    "E_INVALID_ARGS": 9,
    "E_SBF2RIN_ERRCODE": 10,
    "E_OSERROR": 11,
    "E_NORINEXOBS": 12,
    "E_NORINEXNAV": 13,
    "E_PATH_NOT_WRITABLE": 14,
    "E_CREATE_DIR_ERROR": 15,
    "E_PRN_NOT_IN_DATA": 16,
    "E_NOAVAIL_FREQ": 17,
    "E_INCORRECT_TIMES": 18,
    "E_MIXED_GNSS": 19,
    "E_NO_OBS_FILE": 20,
    "E_NO_NAV_FILE": 21,
    "E_NO_CSV_FILE": 22,
    "E_MISSING_BIN": 23,
    "E_NO_SBF_FILE": 24,
    "E_NO_PVTBLOCKS": 25,
    "E_NO_SATVISIBILITY": 26,
    "E_FREQNR": 27,
    "E_INTERRUPT": 37,
    "E_NO_CONFIG_FILE": 38,
    "E_ERROR_CONFIG_FILE": 39,
    "E_FAILED_SUBPROCESS": 40,
    "E_TIMEOUT": 41,
    "E_FILE_NOT_READABLE": 42,
    "E_NO_QUAL": 43,
    "E_NO_SBF_BLOCK": 44,
    "E_SBF_OBJECT": 45,
    "E_NO_RINEX_OBS": 46,
    "E_NO_RINEX_NAV": 47,
    "E_SIGNALTYPE_MISMATCH": 48,
    "E_WRONG_GNSS": 49,
    "E_SBF_BLOCKS": 50,
    "E_INVALID_SOURCE": 51,
    "E_PROCESS": 90,
    "E_FAILURE": 99,
}

DICT_GNSS = {
    "G": {"name": "GPS", "abbrev": "GPS"},
    "R": {"name": "Glonass", "abbrev": "GLO"},
    "E": {"name": "Galileo", "abbrev": "GAL"},
    "C": {"name": "Beidou", "abbrev": "BDS"},
    # "S": "SBAS",
    # "I": "IRNSS",
    # "Z": "QZSS",
}


DICT_SIGNAL_TYPES = {
    0: {"type": "L1CA", "gnss": "GPS", "freq": 1575.42e3, "code": "1C"},
    1: {"type": "L1PY", "gnss": "GPS", "freq": 1575.42e3, "code": "1W"},
    2: {"type": "L2PY", "gnss": "GPS", "freq": 1227.60e3, "code": "2W"},
    3: {"type": "L2C", "gnss": "GPS", "freq": 1227.60e3, "code": "2L"},
    4: {"type": "L5", "gnss": "GPS", "freq": 1176.45e3, "code": "5Q"},
    5: {"type": "L1C", "gnss": "GPS", "freq": 1575.42e3, "code": "1L"},
    6: {"type": "L1CA", "gnss": "QZSS", "freq": 1575.42e3, "code": "1C"},
    7: {"type": "L2C", "gnss": "QZSS", "freq": 1227.60e3, "code": "2L"},
    8: {
        "type": "L1CA",
        "gnss": "GLONASS",
        "freq": "1602.00E3+(FreqNr-8)*9/16",
        "code": "1C",
    },
    9: {
        "type": "L1P",
        "gnss": "GLONASS",
        "freq": "1602.00E3+(FreqNr-8)*9/16",
        "code": "1P",
    },
    10: {
        "type": "L2P",
        "gnss": "GLONASS",
        "freq": "1246.00E3+(FreqNr-8)*7/16",
        "code": "2P",
    },
    11: {
        "type": "L2CA",
        "gnss": "GLONASS",
        "freq": "1246.00E3+(FreqNr-8)*7/16",
        "code": "2C",
    },
    12: {"type": "L3", "gnss": "GLONASS", "freq": 1202.025e3, "code": "3Q"},
    13: {"type": "B1C", "gnss": "BeiDou", "freq": 1575.42e3, "code": "1P"},
    14: {"type": "B2a", "gnss": "BeiDou", "freq": 1176.45e3, "code": "5P"},
    15: {"type": "L5", "gnss": "NavIC/IRNSS", "freq": 1176.45e3, "code": "5A"},
    17: {"type": "E1BC", "gnss": "Galileo", "freq": 1575.42e3, "code": "1C"},
    19: {"type": "E3 (E3BC)", "gnss": "Galileo", "freq": 1278.75e3, "code": "6C"},
    20: {"type": "E5a", "gnss": "Galileo", "freq": 1176.45e3, "code": "5Q"},
    21: {"type": "E5b", "gnss": "Galileo", "freq": 1207.14e3, "code": "7Q"},
    22: {"type": "E5", "gnss": "Galileo", "freq": 1191.795e3, "code": "8Q"},
    23: {"type": "LBand", "gnss": "MSS", "freq": "L-bandE3 beam speciﬁc", "code": "NA"},
    24: {"type": "L1CA", "gnss": "SBAS", "freq": 1575.42e3, "code": "1C"},
    25: {"type": "L5", "gnss": "SBAS", "freq": 1176.45e3, "code": "5I"},
    26: {"type": "L5", "gnss": "QZSS", "freq": 1176.45e3, "code": "5Q"},
    27: {"type": "L6", "gnss": "QZSS", "freq": 1278.7528e3, "code": ""},
    28: {"type": "B1I", "gnss": "BeiDou", "freq": 1561.098e3, "code": "2I"},
    29: {"type": "B2I", "gnss": "BeiDou", "freq": 1207.14e3, "code": "7I"},
    30: {"type": "B3I", "gnss": "BeiDou", "freq": 1268.52e3, "code": "6I"},
    32: {"type": "L1C", "gnss": "QZSS", "freq": 1575.42e3, "code": "1L"},
    33: {"type": "L1S", "gnss": "QZSS", "freq": 1575.42e3, "code": "1Z"},
    34: {"type": "B2b", "gnss": "BeiDou", "freq": 1207.14e3, "code": "7D"},
}
