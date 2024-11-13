#!/usr/bin/env python

import os
import sys
from logging import Logger

import polars as pl

from config import ERROR_CODES
from rinex.rinex_nav_class import RINEX_NAV
from utils import argument_parser, init_logger
from utils.utilities import str_green


def rnxnav_csv(argv: list):
    """reads RINEX navigation file and converts it to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rnxnav_csv(args=argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create the RINEX object
    try:
        rnxnav = RINEX_NAV(
            rnxnav_fn=args_parsed.rnx_fn,
            gnss=args_parsed.gnss,
            logger=logger,
        )
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_NO_RINEX_NAV"])

    rnxnav_dict = rnxnav.gfzrnx_tabnav()


if __name__ == "__main__":
    rnxnav_csv(argv=sys.argv)
