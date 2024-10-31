#! /usr/bin/env python

import os
import sys
import argparse
from logging import Logger

from sbf import sbf_constants as sbfc
from utils import argument_parser, init_logger
import get_ebh_timings
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
    ebh_timings = get_ebh_timings.get_ebh_timings(parsed_args=parsed_args, logger=logger)

    # launching ebh_lines in RTK mode to get ebh lines. It returns a quality analysis of each line in dict
    parsed_args.timing_ifn = (
        parsed_args.sbf_ifn + "_ebh_timings.txt"
    )
    ebh_qual_rtk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)
    # Checking RTK quality and rejecting lines that are not of sufficient quality
    rejected_rtk_lines = rkt_ppk_decider(
        qual_analysis=ebh_qual_rtk, RTK_mode=True, rejection_level=99, logger=logger
    )

    # Checking RTK quality of each ebh line and deciding whether to continue with RTK or PPK solution
    # If one RTK ebh line is not sufficient, all the ebh lines will be recalculated in PPK mode
    # TODO create script based on rnx2rtkp to calculate PPK with timing args so that a specific ebh lines can be recalculated
    # Instead of recalculating all the ebh lines if only one RTK ebh line is rejected
    if len(rejected_rtk_lines) == 0:
        logger.info(
            "RTK solution for all ebh lines is of sufficient quality."
        )
    elif len(rejected_rtk_lines) == 1:
        logger.warning(
            "RTK solution for one ebh lines is not of sufficient quality. Calculating this single line in PPK mode."
        )
        print(f"CALCULATING SINGLE LINE {rejected_rtk_lines} IN PPK MODE with timing {ebh_timings[rejected_rtk_lines]}")
    else:
        logger.warning(
            "RTK solution for one or more ebh lines is not of sufficient quality. Calculating all ebh lines in PPK mode."
        )
        print(f"Calculating all ebh lines in PPK mode. Timings {ebh_timings}")
        
    sys.exit(1)    
        
    # launching ebh_lines in PPK mode to get ebh lines. It returns a quality analysis of each line in dict
    ebh_qual_ppk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)

    ppk_qual_decision = rkt_ppk_decider(
        qual_analysis=ebh_qual_ppk, RTK_mode=False, rejection_level=99, logger=logger
    )
    for key, value in ppk_qual_decision.items():
        if value == False:
            logger.warning(
                f"PPK solution for ebh line {key} is not of sufficient quality."
            )


def rkt_ppk_decider(
    qual_analysis: dict, RTK_mode: bool, rejection_level: float, logger: Logger
) -> list:
    """Decides whether the RTK or PPK solution has a sufficient quality
    to be used for the ebh_lines calculation and ASSURtool.

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
        f"rkt_ppk decider launched for {qual_analysis} in RTK mode {RTK_mode} with a rejection level of {rejection_level}"
    )

    rejected_ebh_lines = [] # list to store the decision for each ebh line
    #rejection_counter = 0 # counter to count the number of rejected ebh lines
    for ebh_key, ebh_qual_value in qual_analysis.items():
        if RTK_mode:
            if ebh_qual_value[2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.warning(
                    f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[2]}"
                )
                #rejection_counter += 1

        else: # PPK MODE
            if ebh_qual_value[2] >= rejection_level:
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                rejected_ebh_lines.append(ebh_key)
                logger.info(
                    f"ebh line {ebh_key} does not meet the quality of {ebh_qual_value[2]}"
                )
                #rejection_counter += 1
    
    """
    if rejection_counter == 0:
        logger.info(f"All ebh lines have passed the quality check")
    elif rejection_counter == 1:
        logger.warning(f"only ebh line {rejected_ebh_lines} has not passed the quality check")
    else:
        logger.warning(f"The ebh lines {rejected_ebh_lines} have not passed the quality check")
    """
     
    return rejected_ebh_lines


if __name__ == "__main__":

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_ebh_process_launcher(args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest)
    logger.info(f"Parsed arguments: {parsed_args}")

    ebh_process_launcher(parsed_args=parsed_args, logger=logger)
