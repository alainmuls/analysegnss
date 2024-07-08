#!/usr/bin/env python

import os
import sys

import polars as pl
from tabulate import tabulate

import globalvars
from rtkpos import rtk_constants as rtkc
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger


def rtkp_pos(argv: list) -> pl.DataFrame:
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments

    Returns:
        pl.DataFrame: RTK position dataframe
    """
    # init the global variables
    globalvars.initialize()

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ppk(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        rtkpos = Rtkpos(
            pos_fn=args_parsed.pos_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating RTKPos object: {e}")
        sys.exit(1)

    # read the CVS position file into polars dataframe
    pos_df = rtkpos.read_pos_file()

    # with pl.Config(tbl_cols=-1):
    #     print(f"pos_df.describe(): \n{pos_df.describe()}")

    # analysis of the quality of the position data
    print(f"\nAnalysis of the quality of the position data")
    qual_analysis = []
    total_obs = pos_df.shape[0]
    for qual, qual_data in pos_df.groupby("Q"):
        qual_analysis.append(
            [
                rtkc.dict_rtk_pvtmode[qual]["desc"],
                qual_data.shape[0],
                f"{qual_data.shape[0]/total_obs*100:.2f}%",
            ]
        )

    print(
        tabulate(
            qual_analysis,
            headers=["PNT Mode", "Count", "Percentage"],
            tablefmt="fancy_outline",
        )
    )

    return pos_df


if __name__ == "__main__":
    df_rtkpos = rtkp_pos(argv=sys.argv)
    with pl.Config(tbl_cols=-1):
        print(df_rtkpos)
