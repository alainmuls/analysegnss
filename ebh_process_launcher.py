#! /usr/bin/env python

import os
import argparse

from utils import argument_parser, init_logger


def ebh_process_launcher(parsed_args: argparse.Namespace) -> None:
    """Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings, 
    decides whether the RTK or PPK solution has a sufficient quality, 
    and finally outputs correct ASSUR formatted files for each ebh line.
    
    Args: 
    argv (list): CLI arguments (check argument_parser.py for more info)
    
    """

    
    


if __name__ == "__main__":
    
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    parsed_args = argument_parser.argument_parser_rtk(args=argv[1:])
    
    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {parsed_args}")
    
    ebh_process_launcher(parsed_args=parsed_args, logger=logger)