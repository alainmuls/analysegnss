#! /usr/bin/env python

# import standard libraries
import argparse
from logging import Logger
import os
import sys

# import third-party libraries
import numpy as np
import polars as pl

# import local libraries
from analysegnss.utils import argument_parser, init_logger


# get_gradient_ebhlines is the main function that calls other functions to get the gradient of the EBH lines
def gradient_ebhlines(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """
    Get the gradient of the EBH lines
    """

    # collect the ebh lines from the directory #TODO get the ebh lines from the ebh_lines.py script?
    ebh_lines = collect_ebh_lines(parsed_args=parsed_args, logger=logger)


    #################################################
    ##### Determine MAX LONGITUDINAL GRADIENT #######
    #################################################
    
    # determine the lowest threshold and the highest point on the CLine
    lowest_threshold, highest_point_CL = lowest_runway_threshold_and_highest_point_CL(
        ebh_line=ebh_lines["CL"], logger=logger
    )
    
    # determine the highest gradient from the lowest threshold to the highest point on the CLine
    max_gradient_runway, dist_threshold_and_Hpoint_CL, slope_threshold_to_Hpoint_CL = gradient_3D(
        x1=lowest_threshold["UTM.E"],
        y1=lowest_threshold["UTM.N"],
        z1=lowest_threshold["orthoH"],
        x2=highest_point_CL["UTM.E"],
        y2=highest_point_CL["UTM.N"],
        z2=highest_point_CL["orthoH"],
        logger=logger,
    )
    logger.info(f"Max gradient from lowest threshold to highest point on the CLine is {max_gradient_runway} degrees")
    logger.info(f"Distance from lowest threshold to highest point on the CLine is {dist_threshold_and_Hpoint_CL} meters")
    logger.info(f"Slope from lowest threshold to highest point on the CLine is {slope_threshold_to_Hpoint_CL}")

    #################################################
    ##### Determine MAX GRADIENT ACROSS RUNWAY #####
    #################################################

    # Determine the max gradient across the width of the runway
    max_gradient_runwaywidth = max_gradient_runwaywidth(ebh_lines=ebh_lines, logger=logger)
    
    
# collect_ebh_lines is a function that collects the ebh lines csv files from a directory
def collect_ebh_lines(parsed_args: argparse.Namespace, logger: Logger) -> dict:
    """
    Collect the ebh lines csv files from a directory

    args:
    parsed_args (argparse.Namespace): parsed arguments
    logger (Logger): Logger object

    returns:
    ebh_lines (dict): dictionary with ebh line keys and ebh line dataframes
    """

    # get the ebh lines from the directory
    ebh_lines = {}
    for file in os.listdir(parsed_args.dir_file):
        if file.endswith(".csv"):
            logger.info(
                f"Collecting ebh line {file} from directory {parsed_args.dir_file}"
            )
            ebh_lines[file] = pl.read_csv(
                source=os.path.join(parsed_args.dir_file, file),
                separator=";",
                columns=["UTM.E", "UTM.N", "orthoH"],
                comment_prefix="#",
                has_header=False,
                dtypes={"UTM.E": float, "UTM.N": float, "orthoH": float},
                null_values="NaN",
            )
            logger.debug(f"Extracted {len(ebh_lines[file])} rows from ebh line {file}")

    return ebh_lines


def gradient_3D(
    x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, logger: Logger
) -> float:
    """
    Calculate the gradient between two coordinates

    args:
    x1 (float): x coordinate of the first point
    y1 (float): y coordinate of the first point
    z1 (float): z coordinate of the first point
    x2 (float): x coordinate of the second point
    y2 (float): y coordinate of the second point
    z2 (float): z coordinate of the second point
    logger (Logger): Logger object

    returns:
    gradient (float): gradient between two coordinates expressed in degrees
    distance (float): distance between two coordinates
    slope (float): slope between two coordinates
    """

    # calculate the gradient between two coordinates in degrees
    gradient = np.arctan((z2 - z1) / (x2 - x1)) * 180 / np.pi
    # calculate the distance between the two coordinates
    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    # calculate the slope between the two coordinates
    slope = (z2 - z1) / np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    logger.info(
        f"Gradient between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {gradient} degrees"
    )
    logger.info(
        f"Distance between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {distance} meters"
    )
    logger.info(
        f"Slope between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {slope}"
    )

    return gradient, distance, slope


# determine the lowest threshold and the highest point on the CLine
def lowest_runway_threshold_and_highest_point_CL(
    ebh_line: pl.DataFrame, logger: Logger
) -> dict:
    """
    Determine the lowest runway threshold and the highest point on the CLine (DATM specifies CLine as reference line)

    args:
    ebh_line (pl.DataFrame): ebh line dataframe
    logger (Logger): Logger object

    returns:
    lowest_threshold (pl.DataFrame): lowest runway threshold coordinates
    highest_point_CL (pl.DataFrame): highest point on the CLine coordinates
    """

    # get the lowest threshold and the highest point on the CLine
    lowest_threshold = ebh_line.filter(pl.col("orthoH") == ebh_line["orthoH"].min())
    highest_point_CL = ebh_line.filter(pl.col("orthoH") == ebh_line["orthoH"].max())

    logger.info(f"Lowest runway threshold is {lowest_threshold}")
    logger.info(f"Highest point on the CLine is {highest_point_CL}")

    return lowest_threshold, highest_point_CL


def main():
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_gradient_ebhlines(
        args=sys.argv[1:]
    )
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    get_gradient_ebhlines(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":
    main()
