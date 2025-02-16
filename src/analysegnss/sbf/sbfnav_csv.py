#!/usr/bin:env python3

import argparse
import logging
import os
import sys

import polars as pl
from rich import print

from analysegnss.config import DICT_GNSS, DICT_SIGNAL_TYPES, ERROR_CODES
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_sbfnav_csv
from analysegnss.utils.utilities import str_red, str_green


def sbfnav_csv(parsed_args: argparse.Namespace):
    """reads SBF file and converts Navigation blocks to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # create the file/console logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name)
    logger.info(f"Parsed arguments: {parsed_args} | {type(parsed_args)}")

    # create a SBF class object
    try:
        sbf = SBF(sbf_fn=parsed_args.sbf_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])
    logger.info(f"sbf object: {sbf}")

    # check which SBFBlock for measurements are available in the SBF file
    sbf_blocks = sbf.get_sbf_blocks()
    logger.debug(f"Available SBF blocks: {sbf_blocks}")
    if not sbf_blocks:
        logger.error(f"No SBF blocks found in {parsed_args.sbf_ifn}")
        sys.exit(ERROR_CODES["E_SBF_BLOCKS"])

    sbf_nav_blocks = [block for block in sbf_blocks if block.endswith("Nav")]
    logger.debug(f"Available SBF Nav blocks: {sbf_nav_blocks}")

    if not sbf_nav_blocks:
        logger.error(f"No SBF Nav blocks found in {parsed_args.sbf_ifn}")
        sys.exit(ERROR_CODES["E_SBF_NAV_BLOCKS"])

    # create a list of dictionaries to hold the dataframes for each navigation SBF block
    nav_dfs = sbf.bin2asc_dataframe(
        lst_sbfblocks=sbf_nav_blocks, archive=parsed_args.archive
    )
    for sbf_block, nav_df in nav_dfs.items():
        logger.info(f"nav_df[{sbf_block}]:\n{nav_df}")


def main():
    # parse the CLI arguments and run sbfnav_csv
    args_parsed = argument_parser_sbfnav_csv(
        args=sys.argv[1:], script_name=os.path.basename(__file__)
    )

    print(f"args_parsed: {args_parsed}")

    sbfnav_csv(parsed_args=args_parsed)


if __name__ == "__main__":
    main()
