#!/usr/bin/env python

import os
import sys

import polars as pl
from tabulate import tabulate

# import globalvars
from sbf import sbf_constants as sbfc
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger
from config import ERROR_CODES


def quality_analysis(geod_df: pl.DataFrame, logger) -> None:
    """display the quality analysis

    Args:
        df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    print(f"\nAnalysis of the quality of the position data")
    qual_analysis = []
    total_obs = geod_df.shape[0]
    for qual, qual_data in geod_df.groupby("Type"):
        qual_analysis.append(
            [
                sbfc.dict_sbf_pvtmode[qual]["desc"],
                qual_data.shape[0],
                f"{qual_data.shape[0]/total_obs*100:.2f}%",
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "Count", "Percentage"],
        tablefmt="fancy_outline",
    )
    print(qual_tabular)

    if logger is not None:
        logger.warn(qual_tabular)


def rtk_pvtgeod(argv: list) -> pl.DataFrame:
    """
    Convert PVT Geodetic2 SBF block to dataframe and analyse quality of data

    Returns:
        pl.DataFrame: PVT Geodetic2 dataframe
    """
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
        sys.exit(ERROR_CODES["ERROR_SBF_OBJECT"])

    if not args_parsed.sbf2asc:
        # extract the PVT Geodetic2 block from SBF file
        df_geod = sbf.bin2asc_dataframe(lst_sbfblocks=["PVTGeodetic2"])["PVTGeodetic2"]

        # analyse the quality of the solution
        quality_analysis(geod_df=df_geod, logger=logger)

        with pl.Config(tbl_cols=-1):
            logger.debug(f"df_geod: \n{df_geod}")

        return df_geod

    else:
        df_poscov = sbf.sbf2asc_dataframe(lst_sbfblocks=["PosCovGeodetic1"])[
            "PosCovGeodetic1"
        ]
        with pl.Config(tbl_cols=-1):
            print(f"df_poscov: \n{df_poscov}")
            logger.debug(f"df_poscov: \n{df_poscov}")

        return None


if __name__ == "__main__":
    geod_df = rtk_pvtgeod(argv=sys.argv)

    if geod_df is not None:
        with pl.Config(tbl_cols=-1):
            print(geod_df)
