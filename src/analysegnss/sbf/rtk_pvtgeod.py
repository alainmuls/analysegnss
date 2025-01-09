#!/usr/bin/env python

# Standard library imports
import os
import sys
from logging import Logger

# Third-party imports
import polars as pl
from tabulate import tabulate

# Local application imports
from analysegnss.config import ERROR_CODES
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import argument_parser, init_logger


def quality_analysis(geod_df: pl.DataFrame, logger: Logger = None) -> list:
    """display the quality analysis

    Args:
        df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = geod_df.shape[0]
    for qual, qual_data in geod_df.group_by("Type"):
        qual_analysis.append(
            [
                sbfc.dict_sbf_pvtmode[qual]["desc"],
                qual_data.shape[0],
                round(qual_data.shape[0]/total_obs*100,2)
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "Count", "Percentage"],
        tablefmt="fancy_outline",
    )
    #print(f"\nAnalysis of the quality of the position data\n{qual_tabular}")

    if logger is not None:
        logger.info(f"Quality analysis:\n{qual_tabular}")

    return qual_analysis

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
    logger.debug(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(
            sbf_fn=args_parsed.sbf_ifn, logger=logger
        )
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["ERROR_SBF_OBJECT"])

    if not args_parsed.sbf2asc:
        # extract the PVT Geodetic2 block from SBF file
        df_geod = sbf.bin2asc_dataframe(lst_sbfblocks=["PVTGeodetic2"], archive=args_parsed.archive)["PVTGeodetic2"]

        # analyse the quality of the solution
        quality_analysis(geod_df=df_geod, logger=logger)

        with pl.Config(tbl_cols=-1):
            logger.debug(f"df_geod: \n{df_geod}")

        return df_geod

    else:
        df_geod = sbf.sbf2asc_dataframe(lst_sbfblocks=["PVTGeodetic2"], archive=args_parsed.archive)[
            "PVTGeodetic2"
        ]
        with pl.Config(tbl_cols=-1):
            print(f"df_geod: \n{df_geod}")
            logger.info(f"df_geod: \n{df_geod}")

    return df_geod


def main():
    
    geod_df = rtk_pvtgeod(argv=sys.argv)

    if geod_df is not None:
        with pl.Config(tbl_cols=-1):
            print(geod_df)  

if __name__ == "__main__":
    main()