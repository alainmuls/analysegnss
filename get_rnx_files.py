#!/usr/bin/env python

import argparse
import os 
import sys
import glob
from logging import Logger
import subprocess

from utils import argument_parser, init_logger, utilities



"""
Creates rinex files from raw/binary data files (such as Septentrio SBF files)
Idea is the extend this to more file formats in the future (UBX (u-blox), RTCM3)
"""


def get_rnx_frm_sbf(parsed_args: argparse.Namespace, logger: Logger) -> str:
    """
    This function uses sbf2rin.sh to extract RNX files from the provided SBF file. And stores them in a directory named after the SBF file.

    args:
    parsed_args: parsed_args.sbf_ifn

    returns:
    rnx_odir (str): output directory for the RNX files
    """
    
    # generating RNX files from sbf_ifn using sbf2rin.sh

    # Path to sbf2rin shell script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sbf2rin_path = os.path.join(current_dir, "scripts/sbf2rin.sh")
    logger.debug(f"Using sbf2rin.sh full path {sbf2rin_path}")

    # get basename of sbf_ifn without extension
    sbf_basename = os.path.basename(parsed_args.sbf_ifn).split(".")[0]
    # output directory of rinex files
    rnx_odir = os.path.join(os.path.dirname(parsed_args.sbf_ifn), sbf_basename + "_RNX")

    # Check if the directory already exists
    if not os.path.exists(rnx_odir):
        try:
            os.mkdir(rnx_odir)
            logger.info(f"Directory created: {rnx_odir}")
        except OSError as e:
            logger.info(f"Error creating directory {rnx_odir}: {e}")
    else:
        # checking if rinex files already exist
        existing_rnx_files = os.listdir(rnx_odir)
        logger.debug(
            f"RNX dir {rnx_odir} already exists with files {existing_rnx_files}"
        )

        if glob.glob(os.path.join(rnx_odir, "*MO.rnx")) and glob.glob(
            os.path.join(rnx_odir, "*MN.rnx")
        ):
            logger.warning(
                f"RNX obs and nav files already exist in {rnx_odir}. Skipping running sbf2rin.sh"
            )
            return rnx_odir

    # define CLI arguments
    sbf2rin_args = [
        sbf2rin_path,
        "-f",
        parsed_args.sbf_ifn,
        "-r",
        rnx_odir,
    ]

    # Run the script
    logger.info(f"Running sbf2rin.sh with arguments: {sbf2rin_args}")
    try:
        process = subprocess.run(
            sbf2rin_args, check=True, text=True, capture_output=True
        )
        logger.debug(f"Output: {process.stdout}")  # Output from the script
    except subprocess.CalledProcessError as e:
        logger.error(f"sbf2rin failed with error code {e.returncode}")
        sys.exit(ERROR_CODES["E_PROCESS"])

    logger.info(f"Rinex files created in {rnx_odir}")

    return rnx_odir

if __name__ == "__main__":

    # make script standalone

    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_rnx_files(args=sys.argv[1:])
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    get_rnx_frm_sbf(parsed_args=parsed_args, logger=logger)

