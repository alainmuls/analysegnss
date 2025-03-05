#!/usr/bin:env python3

import argparse
import logging
import os
import sys

import polars as pl
from rich import print as rprint

from analysegnss.config import DICT_GNSS, ERROR_CODES
from analysegnss.sbf.sbf_class import SBF
from analysegnss.sbf.sbf_column_mapping import (
    GNSS_NAV_COLUMN_MAPPINGS,
    convert_semicircles_to_radians,
    rename_nav_columns,
)
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_sbfnav_csv


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

    # select the navigation SBF blocks for the selected GNSSq
    sbf_nav_blocks_gnss = []
    for gnss in parsed_args.gnss:
        gnss_abbrev = DICT_GNSS[gnss]["abbrev"]
        logger.debug(f"Selected GNSS: {gnss_abbrev}")
        sbf_nav_blocks_gnss.append(
            [block for block in sbf_nav_blocks if gnss_abbrev in block][0]
        )

    # create a list of dictionaries to hold the dataframes for each navigation SBF block
    nav_dfs = sbf.bin2asc_dataframe(
        lst_sbfblocks=sbf_nav_blocks_gnss, archive=parsed_args.archive
    )

    for sbf_block, nav_df in nav_dfs.items():
        # identify the gnss type from the SBF block name
        gnss_abbrev = sbf_block[:3]
        rprint(f"gnss_abbrev: {gnss_abbrev}")

        # if sbf_block == "GPSNav":
        nav_df = convert_semicircles_to_radians(df=nav_df, gnss_type=gnss_abbrev)
        nav_df = rename_nav_columns(df=nav_df, gnss_type=gnss_abbrev)

        logger.info(
            f"nav_df[{sbf_block}]:\n{nav_df.select(nav_df.columns[:20]).head(3)}"
            f"nav_df[{sbf_block}]:\n{nav_df.select(nav_df.columns[20:]).head(3)}"
        )

        # convert the polars dataframe to CSV for each navigation SBF block
        csv_filename = f"{parsed_args.sbf_ifn}_{sbf_block}.csv"  # Add a descriptive name to output.
        try:
            nav_df.write_csv(csv_filename)
            logger.info(f"Successfully wrote {sbf_block} data to {csv_filename}")
        except Exception as e:
            logger.error(f"Failed to write {sbf_block} data to {csv_filename}: {e}")


def main():
    # parse the CLI arguments and run sbfnav_csv
    args_parsed = argument_parser_sbfnav_csv(
        args=sys.argv[1:], script_name=os.path.basename(__file__)
    )

    # print(f"args_parsed: {args_parsed}")

    sbfnav_csv(parsed_args=args_parsed)


if __name__ == "__main__":
    main()
