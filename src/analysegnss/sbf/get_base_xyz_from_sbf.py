#! /usr/bin/env python

# Standard library imports
import argparse
import datetime
import os
import sys
from logging import Logger
from typing import Tuple

# Third-party imports
import polars as pl

# Local application imports
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import argument_parser, init_logger


def get_base_coord_from_sbf(
    
    parsed_args: argparse.Namespace, logger: Logger

) -> Tuple[float, float, float]:
    """
    This function extracts the base station coordinates from the BaseStation1 SBF block.
    Which is logged on the rover which received diffcorr from the basestation.

    args:
    sbf_ifn (str): SBF input filename
    datetime (str): date time instance of the base station coordinates [YYYY-MM-DD_HH:MM:SS.s]

    return:
    base_coord (Tuple[float, float, float]): base station coordinates (X, Y, Z)
    """
    logger.debug("Creating SBF object from SBF file")
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
        lst_sbfblocks=["BaseStation1"], archive=parsed_args.archive
    )["BaseStation1"]

    logger.debug(f"Extracted sbf block from SBF file.\n{df_sbfBaseStation}")

    if hasattr(parsed_args, "datetime") and parsed_args.datetime:
        logger.info(
            f"Extracting basestation coordinates from sbf dataframe at date time {parsed_args.datetime}"
        )

        # remove underscore from datetime format to get isoformat %Y-%m-%d %H:%M:%S
        dt = parsed_args.datetime.replace("_", " ")
        dt_obj = datetime.datetime.fromisoformat(
            dt
        )  # isoformat has a looser format conversion requirements. Definitely with milliseconds, microsec, ...
        logger.info(
            f"Converted time to datetime object to compare with DT column (sbf_class): {dt_obj}"
        )

        # Select columns X, Y, Z at date time instance
        base_coord = df_sbfBaseStation.filter(pl.col("DT") == dt_obj).select(
            ["X [m]", "Y [m]", "Z [m]"]
        )
        # Convert the dataframe to a tuple
        if base_coord.height > 0:
            base_coord = tuple(base_coord.row(0))
        else:
            base_coord = tuple(
                df_sbfBaseStation.select(["X [m]", "Y [m]", "Z [m]"]).row(-1)
            )
            logger.warning(
                f"Time instant not found in SBF file. Using last row of dataframe with the XYZ coordinates: {base_coord}"
            )

    else:
        logger.info(f"Extracted basestation coordinates from sbf dataframe last row")

        # extract the last row of the dataframe
        base_coord = tuple(
            df_sbfBaseStation.select(["X [m]", "Y [m]", "Z [m]"]).row(-1)
        )

    logger.info(f"Base station coordinates (float): {base_coord}")

    return base_coord


def main():
    """
    Main function to extract the base station coordinates from the SBF file
    """
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_base_coord(
        script_name=script_name, args=sys.argv[1:]
    )
    parsed_args = argument_parser.argument_parser_get_base_coord(
        script_name=script_name, args=sys.argv[1:]
    )
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    get_base_coord_from_sbf(parsed_args=parsed_args, logger=logger)



if __name__ == "__main__":
    main()
