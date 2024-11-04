#! /usr/bin/env python

import argparse
import datetime
import os
import sys
import subprocess

import logging
from utils import argument_parser, init_logger
from utils.utilities import locate



def rnx2rtkp_ppk(obs: str, nav: str, base_corr: str, ppk_config_file: str, start_time: str, end_time: str, out_dir: str, logger: logging.Logger):
    """
    This function launches the rnx2rtkp program to process the RINEX observation and navigation files.
    The resulting RTKLIB PPP solution is stored in the output directory.
    
    args:
    obs (str): RINEX observation file
    nav (str): RINEX navigation file
    base_corr (str): base correction file. Corrections can be formatted in RTCM3 or RNX obs
    out_dir: output directory
    
    """
    
    
    # check if rnx2rtkp is installed
    rnx2rtkp_path = locate("rnx2rtkp")
    if rnx2rtkp_path is None:
        print("rnx2rtkp not found in PATH. Please install RTKLIB. Program exits.")
        sys.exit(ERROR_CODES["E_PROCESS"])
        
    # define command line arguments
    
    cmd_rnx2rtkp = [
        rnx2rtkp_path,
        "-k",
        ppk_config_file,
        "-o",
        out_dir,
        obs,
        nav,
        base_corr,
        "-x",
        2,
    ]
    
    if start_time and end_time:
        start_time = datetime.datetime.strptime(start_time, "%Y/%m/%d_%H:%M:%S")
        end_time = datetime.datetime.strptime(end_time, "%Y/%m/%d_%H:%M:%S")
        cmd_rnx2rtkp.extend(["-ts", start_time.strftime("%Y/%m/%d %H:%M:%S"), "-te", end_time.strftime("%Y/%m/%d %H:%M:%S")])
    
    logger.info(f"Running rnx2rtkp for PPK solution with command: {cmd_rnx2rtkp}")

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
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest)
    logger.info(f"Parsed arguments: {parsed_args}")

    rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)