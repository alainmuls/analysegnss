#! /usr/bin/env python

# Standard library imports
from logging import Logger
import os
import shutil
import subprocess
import sys

# Local application imports
from analysegnss.rinex.get_rnx_files import get_rnx_frm_sbf
from analysegnss.utils import argument_parser, init_logger

"""
    This script checks and reformats rnx files for OPUS processing.
    The scripts accepts sbf and rnx files.
"""

def exec_gfzrnx(rnx_obs_ifn: str, rnx_nav_ifn: str | None, gnss: str, duration: int, epoch_interval: int, logger=Logger | None):
    """
    This function uses gfzrnx to create RNX files for OPUS processing.
    
    args:
    rnx_obs_ifn (str): path to the RINEX observation file
    rnx_nav_ifn (str): path to the RINEX navigation file
    gnss (str): GNSS system to be used for OPUS processing (e.g. G, R, E, J)
    duration (int): duration of the RINEX file
    epoch_interval (int): epoch interval of the RINEX file measured in seconds
    logger (Logger): logger object
    
    """
     
    # get directory of input file and use it for the output directory
    dir_ofn = os.path.dirname(os.path.realpath(rnx_obs_ifn))
    dir_ofn = os.path.join(dir_ofn, "OPUS_RNX")

    # create output directory
    if not os.path.exists(dir_ofn):
        try:
            os.mkdir(dir_ofn)
            if logger:
                logger.info(f"Directory created: {dir_ofn}")
        except OSError as e:
            print(f"Error creating directory {dir_ofn}: {e}")
            sys.exit(1)
            
    # configure executables: gfzrnx (Rinex tool)
    exec_gfzrnx = shutil.which("gfzrnx")

    logger.debug(f"gfzrnx executable: {exec_gfzrnx}")

    for rnx_ifn in [rnx_obs_ifn, rnx_nav_ifn]:    
       
        if rnx_ifn:
            rnx2OPUS = [
                exec_gfzrnx,
                "-f",
                "-finp",
                rnx_ifn,
                "-fout",
                f"{dir_ofn}/::RX3::",
                "-smp",
                f"{epoch_interval}",
                "-satsys",
                gnss,
                "--duration",
                f"{duration}",
            ]

            logger.debug(f"gfzrnx command: {rnx2OPUS}")

            try:
                proc_OPUS = subprocess.run(rnx2OPUS)
            except subprocess.CalledProcessError as e:
                print(f"Error in running gfzrnx: {e}")
                sys.exit()

            
            print(
                f"gfzrnx process finished. Created RNX from {rnx_ifn} file for OPUS processing and stored it in {dir_ofn}"
            )
            if logger:
                logger.info(f"gfzrnx process finished. Created RNX file from {rnx_ifn} for OPUS processing and stored it in {dir_ofn}")
        else:
            logger.warning(f"RINEX file name {rnx_ifn} is empty. Skipping OPUS processing") 

def main():

    # fetch script name
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # parse arguments
    parsed_args = argument_parser.argument_parser_reformat_sbf_rnx_for_opus(
        args=sys.argv, script_name=script_name
    )
    # initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    # manage and check input files
    if parsed_args.rnx_ifn:
        rnx_ifn = parsed_args.rnx_ifn
        
        if os.path.exists(rnx_ifn):
            parsed_args.OPUS = True
        else:
            print("Error: RINEX file does not exist")
            sys.exit(0)

        # create OPUS rnx file
        exec_gfzrnx(
            rnx_obs_ifn=rnx_ifn,
            gnss=parsed_args.gnss,
            duration=parsed_args.duration,
            epoch_interval=parsed_args.epoch_interval,
            logger=logger,
        )

    elif parsed_args.sbf_ifn:

        # create RINEX files from SBF file
        parsed_args.excl_gnss = "J" # exclude no GNSS / QZSS is excluded here because in sbf2rin.sh the -x option is hardcoded, when giving no value it will throw an error 
        rnx_obs_ofp, rnx_nav_ofp  = get_rnx_frm_sbf(parsed_args=parsed_args, logger=logger)

        if parsed_args.OPUS:
            # create OPUS rnx file
            exec_gfzrnx(
                rnx_obs_ifn=rnx_obs_ofp,
                rnx_nav_ifn=rnx_nav_ofp,
                gnss=parsed_args.gnss,
                duration=parsed_args.duration,
                epoch_interval=parsed_args.epoch_interval,
                logger=logger,
            )

    else:
        print("Error: No input file specified")
        sys.exit(0)


if __name__ == "__main__":
    
    main()

