#!/usr/bin/env python

# Standard library imports
import argparse
from logging import Logger
import os
import sys

# Third-party imports
from rich import print as rprint

# Local application imports
from analysegnss.config import ERROR_CODES
from analysegnss.ublox.ubx_class import UBX
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import (
    argument_parser_ubx_parser,
    auto_populate_args_namespace,
)


def ubx_reader(parsed_args: argparse.Namespace, logger: Logger):
    """
    Convert UBX binary file to CSV
    Args:
        parsed_args (argparse.Namespace): Parsed arguments
        logger (Logger): Logger object
    """
    # Ensure compatibility when passing on parsed_args from a higher level script.
    parsed_args = auto_populate_args_namespace(
        parsed_args,
        argument_parser_ubx_parser,
        os.path.splitext(os.path.basename(__file__))[0],
    )
    logger.debug(f"Auto-populated parsed arguments: {parsed_args}")

    # create a SBF class object
    try:
        ubx = UBX(ubx_fn=parsed_args.ubx_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating UBX object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])

    # start parsing the ublox file and conversion of selected blocks to CSV
    ubx.parse_ubx_stream()


def main():
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    args_parsed = argument_parser_ubx_parser(
        args=sys.argv[1:], script_name=os.path.basename(__file__)
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    ubx_reader(parsed_args=args_parsed, logger=logger)


if __name__ == "__main__":
    main()
