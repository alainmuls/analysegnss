#! /usr/bin/env python

import argparse
import datetime
import logging
import os
import polars as pl
import sys
import subprocess

from analysegnss.config import ERROR_CODES
from analysegnss.gnss import gnss_dt
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import argument_parser, init_logger, utilities


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
    rnx2rtkp_config_fn (str): rnx2rtkp configuration file
    datetime_start (str): start time of calculation. format: YYYY-MM-DD_HH:MM:SS.f
    datetime_end (str): end time of calculation YYYY-MM-DD_HH:MM:SS.f
    out_fn: output directory

    returns:
    pos_ofn (str): output filename of PPK solution

    """

    # configure output filename
    if hasattr(parsed_args, "pos_ofn") and parsed_args.pos_ofn:
        pos_ofn = parsed_args.pos_ofn
    else:
        pos_ofn, _ = os.path.splitext(parsed_args.obs)
        pos_ofn = pos_ofn + "_PPK.pos"

    # check if rnx2rtkp is installed
    rnx2rtkp_path = utilities.locate("rnx2rtkp")
    if rnx2rtkp_path is None:
        print("rnx2rtkp not found in PATH. Please install RTKLIB. Program exits.")
        sys.exit(ERROR_CODES["E_PROCESS"])

    # define command line arguments

    cmd_rnx2rtkp = [
        rnx2rtkp_path,
        "-k",
        parsed_args.config_ppk,
        "-r",
        parsed_args.base_coord_X,
        parsed_args.base_coord_Y,
        parsed_args.base_coord_Z,
    ]

    # adding timings to the command line arguments
    if (
        hasattr(parsed_args, "datetime_start")
        and hasattr(parsed_args, "datetime_end")
        and parsed_args.datetime_start
        and parsed_args.datetime_end
    ):
        # remove underscore from datetime format to get isoformat %Y-%m-%d %H:%M:%S
        s_dt = parsed_args.datetime_start.replace("_", " ")
        e_dt = parsed_args.datetime_end.replace("_", " ")
        s_dt_obj = datetime.datetime.fromisoformat(s_dt)
        e_dt_obj = datetime.datetime.fromisoformat(e_dt)
        cmd_rnx2rtkp.extend(
            [
                "-ts",
                s_dt_obj.strftime("%Y/%m/%d"),
                s_dt_obj.strftime("%H:%M:%S"),
                "-te",
                e_dt_obj.strftime("%Y/%m/%d"),
                e_dt_obj.strftime("%H:%M:%S"),
            ]
        )
    else:
        s_dt_obj = None
        e_dt_obj = None

    # configure output filename
    if hasattr(parsed_args, "pos_ofn") and parsed_args.pos_ofn:
        pos_ofn = parsed_args.pos_ofn
        logger.info(f"Using {pos_ofn} as output file name for rnx2rtkp process")
    else:
        pos_ofn, _ = os.path.splitext(parsed_args.obs)
        if s_dt_obj and e_dt_obj:
            s_time = s_dt_obj.strftime("%H%M%S")
            tdiff = e_dt_obj - s_dt_obj
            tdiff_s = round(tdiff.total_seconds())
            # file name resembles RNX naming fmt: obs_PPK_000000_100S.pos
            pos_ofn = (
                pos_ofn + "_PPK_" + s_time + "_" + str(tdiff_s) + "S.pos"
            )  # TODO this naively trusts the cli timings, better would be to check first epoch of observation
        else:
            pos_ofn = pos_ofn + "_PPK.pos"
        logger.info(f"Using {pos_ofn} as output file name for rnx2rtkp process")

    cmd_rnx2rtkp.extend(["-o", pos_ofn])

    # TODO Get effective log leveli
    logger.info("Putting rnx2rtkp in debugging mode")
    print("rnx2rtkp in debugging mode")
    cmd_rnx2rtkp.extend(["-x", "2"])

    # add obs and nav rnx filenames to cli
    cmd_rnx2rtkp.extend([parsed_args.obs, parsed_args.base_corr])
    cmd_rnx2rtkp.extend(
        parsed_args.nav
    )  # parsed_args.nav is a list of multiple nav files

    logger.debug(
        f"Running rnx2rtkp using input files {parsed_args.obs}, {parsed_args.base_corr} and {parsed_args.nav} \
    base station XYZ {parsed_args.base_coord_X}, {parsed_args.base_coord_Y}, {parsed_args.base_coord_Z}"
    )
    logger.debug(f"Running rnx2rtkp for PPK solution with command: {cmd_rnx2rtkp}")

    # run rnx2rtkp
    try:
        proc_rnx2rtkp = subprocess.run(
            cmd_rnx2rtkp, check=True, stdout=sys.stdout, stderr=sys.stderr
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"rnx2rtkp failed with error code {e.returncode}")
        sys.exit(ERROR_CODES["E_PROCESS"])

    logger.info(f"Finished calculating PPK solution. Written file to {pos_ofn}")

    return pos_ofn


def main():

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_rnx2rtkp_launcher(args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    logger.debug(f"Parsed arguments: {parsed_args}")

    rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":

    main()