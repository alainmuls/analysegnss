#!/usr/bin/env python

import os
import sys

import polars as pl

import globalvars
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger
from rtkpos import rtk_constants as rtkc


def rtkp_pos(argv: list) -> pl.DataFrame:
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments

    Returns:
        pl.DataFrame: RTK position dataframe
    """
    pass
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rtkpos(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    # logger.warning(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

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

    with pl.Config(tbl_cols=-1):
        print(f"pos_df.describe(): \n{pos_df.describe()}")

    # analysis of the quality of the position data
    print(f"\nAnalysis of the quality of the position data")
    for qual, qual_data in pos_df.groupby("Q"):
        print(f"\t{rtkc.dict_rtk_pvtmode[qual]['desc']}: {qual_data.shape[0]}")

    import TableIt

    myList = [
        ["Name", "Email"],
        ["Richard", "richard@fakeemail.com"],
        ["Tasha", "tash@fakeemail.com"],
    ]

    TableIt.print(myList, useFieldNames=True)

    return pos_df


if __name__ == "__main__":
    df_rtkpos = rtkp_pos(argv=sys.argv)
    with pl.Config(tbl_cols=-1):
        print(df_rtkpos)
