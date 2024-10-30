#!/usr/bin/env python

import os
import sys
from logging import Logger

from utils import argument_parser, init_logger


def rnxobs_csv(argv: list):
    """reads RINEX observation file and converts it to CSV file similar to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_rnxobs_csv(args=argv[1:])
    print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")


if __name__ == "__main__":
    rnxobs_csv(argv=sys.argv)
