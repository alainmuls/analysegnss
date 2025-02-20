import polars as pl
import numpy as np

# Define columns that need conversion from semi-circles to radians
SEMICIRCLE_COLUMNS = {
    "GPS": [
        "IDOT [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
        "DEL_N [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
        "M_0 [semi-circle]",  # [semi-circles] -> [rad]
        "OMEGA_0 [semi-circle]",  # [semi-circles] -> [rad]
        "i_0 [semi-circle]",  # [semi-circles] -> [rad]
        "omega [semi-circle]",  # [semi-circles] -> [rad]
        "OMEGADOT [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
    ],
    "GAL": [],
    "BDS": [],
}


def convert_semicircles_to_radians(df: pl.DataFrame, gnss_type: str) -> pl.DataFrame:
    """converts the columns using semi-circles to radians

    Args:
        df (pl.DataFrame): dataframe with semi-circles units
        gnss_type (str): type of GNSS system (GPS, GAL, BDS, etc.)

    Returns:
        pl.DataFrame: dataframe with radians units
    """
    # Conversion factor: 1 semi-circle = π radians
    SEMI_TO_RAD = np.pi

    # Convert each column containing semi-circles
    for col in SEMICIRCLE_COLUMNS[gnss_type]:
        if col in df.columns:
            df = df.with_columns(pl.col(col) * SEMI_TO_RAD)

    return df


def rename_nav_columns(df: pl.DataFrame, gnss_type: str) -> pl.DataFrame:
    """rename the columns of a polars dataframe according to the GNSS type

    Args:
        df (pl.DataFrame): navigation message dataframe obtained for a gnss type
        gnss_type (str): type of GNSS system (GPS, GAL, BDS, etc.)

    Returns:
        pl.DataFrame: _description_
    """
    return df.rename(GNSS_NAV_COLUMN_MAPPINGS[gnss_type])


def convert_and_rename_semicircles(df):
    SEMI_TO_RAD = np.pi

    for orig_col in SEMICIRCLE_COLUMNS.keys():
        if orig_col in df.columns:
            df = df.with_columns(pl.col(orig_col) * SEMI_TO_RAD)

    return df.rename({k: v for k, v in SEMICIRCLE_COLUMNS.items()})


GNSS_NAV_COLUMN_MAPPINGS = {
    "GPS": {
        "PRN": "prn",
        "WNc [w]": "WNc",
        "WN [w]": "WN",
        "URA": "SVacc",
        "CAorPonL2": "CodesL2",
        "IDOT [semi-circle/s]": "IDOT",
        "IODE2": "IODE",
        "t_oc [s]": "toc",
        "a_f2 [s/s²]": "af2",
        "a_f1 [s/s]": "af1",
        "a_f0 [s]": "af0",
        "IODC": "IODC",
        "C_rs [m]": "Crs",
        "DEL_N [semi-circle/s]": "deltaN",
        "M_0 [semi-circle]": "M0",
        "C_uc [rad]": "Cuc",
        "e": "eccen",
        "C_us [rad]": "Cus",
        "SQRT_A [m**1/2]": "sqrtA",
        "t_oe [s]": "toe",
        "C_ic [rad]": "Cic",
        "OMEGA_0 [semi-circle]": "Omega0",
        "C_is [rad]": "Cis",
        "i_0 [semi-circle]": "Io",
        "C_rc [m]": "Crc",
        "omega [semi-circle]": "omega",
        "OMEGADOT [semi-circle/s]": "omegaDot",
        "T_gd [s]": "TGD",
        "health": "health",
        "L2DataFlag": "L2Pflag",
        "FitIntFlg": "Fit",
    },
    "GAL": {
        "PRN": "prn",
        "WN ": "WN",
        "SISA": "SVacc",  # Galileo uses SISA instead of URA
        # ... Galileo specific mappings
    },
    "BDS": {
        "PRN": "prn",
        "WN ": "WN",
        "URA": "SVacc",
        # ... BeiDou specific mappings
    },
}
