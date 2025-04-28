#!/usr/bin/env python

import argparse
import os
import re
import sys
from logging import Logger
from math import atan2, degrees, fabs, sqrt

import polars as pl
from rich import print as rprint
from tabulate import tabulate

from analysegnss.analyse.pnt_quality_analysis import quality_analysis
from analysegnss.config import ERROR_CODES
from analysegnss.gnss.gnss_dt import gnss2dt
import analysegnss.rtkpos.rtkpos_reader as rtkpos_reader
import analysegnss.rtkpos.rtklib_constants as rtklibc
import analysegnss.sbf.sbf_reader as sbf_reader
from analysegnss.utils import init_logger
from analysegnss.utils.utilities import str_red, str_yellow
from analysegnss.utils.argument_parser import argument_parser_ebh_lines


def get_ppk_dataframe(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """get the dataframe obtained from PPK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with PPK solution
    """

    df_pos, _ = rtkpos_reader.rtkp_pos(parsed_args=parsed_args, logger=logger)

    return df_pos


def get_rtk_dataframe(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """get the dataframe obtained from RTK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with RTK solution
    """

    df_pos, _ = sbf_reader.sbf_reader(parsed_args=parsed_args, logger=logger)

    return df_pos


def read_ebh_line_timings(
    timings_fn: str | None, timings: dict | None, logger: Logger
) -> dict:
    """read the ebh lines timings from the file or dict

    Args:
        timings_fn (str): text file with timings of ebh lines
        timings (dict): dict with ebh keys and timestamps (week number and tow) as tuples
    Returns:
        dict: contains the ebh lines and begin- end-timings
    """
    if timings_fn is not None:
        # check if the timings file is readable
        if not os.path.isfile(timings_fn) or not os.access(timings_fn, os.R_OK):
            logger.error(f"File {timings_fn} is not readable")
            sys.exit(ERROR_CODES["E_FILE_NOT_EXIST"])

        logger.debug(f"Reading ebh timings from file {timings_fn}")

        # Regular expression pattern to match both integers and float values
        pattern = r"\d+\.\d+|\d+"

        # read the timings file
        line_timings = dict()
        with open(timings_fn, "r") as f:
            while line := f.readline():
                key = line.split(":")[0]
                vals = line.split(":")[1:]

                # Find all matches of the pattern in the input string
                matches = re.findall(pattern, vals[0])

                # Convert the extracted strings to their appropriate types (int or float)
                values = [
                    float(value) if "." in value else int(value) for value in matches
                ]
                # print(f"values = {values}")

                line_timings[key] = [
                    gnss2dt(week=values[0], tow=values[1]),
                    gnss2dt(week=values[2], tow=values[3]),
                ]

    elif timings is not None:
        logger.debug(f"ebh_timings from dict = {timings}")
        line_timings = {}
        for key, value in timings.items():
            line_timings[key] = [
                gnss2dt(week=value[0][0], tow=value[0][1]),
                gnss2dt(week=value[1][0], tow=value[1][1]),
            ]

    else:
        logger.error("No ebh timings provided. EXITING.")
        sys.exit(ERROR_CODES["E_NO_EBH_TIMINGS"])

    # check if the timings file is empty
    if not line_timings:
        rprint(
            f"[red]ERROR: File {timings_fn} is empty. Probably no timings key found in SBF comments or sbf comment are modified. Exiting[/red]"
        )
        logger.critical(f"File {timings_fn} is empty. Exiting")
        sys.exit(ERROR_CODES["E_FILE_EMPTY"])

    logger.debug(
        tabulate(
            line_timings.items(),
            headers=["EBH Line", "EBH Timings"],
            tablefmt="fancy_outline",
        )
    )

    return line_timings


def ebh_lines_map_angle(
    df_pos: pl.DataFrame,
    ebh_timings: dict,
    logger: Logger = None,
) -> None:
    """calculate the map angle for each ebh line

    Args:
        df_pos (pl.DataFrame): dataframe with position information
        ebh_timings (dict): dictionary with ebh lines and timings
    """
    for ebh_key, timings in ebh_timings.items():
        # print(f"ebh_key = {ebh_key}, timings = {timings}")

        row_start = df_pos.filter(pl.col("DT") == timings[0])
        row_end = df_pos.filter(pl.col("DT") == timings[1])

        # Checking if dataframe is not empty. The following if clause handles the case when fewer lines are processed (for PPK) than there are key in ebh_timings
        if row_start.is_empty():
            logger.warning(
                f"No data found for {timings[0].strftime('%Y/%m/%d %H:%M:%S')}. Skipping line {ebh_key}."
            )

        else:
            if logger is not None:
                logger.debug(f"row_start = {row_start}")
                logger.debug(f"row_end = {row_end}")

            # calculate the map_angle
            map_angle = atan2(
                row_end["UTM.E"].to_numpy()[0] - row_start["UTM.E"].to_numpy()[0],
                row_end["UTM.N"].to_numpy()[0] - row_start["UTM.N"].to_numpy()[0],
            )
            # print(f"map_angle = {map_angle} | {degrees(map_angle)}")

            # add the map_angle to the ebh_timings dictionary
            ebh_timings[ebh_key].append(degrees(map_angle))


def ebh_lines_extract(
    df_pos: pl.DataFrame,
    ebh_timings: dict,
    logger: Logger = None,
):
    """extract the EBH lines from the dataframe and order them according to the same map_angle

    Args:
        df_pos (pl.DataFrame): dataframe of whole measurement campaign
        ebh_timings (dict): timings and map_angle of each EBH line
        logger (Logger): logger object
    """

    # init reference map angle
    ref_map_angle = ""
    # keep the dataframes in a dictionary
    ebh_lines_assur = dict()

    for ebh_key, timings in ebh_timings.items():

        # We are going fetch the reference map angle and use this to order the EBH lines in the same direction

        if ref_map_angle == "":
            ref_map_angle = ebh_timings[ebh_key][2]
            logger.info(f"Using {ebh_key} as reference for ebh line direction")

        # check orientation of the current line
        if ref_map_angle - 10 < timings[2] < ref_map_angle + 10:
            ebh_lines_assur[ebh_key] = df_pos.filter(
                pl.col("DT").is_between((timings[0]), (timings[1])),
            )
        else:
            ebh_lines_assur[ebh_key] = df_pos.filter(
                pl.col("DT").is_between((timings[0]), (timings[1])),
            ).reverse()

        # print(f"df_line = {df_line}")
        logger.debug(f"Obtained ebh line {ebh_key} between {timings}")

    return ebh_lines_assur


def euclidean_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def ebh_line_thin_out(
    df_line: pl.DataFrame,
    parsed_args: argparse.Namespace,
    logger: Logger = None,
) -> pl.DataFrame:
    """thin out the dataframe to keep positions every 0.5 meters and only keeps RTK/PPK fixed results

    Args:
        df_line (pl.DataFrame): dataframe with positions of the ebh line
        parsed_args (argparse.Namespace): CLI arguments
        logger (Logger): logger object

    Returns:
        pl.DataFrame: thinned out dataframe + only RTK/PPK fixed results
    """
    logger.info(
        f"Thinning out the dataframe to keep positions every 0.5 meters and only keeps RTK/PPK fixed results"
    )
    # get the UTM coordinates of the first point of the line
    utm_start = df_line.select(["UTM.E", "UTM.N"]).row(index=0)
    # print(f"utm_start = {utm_start}")

    # add distance from start point of current line
    df_line = df_line.with_columns(
        pl.struct(["UTM.E", "UTM.N"])
        .map_elements(
            lambda x: euclidean_distance(
                utm_start[0],
                utm_start[1],
                x["UTM.E"],
                x["UTM.N"],
            ),
            return_dtype=pl.Float32,
        )
        .alias("dist0")
    ).lazy()

    # keep only the rows where the quality is FIX and FLOAT (EBH_process warns user if assur results contain floats)
    if hasattr(parsed_args, "pos_ifn") and parsed_args.pos_ifn:
        df_line = df_line.filter(pl.col("Q").is_in([1, 2])).lazy()
    elif hasattr(parsed_args, "sbf_ifn") and parsed_args.sbf_ifn:
        df_line = df_line.filter(pl.col("Type").is_in([4, 5])).lazy()
    else:
        if logger is not None:
            logger.error(
                "No GNSS qual type 'Q' or 'Type' relating to fix or float found. Exiting..."
            )
        sys.exit(ERROR_CODES["E_NO_QUAL"])

    #  Thinning out the dataframe to keep positions every 0.5 meters

    # This is done first by applying the modulo operator of 0.5 on dist0
    df_line = df_line.with_columns(dist0_mod05=pl.col("dist0") % 0.5).lazy()

    # Then, we calculate the difference between the current value and the previous values
    df_line = df_line.with_columns(dist_mod05_diff=pl.col("dist0_mod05").diff()).lazy()

    # keep only the rows where the difference is lower than -0.25. This will produce df with the same length
    df_assur = df_line.filter(pl.col("dist_mod05_diff") < -0.25).lazy()

    if logger is not None:
        pl.Config.set_tbl_rows(20)
        logger.debug(f"df_line = \n{df_line.collect()}")
        logger.debug(f"df_assur = \n{df_assur.collect()}")

    return df_assur.collect()


def ebh_lines(parsed_args: argparse.Namespace, logger: Logger):
    """get the ebh_lines from RTK or PPK processing and write to csv files

    Args:
        parsed_args (argparse.Namespace): parsed CLI arguments.
                                        - pos_ifn: path to the pos_ifn file
                                        - sbf_ifn: path to the sbf_ifn file
                                        - timing_ifn: path to the timing_ifn file
                                        - (optional) ebh_timings: dictionary with ebh line keys and timestamps (week number and t of week)
        logger (Logger): logger object

    return:
    qual_ebh_lines (dict):  dictionary containing the quality of the ebh lines
    """

    # logger.debug(f"program arguments: {parsed_args}")

    # get the dataframe according to the processing type (RTK or PPK)
    # Using hasattr here to check if the argument exists (this fixes argparse.namespace errors across different python scripts)
    if hasattr(parsed_args, "pos_ifn") and parsed_args.pos_ifn:
        # call ppp_rnx2rtkp to get the position dataframe
        pos_df = get_ppk_dataframe(parsed_args=parsed_args, logger=logger)

        logger.info(f"Dataframe obtained from PPK processing of {parsed_args.pos_ifn}")
        # print(
        #    f"Dataframe obtained from {str_yellow('PPK')} processing of {str_yellow(parsed_args.pos_ifn)}"
        # )

        df_pos = pos_df.select(
            [
                "DT",
                "Q",
                "pnt_qual",
                "ns",
                "UTM.E",
                "UTM.N",
                "orthoH",
            ]
        )
    elif hasattr(parsed_args, "sbf_ifn") and parsed_args.sbf_ifn:
        # call rtk_pvtgeod to get the position dataframe
        pos_df = get_rtk_dataframe(parsed_args=parsed_args, logger=logger)

        logger.info(
            f"Dataframe obtained from {str_yellow('RTK')} processing of "
            f"{str_yellow(parsed_args.sbf_ifn)}"
        )
        # print(
        #    f"Dataframe obtained from {str_yellow('RTK')} processing of "
        #    f"{str_yellow(parsed_args.sbf_ifn)}"
        # )
        df_pos = pos_df.select(
            ["DT", "Type", "pnt_qual", "NrSV", "UTM.E", "UTM.N", "orthoH"]
        )
    else:
        logger.error("No processing type selected or no input file provided. EXITING.")
        sys.exit(ERROR_CODES["E_FILE_NOT_EXIST"])

    logger.debug(df_pos)

    # read the timings for the ebh_lines
    if hasattr(parsed_args, "timing_ifn") and parsed_args.timing_ifn:
        ebh_timings = read_ebh_line_timings(
            timings_fn=parsed_args.timing_ifn, timings=None, logger=logger
        )
        logger.debug(f"ebh_timings extracted from {parsed_args.timing_ifn}")
        logger.debug(f"ebh_timings = {ebh_timings}")
    elif hasattr(parsed_args, "ebh_timings") and parsed_args.ebh_timings:
        ebh_timings = read_ebh_line_timings(
            timings_fn=None, timings=parsed_args.ebh_timings, logger=logger
        )
        logger.debug(f"ebh_timings extracted from parsed_args.ebh_timings")
        logger.debug(f"ebh_timings = {ebh_timings}")
    else:
        logger.error("No ebh timings provided. EXITING.")
        sys.exit(ERROR_CODES["E_NO_EBH_TIMINGS"])

    # calculate the map_angle for each ebh_line
    ebh_lines_map_angle(df_pos=df_pos, ebh_timings=ebh_timings, logger=logger)

    # only keep the ebh_timings rows that have the calculated angle timings[2]
    ebh_timings = {key: value for key, value in ebh_timings.items() if len(value) == 3}

    for ebh_key, timings in ebh_timings.items():
        logger.info(
            f"{ebh_key:9s}: {timings[0].strftime('%Y/%m/%d %H:%M:%S')}"
            f" - {timings[1].strftime('%Y/%m/%d %H:%M:%S')} | {timings[2]:6.1f}"
        )

    # extract the lines from the dataframe
    ebh_assur_lines = ebh_lines_extract(
        df_pos=df_pos, ebh_timings=ebh_timings, logger=logger
    )

    qual_ebh_lines = {}  # dict to store the quality of the ebh lines
    qual_ebh_lines_tabular = {}
    # check quality of each ebh line
    # Thin out line, keep RTK/PPK fixed results
    # save in CSV files using ";" as separator
    # TODO check if ebh lines have the same distances
    for ebh_key, ebh_assur_line in ebh_assur_lines.items():
        # Checking quality of each ebh line for ppk and rtk result.
        # This info is needed to decide whether rtk or ppk quality is sufficient for ASSUR
        if hasattr(parsed_args, "pos_ifn") and parsed_args.pos_ifn:
            qual_ebh_lines[ebh_key], qual_ebh_lines_tabular[ebh_key] = quality_analysis(
                df_pnt=ebh_assur_line,
                file_name=os.path.basename(parsed_args.pos_ifn),
                logger=logger,
            )
            logger.info(
                f"The ppk quality of the line {ebh_key} is {qual_ebh_lines[ebh_key]}"
            )
            # TODO put here function (ebhrtk_to_csv) to save dataframes to csv files that can be used for plotting
        elif hasattr(parsed_args, "sbf_ifn") and parsed_args.sbf_ifn:
            qual_ebh_lines[ebh_key], qual_ebh_lines_tabular[ebh_key] = quality_analysis(
                df_pnt=ebh_assur_line,
                file_name=os.path.basename(parsed_args.sbf_ifn),
                logger=logger,
            )
            logger.warning(
                f"The rtk quality of the line {ebh_key} is {qual_ebh_lines[ebh_key]}"
            )

            # TODO put here function (ebhppk_to_csv) to save dataframes to csv files that can be used for plotting
        else:
            pass

        # thin out the df_line to keep positions every 0.5 meters and keep only RTK/PPK fixed results
        ebh_assur_line = ebh_line_thin_out(
            df_line=ebh_assur_line, parsed_args=parsed_args, logger=logger
        )
        # name the file according to the ebh line key
        ebh_line_fn = f"{parsed_args.desc}_{ebh_key}.csv"
        rprint(
            f"\nWriting CSV AssurTool file for [yellow]{ebh_key}[/yellow] to "
            f"[yellow]{ebh_line_fn}[/yellow]"
        )
        logger.debug(
            f"Writing CSV AssurTool file for {str_yellow(ebh_key)} to "
            f"{str_yellow(ebh_line_fn)}"
            f"{ebh_assur_line.select(['UTM.E', 'UTM.N', 'orthoH'])}"
        )

        # keep the columns UTM.E, UTM.N and orthoH
        ebh_assur_df = ebh_assur_line.select(["UTM.E", "UTM.N", "orthoH"])

        # if ebh destination directory is not specified it will write to EBH_ASSUR dir in the directory of the input sbf or pos file
        if parsed_args.ebh_dest_dir == None:

            # destination directory of ebh ASSUR files
            if hasattr(parsed_args, "pos_ifn") and parsed_args.pos_ifn:

                parsed_args.ebh_dest_dir = os.path.join(
                    os.path.dirname(parsed_args.pos_ifn), "EBH_ASSUR"
                )
            elif hasattr(parsed_args, "sbf_ifn") and parsed_args.sbf_ifn:

                parsed_args.ebh_dest_dir = os.path.join(
                    os.path.dirname(parsed_args.sbf_ifn), "EBH_ASSUR"
                )

            else:
                pass

        # writing ebh assur line to file
        ebh_to_assurfmt(
            ebh_assur_df=ebh_assur_df,
            ebh_assur_fn=ebh_line_fn,
            dest_dir=parsed_args.ebh_dest_dir,
            logger=logger,
        )

    return qual_ebh_lines, qual_ebh_lines_tabular


def ebh_to_assurfmt(
    ebh_assur_df: pl.DataFrame, ebh_assur_fn: str, dest_dir: str, logger: Logger
) -> None:
    """
    Write ebh file (according to ASSUR format) to a destination directory

    args:
    ebh_assur_df (pl.DataFrame): EBH ASSUR formatted dataframe
    ebh_assur_fn (str): file name of EBH ASSUR
    dest_dir (str): Path to destination directory
    logger (Logger): Logger object
    """

    # Check if the directory already exists
    if not os.path.exists(dest_dir):
        try:
            os.mkdir(dest_dir)
            logger.info(f"Directory created: {dest_dir}")
        except OSError as e:
            logger.info(f"Error creating directory {dest_dir}: {e}")

    # write ebh assur to a file at dest_dir
    ebh_assur_fp = os.path.join(dest_dir, ebh_assur_fn)  # ebh_assur_fullpath
    logger.debug(f"writing ebh assur df to {ebh_assur_fp}")

    ebh_assur_df.write_csv(
        ebh_assur_fp, separator=";", include_header=False, float_precision=3
    )

    # check if the file was written
    if not os.path.isfile(ebh_assur_fp) or not os.access(ebh_assur_fp, os.R_OK):
        logger.error(f"Error writing ebh assur file to {ebh_assur_fp}")
    else:
        logger.info(f"Done writing ebh assur file to {ebh_assur_fp}")
        rprint(f"Done writing ebh assur file to [yellow]{ebh_assur_fp}[/yellow]\n")


def ebhrtk_to_csv(
    rtk_df: pl.dataframe, rtk_fn: str, dest_dir: str, logger: Logger
) -> None:
    """
    Write ebh rtk (sourced from sbf) dataframe with UTM coordinates, orthometric H, lat lon coordinates, Datetime, Type and NrSV
    to csv file.

    args:
    rtk_df (pl.DataFrame): RTK dataframe
    rtk_fn (str): file name of RTK
    dest_dir (str): Path to destination directory
    logger (Logger): Logger object
    """


def ebhppk_to_csv(
    rtk_df: pl.dataframe, rtk_fn: str, dest_dir: str, logger: Logger
) -> None:
    """
    Write ebh ppk (sourced from sbf) dataframe with UTM coordinates, orthometric H, lat lon coordinates, Datetime, Type and NrSV
    to csv file.

    args:
    rtk_df (pl.DataFrame): RTK dataframe
    rtk_fn (str): file name of RTK
    dest_dir (str): Path to destination directory
    logger (Logger): Logger object
    """


def main():
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    parsed_args = argument_parser_ebh_lines(script_name=script_name, args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {parsed_args}")

    ebh_lines(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":
    main()
