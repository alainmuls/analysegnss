#!/usr/bin:env python3

import logging
import os
import sys

import polars as pl
from rich import print

from analysegnss.config import ERROR_CODES
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_sbfmeas2csv


def sbfmeas2csv(argv: list):
    """reads SBF file and converts it to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_sbfmeas2csv(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    print(f"args_parsed: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(sbf_fn=args_parsed.sbf_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])
    print(f"sbf object: {sbf}")

    # check which SBFBlock for measurements are available in the SBF file
    sbf_blocks = sbf.get_sbf_blocks()
    logger.debug(f"Available SBF blocks: {sbf_blocks}")
    if not sbf_blocks:
        logger.error(f"No SBF blocks found in {args_parsed.sbf_ifn}")
        sys.exit(ERROR_CODES["E_SBF_BLOCKS"])

    # check if Meas3Ranges, Meas3CN0HiRes and Meas3Doppler are available
    required_blocks = [
        "Meas3Ranges",
        "Meas3CN0HiRes",
        "Meas3Doppler",
    ]
    # Check if all required blocks are present
    meas3_present = all(block in sbf_blocks for block in required_blocks)
    print(f"meas3_present: {meas3_present}")
    if meas3_present and False:
        logger.debug("Converting measurements using Meas3 blocks")
        meas_df = sbf.bin2asc_dataframe(
            lst_sbfblocks=["Meas3Ranges"], archive=args_parsed.archive
        )
    elif "MeasEpoch2" in sbf_blocks:
        logger.debug("Converting measurements using MeasEpoch2 block")
        meas_df = sbf.bin2asc_dataframe(
            lst_sbfblocks=["MeasEpoch2"], archive=args_parsed.archive
        )
    else:
        logger.error("No Meas3 or MeasEpoch2 blocks found in SBF file. Exiting.")
        sys.exit(ERROR_CODES["E_SBF_BLOCKS"])

    # print the DataFrame
    for key, key_df in meas_df.items():
        print(f"Dataframe for {key}")
        print(key_df)
        logger.debug(f"dataframe for {key}: \n{key_df}")


def main():
    sbfmeas2csv(argv=sys.argv)


if __name__ == "__main__":
    main()
