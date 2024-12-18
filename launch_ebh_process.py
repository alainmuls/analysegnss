#! /usr/bin/env python

import argparse
import os
from datetime import datetime
import sys
import glob
from logging import Logger
import subprocess

from config import ERROR_CODES
from gnss import gnss_dt
from launch_rnx2rtkp import rnx2rtkp_ppk
from sbf import sbf_constants as sbfc
from utils import argument_parser, init_logger, utilities
import get_ebh_timings
from get_base_coord import get_base_coord_from_sbf
import ebh_lines
import get_rnx_files

"""
This script orchestrates the complete EBH (Equivalent Bump Height) processing workflow.
It implements a quality-based decision system for processing GNSS data.
"""


EBH_REJECTION_LEVEL = 99  # if the number of fixed RTK/PPK points is below this level, the ebh line is rejected


def ebh_process_launcher(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings,
    decides whether the RTK or PPK solution has a sufficient quality,
    and finally outputs correct ASSUR formatted files for each ebh line.

    Args:
    parsed_args: parsed CLI arguments (check argument_parser.py for more info)

    """

    # LAUNCHING get_ebh_timings: to extract timings from sbf_ifn which creates a ebh timings file for ebh_lines
    # timings are week number and time of week format [ebh_line_key: wnc tow, wnc tow]
    ebh_timings = get_ebh_timings.get_ebh_timings(
        parsed_args=parsed_args, logger=logger
    )

    # LAUNCHING ebh_lines: in RTK mode to get ebh lines. It returns a quality analysis of each line in dict
    parsed_args.timing_ifn = parsed_args.sbf_ifn + "_ebh_timings.txt"
    ebh_qual_rtk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)

    # Checking RTK quality and rejecting lines that are not of sufficient quality
    rejected_lines, qual_decision = rtk_ppk_qual_check(
        qual_analysis=ebh_qual_rtk,
        RTK_mode=True,
        rejection_level=EBH_REJECTION_LEVEL,
        logger=logger,
    )

    # checking if ALL ebh lines are meet the criteria. If yes exit with code 0 (success) else it start PPK process
    if qual_decision == "ALL-EBH-OK":
        logger.info(
            "Solution for all ebh lines meet the quality criteria. ASSUR EBH files -> OK."
        )
        print(f"{utilities.str_green(qual_decision)}")

        sys.exit(0)

    elif parsed_args.base_corr:
        
        #### STARTING PPK PROCESS ####

        # LAUNCHING ppk_by_decision: runs rnx2rtkp in PPK mode for the ebh lines that have been rejected. It returns a rtklib pos_file
        parsed_args.pos_ifn = do_ppk_by_decision(
            rejected_rtk_lines=rejected_lines,
            rtk_qual_decision=qual_decision,
            ebh_timings=ebh_timings,
            parsed_args=parsed_args,
            logger=logger,
        )

        # LAUNCHING ebh_lines in PPK mode to get ebh lines. It returns a quality analysis of each line in dict
        del parsed_args.sbf_ifn  # delete sbf_ifn to have ebh_lines run in PPK mode
        ebh_qual_ppk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)

        rejected_lines, qual_decision = rtk_ppk_qual_check(
            qual_analysis=ebh_qual_ppk,
            RTK_mode=False,
            rejection_level=EBH_REJECTION_LEVEL,
            logger=logger,
        )

    else:
        logger.warning("Base corrections are not available. Not possible to calculate PPK. EBH ONLY BASED ON RTK")
        print(f"{utilities.str_yellow('Base correction are not available. Not possible to calculate PPK. EBH result only based on RTK')}")



    if qual_decision == "ALL-EBH-OK":

        logger.info(
            "Solution for all ebh lines meet the quality criteria. ASSUR EBH files -> OK."
        )
        print(f"{utilities.str_green(qual_decision)}")

        sys.exit(0)

    else:
        logger.warning("Solution for all ebh lines DO NOT meet the quality criteria.")

        logger.warning(
            f"EBH files {utilities.str_red(rejected_lines)} DO NOT meet the quality criteria"
        )

        print(
            f"{utilities.str_red(qual_decision)} -> EBH files {utilities.str_red(rejected_lines)} DO NOT meet the quality criteria."
        )

        sys.exit(1)


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
    ebh_qual_decision (str):    string with the decision (ALL-EBH-OK, 1-EBH-OK or ALL-EBH-NOK)
    """

    # check of qual_analysis which contains all the quality analysis of the ebh lines is empty

    if not qual_analysis:
        logger.critical("No quality analysis available. No ebh lines to check.")
        print(utilities.str_red("No quality analysis available. No ebh lines to check. Redo measurement."))
        sys.exit(ERROR_CODES["E_FAILURE"])

    logger.info(
        f"rkt_ppk checker launched for {qual_analysis} in RTK mode {RTK_mode} with a rejection level of {rejection_level}"
    )

    rejected_ebh_lines = []  # list to store the decision for each ebh line
    for ebh_key, ebh_qual_value in qual_analysis.items():
        if RTK_mode:
            if ebh_qual_value[0][2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} passed with {ebh_qual_value[0][2]}")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.warning(
                    f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[0][2]}"
                )

        else:  # PPK MODE
            if ebh_qual_value[0][2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} has passed with {ebh_qual_value[0][2]}")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.info(
                    f"ebh line {ebh_key} does not meet the quality of {ebh_qual_value[0][2]}"
                )

    # Checking PNT solution quality of each ebh line and deciding whether to continue with RTK or PPK solution
    # If more than one RTK ebh line is not sufficient, all the ebh lines will be recalculated in PPK mode
    # If only one is insufficient, the PPK is calculated for this line only
    if len(rejected_ebh_lines) == 0:
        logger.info("Solution for all ebh lines is of sufficient quality.")
        logger.info("ASSUR FILES OK")

        ebh_qual_decision = "ALL-EBH-OK"

    elif len(rejected_ebh_lines) == 1:
        ebh_qual_decision = "1-EBH-NOK"

        print(
            f"\n{utilities.str_red(ebh_qual_decision)}\nThe ebh quality check decides that the line {rejected_ebh_lines[0]} does not comply according to the rejection value of {rejection_level}.\n"
        )

        logger.warning(
            f"The ebh quality check decides that the line {rejected_ebh_lines[0]} does {utilities.str_red("not comply")} according to the rejection value of {rejection_level}."
        )
    else:
        ebh_qual_decision = "ALL-EBH-NOK"

        print(
            f"\n{utilities.str_red(ebh_qual_decision)}\nThe ebh quality check decides that that ALL EBH lines do not comply according to the rejection value of {rejection_level}."
        )
        logger.warning(
            f"The ebh quality check decides that that ALL EBH lines {utilities.str_red("do not comply")} according to the rejection value of {rejection_level}."
        )

    return rejected_ebh_lines, ebh_qual_decision


