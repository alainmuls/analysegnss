#! /usr/bin/env python

import argparse
import os
import polars as pl
import sys

from gnss import gnss_dt
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger






def get_base_coord_from_sbf(parsed_args: argparse.Namespace, logger: logging.Logger) -> tuple:
    """
    This function extracts the base station coordinates from the BaseStation1 SBF block.
    Which is logged on the rover which received diffcorr from the basestation.
    
    args:
    sbf_ifn (str): SBF input filename
    
    return:
    base_coord (tuple): base station coordinates (X, Y, Z)
    """
    logger.info("Creating SBF object from SBF file")
    if parsed_args.sbf_ifn:
        # create a SBF class object
        try:
            sbf = SBF(sbf_fn=parsed_args.sbf_ifn, logger=logger)
        except Exception as e:
            logger.error(f"Error creating SBF object: {e}")
    else:
        logger.error(f"No SBF file provided")
        sys.exit()

    # extract the SBF comment block(s) from SBF file
    df_sbfBaseStation = sbf.bin2asc_dataframe(
        lst_sbfblocks=["BaseStation1"], archive=""
    )["BaseStation1"]
    
    logger.info(f"Extracted sbf block from SBF file.\n{df_sbfBaseStation}")
   
    if parsed_args.start_time:
        logger.info(f"Extracting basestation coordinates from sbf dataframe at time {parsed_args.start_time}") 

        start_wnc_tow =  gnss_dt.dt2gnss(parsed_args.start_time, "%Y/%m/%d_%H:%M:%S")
        # Select columns X, Y, Z from the dataframe at DT = start_wnc_tow
        base_coord = tuple(df_sbfBaseStation.filter(
            (pl.col("DT") == start_wnc_tow)).select(["X [m]", "Y [m]", "Z [m]"]))
    else:
        logger.info(f"Extracted basestation coordinates from sbf dataframe last row") 

        # extract the last row of the dataframe 
        base_coord = tuple(df_sbfBaseStation.tail(1)["X [m]", "Y [m]", "Z [m]"])
    
    return base_coord    


if __name__ == "__main__":
    
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_base_coord(args=sys.argv[1:])
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    
    get_base_coord_from_sbf(parsed_args=parsed_args, logger=logger)