#! /usr/bin/env python

import argparse
import os
import sys
import glob
from logging import Logger
import subprocess

from config import ERROR_CODES
from launch_rnx2rtkp import rnx2rtkp_ppk
from sbf import sbf_constants as sbfc
from utils import argument_parser, init_logger
import get_ebh_timings
from get_base_coord import get_base_coord_from_sbf
import ebh_lines


def ebh_process_launcher(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings,
    decides whether the RTK or PPK solution has a sufficient quality,
    and finally outputs correct ASSUR formatted files for each ebh line.

    Args:
    parsed_args: parsed CLI arguments (check argument_parser.py for more info)

    """

    # launching get_ebh_timings to extract timings from sbf_ifn which creates a ebh timings file for ebh_lines
    ebh_timings = get_ebh_timings.get_ebh_timings(
        parsed_args=parsed_args, logger=logger
    )

    # launching ebh_lines in RTK mode to get ebh lines. It returns a quality analysis of each line in dict
    parsed_args.timing_ifn = parsed_args.sbf_ifn + "_ebh_timings.txt"
    ebh_qual_rtk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)
    # Checking RTK quality and rejecting lines that are not of sufficient quality
    rejected_rtk_lines, rtk_qual_check = rtk_ppk_qual_check(
        qual_analysis=ebh_qual_rtk, RTK_mode=True, rejection_level=99, logger=logger
    )

    # launching ebh_lines in PPK mode to get ebh lines. It returns a quality analysis of each line in dict
    ebh_qual_ppk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)

    ppk_qual_decision = rtk_ppk_qual_check(
        qual_analysis=ebh_qual_ppk, RTK_mode=False, rejection_level=99, logger=logger
    )
    for key, value in ppk_qual_decision.items():
        if value == False:
            logger.warning(
                f"PPK solution for ebh line {key} is not of sufficient quality."
            )


def rtk_ppk_qual_check(
    qual_analysis: dict, RTK_mode: bool, rejection_level: float, logger: Logger
) -> list:
    """Checks the RTK or PPK solutions and checks if the line is of sufficient quality
    to be used for the ebh_lines calculation and ASSURtool. It returns the rejected lines.

    Args:
    qual_analysis (dict):       dictionary with the quality analysis of the RTK/PPK solution
                                for each ebh line
    RTK_mode (bool):            RTK (True) or PPK (False) mode
    rejection level (float):    a level of fixed_points/total (percentage) that needs to be met.
                                Otherwise the results is rejected.

    Returns:
    rejected_ebh_lines (list):  list of ebh lines that are rejected
    """

    logger.info(
        f"rkt_ppk checker launched for {qual_analysis} in RTK mode {RTK_mode} with a rejection level of {rejection_level}"
    )

    rejected_ebh_lines = []  # list to store the decision for each ebh line
    for ebh_key, ebh_qual_value in qual_analysis.items():
        if RTK_mode:
            if ebh_qual_value[0][2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.warning(
                    f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[0][2]}"
                )

        else:  # PPK MODE
            if ebh_qual_value[0][2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.info(
                    f"ebh line {ebh_key} does not meet the quality of {ebh_qual_value[0][2]}"
                )

    # Checking PNT solution quality of each ebh line and deciding whether to continue with RTK or PPK solution
    # If more than one RTK ebh line is not sufficient, all the ebh lines will be recalculated in PPK mode
    # If only one is insufficient, the PPK is calculated for this line only
    if len(rejected_ebh_lines) == 0:
        logger.info(
            "Solution for all ebh lines is of sufficient quality. ASSUR EBH files -> OK."
        )
        ebh_qual_check = "ALL-EBH-OK"
    elif len(rejected_ebh_lines) == 1:
        logger.warning(
            f"Solution for the ebh line {rejected_ebh_lines}  is not of sufficient quality."
        )
        ebh_qual_check = "1-EBH-NOK"

    else:
        logger.warning(
            "Solution for one or more ebh lines is not of sufficient quality. Calculating all ebh lines in PPK mode."
        )
        ebh_qual_check = "ALL-EBH-NOK"

    return rejected_ebh_lines, ebh_qual_check


def do_ppk(
    rejected_rtk_lines: list,
    rtk_qual_sol: str,
    ebh_timings: dict,
    parsed_args: argparse.Namespace,
    logger: Logger,
):
    """A ppk process is launched for the ebh lines depending on the rtk quality check.

    args:
    rejected_rtk_lines (list): list of ebh lines that are rejected
    rtk_qual_sol (str): defines which condition is met for three possible outcomes
                        case 1: rtk_qual_sol = "ALL-RTK-OK"
                        case 2: rtk_qual_sol = "1-RTK-NOK"
                        case 3: rtk_qual_sol = "ALL-RTK-NOK"
    ebh_timings (dict): timings of each ebh line
    parsed_args: RNX Obs, RNX Nav, base corrections (RNX or RTCM) and PPK configuration file.

    """
    
    match rtk_qual_sol:
        case "ALL-RTK-OK":
            logger.info(
                "RTK solution for all ebh lines is of sufficient quality. ASSUR EBH files -> OK."
            )
            
            
        case "1-RTK-NOK":
            
            logger.warning(
                f"RTK solution for the ebh line {rejected_rtk_lines}  is not of sufficient quality. \
                    Calculating this single line in PPK mode with timings {ebh_timings[rejected_rtk_lines[0]]}"
            )
           
            # created and get the rinex files from the sbf input filename
            rnx_odir = get_rnx_files(parsed_args=parsed_args,logger=logger)
            
            # get the path of the rinex files and add them them to parsed_args namespace
            parsed_args.obs = glob.glob(os.path.join(rnx_odir,"*MO.rnx"))
            parsed_args.nav = glob.glob(os.path.join(rnx_odir,"*MN.rnx"))
            
            # Get base coordinates
            base_coord = get_base_coord_from_sbf(parsed_args=parsed_args,logger=logger)    
             
            rnx2rtkp_ppk(parsed_args=parsed_args,logger=logger)
            
            

    
        case "ALL-RTK-NOK": 
        
            logger.warning(
                "RTK solution for one or more ebh lines is not of sufficient quality. Calculating all ebh lines in PPK mode."
            )
        
def get_rnx_files(parsed_args: argparse.Namespace, logger: Logger):
    """
    This function uses sbf2rin.sh to extract RNX files from the provided SBF file.
    
    args:
    parsed_args: parsed_args.sbf_ifn
    
    """
    # generating RNX files from sbf_ifn using sbf2rin.sh

    # Path to your shell script
    sbf2rin_path = 'scripts/sbf2rin.sh'
    
    # output directory of rinex files
    rnx_odir = os.path.join(os.path.dirname(parsed_args.sbf_ifn), 'rnx')

    # Check if the directory already exists
    if not os.path.exists(rnx_odir):
        try:
            os.mkdir(rnx_odir)
            logger.info(f"Directory created: {rnx_odir}")
        except OSError as e:
            logger.info(f"Error creating directory {rnx_odir}: {e}")
    
    # define CLI arguments
    sbf2rin_args = [
        sbf2rin_path,
        "-f",
        parsed_args.sbf_ifn,
        "-r",
        rnx_odir,
    ]
    
    # Run the script
    try:
        process = subprocess.run(['bash', sbf2rin_args], check=True, text=True, capture_output=True)
        logger.debug(f"Output: {process.stdout}")  # Output from the script
        logger.error(f"Error:, {process.stderr}")    # Error output from the script, if any
    except subprocess.CalledProcessError as e:
        logger.error(f"sbf2rin failed with error code {e.returncode}")
        sys.exit(ERROR_CODES["E_PROCESS"])

    logger.info(f"Rinex files created in {rnx_odir}")
    
    return rnx_odir

if __name__ == "__main__":

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_ebh_process_launcher(
        args=sys.argv[1:]
    )

    # create the file/console logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    logger.info(f"Parsed arguments: {parsed_args}")

    ebh_process_launcher(parsed_args=parsed_args, logger=logger)
