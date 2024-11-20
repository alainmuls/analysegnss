#!/usr/bin/env python

import os
import sys
from logging import Logger

import polars as pl

from config import ERROR_CODES, GNSS_DICT

from rinex.rinex_obs_class import RINEX_OBS
from utils import argument_parser, init_logger
import rnxobs_csv
import rnxnav_csv


def rnx_csv(argv: list):
    """reads RINEX observation & navigation file and converts it to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rnx_csv(args=argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # Convert integer verbosity to -v, -vv, or -vvv
    verbosity_arg = "-" + "v" * args_parsed.verbose if args_parsed.verbose else ""

    # call rnxobs_csv.py to convert RINEX observation file to CSV file
    # create the arguments for rnxobs_csv.py
    rnxobs_argv = [
        "rnxobs_csv.py",
        "--obs_fn",
        args_parsed.obs_fn,
        "--gnss",
        args_parsed.gnss,
    ]
    # Add verbosity arg only if it's not empty
    if verbosity_arg:
        rnxobs_argv.append(verbosity_arg)
    # run conversion of RINEX observation file to CSV file
    rnxobs_csv.rnxobs_csv(argv=rnxobs_argv)

    # call rnxnav_csv.py to convert RINEX navigation file to CSV file
    # create the arguments for rnxobs_csv.py
    rnxnav_args = [
        "rnxnav_csv.py",
        "--nav_fn",
        args_parsed.nav_fn,
        "--gnss",
        args_parsed.gnss,
    ]
    # Add verbosity arg only if it's not empty
    if verbosity_arg:
        rnxnav_args.append(verbosity_arg)
    # run conversion of RINEX navigation file to CSV file
    rnxnav_csv.rnxnav_csv(argv=rnxnav_args)


if __name__ == "__main__":
    rnx_csv(argv=sys.argv)
