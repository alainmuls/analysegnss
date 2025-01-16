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

#############################################################
# This script determines the maximum longitudinal and transversal
# gradients of the runway. It needs at least two (ebh) lines 
# that contain xy and height coordinates but preferably more including the centerline.

# The script will output the maximum longitudinal gradient from the lowest threshold
# to the highest point on the centerline and the maximum transversal gradient across
# the width of the runway.
# This is in accordance with the DATM team. 

# IMPORTANT: The script assumes that the coordinates of each line have the same number of points 
# and thus more or less the same spacing. This is to ensure that the gradient is calculated correctly.
# It also assumes that the lines are parallel to each other implying that the coordinates are more or less
# parallel to each other.
#############################################################


# gradient_ebhlines is the main function that calls other functions to get the gradient of the EBH lines
def gradient_ebhlines(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """
    Get the gradient of the EBH lines
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.

    args:
    parsed_args (argparse.Namespace): parsed arguments
    logger (Logger): Logger object

    returns:
    max_gradient_rwy (float): maximum longitudinal gradient from the lowest threshold to the highest point on the CLine
    max_transversal_gradient_rwy (float): maximum transversal gradient across the width of the runway
    highest_point_CL (pl.DataFrame): highest point on the CLine coordinates
    lowest_threshold (pl.DataFrame): lowest runway threshold coordinates
    dist_threshold_and_Hpoint_CL (float): distance from the lowest threshold to the highest point on the CLine
    slope_threshold_to_Hpoint_CL (float): slope from the lowest threshold to the highest point on the CLine
    """

    # collect the ebh lines from the directory #TODO get the ebh lines from the ebh_lines.py script?
    ebh_lines = collect_ebh_lines(parsed_args=parsed_args, logger=logger)

    ########################################################
    ##### Determine MAX LONGITUDINAL RUNWAY GRADIENT #######
    ########################################################

    # determine the lowest threshold and the highest point on the CLine
    lowest_threshold, highest_point_CL = lowest_rwy_threshold_and_highest_point_CL(
        ebh_line=ebh_lines["CL"], logger=logger
    )

    # determine the highest gradient from the lowest threshold to the highest point on the CLine
    max_gradient_rwy, dist_threshold_and_Hpoint_CL, slope_threshold_to_Hpoint_CL = (
        gradient_3d(
            x1=lowest_threshold["UTM.E"].item(),
            y1=lowest_threshold["UTM.N"].item(),
            z1=lowest_threshold["orthoH"].item(),
            x2=highest_point_CL["UTM.E"].item(),
            y2=highest_point_CL["UTM.N"].item(),
            z2=highest_point_CL["orthoH"].item(),
            logger=logger,
        )
    )
    logger.info(
        f"Max LONGITUDINAL gradient from lowest threshold to highest point on the CLine is {max_gradient_rwy} degrees"
    )
    logger.info(
        f"Distance from lowest threshold to highest point on the CLine is {dist_threshold_and_Hpoint_CL} meters"
    )
    logger.info(
        f"Slope from lowest threshold to highest point on the CLine is {slope_threshold_to_Hpoint_CL}"
    )

    ########################################################
    ##### Determine MAX TRANSVERSAL RUNWAY GRADIENT #######
    ########################################################

    # Find the outermost lines
    outer_line1, outer_line2 = outermost_lines(ebh_lines=ebh_lines, logger=logger)
    # Determine the max TRANSVERSAL gradient across the width of the runway
    max_transversal_gradient_rwy = max_transversal_gradient(
        outer_line1=outer_line1, outer_line2=outer_line2, logger=logger
    )

    logger.info(
        f"Max TRANSVERSAL gradient across the width of the runway is {max_transversal_gradient_rwy} degrees"
    )

    return (
        max_gradient_rwy,
        max_transversal_gradient_rwy,
        highest_point_CL,
        lowest_threshold,
        dist_threshold_and_Hpoint_CL,
        slope_threshold_to_Hpoint_CL,
    )


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

    # check if the directory exists
    if not os.path.exists(parsed_args.dir_name):
        logger.error(f"Directory {parsed_args.dir_name} does not exist")
        sys.exit(1)

    # get the ebh lines from the directory
    ebh_lines = {}
    for file in os.listdir(parsed_args.dir_name):
        if file.endswith(".csv"):
            logger.info(
                f"Collecting ebh line {file} from directory {parsed_args.dir_name}"
            )
            ebh_lines[file] = pl.read_csv(
                source=os.path.join(parsed_args.dir_name, file),
                separator=";",
                columns=["UTM.E", "UTM.N", "orthoH"],
                comment_prefix="#",
                has_header=True,
                dtypes={"UTM.E": float, "UTM.N": float, "orthoH": float},
                null_values="NaN",
            )
            logger.debug(f"Extracted {len(ebh_lines[file])} rows from ebh line {file}")

    logger.info(f"Extracted ebh lines {ebh_lines.keys()} from directory {parsed_args.dir_name}")
    
    # select the centerline
    ebh_lines = rename_ebh_line_keys(ebh_lines=ebh_lines, logger=logger)

    return ebh_lines


def gradient_3d(
    x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, logger: Logger
) -> float:
    """
    Calculate the gradient between two coordinates in 3D space.
    The gradient is the arctan of the slope
    The slope is the difference in height between the two coordinates divided
    by the euclidean distance xy (aka the distance on the plane or run).

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
    euclidean_distance (float): euclidean distance between two coordinates
    slope (float): slope between two coordinates
    """

    # calculate the slope between the two coordinates
    slope = (z2 - z1) / euclidean_distance(x1, x2, y1, y2)
    # calculate the gradient between two coordinates in degrees
    gradient = np.arctan(slope) * 180 / np.pi
    # calculate the distance between the two coordinates aka the slope length
    distance = euclidean_distance(x1, x2, y1, y2, z1, z2)

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
def lowest_rwy_threshold_and_highest_point_CL(
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

    logger.info(f"Identified the lowest runway threshold with CLine coordinates {lowest_threshold}")
    logger.info(f"Identified the highest point on the CLine with the coordinates {highest_point_CL}")

    return lowest_threshold, highest_point_CL

def rename_ebh_line_keys(ebh_lines: dict, logger: Logger) -> dict:
    """
    Rename the ebh line keys when line collected from directory
    The file name is the key and have the following format:
    <ebh_project_name>_<line_name>.csv
    The key is the line name without the .csv extension
    
    """
    
    # rename the ebh line keys
    for key in ebh_lines.keys():
        
        # extract only the line name by splitting the key and removing the .csv extension
        # then splitting the key again by "_" and extracting the last element
        line_key = key.split(".")[0].split("_")[-1]
        ebh_lines[line_key] = ebh_lines.pop(key)
        
        logger.debug(f"Renamed ebh line key {key} to {line_key}")
        
        
    return ebh_lines

def outermost_lines(ebh_lines: dict, logger: Logger) -> dict:
    """
    Determine the most outermost lines
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.
    
    args:
    ebh_lines (dict): dictionary with ebh line keys and ebh line dataframes
    logger (Logger): Logger object

    returns:
    outermost_lines (dict): dictionary with the most outermost lines
    """

    # get the first point of each line
    first_coord = {}
    for line_name, line_df in ebh_lines.items():
        first_coord[line_name] = {
            "UTM.E": line_df["UTM.E"].head(1).item(),
            "UTM.N": line_df["UTM.N"].head(1).item(),
        }

    # Find the two lines with maximum distance between their first points
    max_dist = 0
    outer_line1 = None
    outer_line2 = None

    for line1 in first_coord.keys():
        for line2 in first_coord.keys():
            if line1 >= line2:  # Skip duplicate pairs and same line
                continue

            dist = euclidean_distance(
                x1=first_coord[line1]["UTM.E"],
                x2=first_coord[line2]["UTM.E"],
                y1=first_coord[line1]["UTM.N"],
                y2=first_coord[line2]["UTM.N"],
            )

            if dist > max_dist:
                max_dist = dist
                outer_line1 = line1
                outer_line2 = line2

    logger.info(
        f"Found outermost lines: {outer_line1} and {outer_line2} with separation {max_dist:.2f}m"
    )

    return outer_line1, outer_line2


def max_transversal_gradient(
    outer_line1: dict, outer_line2: dict, logger: Logger
) -> float:
    """
    Determine the maximum transversal gradient between the two lines. 
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.

    args:
    outer_line1 (dict): dictionary with the first outermost line
    outer_line2 (dict): dictionary with the second outermost line
    logger (Logger): Logger object

    returns:
    max_transversal_gradient (float): maximum transversal gradient between the two outermost lines in degrees
    """

    # Calculate gradients between corresponding points of the two lines
    max_transversal_gradient = 0
    for i in range(len(outer_line1)):
        # Get corresponding points
        x1, y1, z1 = outer_line1.items.row(i)
        x2, y2, z2 = outer_line2.items.row(i)

        # Calculate gradient
        gradient, _, _ = gradient_3d(x1, y1, z1, x2, y2, z2, logger)
        max_transversal_gradient = max(abs(gradient), max_transversal_gradient)

    logger.info(
        f"Maximum transversal gradient between outermost lines is {max_transversal_gradient:.2f} degrees"
    )

    return max_transversal_gradient


def euclidean_distance(
    x1: float, x2: float, y1: float, y2: float, z1: float | None = None, z2: float | None = None
) -> float:
    """
    Calculate the euclidean distance between two coordinates

    args:
    x1 (float): x coordinate of the first point
    y1 (float): y coordinate of the first point
    z1 (float): z coordinate of the first point
    x2 (float): x coordinate of the second point
    y2 (float): y coordinate of the second point
    z2 (float): z coordinate of the second point

    returns:
    distance (float): euclidean distance between two coordinates
    """

    if z1 is None or z2 is None:
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    else:
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


def main():
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_gradient_ebhlines(
        args=sys.argv[1:]
    )
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    (
        max_gradient_rwy,
        max_transversal_gradient_rwy,
        highest_point_CL,
        lowest_threshold,
        dist_threshold_and_Hpoint_CL,
        slope_threshold_to_Hpoint_CL,
    ) = gradient_ebhlines(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":
    main()
