#!/usr/bin/env python

import os
import sys
from logging import Logger

import polars as pl

from config import ERROR_CODES, GNSS_DICT

from rinex.rinex_obs_class import RINEX_OBS
from utils import argument_parser, init_logger
from utils.utilities import str_green


def rnxobs_csv(argv: list):
    """reads RINEX observation file and converts it to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rnxobs_csv(args=argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create the RINEX object
    try:
        rnxobs = RINEX_OBS(
            rnxobs_fn=args_parsed.obs_fn,
            gnss=args_parsed.gnss,
            logger=logger,
        )
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_NO_RINEX_OBS"])

    # convert RINEX observation file to CSV file using gfzrnx to tabular observations
    tabobs_dfs = rnxobs.gfzrnx_tabobs()
    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        for gnss, tabobs_df in tabobs_dfs.items():
            logger.debug(
                f"Converted RINEX observation file for {str_green(GNSS_DICT[gnss])} to tabular observation file: \n{tabobs_df}"
            )

    # convert the tabular observations to csv format like rtcm3_parser MSM5/7 does
    csv_df = rnxobs.tabobs_to_csv(result_dfs=tabobs_dfs)
    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        logger.warning(f"Converted tabular observation file to CSV file: \n{csv_df}")

    # save the CSV file
    if args_parsed.csv_fn is not None:
        csv_fn = args_parsed.csv_fn
    else:
        csv_fn = os.path.splitext(rnxobs.rnxobs_fn)[0] + ".csv"
    csv_df.write_csv(csv_fn)
    logger.warning(f"Saved CSV file: {str_green(csv_fn)}")


if __name__ == "__main__":
    rnxobs_csv(argv=sys.argv)
