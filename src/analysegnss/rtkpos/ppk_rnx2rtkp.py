#!/usr/bin/env python

# Standard library imports
import json
import os
import sys
from logging import Logger

# Third-party imports
import polars as pl
from rich import print as rprint
from tabulate import tabulate

# Local application imports
from analysegnss.gnss.general_pvt_quality_dict import rtklib_to_general_pvtqual, get_pvtquality_info
from analysegnss.rtkpos import rtklib_constants as rtklibc
from analysegnss.rtkpos.rtkpos_class import Rtkpos
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_ppk


def quality_analysis(df_pos: pl.DataFrame, logger: Logger = None) -> list:
    """display the quality analysis

    Args:
        df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = df_pos.shape[0]
    for qual, qual_data in df_pos.group_by("Q"):
        qual_analysis.append(
            [
                get_pvtquality_info(rtklib_to_general_pvtqual(qual))["desc"],
                qual_data.shape[0],
                round(qual_data.shape[0] / total_obs * 100, 2),
                total_obs
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "PNT Mode Count", "Percentage", "Total Observations"],
        tablefmt="fancy_outline",
    )

    if logger is not None:
        logger.info(f"Analysis of the quality of the position data\n{qual_tabular}")

    return qual_analysis


def rtkp_pos(argv: list) -> pl.DataFrame:
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments

    Returns:
        pl.DataFrame: RTK position dataframe
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_ppk(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    # create a RTKlib pos class object
    try:
        rtkpos = Rtkpos(pos_fn=args_parsed.pos_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating Rtkpos object: {e}")
        sys.exit(1)

    # read the CVS position file into polars dataframe
    info_processing, pos_df = rtkpos.read_pos_file()
    logger.debug(f"Processing info:\n{json.dumps(info_processing, indent=4)}")

    logger.debug(f"df_pos = \n{pos_df}")
    rprint(f"df_pos = \n{pos_df}")
    # analyse the quality of the solution
    quality_analysis(df_pos=pos_df, logger=logger)


    return pos_df

def main():
    df_rtkpos = rtkp_pos(argv=sys.argv)

if __name__ == "__main__":
    main()