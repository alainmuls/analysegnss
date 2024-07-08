#!/usr/bin/env python

# Import the required modules
import datetime
import os
import sys

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import polars as pl
import seaborn as sns

import globalvars
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger
from utils.utilities import bin_nibble
from sbf import sbf_constants as sbfc


def rtk_pvtgeod(argv: list) -> pl.DataFrame:
    """
    Convert PVT Geodetic2 SBF block to dataframe and analyse quality of data

    Returns:
        pl.DataFrame: PVT Geodetic2 dataframe
    """
    # init the global variables
    globalvars.initialize()

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    args_parsed = argument_parser.argument_parser_rtk(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(
            sbf_fn=args_parsed.sbf_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(1)

    # extract the PVT Geodetic2 block from SBF file
    # df_geod = sbf.extract_pvtgeodetic2()
    df_geod = sbf.bin2asc_dataframe(lst_sbfblocks=["PVTGeodetic2"])
    # with pl.Config(tbl_cols=-1):
    #     print(f"df_geod: \n{df_geod}")

    return df_geod


if __name__ == "__main__":
    geod_df = rtk_pvtgeod(argv=sys.argv)
    with pl.Config(tbl_cols=-1):
        print(geod_df)
