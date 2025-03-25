#!/usr/bin/env python

# Standard library imports
import argparse
import glob
import os 
import subprocess
import sys
from logging import Logger

# Local application imports
from analysegnss.config import ERROR_CODES
from analysegnss.utils import argument_parser, init_logger

"""
Creates rinex files from raw/binary data files (such as Septentrio SBF files)
Idea is to extend this to more file formats in the future (UBX (u-blox), RTCM3)
"""

def get_rnx_frm_sbf(parsed_args: argparse.Namespace, logger: Logger) -> tuple:
    """
    This function uses sbf2rin.sh to extract RNX files from the provided SBF file. And stores them in a directory named after the SBF file.

    args:
    parsed_args: parsed_args.sbf_ifn
    parsed_args: parsed_args.exclude_gnss
    parsed_args: parsed_args.begin_epoch
    parsed_args: parsed_args.end_epoch

    returns:
    rnx_obs_ofp: full path to RINEX observation file
    rnx_nav_ofp: full path to RINEX navigation file
    """
    
    # generating RNX files from sbf_ifn using sbf2rin.sh

    # Path to sbf2rin shell script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sbf2rin_path = os.path.join(current_dir, "..", "scripts", "sbf", "sbf2rin.sh")
    logger.debug(f"Using sbf2rin.sh full path {sbf2rin_path}")

    # check if sbf_ifn exists
    if not os.path.exists(parsed_args.sbf_ifn):
        logger.error(f"SBF file {parsed_args.sbf_ifn} does not exist")
        sys.exit(ERROR_CODES["E_FILE_NOT_FOUND"])
        
    # get basename of sbf_ifn without extension --> used for output directory otherwise it saved in the same directory as sbf2rin.sh script
    sbf_basename = os.path.basename(parsed_args.sbf_ifn).split(".")[0]
    # output directory of rinex files (this dir name will be unique for each SBF file) 
    rnx_odir = os.path.join(os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)), sbf_basename + "_RNX")

    # Check if the directory already exists
    if not os.path.exists(rnx_odir):
        try:
            os.mkdir(rnx_odir)
            logger.info(f"Directory created: {rnx_odir}")
        except OSError as e:
            logger.info(f"Error creating directory {rnx_odir}: {e}")
    """
    else:
        # checking if rinex files already exist
        existing_rnx_files = os.listdir(rnx_odir)
        logger.debug(
            f"RNX dir {rnx_odir} already exists with files {existing_rnx_files}"
        )

        if glob.glob(os.path.join(rnx_odir, "*MO.rnx")) and glob.glob(
            os.path.join(rnx_odir, "*MN.rnx")
        ):

            
            rnx_nav_ofp = os.path.join(rnx_odir, "*MN.rnx")
            rnx_obs_ofp = os.path.join(rnx_odir, "*MO.rnx")
            
            logger.warning(
                f"RNX obs and nav files already exist: {rnx_obs_ofp} and {rnx_nav_ofp}. Skipping running sbf2rin.sh"
            )
            
            return rnx_obs_ofp, rnx_nav_ofp
        
        else: 
            logger.warning(
                f"RNX dir {rnx_odir} already exists but no RINEX files found. Overwriting existing directory"
            )
    """

    # define CLI arguments for sbf2rin.sh
    
    sbf2rin_args = [
        sbf2rin_path,
        "-f",
        parsed_args.sbf_ifn,
    ]
    

    # extending the arguments with optional arguments if provided in parsed_args
    ## excl_gnss argument ##
    if hasattr(parsed_args, "excl_gnss"):
        sbf2rin_args.extend(["-x", parsed_args.excl_gnss])
    ## begin_epoch argument ##
    if hasattr(parsed_args, "begin_epoch"):
        sbf2rin_args.extend(["-b", parsed_args.begin_epoch])
    ## end_epoch argument ##
    if hasattr(parsed_args, "end_epoch"):
        sbf2rin_args.extend(["-e", parsed_args.end_epoch])
    
    # extend the arguments with output directory    
    sbf2rin_args.extend(["-r", rnx_odir]) 

    # Run the script
    logger.info(f"Running sbf2rin.sh with arguments: {sbf2rin_args}")
    try:
        process_out = subprocess.run(
            sbf2rin_args, check=True, text=True, capture_output=True
        )
        logger.debug(f"Output: {process_out.stdout}")  # Output from the script
        
        # catch last returned lines which contain the created RINEX files paths
        rnx_nav_ofn = process_out.stdout.splitlines()[-1:][0]
        rnx_obs_ofn = process_out.stdout.splitlines()[-2:-1][0]
        
    except subprocess.CalledProcessError as e:
        logger.error(f"sbf2rin failed with error code {e}")
        logger.error(f"Output: {e.stdout}")
        sys.exit(ERROR_CODES["E_PROCESS"])


    rnx_obs_ofp = os.path.join(rnx_odir, rnx_obs_ofn) # full path to RINEX observation file
    rnx_nav_ofp = os.path.join(rnx_odir, rnx_nav_ofn) # full path to RINEX navigation file
    
    logger.debug(f"Created rinex files\n{rnx_obs_ofp}\n{rnx_nav_ofp}")

    return rnx_obs_ofp, rnx_nav_ofp

def main():

    # make script standalone

    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_rnx_files(args=sys.argv[1:], script_name=script_name)
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    get_rnx_frm_sbf(parsed_args=parsed_args, logger=logger)

if __name__ == "__main__":

    main()
