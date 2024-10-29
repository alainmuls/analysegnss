import os

# Get the directory of the config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the geoid file
GEOID_PATH = os.path.join(BASE_DIR, "gnss", "geoids", "egm2008-1.pgm")


# Error codes
ERROR_CODES = {
    "E_SUCCESS": 0,
    "E_FILE_NOT_EXIST": 1,
    "E_NOT_IN_PATH": 2,
    "E_UNKNOWN_OPTION": 3,
    "E_TIME_PASSED": 4,
    "E_WRONG_OPTION": 5,
    "E_SIGNALTYPE_MISMATCH": 6,
    "E_DIR_NOT_EXIST": 7,
    "E_INVALID_ARGS": 8,
    "E_SBF2RIN_ERRCODE": 9,
    "E_OSERROR": 10,
    "E_NORINEXOBS": 11,
    "E_NORINEXNAV": 12,
    "E_PATH_NOT_WRITABLE": 13,
    "E_CREATE_DIR_ERROR": 14,
    "E_PRN_NOT_IN_DATA": 15,
    "E_NOAVAIL_FREQ": 16,
    "E_INCORRECT_TIMES": 17,
    "E_MIXED_GNSS": 18,
    "E_NO_OBS_FILE": 19,
    "E_NO_NAV_FILE": 20,
    "E_NO_CSV_FILE": 21,
    "E_MISSING_BIN": 22,
    "E_NO_SBF_FILE": 23,
    "E_NO_PVTBLOCKS": 24,
    "E_NO_SATVISIBILITY": 35,
    "E_FREQNR": 36,
    "E_INTERRUPT": 37,
    "E_NO_CONFIG_FILE": 38,
    "E_ERROR_CONFIG_FILE": 39,
    "E_FAILED_SUBPROCESS": 40,
    "E_TIMEOUT": 41,
    "E_FILE_NOT_READABLE": 42,
    "E_NO_QUAL": 43,
    "E_NO_SBF_BLOCK": 44,
    "ERROR_SBF_OBJECT": 45,
    "E_PROCESS": 90,
    "E_FAILURE": 99,
}

GNSS_DICT = {
    "G": "GPS",
    "E": "Galileo",
    "R": "Glonass",
    "B": "Beidou",
    "S": "SBAS",
    "I": "IRNSS",
    "Z": "QZSS",
}
