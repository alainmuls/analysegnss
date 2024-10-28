#!/usr/bin/env python

import json
import os
import sys
from logging import Logger

import polars as pl
from tabulate import tabulate

# import globalvars
from plots import plot_utm
from rtkpos import rtk_constants as rtkc
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger


def quality_analysis(df_pos: pl.DataFrame, logger: Logger = None) -> None:
    """display the quality analysis

    Args:
        df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = df_pos.shape[0]
    for qual, qual_data in df_pos.group_by(["Q"]):
        qual_analysis.append(
            [
                rtkc.dict_rtk_pvtmode[qual[0]]["desc"],
                qual_data.shape[0],
                f"{qual_data.shape[0]/total_obs*100:.2f}%",
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "Count", "Percentage"],
        tablefmt="fancy_outline",
    )

    print(f"\nAnalysis of the quality of the position data\n{qual_tabular}")

    if logger is not None:
        logger.warning(f"\n{qual_tabular}")


def rtkp_pos(argv: list) -> pl.DataFrame:
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments

    Returns:
        pl.DataFrame: RTK position dataframe
    """
    # init the global variables
    # globalvars.initialize()

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ppk(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        rtkpos = Rtkpos(
            pos_fn=args_parsed.pos_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating RTKPos object: {e}")
        sys.exit(1)

    # read the CVS position file into polars dataframe
    info_processing, pos_df = rtkpos.read_pos_file()
    print(f"Processing info:\n{json.dumps(info_processing, indent=4)}")

    # analyse the quality of the solution
    quality_analysis(df_pos=pos_df, logger=logger)

    with pl.Config(tbl_cols=-1):
        logger.debug(f"df_pos = \n{pos_df}")

    return pos_df


if __name__ == "__main__":
    df_rtkpos = rtkp_pos(argv=sys.argv)
    with pl.Config(tbl_cols=-1):
        print(df_rtkpos)
