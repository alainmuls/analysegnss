#! /usr/bin/env python

# Standard library imports
import argparse
import os
from datetime import datetime
import sys
from logging import Logger
from rich import print as rprint
import glob

# Local imports
from analysegnss.config import ERROR_CODES
from analysegnss.gnss import gnss_dt
from analysegnss.launch.launch_rnx2rtkp import rnx2rtkp_ppk
from analysegnss.utils import argument_parser, init_logger, utilities
from analysegnss.scripts.ebh.ebh_exit_codes import EBH_EXIT_CODES
from analysegnss.scripts.ebh.get_ebh_timings import get_ebh_timings
from analysegnss.sbf.get_base_coord_from_sbf import get_base_coord_from_sbf
from analysegnss.scripts.ebh.ebh_lines import ebh_lines
from analysegnss.rinex import get_rnx_files
from analysegnss.scripts.ebh.gradient_ebhlines import gradient_ebhlines
from analysegnss.scripts.ebh.ebh_print import (
    print_ebh_ok,
    print_ebh_nok,
    print_starting_ppk_process,
)
from analysegnss.utils.utilities import ProcessOutputCollector
from analysegnss.pnt.pnt_data_collector import pnt_data_collector
from analysegnss.plots.plot_coords import plot_coords

"""
This script orchestrates the complete EBH (Equivalent Bump Height) processing workflow.
It implements a quality-based decision system for processing GNSS data and calculates runway gradients.
"""
# TODO: remove case one-EBH-OK. If one line is rejected, calculate PPK for all lines. (Also risk of map angle being wrong when only one line is processed)
# TODO: improve the RTK/PPK quality check by also checking standard deviation error of RTK/PPK solution

EBH_REJECTION_LEVEL = 99  # if the number of fixed RTK/PPK points is below this level, the ebh line is rejected


