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
from analysegnss.sbf.sbf_blocks_polars import SBF_BLOCK_COLUMNS_BIN2ASC


def extract_semicircle_columns() -> dict:
    """extract columns containing semi-circles from each navigation block
    for GNSS

    Returns:
        dict: dictionary of columns containing semi-circles for the GNSS type
    """
    # Map navigation block names to GNSS types
    block_to_gnss = {"GPSNav": "GPS", "GALNav": "GAL", "BDSNav": "BDS"}

    # Initialize result dictionary with empty lists for each GNSS type
    result = {gnss_type: [] for gnss_type in set(block_to_gnss.values())}

    # Extract columns containing "semi-circle" from each navigation block
    for block_name, gnss_type in block_to_gnss.items():
        if block_name in SBF_BLOCK_COLUMNS_BIN2ASC:
            for dtype, columns in SBF_BLOCK_COLUMNS_BIN2ASC[block_name].items():
                # Skip non-list items (like the Date type which appears to be just pl.Date)
                if not isinstance(columns, list):
                    continue

                # Filter columns containing "semi-circle"
                semicircle_cols = [col for col in columns if "semi-circle" in col]
                result[gnss_type].extend(semicircle_cols)

    return result


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

    # Replace your hardcoded SEMICIRCLE_COLUMNS with this
    SEMICIRCLE_COLUMNS = extract_semicircle_columns()

    # Replace your hardcoded SEMICIRCLE_COLUMNS with this
    SEMICIRCLE_COLUMNS = extract_semicircle_columns()

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


def convert_and_rename_semicircles(df: pl.DataFrame, gnss_type: str) -> pl.DataFrame:
    """converts the columns using semi-circles to radians and renames the columns
    according to the GNSS type

    Args:
        df (pl.DataFrame): navigation message dataframe obtained for a gnss type
        gnss_type (str): type of GNSS system (GPS, GAL, BDS, etc.)

    Returns:
        pl.DataFrame: navigation message dataframe with radians units and renamed columns
    """
    # Conversion factor: 1 semi-circle = π radians
    SEMI_TO_RAD = np.pi

    # Replace your hardcoded SEMICIRCLE_COLUMNS with this
    SEMICIRCLE_COLUMNS = extract_semicircle_columns(gnss=gnss_type)

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
        "TOW [0.001 s]": "TOW",
        "WNc [w]": "WNc",
        "WN [w]": "WN",
        "CAorPonL2": "CodesL2",
        "IDOT [semi-circle/s]": "IDOT",
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
        "WNt_oc [w]": "WNt_oc",
        "WNt_oe [w]": "WNt_oe",
    },
    "GAL": {
        "TOW [0.001 s]": "TOW",
        "WNc [w]": "WNc",
        "t_oc [s]": "toc",
        "a_f0 [s]": "af0",
        "a_f1 [s/s]": "af1",
        "a_f2 [s/s²]": "af2",
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
        "IDOT [semi-circle/s]": "IDOT",
        "BGD_L1E5a [s]": "BGD_L1E5a",
        "BGD_L1E5b [s]": "BGD_L1E5b",
        "BGD_L1AE6A [s]": "BGD_L1AE6A",
        "WNt_oc [w]": "WNt_oc",
        "WNt_oe [w]": "WNt_oe",
    },
    "BDS": {
        "WN ": "WN",
        "URA": "SVacc",
        # ... BeiDou specific mappings
        "TOW [0.001 s]": "TOW",
        "WNc [w]": "WNc",
        "WN [w]": "WN",
        "PRN": "PRN",
        "CAorPonL2": "CAorPonL2",
        "URA": "SVacc",
        "SatH1": "SatH1",
        "IODC": "IODC",
        "IODE": "IODE",
        "t_oc [s]": "toc",
        "t_oe [s]": "toe",
        "a_f0 [s]": "af0",
        "a_f1 [s/s]": "af1",
        "a_f2 [s/s²]": "af2",
        "T_GD1 [s]": "TGD1",
        "T_GD2 [s]": "TGD2",
        "DEL_N [semi-circle/s]": "deltaN",
        "M_0 [semi-circle]": "M0",
        "e": "eccen",
        "SQRT_A [m**1/2]": "sqrtA",
        "OMEGA_0 [semi-circle]": "Omega0",
        "i_0 [semi-circle]": "Io",
        "omega [semi-circle]": "omega",
        "OMEGADOT [semi-circle/s]": "omegaDot",
        "IDOT [semi-circle/s]": "IDOT",
        "C_rs [m]": "Crs",
        "C_rc [m]": "Crc",
        "C_uc [rad]": "Cuc",
        "C_us [rad]": "Cus",
        "C_ic [rad]": "Cic",
        "C_is [rad]": "Cis",
    },
    "GLO": {
        "TOW [0.001 s]": "TOW",
        "WNc [w]": "WNc",
        "SVID": "SVID",
        "FreqNr": "FreqNr",
        "X [1000 m]": "X",
        "Y [1000 m]": "Y",
        "Z [1000 m]": "Z",
        "Dx [1000 m/s]": "Dx",
        "Dy [1000 m/s]": "Dy",
        "Dz [1000 m/s]": "Dz",
        "Ddx [1000 m/s²]": "Ddx",
        "Ddy [1000 m/s²]": "Ddy",
        "Ddz [1000 m/s²]": "Ddz",
        "gamma [Hz/Hz]": "gamma",
        "tau [s]": "tau",
        "dtau [s]": "dtau",
        "t_oe [s]": "t_oe",
        "WN_toe [w]": "WN_toe",
        "P1 [min.]": "P1",
        "P2": "P2",
        "E [d]": "E",
        "B": "B",
        "tb [min.]": "tb",
        "M": "M",
        "P": "P",
        "l": "l",
        "P4": "P4",
        "N_T [d]": "N_T",
        "F_T [0.01 m]": "F_T",
        "C": "C",
    },
}
