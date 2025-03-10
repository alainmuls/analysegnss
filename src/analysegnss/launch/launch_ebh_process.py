#! /usr/bin/env python

# Standard library imports
import argparse
import os
from datetime import datetime
import sys
from logging import Logger
from rich import print as rprint

# Local imports
from analysegnss.config import ERROR_CODES
from analysegnss.gnss import gnss_dt
from analysegnss.launch.launch_rnx2rtkp import rnx2rtkp_ppk
from analysegnss.utils import argument_parser, init_logger, utilities
from analysegnss.scripts.ebh.ebh_exit_codes import EBH_EXIT_CODES
from analysegnss.scripts.ebh.get_ebh_timings import get_ebh_timings
from analysegnss.sbf.get_base_xyz_from_sbf import get_base_coord_from_sbf
from analysegnss.scripts.ebh.ebh_lines import ebh_lines
from analysegnss.rinex import get_rnx_files
from analysegnss.scripts.ebh.gradient_ebhlines import gradient_ebhlines
from analysegnss.scripts.ebh.ebh_print import (
    print_ebh_ok,
    print_ebh_nok,
    print_starting_ppk_process,
)
from analysegnss.utils.utilities import ProcessOutputCollector

"""
This script orchestrates the complete EBH (Equivalent Bump Height) processing workflow.
It implements a quality-based decision system for processing GNSS data and calculates runway gradients.
"""

# TODO: improve the RTK/PPK quality check by also checking standard deviation error of RTK/PPK solution
# TODO: create sys exit EBH decision look up table

EBH_REJECTION_LEVEL = 99  # if the number of fixed RTK/PPK points is below this level, the ebh line is rejected