def ebh_process_launcher(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Launches the appropriate functions to calculate the ebh_lines from the sbf_ifn file,
    retrieves the correct timings, decides whether the RTK or PPK solution has sufficient quality,
    outputs ASSUR formatted files for each ebh line, and calculates runway gradients.

    Args:
        parsed_args: parsed CLI arguments (check argument_parser.py for more info)
        logger: logger object for logging messages

    Returns:
        None, but exits with appropriate exit code:
        - EBH_MEASUREMENT_SUCCESS (0) if ebh lines are of sufficient quality
        - EBH_MEASUREMENT_INSUFFICIENT (1) if ebh lines are not of sufficient quality
        - EBH_MEASUREMENT_FAILED (2) if there was an error in processing
    """
    message_collector = ProcessOutputCollector()
    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(parsed_args.sbf_ifn)), "EBH_ASSUR"
    )
    summary_file = os.path.join(output_dir, "EBH_process_summary.txt")

    message_collector.add_message(
        f"[START] Starting EBH process for {parsed_args.sbf_ifn} with {parsed_args.desc} as description\n"
    )

    try:
        # Step 1: Get EBH timings
        logger.info("Starting EBH timing extraction")
        ebh_timings = get_ebh_timings(parsed_args=parsed_args, logger=logger)
        logger.info(f"Successfully extracted timings for {len(ebh_timings)} EBH lines")

        # Step 2: Process RTK solution
        logger.info("Starting RTK solution processing")
        message_collector.add_message("Starting RTK solution processing")
        rtk_result = process_rtk_solution(
            parsed_args=parsed_args, ebh_timings=ebh_timings, logger=logger
        )

        # Store RTK process results
        message_collector.add_message(rtk_result.get("msg_pnt_analysis", ""))
        message_collector.add_message(rtk_result.get("msg_ebh_decision", ""))

        if rtk_result.get("success", False):
            logger.info("RTK solution meets quality criteria")
            calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "Calculation of runway gradients successful.\n"
            )
            # Collect and plot EBH data
            collect_and_plot_ebh_data(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "PNT data collection and plotting successful.\n"
            )
            message_collector.save_to_file(output_path=summary_file)
            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_SUCCESS"])

        # Step 3: Process PPK solution if RTK wasn't sufficient
        logger.info("Starting PPK solution processing")
        message_collector.add_message("Starting PPK solution processing")
        ppk_result = process_ppk_solution(
            parsed_args=parsed_args,
            rtk_result=rtk_result,
            ebh_timings=ebh_timings,
            logger=logger,
        )

        # Store PPK process results
        message_collector.add_message(
            ppk_result.get(
                "msg_pnt_analysis",
                "[WARNING] Unable to calculate PPK. Check logs for more info.\n",
            )
        )
        message_collector.add_message(
            ppk_result.get(
                "msg_ebh_decision",
                "[WARNING] EBH measurement only based on (insufficient) RTK solution.\n",
            )
        )

        if ppk_result.get("success", False):
            logger.info("PPK solution meets quality criteria")
            calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "Calculation of runway gradients successful.\n"
            )
            # Collect and plot EBH data
            collect_and_plot_ebh_data(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "PNT data collection and plotting successful.\n"
            )
            message_collector.save_to_file(output_path=summary_file)
            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_SUCCESS"])

        # If both RTK and PPK failed, try to calculate gradients with insufficient data
        logger.warning(
            "Both RTK and PPK solutions failed quality check. Attempting to calculate gradients with insufficient data."
        )
        try:
            calculate_runway_gradients(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "Calculation of runway gradients successful.\n"
            )
            # Collect and plot EBH data even with insufficient quality
            collect_and_plot_ebh_data(parsed_args=parsed_args, logger=logger)
            message_collector.add_message(
                "PNT data collection and plotting successful.\n"
            )
            message_collector.save_to_file(output_path=summary_file)
            sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_INSUFFICIENT"])
        except Exception as e:
            logger.error(f"Calculation of runway gradients failed: {e}")
            rprint(f"[red]Calculation of runway gradients failed: {e}[/red]")

        message_collector.add_message(
            "[WARNING] Determined ASSUR EBH files are not of sufficient quality.\n"
        )
        message_collector.save_to_file(output_path=summary_file)

        sys.exit(EBH_EXIT_CODES["EBH_MEASUREMENT_INSUFFICIENT"])

    except Exception as e:
        error_msg = f"Error in ebh_process_launcher: {e}"
        logger.error(error_msg)
        rprint(f"[red]ERROR {e} in measurements. Redo measurement.[/red]")
        message_collector.add_message(
            f"[ERROR] {error_msg} in measurements. Redo measurement.\n"
        )
        message_collector.save_to_file(output_path=summary_file)
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
        ebh_qual_rtk, ebh_qual_rtk_tabular = ebh_lines(
            parsed_args=parsed_args, logger=logger
        )

        # Check RTK quality
        rejected_lines, qual_decision = rtk_ppk_qual_check(
            qual_analysis=ebh_qual_rtk,
            rejection_level=EBH_REJECTION_LEVEL,
            logger=logger,
        )

        if qual_decision == "ALL-EBH-OK":
            msg_ebh_decision, msg_pnt_analysis = print_ebh_ok(
                logger=logger, pnt_analysis=ebh_qual_rtk_tabular, source="RTK"
            )
            return {
                "success": True,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pnt_analysis": msg_pnt_analysis,
            }
        else:
            msg_ebh_decision, msg_pnt_analysis = print_ebh_nok(
                logger=logger,
                pnt_analysis=ebh_qual_rtk_tabular,
                rejected_lines=rejected_lines,
                rejection_level=EBH_REJECTION_LEVEL,
                source="RTK",
            )
            return {
                "success": False,
                "rejected_lines": rejected_lines,
                "qual_decision": qual_decision,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pnt_analysis": msg_pnt_analysis,
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
        ebh_qual_ppk, ebh_qual_ppk_tabular = ebh_lines(
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
            msg_ebh_decision, msg_pnt_analysis = print_ebh_ok(
                logger=logger, pnt_analysis=ebh_qual_ppk_tabular, source="PPK"
            )
            return {
                "success": True,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pnt_analysis": msg_pnt_analysis,
            }
        else:
            msg_ebh_decision, msg_pnt_analysis = print_ebh_nok(
                logger=logger,
                pnt_analysis=ebh_qual_ppk_tabular,
                rejected_lines=rejected_lines,
                rejection_level=EBH_REJECTION_LEVEL,
                source="PPK",
            )
            return {
                "success": False,
                "msg_ebh_decision": msg_ebh_decision,
                "msg_pnt_analysis": msg_pnt_analysis,
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
) -> tuple[list, str]:
    """Checks the RTK or PPK solutions and determines if the lines are of sufficient quality
    to be used for the ebh_lines calculation and ASSURtool.

    Args:
        qual_analysis (dict): Dictionary with the quality analysis of the RTK/PPK solution
                            for each ebh line
        rejection_level (float): Minimum percentage of fixed_points/total that needs to be met
        logger (Logger): Logger object for logging messages

    Returns:
        tuple[list, str]: A tuple containing:
            - rejected_ebh_lines (list): List of ebh lines that are rejected
            - ebh_qual_decision (str): Decision string ("ALL-EBH-OK" or "ALL-EBH-NOK")
    """
    if not qual_analysis:
        logger.critical("No quality analysis available. No ebh lines to check.")
        rprint(
            "[red]No quality analysis available. No ebh lines to check. Redo measurement.[/red]"
        )
        return [], "ALL-EBH-NOK"

    logger.info(
        f"RTK/PPK checker launched for {len(qual_analysis)} lines with rejection level of {rejection_level}% fixed PNT points."
    )

    rejected_ebh_lines = []
    for ebh_key, ebh_qual_value in qual_analysis.items():
        # check if FIXED quality is met by checking the standard_pnt_quality lookup table (standard_pnt_quality_dict.py)

        # Find the first entry with "RTK with fixed ambiguities" quality
        fixed_quality_entry = next(
            (
                entry
                for entry in ebh_qual_value
                if entry[0] == "RTK with fixed ambiguities"
            ),
            None,
        )

        if (
            fixed_quality_entry and fixed_quality_entry[1] > 0
        ):  # checks if ebh lines holds any data with fixed quality
            fixed_points, total_points = fixed_quality_entry[1], fixed_quality_entry[3]
            percentage = fixed_quality_entry[2]

            logger.info(
                f"Line {ebh_key}: {fixed_points}/{total_points} points with FIXED quality ({percentage}%)"
            )

            if percentage >= rejection_level:
                logger.info(f"Line {ebh_key} passed quality check")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.warning(
                    f"Line {ebh_key} rejected: {percentage}% < {rejection_level}% threshold"
                )
        else:
            logger.warning(f"Line {ebh_key} has no FIXED quality points")
            rejected_ebh_lines.append(ebh_key)

    # Determine overall quality decision
    ebh_qual_decision = "ALL-EBH-OK" if not rejected_ebh_lines else "ALL-EBH-NOK"
    logger.info(f"Quality decision: {ebh_qual_decision}")

    return rejected_ebh_lines, ebh_qual_decision


def do_ppk_by_decision(
    rejected_ebh_lines: list,
    ebh_qual_decision: str,
    ebh_timings: dict,
    parsed_args: argparse.Namespace,
    logger: Logger,
) -> str:
    """Process PPK solution based on quality decision.

    Args:
        rejected_ebh_lines (list): List of rejected EBH lines
        ebh_qual_decision (str): Quality decision ("ALL-EBH-OK" or "ALL-EBH-NOK")
        ebh_timings (dict): Dictionary of EBH line timings
        parsed_args (argparse.Namespace): Command line arguments
        logger (Logger): Logger object for logging messages

    Returns:
        str: Path to the PPK position output file, or None if processing fails
    """
    if not parsed_args.base_corr:
        logger.warning("Base corrections are not available. Cannot calculate PPK.")
        rprint(
            "[yellow][WARNING] Base corrections are not available. Cannot calculate PPK.[/yellow]"
        )
        return None

    # Initialize output file name and navigation file list
    ppk_pos_ofn = ""
    # parsed_args.nav is configured with nargs=+ option in argument_parser_rnx2rtkp_launcher. This option requires the argument to be a list of strings.
    parsed_args.nav = []

    # Configure RTKlib PPK config file if not specified
    if parsed_args.config_ppk is None:
        rtklib_ppk_config = os.path.join(
            os.path.dirname(__file__),
            "..",
            "rtkpos",
            "rnx2rtkp_config",
            "rnx2rtkp_EBH_PPK_default.conf",
        )
        parsed_args.config_ppk = os.path.normpath(rtklib_ppk_config)
        logger.debug(f"Using default PPK configuration file: {parsed_args.config_ppk}")

    if ebh_qual_decision == "ALL-EBH-OK":
        logger.info("No PPK processing needed - all lines meet quality criteria")
        return None

    # Process PPK for all lines
    print_starting_ppk_process(logger, rejected_ebh_lines, ebh_timings)

    try:
        # Get rover data
        rnx_obs_fn, rnx_nav_fn = get_rnx_files.get_rnx_frm_sbf(
            parsed_args=parsed_args, logger=logger
        )
        parsed_args.obs = rnx_obs_fn
        parsed_args.nav.append(rnx_nav_fn)

        # Get base data
        rnx_obs_fn, rnx_nav_fn, base_coord_X, base_coord_Y, base_coord_Z = (
            get_base_data_for_PPK(parsed_args=parsed_args, logger=logger)
        )

        # Update parsed_args with base data
        parsed_args.base_corr = rnx_obs_fn
        parsed_args.nav.append(rnx_nav_fn)
        parsed_args.base_coord_X = base_coord_X
        parsed_args.base_coord_Y = base_coord_Y
        parsed_args.base_coord_Z = base_coord_Z

        # Calculate PPK
        logger.info("Starting PPK calculation")
        ppk_pos_ofn = rnx2rtkp_ppk(parsed_args=parsed_args, logger=logger)
        logger.info(f"PPK solution saved to: {ppk_pos_ofn}")

        return ppk_pos_ofn

    except Exception as e:
        logger.error(f"Error in PPK processing: {e}")
        rprint(f"[red]Failed to calculate PPK: {e}[/red]")
        return None


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


def collect_and_plot_ebh_data(parsed_args: argparse.Namespace, logger: Logger) -> None:
    """Collect PNT data from EBH files and create plots.

    Args:
        parsed_args (argparse.Namespace): Parsed arguments
        logger (Logger): Logger object
    """
    try:
        # get absolute path of sbf_ifn
        sbf_ifn_abs = os.path.abspath(parsed_args.sbf_ifn)

        # Create EBH-analysis directory if it doesn't exist
        ebh_analysis_dir = os.path.join(os.path.dirname(sbf_ifn_abs), "EBH_analysis")
        os.makedirs(ebh_analysis_dir, exist_ok=True)
        logger.info(f"Created EBH-analysis directory: {ebh_analysis_dir}")

        # Get the directory containing the ASSUR files (csv files)
        assur_dir = os.path.join(os.path.dirname(sbf_ifn_abs), "EBH_ASSUR")

        # Find all matching CSV files using glob
        csv_files = glob.glob(os.path.join(assur_dir, f"{parsed_args.desc}_*.csv"))

        if not csv_files:
            logger.warning(
                f"No CSV files found matching pattern: {parsed_args.desc}_*.csv in {assur_dir}"
            )
            return

        # Set up arguments for PNT data collection
        pnt_args = argparse.Namespace(
            csv_ifn=csv_files,  # Pass the list of matched files directly
            output_dir=ebh_analysis_dir,
            csv_out=True,
            merge=True,
            merge_ofn=os.path.join(ebh_analysis_dir, parsed_args.desc),
            columns_csv=["UTM.E", "UTM.N", "orthoH"],
            no_header=True,
            sep=";",
        )

        # Collect and merge PNT data
        logger.info("Collecting and merging PNT data from EBH files")
        logger.debug(f"calling pnt_data_collector with pnt_args: {pnt_args}")
        standard_pnt_dfs, _ = pnt_data_collector(parsed_args=pnt_args, logger=logger)

        # Set up arguments for plotting
        plot_args = argparse.Namespace(
            csv_ifn=os.path.join(
                ebh_analysis_dir, f"{parsed_args.desc}_merged_pnt_standardized.csv"
            ),
            mpl=True,
        )

        # Create plots
        logger.info("Creating plots from merged PNT data")
        logger.debug(f"calling plot_coords with plot_args: {plot_args}")
        plot_coords(parsed_args=plot_args, logger=logger)

    except Exception as e:
        logger.error(f"Error in collect_and_plot_ebh_data: {e}")
        rprint(f"[yellow]Warning: Could not create plots: {e}[/yellow]")


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
