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
from rich import print

from analysegnss.config import ERROR_CODES, DICT_GNSS, rich_console
from analysegnss.CSV.CSV_class import GNSS_CSV
from analysegnss.utils import argument_parser, init_logger
from analysegnss.utils.utilities import str_red


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
    # print(args_parsed)

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create the CSV_OBS object
    try:
        cvs_obs = GNSS_CSV(
            csv_fn=args_parsed.obs_fn,
            GNSS=args_parsed.gnss,
            interval=args_parsed.interval,
            signal_type=args_parsed.sigtype,
            logger=logger,
        )
    except ValueError as e:
        logger.error(f"Error: {str_red(e)}")
        sys.exit(ERROR_CODES["E_SIGNALTYPE_MISMATCH"])

    print(f"cvs_obs = {cvs_obs}")

    # read the CSV file in a polars DataFrame
    df_cn0 = cvs_obs.csv_df()
    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        print(f"df_cn0 = {df_cn0}")


def main():
    cn0_analyse(argv=sys.argv)


if __name__ == "__main__":
    main()