def ebh_process_launcher(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Launches the appropriate functions to calculate the ebh_lines from the sbf_ifn file,
    retrieves the correct timings, decides whether the RTK or PPK solution has sufficient quality,
    outputs ASSUR formatted files for each ebh line, and calculates runway gradients.

    Args:
    parsed_args: parsed CLI arguments (check argument_parser.py for more info)

    Returns:
    sys.exit(0) if ebh lines are of sufficient quality
    sys.exit(1) if ebh lines are not of sufficient quality
    """
    message_collector = (
        ProcessOutputCollector()
    )  # collects EBH checkpoint messages and saves them to a file

    try:
        # Step 1: Get EBH timings
        ebh_timings = get_ebh_timings(parsed_args=parsed_args, logger=logger)

        # Step 2: Process RTK solution
        rtk_result = process_rtk_solution(
            parsed_args=parsed_args, ebh_timings=ebh_timings, logger=logger
        )

        ## store RTK process EBH decision and PVT quality analysis
        message_collector.add_message(rtk_result.get("msg_pvt_qanalysis", ""))
        message_collector.add_message(rtk_result.get("msg_ebh_decision", ""))

        if rtk_result.get("success", False):
            # Calculate and save runway gradients if RTK was successful
            calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
            message_collector.save_to_file(
                output_path=os.path.join(
                    os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)),
                    "EBH_ASSUR",
                    "EBH_process_summary.txt",
                )
            )
            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_SUCCESS"])

        # Step 3: Process PPK solution if RTK wasn't sufficient
        ppk_result = process_ppk_solution(
            parsed_args=parsed_args,
            rtk_result=rtk_result,
            ebh_timings=ebh_timings,
            logger=logger,
        )

        ## store PPK process EBH decision and PVT quality analysis
        message_collector.add_message(ppk_result.get("msg_pvt_qanalysis", "[WARNING] Unable to calculate PPK. Check logs for more info.\n"))
        message_collector.add_message(ppk_result.get("msg_ebh_decision", "[WARNING] EBH measurement only based on (insufficient) RTK solution.\n"))

        if ppk_result.get("success", False):
            # Calculate and save runway gradients if PPK was successful
            calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
            message_collector.save_to_file(
                output_path=os.path.join(
                    os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)),
                    "EBH_ASSUR",
                    "EBH_process_summary.txt",
                )
            )
            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_SUCCESS"])

        else:
            try:
                logger.warning(
                    "Trying to calculate runway gradients using insufficient RTK/PPK solution."
                )
                calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
                message_collector.save_to_file(
                    output_path=os.path.join(
                        os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)),
                        "EBH_ASSUR",
                        "EBH_process_summary.txt",
                    )
                )
            except Exception as e:
                logger.error(f"Calculation of runway gradients failed: {e}")
                rprint(f"[red]Calculation of runway gradients failed: {e}[/red]")

            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_INSUFFICIENT"])

    except Exception as e:
        logger.error(f"Error in ebh_process_launcher: {e}")
        rprint(f"[red]ERROR {e} in measurements. Redo measurement.[/red]")
        message_collector.add_message(f"ERROR {e} in measurements. Redo measurement.")
        message_collector.save_to_file(
            output_path=os.path.join(
                os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)),
                "EBH_ASSUR",
                "EBH_process_summary.txt",
            )
        )
        sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_FAILED"])


def process_rtk_solution(
    parsed_args: argparse.Namespace, ebh_timings: dict, logger: Logger
) -> dict:
    """Process RTK solution and check its quality.

    Args:
    parsed_args (argparse.Namespace): parsed CLI arguments.
                                        - sbf_ifn: path to the sbf_ifn file
                                        - timing_ifn: path to the timing_ifn file
                                        - log_dest: destination of the log file
    ebh_timings (dict): timings of each ebh line [ebh_line_key: wnc tow, wnc tow]
    logger (Logger): logger object

    Returns:
    dict containing success status and rejected lines if any
    """
    try:
        # Get RTK solution
        parsed_args.ebh_timings = ebh_timings
        ebh_qual_rtk = ebh_lines(parsed_args=parsed_args, logger=logger)

        # Check RTK quality
        rejected_lines, qual_decision = rtk_ppk_qual_check(
            qual_analysis=ebh_qual_rtk,
            rejection_level=EBH_REJECTION_LEVEL,
            logger=logger,
        )

        if qual_decision == "ALL-EBH-OK":
            msg_ebh_decision, msg_pvt_qanalysis = print_ebh_ok(
                logger=logger, pvt_qanalysis=ebh_qual_rtk, source="RTK"
            )
            return {
                "success": True,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pvt_qanalysis": msg_pvt_qanalysis,
            }
        else:
            msg_ebh_decision, msg_pvt_qanalysis = print_ebh_nok(
                logger=logger,
                pvt_qanalysis=ebh_qual_rtk,
                rejected_lines=rejected_lines,
                rejection_level=EBH_REJECTION_LEVEL,
                source="RTK",
            )
            return {
                "success": False,
                "rejected_lines": rejected_lines,
                "qual_decision": qual_decision,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pvt_qanalysis": msg_pvt_qanalysis,
            }

    except Exception as e:
        logger.error(f"Error in RTK processing: {e}")
        logger.error("Not able to calculate RTK")
        rprint(f"[red]Not able to calculate RTK[/red]")
        return {"success": False, "error": str(e)}


def process_ppk_solution(
    parsed_args: argparse.Namespace, rtk_result: dict, ebh_timings: dict, logger: Logger
) -> dict:
    """Process PPK solution if RTK wasn't sufficient.

    Args:
    parsed_args (argparse.Namespace): parsed arguments.
                                        - base_corr: path to the base correction file
                                        - pos_ifn: path to the pos_ifn file
                                        - sbf_ifn: path to the sbf_ifn file
                                        - timing_ifn: path to the timing_ifn file
                                        - log_dest: destination of the log file
    rtk_result (dict): result of RTK processing
    ebh_timings (dict): timings of each ebh line [ebh_line_key: wnc tow, wnc tow]
    logger (Logger): logger object

    Returns:
    dict containing success status, message ebh decision and message PVT quality analysis
    """
    if not parsed_args.base_corr:
        logger.warning(
            "Base corrections are not available. Not possible to calculate PPK."
        )
        rprint(
            f"[yellow][WARNING][/yellow] Base corrections are not available. Not possible to calculate PPK."
        )
        return {"success": False}

    try:
        # Run PPK processing
        parsed_args.pos_ifn = do_ppk_by_decision(
            rejected_ebh_lines=rtk_result["rejected_lines"],
            ebh_qual_decision=rtk_result["qual_decision"],
            ebh_timings=ebh_timings,
            parsed_args=parsed_args,
            logger=logger,
        )

        # Process PPK results
        sbf_ifn = parsed_args.sbf_ifn
        del (
            parsed_args.sbf_ifn
        )  # delete sbf_ifn from parsed_args to avoid it being used in the ebh_lines function
        # ebh_lines function is called with pos_ifn as input
        ebh_qual_ppk = ebh_lines(
            parsed_args=parsed_args, logger=logger
        )  # TODO maybe adapt mutually exclusive group to only allow sbf_ifn or pos_ifn?
        parsed_args.sbf_ifn = sbf_ifn  # restore sbf_ifn in parsed_args

        # Check PPK quality
        rejected_lines, qual_decision = rtk_ppk_qual_check(
            qual_analysis=ebh_qual_ppk,
            rejection_level=EBH_REJECTION_LEVEL,
            logger=logger,
        )

        if qual_decision == "ALL-EBH-OK":
            msg_ebh_decision, msg_pvt_qanalysis = print_ebh_ok(
                logger=logger, pvt_qanalysis=ebh_qual_ppk, source="PPK"
            )
            return {
                "success": True,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pvt_qanalysis": msg_pvt_qanalysis,
            }
        else:
            msg_ebh_decision, msg_pvt_qanalysis = print_ebh_nok(
                logger=logger,
                pvt_qanalysis=ebh_qual_ppk,
                rejected_lines=rejected_lines,
                rejection_level=EBH_REJECTION_LEVEL,
                source="PPK",
            )
            return {
                "success": False,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pvt_qanalysis": msg_pvt_qanalysis,
            }

    except Exception as e:
        logger.error(f"Error in PPK processing: {e}")
        rprint(f"[red]Not able to calculate PPK[/red]")
        return {"success": False, "error": str(e)}


def calculate_runway_gradients(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Calculate and save runway gradients after successful EBH processing.

    Args:
    parsed_args (argparse.Namespace): parsed_args.
                                        - sbf_ifn: path to the sbf_ifn file
                                        - log_dest: destination of the log file
    logger (Logger): logger object

    Returns:
    None
    """
    try:
        # Set up arguments for gradient calculation
        gradient_args = argparse.Namespace(
            input_dir=os.path.join(os.path.dirname(parsed_args.sbf_ifn), "EBH_ASSUR"),
            desc=parsed_args.desc,
            output_dir=os.path.join(os.path.dirname(parsed_args.sbf_ifn), "EBH_ASSUR"),
            output_filename="runway_gradients.txt",
            log_dest=parsed_args.log_dest,
        )

        # Calculate gradients
        gradient_ebhlines(parsed_args=gradient_args, logger=logger)

    except Exception as e:
        logger.error(f"Error calculating runway gradients: {e}")
        rprint(f"[yellow]Warning: Could not calculate runway gradients[/yellow]")


def rtk_ppk_qual_check(
    qual_analysis: dict, rejection_level: float, logger: Logger
) -> list:
    """Checks the RTK or PPK solutions and checks if the line is of sufficient quality
    to be used for the ebh_lines calculation and ASSURtool. It returns the rejected lines.

    Args:
    qual_analysis (dict):       dictionary with the quality analysis of the RTK/PPK solution
                                for each ebh line
    rejection level (float):    a level of fixed_points/total (percentage) that needs to be met.
                                Otherwise the results is rejected.

    Returns:
    rejected_ebh_lines (list):  list of ebh lines that are rejected
    ebh_qual_decision (str):    string with the decision (ALL-EBH-OK, 1-EBH-OK or ALL-EBH-NOK)
    """

    logger.info(
        f"RTK/PPK checker launched for {qual_analysis} with a rejection level of ebh {rejection_level}% fixed PNT points."
    )

    number_ebh_lines = len(qual_analysis)

    if number_ebh_lines == 0:
        logger.critical("No quality analysis available. No ebh lines to check.")
        rprint(
            "[red]No quality analysis available. No ebh lines to check. Redo measurement.[/red]"
        )
        sys.exit(1)

    logger.info(f"Number of measured ebh lines: {number_ebh_lines}")

    rejected_ebh_lines = []  # list to store the decision for each ebh line
    for ebh_key, ebh_qual_value in qual_analysis.items():

        # check if FIXED quality is met by matching RTKLIB AND SBF PVT QUAL TABLES
        # loop though the saved quality tables to select only the FIXED quality / TODO: CREATE general GNSS qual lookup table
        for n in range(len(ebh_qual_value)):
            if (
                ebh_qual_value[n][0] == "RTK with ﬁxed ambiguities"
                or ebh_qual_value[n][0] == "PPK with ﬁxed ambiguities"
            ):

                if (
                    ebh_qual_value[n][1] > 0
                ):  # checks if ebh lines holds any data with fixed quality
                    logger.info(
                        f"Number of measured points with FIXED quality for {ebh_key}: {ebh_qual_value[n][1]}/{ebh_qual_value[n][3]}"
                    )

                    if ebh_qual_value[n][2] >= rejection_level:
                        logger.info(
                            f"ebh line {ebh_key} passed with {ebh_qual_value[n][2]}"
                        )
                    else:
                        rejected_ebh_lines.append(ebh_key)
                        logger.warning(
                            f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[n][2]} against the rejection level of {rejection_level}% fixed PNT points."
                        )
                    break
            else:
                logger.debug(
                    f"<{ebh_qual_value[n][0]}> does not match <RTK with fixed ambiguities> or <PPK with fixed ambiguities>"
                )
                logger.warning(
                    f"measurements for ebh line {ebh_key} do not contain any FIXED PNT quality points."
                )
                rejected_ebh_lines.append(ebh_key)

    # Checking PNT solution quality of each ebh line and deciding whether to continue with RTK or PPK solution
    # If more than one RTK ebh line is not sufficient, all the ebh lines will be recalculated in PPK mode
    # If only one is insufficient, the PPK is calculated for this line only
    if len(rejected_ebh_lines) == 0:

        ebh_qual_decision = "ALL-EBH-OK"

        logger.info(f"ebh_qual_decision: {ebh_qual_decision}")

    elif len(rejected_ebh_lines) == 1:

        ebh_qual_decision = "1-EBH-NOK"

        logger.info(f"ebh_qual_decision: {ebh_qual_decision}")

    else:
        ebh_qual_decision = "ALL-EBH-NOK"

        logger.info(f"ebh_qual_decision: {ebh_qual_decision}")

    return rejected_ebh_lines, ebh_qual_decision


