#!/usr/bin/env python

import os
import sys

import globalvars
from utils import argument_parser, init_logger
from rtkpos.rtkpos_class import Rtkpos


def rnx2rtkp_pos(argv: list):
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments
    """
    pass
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_pos(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    # logger.warning(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

    # create a SBF class object
    try:
        rtkpos = Rtkpos(
            pos_fn=args_parsed.pos_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating RTKPos object: {e}")
        sys.exit(1)

    # read the CVS position file into polars dataframe
    rtkpos.read_pos_file()


if __name__ == "__main__":
    rnx2rtkp_pos(argv=sys.argv)
