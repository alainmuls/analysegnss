#!/usr/bin/env python

import argparse
import os
import re
import sys
from logging import Logger
from math import atan2, degrees, sqrt, fabs

import polars as pl
from tabulate import tabulate

from config import ERROR_CODES
import ppk_rnx2rtkp
import rtk_pvtgeod
from gnss.gnss_dt import gnss2dt
from rtkpos import rtk_constants as rtkc
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger
from utils.utilities import str_yellow


def get_ppk_dataframe(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """get the dataframe obtained from PPK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with PPK solution
    """
    ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py"]
    ppk_rnx2rtkp_args.append("--pos_fn")
    ppk_rnx2rtkp_args.append(parsed_args.ebh_fn)
    if parsed_args.verbose:
        match parsed_args.verbose:
            case 1:
                ppk_rnx2rtkp_args.append("-v")
            case 2:
                ppk_rnx2rtkp_args.append("-vv")
            case 3:
                ppk_rnx2rtkp_args.append("-vvv")

    logger.info(f"ppk_rnx2rtkp_args = {ppk_rnx2rtkp_args}")

    df_pos = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

    return df_pos


def get_rtk_dataframe(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """get the dataframe obtained from RTK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with RTK solution
    """
    rtk_pvtgeod_args = ["rtk_pvtgeod.py"]
    rtk_pvtgeod_args.append("--sbf_fn")
    rtk_pvtgeod_args.append(parsed_args.ebh_fn)
    if parsed_args.verbose:
        match parsed_args.verbose:
            case 1:
                rtk_pvtgeod_args.append("-v")
            case 2:
                rtk_pvtgeod_args.append("-vv")
            case 3:
                rtk_pvtgeod_args.append("-vvv")

    logger.info(f"rtk_pvtgeod_args = {rtk_pvtgeod_args}")

    df_pos = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

    return df_pos


def read_ebh_line_timings(timings_fn: str, logger: Logger) -> dict:
    """read the ebh lines timings from the file

    Args:
        timings_fn (str): text file with timings of ebh lines

    Returns:
        dict: contains the ebh lines and begin- end-timings
    """
    # check if the timings file is readable
    if not os.path.isfile(timings_fn) or not os.access(timings_fn, os.R_OK):
        print(f"File {timings_fn} is not readable")
        sys.exit(ERROR_CODES["E_FILE_NOT_EXIST"])

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
            values = [float(value) if "." in value else int(value) for value in matches]
            # print(f"values = {values}")

            line_timings[key] = [
                gnss2dt(week=values[0], tow=values[1]),
                gnss2dt(week=values[2], tow=values[3]),
            ]

            # line_timings[key] = tuple(
            #     [sod_to_time(float(value)) for value in vals[0].strip().split(",")]
            # )

    # for line, timings in line_timings.items():
    #     print(
    #         f"{line} = {timings[0].strftime('%Y/%m/%d %H:%M:%S')} - {timings[1].strftime('%Y/%m/%d %H:%M:%S')}"
    #     )

    logger.info(
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

        if logger is not None:
            logger.debug(f"row_start = {row_start}")
            logger.debug(
                f"row_start.select(['UTM.E']) = {row_start.select(['UTM.E'])} |  {type(row_start.select(['UTM.E']))}"
            )
            logger.debug(
                f"row_start.select(['UTM.E']).to_numpy()[0] = {row_start.select(['UTM.E'])} |  {type(row_start.select(['UTM.E']))}"
            )
            logger.debug(
                f"row_start.select(['UTM.E', 'UTM.N']) = {row_start.select(['UTM.E', 'UTM.N'])}"
            )
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
    parsed_args: argparse.Namespace,
    logger: Logger = None,
):
    """extract the EBH lines from the dataframe and order them according to the same map_angle

    Args:
        df_pos (pl.DataFrame): dataframe of whole measurement campaign
        ebh_timings (dict): timings and map_angle of each EBH line
        parsed_args (argparse.Namespace): CLI arguments
        logger (Logger): logger object
    """
    cl_map_angle = ebh_timings["CL"][2]
    # print(f"cl_map_angle = {cl_map_angle}")

    # keep the dataframes in a dictionary
    ebh_lines_assur = dict()

    for ebh_key, timings in ebh_timings.items():
        # print(f"ebh_key = {ebh_key}, timings = {timings}")

        # filter the dataframe for the ebh line
        ebh_df = df_pos.filter(pl.col("DT") >= timings[0]).filter(
            pl.col("DT") <= timings[1]
        )

        # check orientation of the current line
        if cl_map_angle - 10 < timings[2] < cl_map_angle + 10:
            df_line = df_pos.filter(
                pl.col("DT").is_between((timings[0]), (timings[1])),
            )
        else:
            df_line = df_pos.filter(
                pl.col("DT").is_between((timings[0]), (timings[1])),
            ).reverse()

        print(f"df_line = {df_line}")

        # thin out the df_line to keep positions every 0.5 meters
        ebh_lines_assur[ebh_key] = ebh_lines_thin_out(
            df_line=df_line, parsed_args=parsed_args, logger=logger
        )

    return ebh_lines_assur


def euclidean_distance(x1, y1, x2, y2):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def ebh_lines_thin_out(
    df_line: pl.DataFrame,
    parsed_args: argparse.Namespace,
    logger: Logger = None,
) -> pl.DataFrame:
    """thin out the dataframe to keep positions every 0.5 meters

    Args:
        df_line (pl.DataFrame): dataframe with positions of the ebh line
        parsed_args (argparse.Namespace): CLI arguments
        logger (Logger): logger object

    Returns:
        pl.DataFrame: thinned out dataframe
    """
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

    # keep only the rows where the quality is 1 (FIX)
    if parsed_args.ppk:
        df_line = df_line.filter(pl.col("Q") == 1).lazy()
    elif parsed_args.rtk:
        df_line = df_line.filter(pl.col("Type") == 4).lazy()
    else:
        if logger is not None:
            logger.error("No processing type 'Q' or 'Type' found. Exiting...")
        sys.exit(ERROR_CODES["E_NO_QUAL"])

    #  Thinning out the dataframe to keep positions every 0.5 meters

    # This is done first by applying the modulo operator of 0.5 on dist0
    df_line = df_line.with_columns(
        dist0_mod05=pl.col("dist0").map_elements(lambda x: x % 0.5, return_dtype=float)
    ).lazy()

    # Then, we calculate the difference between the current value and the previous values
    df_line = df_line.with_columns(dist_mod05_diff=pl.col("dist0_mod05").diff()).lazy()

    # keep only the rows where the difference is lower than -0.25. This will produce df with the same length
    df_assur = df_line.filter(pl.col("dist_mod05_diff") < -0.25).lazy()

    if logger is not None:
        pl.Config.set_tbl_rows(30)
        logger.debug(f"df_line = \n{df_line.collect()}")
        # logger.debug first 30 rows of the dataframe
        logger.debug(f"df_line.head(30) = \n{df_line.head(30)}")
        # thin out the df_line to keep positions every 0.5 meters
        logger.debug(f"df_assur = \n{df_assur.collect()}")
        logger.debug(f"df_assur.head(30) = \n{df_assur.head(30)}")

    return df_assur.collect()


def ebh_lines(argv: list):
    """get the ebh_lines from RTK or PPK processing

    Args:
        argv (list): CLI arguments
    """
    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ebh_lines(args=argv[1:])
    # print(f"\nParsed arguments: {type(args_parsed)}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {args_parsed}")

    # logger.debug(f"program arguments: {args_parsed}")

    # get the dataframe according to the processing type (RTK or PPK)
    if args_parsed.ppk:
        # call ppp_rnx2rtkp to get the position dataframe
        pos_df = get_ppk_dataframe(parsed_args=args_parsed, logger=logger)

        logger.info(f"Dataframe obtained from PPK processing of {args_parsed.ebh_fn}")
        print(
            f"Dataframe obtained from {str_yellow('PPK')} processing of {str_yellow(args_parsed.ebh_fn)}"
        )
        df_pos = pos_df.select(
            [
                "DT",
                "Q",
                "ns",
                "UTM.E",
                "UTM.N",
                "orthoH",
                # "latitude(deg)",
                # "longitude(deg)",
            ]
        )
    elif args_parsed.rtk:
        # call rtk_pvtgeod to get the position dataframe
        pos_df = get_rtk_dataframe(parsed_args=args_parsed, logger=logger)

        logger.info(
            f"Dataframe obtained from {str_yellow('RTK')} processing of "
            f"{str_yellow(args_parsed.ebh_fn)}"
        )
        print(
            f"Dataframe obtained from {str_yellow('RTK')} processing of "
            f"{str_yellow(args_parsed.ebh_fn)}"
        )
        df_pos = pos_df.select(["DT", "Type", "NrSV", "UTM.E", "UTM.N", "orthoH"])
    else:
        logger.error("No processing type selected")
        sys.exit(ERROR_CODES["E_FILE_NOT_EXIST"])

    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        logger.info(df_pos)
        print(df_pos)

    # read the timings for the ebh_lines
    ebh_timings = read_ebh_line_timings(timings_fn=args_parsed.timing_fn, logger=logger)

    # calculate the map_angle for each ebh_line
    ebh_lines_map_angle(df_pos=df_pos, ebh_timings=ebh_timings, logger=logger)
    for ebh_key, timings in ebh_timings.items():
        logger.info(
            f"{ebh_key:9s}: {timings[0].strftime('%Y/%m/%d %H:%M:%S')}"
            f" - {timings[1].strftime('%Y/%m/%d %H:%M:%S')} | {timings[2]:6.1f}"
        )

    # extract the lines from the dataframe
    ebh_assur_lines = ebh_lines_extract(
        df_pos=df_pos, ebh_timings=ebh_timings, parsed_args=args_parsed, logger=logger
    )

    # save in CSV files using ";" as separator
    for ebh_key, ebh_assur_line in ebh_assur_lines.items():
        # name the file according to the ebh line key
        ebh_line_fn = f"{args_parsed.desc}_{ebh_key}.csv"
        logger.info(
            f"Writing CSV AssurTool file for {str_yellow(ebh_key)} to "
            f"{str_yellow(ebh_line_fn)}\n"
            f"{ebh_assur_line.select(['UTM.E', 'UTM.N', 'orthoH'])}"
        )

        # keep the columns UTM.E, UTM.N and ortoH and write to CSV file
        ebh_assur_line.select(["UTM.E", "UTM.N", "orthoH"]).write_csv(
            ebh_line_fn, separator=";", include_header=False, float_precision=3
        )
        pass


if __name__ == "__main__":
    ebh_lines(argv=sys.argv)
