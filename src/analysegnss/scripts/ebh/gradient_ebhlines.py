#! /usr/bin/env python

# import standard libraries
import argparse
from logging import Logger
import os
import sys

# import third-party libraries
import numpy as np
import polars as pl
from rich import print as rprint

# import local libraries
from analysegnss.utils import argument_parser, init_logger

#############################################################
# This script determines the maximum longitudinal and transversal
# gradients of the runway. It needs at least two (ebh) lines
# that contain xy and height coordinates but preferably more including the centerline.

# A design decision was made to import the generated ASSUR formatted csv files from a directory.
# This ensures that the script is standalone.

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
def gradient_ebhlines(parsed_args: argparse.Namespace, logger: Logger) -> str:
    """
    Get the gradient of the EBH lines
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.

    args:
    parsed_args (argparse.Namespace): parsed arguments.
                                            - input_dir: directory containing the ebh lines
                                            - output_dir: directory to save the output
                                            - output_filename: name of the output file
                                            - log_dest: destination of the log file
    logger (Logger): Logger object

    returns:
    gradient_runway_output (str):  string with the
                                    longitudinal and transversal gradient information of the runway
                                    the coordinates of the highest point on the CLine
                                    the centerline coordinates on the lowest threshold
                                    the distance from the lowest threshold to the highest point on the CLine
                                    the slope from the lowest threshold to the highest point on the CLine
    """

    # collect the ebh lines from the directory #TODO get the ebh lines from the ebh_lines.py script?
    ebh_lines, ebh_project_name = collect_ebh_lines(parsed_args=parsed_args, logger=logger)

    # calculate the length of the runway
    length_of_runway = euclidean_distance(
        x1=ebh_lines["CL"].select("UTM.E").head(1).item(),
        x2=ebh_lines["CL"].select("UTM.E").tail(1).item(),
        y1=ebh_lines["CL"].select("UTM.N").head(1).item(),
        y2=ebh_lines["CL"].select("UTM.N").tail(1).item(),
        z1=ebh_lines["CL"].select("orthoH").head(1).item(),
        z2=ebh_lines["CL"].select("orthoH").tail(1).item(),
    )

    ########################################################
    ##### Determine MAX LONGITUDINAL RUNWAY GRADIENT #######
    ########################################################

    # determine the lowest threshold and the highest point on the Centerline
    lowest_threshold, highest_point_CL = lowest_rwy_threshold_and_highest_point_CL(
        ebh_line=ebh_lines["CL"], logger=logger
    )

    # determine the highest gradient from the lowest threshold to the highest point on the CLine
    (
        max_longitudinal_gradient_rwy,
        dist_threshold_and_Hpoint_CL,
        slope_threshold_to_Hpoint_CL,
    ) = gradient_3d(
        x1=lowest_threshold[0],
        y1=lowest_threshold[1],
        z1=lowest_threshold[2],
        x2=highest_point_CL[0],
        y2=highest_point_CL[1],
        z2=highest_point_CL[2],
        logger=logger,
    )
    logger.info(
        f"Max LONGITUDINAL gradient from lowest threshold to highest point on the CLine is {max_longitudinal_gradient_rwy} degrees"
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
    outer_line1, outer_line2, max_dist = outermost_lines(ebh_lines=ebh_lines, logger=logger)
    # Determine the max TRANSVERSAL gradient across the width of the runway
    max_transversal_gradient_rwy = max_transversal_gradient(
        outer_line1=ebh_lines[outer_line1],
        outer_line2=ebh_lines[outer_line2],
        logger=logger,
    )

    # store the output in a dictionary #TODO: add UTM.Z to the output
    gradient_runway_output = f"""
        EBH project name:\t\t\t\t\t\t\t{ebh_project_name}\n
        Measured length of the runway (meters):\t\t\t\t\t{length_of_runway:.2f}
        Measured width of the runway (meters):\t\t\t\t\t{max_dist:.2f}\n
        Maximum LONGITUDINAL gradient of the runway (degrees):\t\t\t{max_longitudinal_gradient_rwy:.2f}
        Maximum TRANSVERSAL gradient of the runway (degrees):\t\t\t{max_transversal_gradient_rwy:.2f}\n
        Centerline coordinates of highest point (UTM.E, UTM.N, orthoH):\t\t{highest_point_CL}
        Centerline coordinates of lowest threshold (UTM.E, UTM.N, orthoH):\t{lowest_threshold}\n
        Distance from lowest threshold to highest point on centerline (meters):\t{dist_threshold_and_Hpoint_CL:.2f}
    """

    # save the output to a file
    save_output_to_file(
        parsed_args=parsed_args, logger=logger, output=gradient_runway_output
    )

    return gradient_runway_output


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

    """
    logger.debug(
        f"Gradient between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {gradient} degrees"
    )
    logger.debug(
        f"Distance between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {distance} meters"
    )
    logger.debug(
        f"Slope between coordinates ({x1}, {y1}, {z1}) and ({x2}, {y2}, {z2}) is {slope}"
    )
    """

    return gradient, distance, slope


# determine the lowest threshold and the highest point on the CLine
def lowest_rwy_threshold_and_highest_point_CL(
    ebh_line: pl.DataFrame, logger: Logger
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
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

    # convert the lowest threshold and highest point on the CLine to a tuple
    lowest_threshold = (
        lowest_threshold["UTM.E"].item(),
        lowest_threshold["UTM.N"].item(),
        lowest_threshold["orthoH"].item(),
    )
    highest_point_CL = (
        highest_point_CL["UTM.E"].item(),
        highest_point_CL["UTM.N"].item(),
        highest_point_CL["orthoH"].item(),
    )

    logger.info(
        f"Identified the lowest runway threshold with CLine coordinates {lowest_threshold}"
    )
    logger.info(
        f"Identified the highest point on the CLine with the coordinates {highest_point_CL}"
    )

    return lowest_threshold, highest_point_CL


def collect_ebh_lines(parsed_args: argparse.Namespace, logger: Logger) -> dict:
    """
    Collect the ebh lines csv files from a directory

    args:
    parsed_args (argparse.Namespace): parsed arguments.
                                        - input_dir: directory containing the ebh lines
                                        - desc: description of the ebh lines
                                        - output_dir: directory to save the output
                                        - output_filename: name of the output file
                                        - log_dest: destination of the log file
    logger (Logger): Logger object

    returns:
    ebh_lines (dict): dictionary with ebh line keys and ebh line dataframes
    ebh_project_name (str): name of the ebh project
    """

    # check if the directory exists
    if not os.path.exists(parsed_args.input_dir):
        logger.error(f"Directory {parsed_args.input_dir} does not exist")
        sys.exit(1)

    # collect the ebh lines from the directory + metadata
    ebh_project_name = None
    ebh_line_metadata = {} # ebh_line_metadata = {ebh_line_key: ebh_line_fn}
    ebh_lines = {} # ebh_lines = {ebh_line_key: pl.DataFrame}
    for file in os.listdir(parsed_args.input_dir):
        
        # if no tag is provided, collect all ebh lines
        if parsed_args.desc is None:
            if file.endswith(".csv"):
                logger.info(
                    f"Collecting ebh line {file} from directory {parsed_args.input_dir}"
                )
                
                if ebh_project_name is None:
                    # get the ebh project name from the first key/ file name 
                    ebh_project_name = "_".join(file.split("_")[:-1])
                    logger.info(f"Identified ebh project name: {ebh_project_name}")
                
                # create a key for the ebh line sourced from the filename
                ebh_line_key = file.split(".")[0].split("_")[-1]                
                # store the ebh line filename in the metadata
                ebh_line_metadata[ebh_line_key] = file

                logger.debug(f"Collected ebh line metadata: {ebh_line_metadata[ebh_line_key]}")

        # if a tag is provided, collect only the ebh lines with the given tag
        elif parsed_args.desc is not None:
            if file.endswith(".csv") and parsed_args.desc in file:
                logger.info(
                    f"Collecting ebh line {file} from directory {parsed_args.input_dir}"
                )

                if ebh_project_name is None:
                    # get the ebh project name from the first key/ file name 
                    ebh_project_name = "_".join(file.split("_")[:-1])
                    logger.info(f"Identified ebh project name: {ebh_project_name}")

                # create a key for the ebh line sourced from the filename
                ebh_line_key = file.split(".")[0].split("_")[-1]

                # store the ebh line filename in the metadata
                ebh_line_metadata[ebh_line_key] = file

                logger.debug(f"Collected ebh line metadata: {ebh_line_metadata[ebh_line_key]}")
        else:
                pass
           
        # reading the collected ebh lines from dir and storing them in a ebh_lines dictionary {ebh_line_key: pl.DataFrame}
        for ebh_line_key, ebh_line_fn in ebh_line_metadata.items():
            # read the ebh line from the file
            ebh_lines[ebh_line_key] = pl.read_csv(
                source=os.path.join(parsed_args.input_dir, ebh_line_fn),
                separator=";", 
                columns=["UTM.E", "UTM.N", "orthoH"],
                comment_prefix="#",
                has_header=True,
                dtypes={"UTM.E": float, "UTM.N": float, "orthoH": float},
                null_values="NaN",
                )

            logger.debug(f"Extracted {len(ebh_lines[ebh_line_key])} rows from ebh line {ebh_line_fn}")
                

    logger.info(
        f"Extracted ebh lines {ebh_lines.keys()} from directory {parsed_args.input_dir}"
    )

    return ebh_lines, ebh_project_name


def outermost_lines(ebh_lines: dict, logger: Logger) -> tuple[str, str]:
    """
    Determine the most outermost lines
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.

    args:
    ebh_lines (dict): dictionary with ebh line keys and ebh line dataframes
    logger (Logger): Logger object

    returns:
    outer_line1, outer_line2 (str): keys of the most outermost lines
    """

    # get the first point of each line
    first_coords = {}
    for line_name, line_df in ebh_lines.items():
        first_coords[line_name] = {
            "UTM.E": line_df["UTM.E"].head(1).item(),
            "UTM.N": line_df["UTM.N"].head(1).item(),
        }

    # Find the two lines with maximum distance between their first points
    max_dist = 0
    outer_line1 = None
    outer_line2 = None

    for line1 in first_coords.keys():
        for line2 in first_coords.keys():
            if line1 >= line2:  # Skip duplicate pairs and same line
                continue

            dist = euclidean_distance(
                x1=first_coords[line1]["UTM.E"],
                x2=first_coords[line2]["UTM.E"],
                y1=first_coords[line1]["UTM.N"],
                y2=first_coords[line2]["UTM.N"],
            )

            if dist > max_dist:
                max_dist = dist
                outer_line1 = line1
                outer_line2 = line2

    logger.info(
        f"Found outermost lines: {outer_line1} and {outer_line2} with separation {max_dist:.2f}m"
    )

    return outer_line1, outer_line2, max_dist


def max_transversal_gradient(
    outer_line1: pl.DataFrame, outer_line2: pl.DataFrame, logger: Logger
) -> float:
    """
    Determine the maximum transversal gradient between the two lines.
    This is required that the coordinates of each line are more or less parallel to each other.
    Implying thus that the direction of the lines are the same
    This is to ensure that the gradient is calculated correctly.

    args:
    outer_line1 (pl.DataFrame): dataframe with the first outermost line
    outer_line2 (pl.DataFrame): dataframe with the second outermost line
    logger (Logger): Logger object

    returns:
    max_transversal_gradient (float): maximum transversal gradient between the two outermost lines in degrees
    """

    # Calculate gradients between corresponding points of the two lines
    max_transversal_gradient = 0
    # iterate over the number of points in the outermost lines
    # length of the outermost lines are not the same, thus we need to iterate over the shortest line
    for i in range(min(len(outer_line1), len(outer_line2))):
        # Get corresponding points from the polars dataframes
        x1, y1, z1 = outer_line1.row(i)
        x2, y2, z2 = outer_line2.row(i)

        # Calculate gradient
        gradient, _, _ = gradient_3d(x1, y1, z1, x2, y2, z2, logger)
        max_transversal_gradient = max(abs(gradient), max_transversal_gradient)

    logger.info(
        f"Maximum transversal gradient between outermost lines is {max_transversal_gradient:.2f} degrees"
    )

    return max_transversal_gradient


def euclidean_distance(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    z1: float | None = None,
    z2: float | None = None,
) -> float:
    """
    Calculate the euclidean distance between two coordinates in 2D or 3D space.
    # TODO: add this function to the utils.utilities.py file?
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


def save_output_to_file(
    parsed_args: argparse.Namespace, logger: Logger, output: str
) -> str:
    """
    Save the output to a text file

    args:
    parsed_args (argparse.Namespace): parsed arguments
                                        - input_dir: directory containing the ebh lines
                                        - output_dir: directory to save the output
                                        - output_filename: name of the output file
                                        - log_dest: destination of the log file
    logger (Logger): Logger object
    output (str): string with the output to be saved to a file

    returns:
    output_file_path (str): path to the output file
    """
    if parsed_args.output_dir is None:
        # save the output to the same directory as the directory containing the ebh lines
        output_dir = parsed_args.input_dir
    else:
        output_dir = parsed_args.output_dir

    # create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file_path = os.path.join(output_dir, parsed_args.output_filename)
    # save the output to a file
    with open(output_file_path, "w") as f:
        f.write(output)

    # check if the file exists
    if not os.path.exists(output_file_path):
        logger.error(f"Failed to save output to file {output_file_path}")
        sys.exit(1)

    logger.info(f"Saved runway gradients to file {output_file_path}")
    rprint(f"\nSaved runway gradients to file [green]{output_file_path}[/green]\n")

    return output_file_path


def main():
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_gradient_ebhlines(
        args=sys.argv[1:], script_name=script_name
    )
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    # get the gradient of the runway and store the output in a dictionary
    gradient_runway_output = gradient_ebhlines(parsed_args=parsed_args, logger=logger)

    # save the output to a file
    output_file_path = save_output_to_file(
        parsed_args=parsed_args, logger=logger, output=gradient_runway_output
    )

    # print the output to the console
    rprint(f"Output:\n{gradient_runway_output}\n")
    rprint(f"Output file path:\n{output_file_path}\n")


if __name__ == "__main__":
    main()
