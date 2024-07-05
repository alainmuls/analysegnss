#!/usr/bin/env python

import argparse
import os
import sys

import polars as pl
from tabulate import tabulate

import globalvars
import ppk_rnx2rtkp
import rtk_pvtgeod
from rtkpos import rtk_constants as rtkc
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger
from utils.utilities import str_yellow
from gnss.gnss_dt import sod_to_time


def get_ppk_dataframe(parsed_args: argparse.Namespace) -> pl.DataFrame:
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

    print(f"ppk_rnx2rtkp_args = {ppk_rnx2rtkp_args}")

    df_pos = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

    return df_pos


def get_rtk_dataframe(parsed_args: argparse.Namespace) -> pl.DataFrame:
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

    print(f"rtk_pvtgeod_args = {rtk_pvtgeod_args}")

    df_pos = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

    return df_pos


def read_ebh_line_timings(timings_fn: str) -> dict:
    """read the ebh lines timings from the file

    Args:
        timings_fn (str): text file with timings of ebh lines

    Returns:
        dict: contains the ebh lines and begin- end-timings
    """
    # check if the timings file is readable
    if not os.path.isfile(timings_fn) or not os.access(timings_fn, os.R_OK):
        print(f"File {timings_fn} is not readable")
        sys.exit(globalvars._ERROR_CODES["E_FILE_NOT_EXIST"])

    # read the timings file
    line_timings = dict()
    with open(timings_fn, "r") as f:
        while line := f.readline():
            key = line.split(":")[0]
            vals = line.split(":")[1:]
            line_timings[key] = [
                sod_to_time(float(value)) for value in vals[0].strip().split(",")
            ]

    for line, timings in line_timings.items():
        print(
            f"{line} = {timings[0].strftime('%H:%M:%S')} - {timings[1].strftime('%H:%M:%S')}"
        )


def ebh_lines(argv: list):
    """get the ebh_lines from RTK or PPK processing

    Args:
        argv (list): CLI arguments
    """
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ebh_lines(args=argv[1:])
    print(f"\nParsed arguments: {args_parsed}")
    print(f"\nParsed arguments: {type(args_parsed)}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

    # get the dataframe according to the processing type (RTK or PPK)
    if args_parsed.ppk:
        # call ppp_rnx2rtkp to get the position dataframe
        pos_df = get_ppk_dataframe(parsed_args=args_parsed)

        logger.info(f"Dataframe obtained from PPK processing of {args_parsed.ebh_fn}")
        print(
            f"Dataframe obtained from {str_yellow('PPK')} processing of {str_yellow(args_parsed.ebh_fn)}"
        )
        df_pos = pos_df.select(["DT", "Q", "ns", "UTM.E", "UTM.N", "orthoH"])
    elif args_parsed.rtk:
        # call rtk_pvtgeod to get the position dataframe
        pos_df = get_rtk_dataframe(parsed_args=args_parsed)

        logger.info(f"Dataframe obtained from RTK processing of {args_parsed.ebh_fn}")
        print(
            f"Dataframe obtained from {str_yellow('RTK')} processing of {str_yellow(args_parsed.ebh_fn)}"
        )
        df_pos = pos_df.select(["DT", "Type", "NrSV", "UTM.E", "UTM.N", "orthoH"])
    else:
        logger.error("No processing type selected")
        sys.exit(globalvars._ERROR_CODES["E_FILE_NOT_EXIST"])

    with pl.Config(tbl_cols=-1):
        logger.info(df_pos)
        print(df_pos)

    # read the timings for the ebh_lines
    ebh_timings = read_ebh_line_timings(timings_fn=args_parsed.timing_fn)


if __name__ == "__main__":
    ebh_lines(argv=sys.argv)
