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

    # launching get_ebh_timings to extract timings from sbf_ifn which creates a description file
    get_ebh_timings.get_ebh_timings(parsed_args=parsed_args, logger=logger)

    # launching ebh_lines in RTK mode to get ebh lines. It returns a quality analysis of each line in dict
    parsed_args.rtk = True  # starting with the RTK data
    parsed_args.ppk = False
    parsed_args.desc = (
        parsed_args.sbf_ifn + "_ebh_timings.txt"
    )  # location of the ebh timings file
    parsed_args.ebh_ifn = parsed_args.sbf_ifn
    ebh_qual_rtk = ebh_lines.ebh_lines(parsed_args=parsed_args, logger=logger)
    # Checking RTK quality and rejecting lines that are not of sufficient quality
    rtk_qual_decision = rkt_ppk_decider(
        qual_analysis=ebh_qual_rtk, RTK_mode=True, rejection_level=99, logger=logger
    )

    # Checking RTK quality of each ebh line and deciding whether to continue with RTK or PPK solution
    # If one RTK ebh line is not sufficient, all the ebh lines will be recalculated in PPK mode
    # TODO rewrite ebh_lines with the extra option that specific ebh lines can be recalculated
    # Instead of recalculating all the ebh lines if only one RTK ebh line is rejected
    for key, value in rtk_qual_decision.items():
        if value == False:
            logger.info(
                f"RTK solution for ebh line {key} is not sufficient quality. Calculating the PPK solution."
            )
            parsed_args.rtk = False
            parsed_args.ppk = True
        else:
            logger.info(
                f"RTK solution for ebh line {key} is sufficient quality. Continuing with RTK result."
            )

    if parsed_args.ppk == True:
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
) -> bool:
    """Decides whether the RTK or PPK solution has a sufficient quality
    to be used for the ebh_lines calculation and ASSURtool.

    Args:
    qual_analysis (dict):       dictionary with the quality analysis of the RTK/PPK solution
                                for each ebh line
    RTK_mode (bool):            RTK (True) or PPK (False) mode
    rejection level (float):    a level of fixed_points/total (percentage) that needs to be met.
                                Otherwise the results is rejected.

    Returns:
    ebh_qual_decision (dict):   for each ebh line, a boolean value indicating
                                whether the RTK or PPK solution is sufficient
    """

    logger.info(
        f"rkt_ppk decider launched for {qual_analysis} in RTK mode {RTK_mode} with a rejection level of {rejection_level}"
    )

    ebh_qual_decision = {}  # dictionary to store the decision for each ebh line
    for ebh_key, ebh_qual_value in qual_analysis.items():
        if RTK_mode:
            if ebh_qual_value[2] >= rejection_level:
                ebh_qual_decision[ebh_key] = True
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                ebh_qual_decision[ebh_key] = False
                logger.warning(
                    f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[2]}"
                )

        else:
            if ebh_qual_value[2] >= rejection_level:
                ebh_qual_decision[ebh_key] = True
                logger.info(f"ebh line {ebh_key} has passed")
            else:
                ebh_qual_decision[ebh_key] = False
                logger.info(
                    f"ebh line {ebh_key} is rejected with the quality of {ebh_qual_value[2]}"
                )

    return ebh_qual_decision


if __name__ == "__main__":

    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_ebh_process_launcher(args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest)
    logger.info(f"Parsed arguments: {parsed_args}")

    ebh_process_launcher(parsed_args=parsed_args, logger=logger)
