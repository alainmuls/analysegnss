# standard library imports
import logging
import os
import sys

# third party imports
import polars as pl
from rich import print as rprint
from tabulate import tabulate

# local application imports
from analysegnss.gnss.standard_pnt_quality_dict import get_pntquality_info
from analysegnss.gnss.gnss_utils import euclidean_distance


def quality_analysis(
    df_pnt: pl.DataFrame, file_name: str, logger: logging.Logger = None
) -> tuple[list, str]:
    """
    Analyse the quality of the PNT data

    Args:
        df_pnt (pl.DataFrame): The dataframe containing the PNT data and the standard PNT quality column 'pnt_qual'
        file_name (str): The name of the file containing the PNT data
        logger (Logger): The logger object

    Returns:
        tuple[list, str]: A tuple containing:
            - qual_analysis (list): The quality analysis of the PNT data
                    - PNT Mode: The PNT mode
                    - PNT Mode Count: The number of observations in the PNT mode
                    - Percentage: The percentage of observations in the PNT mode
                    - Total Observations: The total number of observations
                    - Distance between First and Last Point of PNT Mode: The distance between the first and last point of the PNT mode
                    - Distance between First and Last Point across All Observations: The distance between the first and last point of all observations

            - qual_tabular (str): The quality analysis of the PNT data in tabular format for display
    """
    logger.info(f"Analyzing quality of PNT data from {file_name}")
    logger.debug(f"Quality analysis for {file_name}:\n{df_pnt}")

    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = df_pnt.shape[0]

    for qual, qual_data in df_pnt.group_by(["pnt_qual"]):
        qual_analysis.append(
            [
                get_pntquality_info(qual[0])["desc"],
                qual_data.shape[0],
                round(qual_data.shape[0] / total_obs * 100, 2),
                total_obs,
                distance_first_last_point(qual_data),
                distance_first_last_point(df_pnt),
                file_name,
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=[
            "PNT Mode",
            "PNT Mode Count",
            "Percentage",
            "Total Observations",
            "Distance between First and Last Point of PNT Mode",
            "Distance between First and Last Point across All Observations",
            "Source File",
        ],
        tablefmt="fancy_outline",
    )

    if logger is not None:
        logger.info(f"Quality analysis for {file_name}:\n{qual_tabular}")

    return qual_analysis, qual_tabular


def distance_first_last_point(df: pl.DataFrame) -> float:
    """
    Calculate the distance between the first and last point in the dataframe using UTM coordinates and orthometric height
    """

    if "UTM.E" in df.columns and "UTM.N" in df.columns and "orthoH" in df.columns:
        return euclidean_distance(
            df.select(pl.col("UTM.E").first()).to_series().item(),
            df.select(pl.col("UTM.E").last()).to_series().item(),
            df.select(pl.col("UTM.N").first()).to_series().item(),
            df.select(pl.col("UTM.N").last()).to_series().item(),
            df.select(pl.col("orthoH").first()).to_series().item(),
            df.select(pl.col("orthoH").last()).to_series().item(),
        )
    elif "UTM.E" in df.columns and "UTM.N" in df.columns:
        return euclidean_distance(
            df.select(pl.col("UTM.E").first()).to_series().item(),
            df.select(pl.col("UTM.E").last()).to_series().item(),
            df.select(pl.col("UTM.N").first()).to_series().item(),
            df.select(pl.col("UTM.N").last()).to_series().item(),
        )
    else:
        return None