def do_ppk_by_decision(
    rejected_ebh_lines: list,
    ebh_qual_decision: str,
    ebh_timings: dict,
    parsed_args: argparse.Namespace,
    logger: Logger,
) -> str:
    """A ppk process is launched for the ebh lines according to ebh quality decision.

    args:
    rejected_ebh_lines (list): list of ebh lines that are rejected
    ebh_qual_decision (str): defines which condition is met for three possible outcomes
                        case 1: ebh_qual_sol = "ALL-EBH-OK"
                        case 2: ebh_qual_sol = "1-EBH-NOK"
                        case 3: ebh_qual_sol = "ALL-EBH-NOK"
    ebh_timings (dict): timings of each ebh line [ebh_line_key: wnc tow, wnc tow]
    parsed_args: RNX Obs, RNX Nav, base corrections (RNX or RTCM) and PPK configuration file.

    return:
    ppk_pos_ofn (str):  path to the ppk pos file
    #ebh_timings (dict): dictionary with the ebh_lines and the corresponding timings used in the ppk solution

    """

    # initialize ppk_pos output file name and rnx navigation filename list (if PPK is needed)
    ppk_pos_ofn = ""
    parsed_args.nav = (
        []
    )  # parsed_args.nav is configured with nargs=+ option in argument_parser_rnx2rtkp_launcher. This option requires the argument to be a list of strings.

    # configure rtklib PPK config file if not specified
    if parsed_args.config_ppk is None:
        # get relative path of the rtklib PPK config file
        rtklib_ppk_config = os.path.join(
            os.path.dirname(__file__),
            "..",
            "rtkpos",
            "rnx2rtkp_config",
            "rnx2rtkp_EBH_PPK_default.conf",
        )
        parsed_args.config_ppk = os.path.normpath(rtklib_ppk_config)
        logger.debug(
            f"PPK configuration file not specified. Using default configuration file {parsed_args.config_ppk}"
        )

    match ebh_qual_decision:
        case "ALL-EBH-OK":
            pass

        case "1-EBH-NOK":
            print_starting_ppk_process(logger, rejected_ebh_lines, ebh_timings)

            ### EXTRACTING EBH TIMING INFO OF REJECTED EBH LINE ###
            wnctow_start = ebh_timings[rejected_ebh_lines[0]][0]  # start of ebh line
            wnctow_end = ebh_timings[rejected_ebh_lines[0]][1]  # end of ebh line

            # gnss_dt.gnss2dt returns a datetime object however get_base_coord_from_sbf used in get_base_data_for_PPK expects a string in the format of YYYY-MM-DD_HH:MM:SS.s
            parsed_args.datetime = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_start[0], wnctow_start[1]),
                "%Y-%m-%d_%H:%M:%S.%f",
            )
            # Converting timings to RTKlib fmt. gnss_dt.gnss2dt returns a datetime object however rnx2rtkp expects a string in the format of YYYY-MM-DD_HH:MM:SS
            parsed_args.datetime_start = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_start[0], wnctow_start[1]), "%Y-%m-%d_%H:%M:%S"
            )
            parsed_args.datetime_end = datetime.strftime(
                gnss_dt.gnss2dt(wnctow_end[0], wnctow_end[1]), "%Y-%m-%d_%H:%M:%S"
            )

            ### GET ROVER DATA FOR PPK ###
            rnx_obs_fn, rnx_nav_fn = get_rnx_files.get_rnx_frm_sbf(
                parsed_args=parsed_args, logger=logger
            )
            parsed_args.obs = rnx_obs_fn
            parsed_args.nav.append(rnx_nav_fn)

            ### GET BASE COORDINATES ###
            if parsed_args.base_corr is None:
                logger.error(
                    f"Base correction file = {parsed_args.base_corr} is not imported correctly. Breaking PPK process"
                )
                ppk_pos_ofn = None

                return ppk_pos_ofn
            else:
                logger.debug(
                    f"base correction file is imported correctly: {parsed_args.base_corr}"
                )

                # getting obs, nav and base coordinates from sbf_ifn
                rnx_obs_fn, rnx_nav_fn, base_coord_X, base_coord_Y, base_coord_Z = (
                    get_base_data_for_PPK(parsed_args=parsed_args, logger=logger)
                )

                # adding obs and nav file to parsed_args.base_corr and parsed_args.nav
                parsed_args.base_corr = rnx_obs_fn
                parsed_args.nav.append(rnx_nav_fn)

                # adding base coordinates to parsed_args
                parsed_args.base_coord_X = base_coord_X
                parsed_args.base_coord_Y = base_coord_Y
                parsed_args.base_coord_Z = base_coord_Z

            ### CALCULATING PPK ###
            logger.info(
                f"Starting PPK calculation for ebh line {rejected_ebh_lines[0]} with timings {ebh_timings[rejected_ebh_lines[0]]}"
            )
            logger.debug(
                f"running rnx2rtkp_ppk function with parsed_args {parsed_args}"
            )
            ppk_pos_ofn = rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)

            logger.info(
                f"Finished calculating PPK solution for ebh line {rejected_ebh_lines}. Solution saved to {ppk_pos_ofn}"
            )

        case "ALL-EBH-NOK":
            print_starting_ppk_process(logger, rejected_ebh_lines, ebh_timings)

            ### GET ROVER DATA FOR PPK ###
            rnx_obs_fn, rnx_nav_fn = get_rnx_files.get_rnx_frm_sbf(
                parsed_args=parsed_args, logger=logger
            )
            parsed_args.obs = rnx_obs_fn
            parsed_args.nav.append(
                rnx_nav_fn
            )  # parsed_args.nav is configured with nargs=+ option. This option requires the argument to be a list of strings.

            ### GET BASE DATA FOR PPK ###
            if parsed_args.base_corr is None:
                logger.error(
                    f"Base correction file = {parsed_args.base_corr} is not imported correctly. Breaking PPK process"
                )
                ppk_pos_ofn = None

                return ppk_pos_ofn
            else:

                logger.debug(
                    f"base correction file is imported correctly: {parsed_args.base_corr}"
                )

                # getting obs, nav and base coordinates from sbf_ifn
                rnx_obs_fn, rnx_nav_fn, base_coord_X, base_coord_Y, base_coord_Z = (
                    get_base_data_for_PPK(parsed_args=parsed_args, logger=logger)
                )

                # adding obs and nav file to parsed_args.base_corr and parsed_args.nav
                parsed_args.base_corr = rnx_obs_fn
                parsed_args.nav.append(rnx_nav_fn)

                # adding base coordinates to parsed_args
                parsed_args.base_coord_X = base_coord_X
                parsed_args.base_coord_Y = base_coord_Y
                parsed_args.base_coord_Z = base_coord_Z

            ### CALCULATING PPK ###
            logger.debug(
                f"running rnx2rtkp_ppk function with parsed_args {parsed_args}"
            )
            ppk_pos_ofn = rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)

            logger.info(
                f"Finished calculating PPK solution for ebh lines {rejected_ebh_lines} with timings {ebh_timings}. Saved solution to {ppk_pos_ofn}"
            )

    return ppk_pos_ofn


