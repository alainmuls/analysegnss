import polars as pl
import numpy as np

from analysegnss.sbf.sbf_blocks_polars import SBF_BLOCK_COLUMNS_BIN2ASC

# # Define columns that need conversion from semi-circles to radians
# SEMICIRCLE_COLUMNS = {
#     "GPS": [
#         "IDOT [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
#         "DEL_N [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
#         "M_0 [semi-circle]",  # [semi-circles] -> [rad]
#         "OMEGA_0 [semi-circle]",  # [semi-circles] -> [rad]
#         "i_0 [semi-circle]",  # [semi-circles] -> [rad]
#         "omega [semi-circle]",  # [semi-circles] -> [rad]
#         "OMEGADOT [semi-circle/s]",  # [semi-circles/s] -> [rad/s]
#     ],
#     "GAL": [],
#     "BDS": [],
# }


def extract_semicircle_columns() -> dict:
    """extract columns containing semi-circles from each navigation block
    for GNSS

    Returns:
        dict: dictionary of columns containing semi-circles for the GNSS type
    """
    # Map navigation block names to GNSS types
    block_to_gnss = {
        "GPSNav": "GPS",
        "GALNav": "GAL",
        # Add more mappings as needed
        # "BDSNav": "BDS"  # Include when BeiDou navigation block is added
    }

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
    SEMICIRCLE_COLUMNS = extract_semicircle_columns(gnss=gnss_type)

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
        "TOW [0.001 s]": "TOW",
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
        "WNt_oc [w]": "WNt_oc",
        "WNt_oe [w]": "WNt_oe",
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
