#!/usr/bin/env python

# Standard library imports
import argparse
import json
import os
import sys
from logging import Logger

# Third-party imports
import polars as pl
from rich import print as rprint
from tabulate import tabulate

# Local application imports
from analysegnss.gnss.standard_pnt_quality_dict import (
    rtklib_to_standard_pntqual,
    get_pntquality_info,
)
from analysegnss.rtkpos.rtkpos_class import Rtkpos
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import (
    argument_parser_ppk,
    auto_populate_args_namespace,
)
from analysegnss.utils.utilities import print_df_in_chunks


def quality_analysis(df_pos: pl.DataFrame, logger: Logger = None) -> list:
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
                get_pntquality_info(rtklib_to_standard_pntqual(qual[0]))["desc"],
                qual_data.shape[0],
                round(qual_data.shape[0] / total_obs * 100, 2),
                total_obs,
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "PNT Mode Count", "Percentage", "Total Observations"],
        tablefmt="fancy_outline",
    )

    # # print the quality analysis
    # rprint(f"Analysis of the quality of the position data:\n{qual_tabular}")

    if logger is not None:
        logger.info(f"Analysis of the quality of the position data\n{qual_tabular}")

    return qual_analysis


def rtkp_pos(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        parsed_args (argparse.Namespace): parsed CLI arguments
            - pos_ifn: input rnx2rtkp pos file
            - archive: archive's directory name which archives the extracted rnx2rtkp pos file
        logger (Logger): logger object

    Returns:
        pl.DataFrame: RTK position dataframe
    """
    # Ensure compatibility when passing on parsed_args from a higher level script.
    parsed_args = auto_populate_args_namespace(
        parsed_args,
        argument_parser_ppk,
        os.path.splitext(os.path.basename(__file__))[0],
    )

    logger.debug(f"Parsed arguments: {parsed_args}")

    # create a RTKlib pos class object
    try:
        rtkpos = Rtkpos(pos_fn=parsed_args.pos_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating Rtkpos object: {e}")
        sys.exit(1)

    # read the CVS position file into polars dataframe
    info_processing, pos_df = rtkpos.read_pos_file()
    logger.debug(f"Processing info:\n{json.dumps(info_processing, indent=4)}")

    logger.info(f"rtkpos dataframe: \n{pos_df}")
    # analyse the quality of the solution
    qual_analysis = quality_analysis(df_pos=pos_df, logger=logger)

    return pos_df, qual_analysis


def main():

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_ppk(args=sys.argv[1:], script_name=script_name)

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    # call df_rtkpos to create dataframe from rtklib pos file
    df_rtkpos, qual_analysis = rtkp_pos(parsed_args=args_parsed, logger=logger)

    # print the quality analysis
    rprint(f"rtkpos dataframe: \n{print_df_in_chunks(title='df_rtkpos', df=df_rtkpos)}")

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "PNT Mode Count", "Percentage", "Total Observations"],
        tablefmt="fancy_outline",
    )
    rprint(f"Quality analysis:\n{qual_tabular}")


if __name__ == "__main__":
    main()
