#!/usr/bin/env python

import logging
import os
import sys

import polars as pl
from rich import print

from analysegnss.config import ERROR_CODES, DICT_GNSS
from analysegnss.rinex.rinex_nav_class import RINEX_NAV
from analysegnss.utils import argument_parser, init_logger
from analysegnss.utils.utilities import str_green, str_yellow


def rnxnav_csv(argv: list):
    """reads RINEX navigation file and converts it to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rnxnav_csv(
        args=argv[1:], script_name=os.path.basename(__file__)
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create the RINEX object
    try:
        rnxnav = RINEX_NAV(
            rnxnav_fn=args_parsed.nav_fn,
            gnss=args_parsed.gnss,
            logger=logger,
        )
    except Exception as e:
        if logger is not None:
            logger.error(f"Error creating SBF object: {e}")
        sys.stderr.write(f"Error creating SBF object: {e}\n")
        sys.exit(ERROR_CODES["E_NO_RINEX_NAV"])

    # convert RINEX navigation file to tabular format for selected GNSS
    try:
        gnss_nav_dict = rnxnav.gfzrnx_tabnav()
    except RuntimeError:
        print("No data available for selected GNSS")
        return 1

    # get directory part and filename without extension part of the RINEX navigation file
    rnxnav_dir, rnxnav_fn = os.path.split(args_parsed.nav_fn)
    rnxnav_dir = rnxnav_dir or "."

    # change to the directory part of the RINEX navigation file in try block
    # so that the CSV file is created in the same directory as the RINEX navigation file
    os.chdir(rnxnav_dir)

    # convert each GNSS / Navigation type dataframe to CSV file
    for (gnss, nav_type), nav_df in gnss_nav_dict.items():
        csv_fn = f"{rnxnav_dir}/{os.path.basename(rnxnav_fn).split('.')[0]}_{DICT_GNSS[gnss]}_{nav_type}.csv"
        if logger:
            logger.warning(
                f"Created for {str_green(DICT_GNSS[gnss])}-{str_green(nav_type)}: {str_yellow(csv_fn)}"
            )

        if rnxnav._console_loglevel > logging.WARNING:
            print(f"Created for {DICT_GNSS[gnss]}-{nav_type}: {csv_fn}")

        nav_df.write_csv(
            csv_fn,
            separator=",",
            include_header=True,
        )


def main():
    rnxnav_csv(argv=sys.argv)


if __name__ == "__main__":
    main()