def do_ppk_by_decision(
    rejected_rtk_lines: list,
    rtk_qual_decision: str,
    ebh_timings: dict,
    parsed_args: argparse.Namespace,
    logger: Logger,
) -> str:
    """A ppk process is launched for the ebh lines according to rtk quality decision.

    args:
    rejected_rtk_lines (list): list of ebh lines that are rejected
    rtk_qual_decision (str): defines which condition is met for three possible outcomes
                        case 1: rtk_qual_sol = "ALL-EBH-OK"
                        case 2: rtk_qual_sol = "1-EBH-NOK"
                        case 3: rtk_qual_sol = "ALL-EBH-NOK"
    ebh_timings (dict): timings of each ebh line [ebh_line_key: wnc tow, wnc tow]
    parsed_args: RNX Obs, RNX Nav, base corrections (RNX or RTCM) and PPK configuration file.

    return:
    ppk_pos_ofn (str):  path to the ppk pos file
    #ebh_timings (dict): dictionary with the ebh_lines and the corresponding timings used in the ppk solution

    """

    ppk_pos_ofn = ""

    logger.info(
        f"Decided {rtk_qual_decision}. Calculating PPK solution for {rejected_rtk_lines}"
    )

    match rtk_qual_decision:
        case "ALL-EBH-OK":
            logger.info(
                "Case ALL-EBH-OK. RTK solution for all ebh lines is of sufficient quality. Nothing to do."
            )
            logger.info("ASSUR FILES OK")
            print("ASSUR FILES OK")

        case "1-EBH-NOK":

            print("Starting PPK process for rejected EBH line")
            logger.warning(
                f"Solution for the ebh line {rejected_rtk_lines} is not of sufficient quality."
                f"Calculating this single line in PPK mode with timings {ebh_timings[rejected_rtk_lines[0]]}"
            )

            # created and get the rinex files from the sbf input filename
            rnx_odir = get_rnx_files.get_rnx_frm_sbf(
                parsed_args=parsed_args, logger=logger
            )

            # get the path of the rinex files and add them them to parsed_args namespace
            rnx_obs_fn = glob.glob(
                os.path.join(rnx_odir, "*MO.rnx")
            )  # TODO check if there are no more than one MO rinex files
            parsed_args.obs = rnx_obs_fn[0]
            rnx_nav_fn = glob.glob(
                os.path.join(rnx_odir, "*MN.rnx")
            )  # TODO check if there are no more than one MN rinex files
            parsed_args.nav = rnx_nav_fn  # rnx_nav_fn is kept as a list because argpase.add_argument --nav uses the nargs=+ option. This option requires the argument to be a list of strings.

            logger.info(
                f"Using RINEX files for PPK calculation: {parsed_args.obs} and {parsed_args.nav}"
            )

            # Converting EBH TIMINGS and adding them to parsed_args namespace

            # updating ebh_timings dict by removing the timings which are not rejected.
            # ebh_timings = {rejected_rtk_lines[0]: ebh_timings[rejected_rtk_lines[0]]}

            wnctow_start = ebh_timings[rejected_rtk_lines[0]][0]  # start of ebh line
            wnctow_end = ebh_timings[rejected_rtk_lines[0]][1]  # end of ebh line

            # gnss_dt.gnss2dt returns a datetime object however get_base_coord_from_sbf expects a string in the format of YYYY-MM-DD_HH:MM:SS.s
            parsed_args.datetime = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_start[0], wnctow_start[1]),
                "%Y-%m-%d_%H:%M:%S.%f",
            )

            # Get base coordinates and them to parsed_args namespace
            base_coord = get_base_coord_from_sbf(parsed_args=parsed_args, logger=logger)
            (
                parsed_args.base_coord_X,
                parsed_args.base_coord_Y,
                parsed_args.base_coord_Z,
            ) = map(
                str, base_coord
            )  # convert to strings for CLI args used by rnx2rtkp
            logger.info(
                f"Using base coordinates: {parsed_args.base_coord_X}, {parsed_args.base_coord_Y}, {parsed_args.base_coord_Z}"
            )

            # STARTING PPK PROCESS
            logger.info(
                f"Starting PPK calculation for ebh line {rejected_rtk_lines[0]} with timings {ebh_timings[rejected_rtk_lines[0]]}"
            )

            # getting base corrections (from imported base sbf file)
            logger.info(f"The correction file is: {parsed_args.base_corr}")

            # Converting timings to RTKlib fmt. gnss_dt.gnss2dt returns a datetime object however rnx2rtkp expects a string in the format of YYYY-MM-DD_HH:MM:SS
            parsed_args.datetime_start = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_start[0], wnctow_start[1]), "%Y-%m-%d_%H:%M:%S"
            )
            parsed_args.datetime_end = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_end[0], wnctow_end[1]), "%Y-%m-%d_%H:%M:%S"
            )

            # Before running rnx2rtkp checking if base coordinates and base correction are imported correctly
            if parsed_args.base_corr is None:
                logger.error(
                    f"Base correction file = {parsed_args.base_corr}  is not imported correctly. Breaking ppk process"
                )
                ppk_pos_ofn = None

                return ppk_pos_ofn

            else:
                logger.info(
                    f"Base corrections are imported correctly. Proceeding with PPK process"
                )
                # check format of base correction file
                if parsed_args.base_corr.endswith(
                    ".sbf"
                ) or parsed_args.base_corr.endswith("_"):
                    logger.info("base correction file is in sbf format")

                    # get obs rnx format from base correction file
                    # get_rnx_frm_sbf expects parsed_args.sbf_ifn as input. So , we need to update parsed_args.sbf_ifn wth base corr sbf fn
                    sbf_ifn_rover = (
                        parsed_args.sbf_ifn
                    )  # storing original sbf file name
                    parsed_args.sbf_ifn = parsed_args.base_corr

                    base_rnx_odir = get_rnx_files.get_rnx_frm_sbf(
                        parsed_args=parsed_args, logger=logger
                    )
                    # get the path of the rinex files and add them them to parsed_args namespace
                    rnx_obs_fn = glob.glob(os.path.join(base_rnx_odir, "*MO.rnx"))
                    parsed_args.base_corr = rnx_obs_fn[0]
                    parsed_args.sbf_ifn = (
                        sbf_ifn_rover  # restore original sbf file name
                    )

                logger.info(f"using base correction file {parsed_args.base_corr}")

                # RUN rnx2rtkp
                logger.debug(
                    f"running rnx2rtkp_ppk function with parsed_args {parsed_args}"
                )
                ppk_pos_ofn = rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)

                logger.info(
                    f"Finished calculating PPK solution for ebh line {rejected_rtk_lines}. Solution saved to {ppk_pos_ofn}"
                )

        case "ALL-EBH-NOK":

            print("Starting PPK process for all EBH lines with rejected status")
            logger.warning(
                "RTK solution for one or more ebh lines is not of sufficient quality. Calculating all ebh lines in PPK mode."
            )

            logger.warning(
                f"RTK solution for all ebh lines {rejected_rtk_lines} are not of sufficient quality. \
                    Recalculating these lines in PPK mode with timings {ebh_timings}"
            )

            # created and get the rinex files from the sbf input filename
            rnx_odir = get_rnx_files.get_rnx_frm_sbf(
                parsed_args=parsed_args, logger=logger
            )

            # get the path of the rinex files and add them them to parsed_args namespace
            rnx_obs_fn = glob.glob(
                os.path.join(rnx_odir, "*MO.rnx")
            )  # TODO check if there are no more than one MO rinex files
            parsed_args.obs = rnx_obs_fn[0]
            rnx_nav_fn = glob.glob(
                os.path.join(rnx_odir, "*MN.rnx")
            )  # TODO check if there are no more than one MN rinex files
            parsed_args.nav = rnx_nav_fn  # rnx_nav_fn is kept as a list because argpase.add_argument --nav uses the nargs=+ option. This option requires the argument to be a list of strings.

            logger.info(
                f"Using RINEX files for PPK calculation: {parsed_args.obs} and {parsed_args.nav}"
            )

            # Get base coordinates and them to parsed_args namespace
            base_coord = get_base_coord_from_sbf(parsed_args=parsed_args, logger=logger)
            (
                parsed_args.base_coord_X,
                parsed_args.base_coord_Y,
                parsed_args.base_coord_Z,
            ) = base_coord
            logger.info(
                f"Using base coordinates: {parsed_args.base_coord_X}, {parsed_args.base_coord_Y}, {parsed_args.base_coord_Z}"
            )

            # Calculate PPK
            logger.info(
                f"Starting PPK calculation for ebh lines {rejected_rtk_lines} with timings {ebh_timings}"
            )
            logger.info(f"The correction file is: {parsed_args.base_corr}")

            # before calculating the PPK solution, check if the base correction file or/and base coordinates are imported correctly

            if parsed_args.base_corr is None:
                logger.error(
                    f"Base correction file = {parsed_args.base_corr} is not imported correctly. Breaking PPK process"
                )
                ppk_pos_ofn = None

                return ppk_pos_ofn

            else:
                logger.info(f"base correction file is imported correctly")

                # check format of base correction file
                if parsed_args.base_corr.endswith(
                    ".sbf"
                ) or parsed_args.base_corr.endswith("_"):
                    logger.info("base correction file is in sbf format")

                    # get obs rnx format from base correction file
                    # get_rnx_frm_sbf expects parsed_args.sbf_ifn as input. So , we need to update parsed_args.sbf_ifn wth base corr sbf fn
                    sbf_ifn_rover = (
                        parsed_args.sbf_ifn
                    )  # storing original sbf file name
                    parsed_args.sbf_ifn = parsed_args.base_corr

                    base_rnx_odir = get_rnx_files.get_rnx_frm_sbf(
                        parsed_args=parsed_args, logger=logger
                    )
                    # get the path of the rinex files and add them them to parsed_args namespace
                    rnx_obs_fn = glob.glob(os.path.join(base_rnx_odir, "*MO.rnx"))
                    parsed_args.base_corr = rnx_obs_fn[0]
                    parsed_args.sbf_ifn = (
                        sbf_ifn_rover  # restore original sbf file name
                    )

                logger.info(f"using base correction file {parsed_args.base_corr}")

                # CALCULATING PPK: calling rnx2rtkp_ppk function
                logger.info(
                    f"running rnx2rtkp_ppk function with parsed_args {parsed_args}"
                )
                ppk_pos_ofn = rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)

                logger.info(
                    f"Finished calculating PPK solution for ebh lines {rejected_rtk_lines} with timings {ebh_timings}. Saved solution to {ppk_pos_ofn}"
                )

    return ppk_pos_ofn


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
