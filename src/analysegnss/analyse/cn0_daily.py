#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 10:46:52 2020
@author: amuls

Examine the CN0 values of a CSV observation file
"""


import logging
import os
import sys

import polars as pl
from rich.console import Console
from rich import print

from analysegnss.config import ERROR_CODES, GNSS_DICT
from analysegnss.CSV.CSV_class import GNSS_CSV
from analysegnss.utils import argument_parser, init_logger
from analysegnss.utils.utilities import str_green, str_yellow


def cn0_analyse(argv: list):
    """reads from CSV observation file the CN0 for a selected GNSS and signal type
    at a specified interval and calculate the mean and standard deviation of the CN0 values.

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_cn0_daily(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    print(args_parsed)

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create a console logger
    console = Console()

    # create the CSV_OBS object
    cvs_obs = GNSS_CSV(
        csv_fn=args_parsed.obs_fn,
        GNSS=args_parsed.gnss,
        interval=args_parsed.interval,
        logger=logger,
    )
    print(cvs_obs)


def main():
    cn0_analyse(argv=sys.argv)


if __name__ == "__main__":
    main()
