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

def exec_gfzrnx(rnx_obs_ifn: str, gnss: str, duration: int, epoch_interval: int, logger=Logger | None):

    # get directory of input file and use it as output directory
    dir_ofn = os.path.dirname(os.path.realpath(rnx_obs_ifn))

    # configure executables: gfzrnx (Rinex tool)
    exec_gfzrnx = shutil.which("gfzrnx")

    logger.debug(f"gfzrnx executable: {exec_gfzrnx}")
    
    rnx2OPUS = [
        exec_gfzrnx,
        "-f",
        "-finp",
        rnx_obs_ifn,
        "-fout",
        f"{dir_ofn}/::RX3::",
        "-smp",
        f"{epoch_interval}",
        "-satsys",
        gnss,
        "--duration",
        f"{duration}",
    ]

    try:
        proc_OPUS = subprocess.run(rnx2OPUS)
    except subprocess.CalledProcessError as e:
        print(f"Error in running gfzrnx: {e}")
        sys.exit()

    print(
        f"gfzrnx process finished. Created RNX file for OPUS processing and stored it in {dir_ofn}"
    )
    if logger:
        logger.info(f"gfzrnx process finished. Created RNX file for OPUS processing and stored it in {dir_ofn}")
    

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
        rnx_obs_ofp, _  = get_rnx_frm_sbf(parsed_args=parsed_args, logger=logger)

        if parsed_args.OPUS:
            # create OPUS rnx file
            exec_gfzrnx(
                rnx_obs_ifn=rnx_obs_ofp,
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