def get_base_data_for_PPK(
    parsed_args: argparse.Namespace, logger: Logger
) -> tuple[str, str, str, str, str]:
    """
    This function creates and gets the base coordinates,the base rinex observation (correction file for PPK) and navigation files from the base sbf file (parsed_args.sbf_ifn)
    It extracts the obs and nav file to parsed_args.base_corr and parsed_args.nav
    It extracts the base coordinates from the SBF file logged by the base station to parsed_args.base_coord_X, parsed_args.base_coord_Y, parsed_args.base_coord_Z
    If parsed_args.datetime is included, it will be used to get base coordinates at that time

    args:
    argparse.Namespace: parsed_args.sbf_ifn, parsed_args.datetime
    Logger: logger

    returns:
    str: rnx_obs_fn
    str: rnx_nav_fn
    str: base_coord_X
    str: base_coord_Y
    str: base_coord_Z

    """

    # Get base coordinates and add them to parsed_args namespace in string format
    base_coord = get_base_coord_from_sbf(parsed_args=parsed_args, logger=logger)
    (
        base_coord_X,
        base_coord_Y,
        base_coord_Z,
    ) = map(str, base_coord)

    logger.info(
        f"Using base coordinates: {base_coord_X}, {base_coord_Y}, {base_coord_Z}"
    )

    # check format of base correction file
    if parsed_args.sbf_ifn.endswith(".sbf") or parsed_args.sbf_ifn.endswith("_"):
        logger.debug("base correction file is in sbf format")

        # Get_base_data_for_PPK expects parsed_args.sbf_ifn as input. So, parsed_args.sbf_ifn is updated with base corr sbf ifn
        parsed_args.sbf_ifn = parsed_args.base_corr
        # get obs rnx format from base correction file
        rnx_obs_fn, rnx_nav_fn = get_rnx_files.get_rnx_frm_sbf(
            parsed_args=parsed_args, logger=logger
        )

    else:
        logger.debug("Specified base correction file is in RNX format")

    logger.info(f"using base rinex correction file {rnx_obs_fn}")

    return rnx_obs_fn, rnx_nav_fn, base_coord_X, base_coord_Y, base_coord_Z


def main():
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_ebh_process_launcher(
        script_name=script_name, args=sys.argv[1:]
    )

    # create the file/console logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    logger.info(f"Parsed arguments: {parsed_args}")

    ebh_process_launcher(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":

    main()
