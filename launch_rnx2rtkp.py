#! /usr/bin/env python

import argparse
import datetime
import os
import polars as pl
import sys
import subprocess

from config import ERROR_CODES
from gnss import gnss_dt
import logging
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger, utilities


def rnx2rtkp_ppk(
    parsed_args: argparse.Namespace,
    logger: logging.Logger,
):
    """
    This function launches the rnx2rtkp program to process the RINEX observation and navigation files.
    The resulting RTKLIB PPP solution is stored in the output directory.

    (parsed) args:
    obs (str): RINEX observation file
    nav (str): RINEX navigation file
    base_corr (str): base correction file. Corrections can be formatted in RTCM3 or RNX obs
    base_coord (tuple): base station coordinates (X, Y, Z)
    out_fn: output directory

    """
    
    # check if rnx2rtkp is installed
    rnx2rtkp_path = utilities.locate("rnx2rtkp")
    if rnx2rtkp_path is None:
        print("rnx2rtkp not found in PATH. Please install RTKLIB. Program exits.")
        sys.exit(ERROR_CODES["E_PROCESS"])

    # define command line arguments

    cmd_rnx2rtkp = [
        rnx2rtkp_path,
        "-k",
        parsed_args.ppk_config_file,
        "-o",
        parsed_args.out_fn,
        parsed_args.obs,
        parsed_args.nav,
        parsed_args.base_corr,
        "-r",
        parsed_args.base_coord[0],
        parsed_args.base_coord[1],
        parsed_args.base_coord[2],
        "-x",
        "2",
    ]

    if parsed_args.start_time and parsed_args.end_time:
        start_time = datetime.datetime.strptime(parsed_args.start_time, "%Y/%m/%d_%H:%M:%S")
        end_time = datetime.datetime.strptime(parsed_args.end_time, "%Y/%m/%d_%H:%M:%S")
        cmd_rnx2rtkp.extend(
            [
                "-ts",
                start_time.strftime("%Y/%m/%d"),
                start_time.strftime("%H:%M:%S"),
                "-te",
                end_time.strftime("%Y/%m/%d"),
                end_time.strftime("%H:%M:%S"),
            ]
        )
    
    #TODO Get effective log level 
    """
    if logger.getEffectiveLevel(....) == "DEBUG":
        print('rnx2rtkp in logging mode')
        cmd_rnx2rtkp.extend(["-x", "2"])
    """
    
    logger.debug(f"Running rnx2rtkp for PPK solution with command: {cmd_rnx2rtkp}")

    # run rnx2rtkp
    try:
        subprocess.run(cmd_rnx2rtkp, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"rnx2rtkp failed with error code {e.returncode}")
        sys.exit(ERROR_CODES["E_PROCESS"])





if __name__ == "__main__":

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_rnx2rtkp_launcher(args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    logger.debug(f"Parsed arguments: {parsed_args}")
    
    rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)
