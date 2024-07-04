#!/usr/bin/env python

import os
import sys

import polars as pl

import globalvars
from utils import argument_parser, init_logger
from gnss.plot import plot_utm
import rtkpos_analyse


def rtkppos_plot(argv: list):
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments
    """
    pass
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rtkpos_plot(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    # logger.warning(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

    # create the RTK position dataframe by calling rtkpos_analyse.py
    # adjust the arguments to exclude the "--plot" argument
    rtkpos_analyse_args = [val for val in argv if val != "--plot"]
    # print(f"rtkpos_analyse_args = {rtkpos_analyse_args}")
    df_pos = rtkpos_analyse.rtkp_pos(argv=rtkpos_analyse_args)
    with pl.Config(tbl_cols=-1):
        print(f"from rtkpos_plot df_pos = \n{df_pos}")

    # plot the UTM and orthoH coordinates
    if args_parsed.plot:
        plot_utm.plot_utm_coords(
            utm_df=df_pos.select(
                ["DT", "Q", "ns", "UTM.E(m)", "UTM.N(m)", "orthoH(m)"]
            ),
            origin="RTKPos",
            title="Salton Sea RWY 31L/13R",
        )


if __name__ == "__main__":
    df_rtkpos = rtkppos_plot(argv=sys.argv)  # type: ignore
