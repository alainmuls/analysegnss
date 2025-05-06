#!/usr/bin/env python

# Standard library imports
import argparse
import os
import logging
import sys

# Third party imports
import polars as pl
from rich import print as rprint
from tabulate import tabulate

# Local application imports
from analysegnss.analyse.pnt_quality_analysis import quality_analysis
from analysegnss.gnss.standard_pnt_quality_dict import (
    nmea_to_standard_pntqual,
    get_pntquality_info,
)
from analysegnss.nmea.nmea_class import NMEA
from analysegnss.utils import argument_parser, init_logger


def nmea_reader(
    parsed_args: argparse.Namespace, logger: logging.Logger
) -> tuple[pl.DataFrame, list]:
    """Read the ascii file with NMEA data and return a dataframe with extracted NMEA data
    and optionally write the dataframe to a csv file

    Args:
        parsed_args (argparse.Namespace):   .nmea_ifn: input file name
                                            .verbose: verbosity level
                                            .log_dest: destination for log files
        logger (logging.Logger): logger object

    Returns:
        pl.DataFrame: NMEA dataframe
        list: quality analysis
    """

    # Ensure compatibility when passing on parsed_args from a higher level script.
    parsed_args = argument_parser.auto_populate_args_namespace(
        parsed_args,
        argument_parser.argument_parser_nmea_reader,
        os.path.splitext(os.path.basename(__file__))[0],
    )

    logger.debug(f"Parsed arguments: {parsed_args}")

    # Create NMEA object
    nmea_data = NMEA(nmea_ifn=parsed_args.nmea_ifn, logger=logger)

    # get the NMEA dataframe
    nmea_df = nmea_data.get_nmea_dataframe()

    # do quality analysis
    qual_analysis, qual_tabular = quality_analysis(
        df_pnt=nmea_df, file_name=os.path.basename(parsed_args.nmea_ifn), logger=logger
    )

    # print quality in tabular form
    rprint(
        f"Analysis of the quality of NMEA position data for\
            {os.path.basename(parsed_args.nmea_ifn)}:\n{qual_tabular}"
    )

    if nmea_data._console_loglevel <= logging.INFO:
        # print number of observations
        logger.info(
            f"Number of observations extracted from the NMEA messages: {nmea_df.shape[0]}"
        )
        rprint(
            f"Number of observations extracted from the NMEA messages: {nmea_df.shape[0]}"
        )

    rprint(f"NMEA dataframe:\n{nmea_df}")
    logger.info(f"NMEA dataframe:\n{nmea_df}")

    if parsed_args.csv_out:
        ofn = os.path.abspath(parsed_args.nmea_ifn + "_nmea.csv")
        write_nmea_df(nmea_df=nmea_df, ofn=ofn, logger=logger)

    return nmea_df, qual_analysis


def write_nmea_df(nmea_df: pl.DataFrame, ofn: str, logger: logging.Logger) -> None:
    """Write the NMEA dataframe to a csv file

    Args:
        nmea_df (pl.DataFrame): NMEA dataframe
        ofn (str): output file name
        logger (logging.Logger): logger object
    """
    nmea_df.write_csv(ofn)
    if os.path.exists(ofn):
        logger.info(f"NMEA dataframe written to {ofn}")
        rprint(f"NMEA dataframe written to {ofn}")
    else:
        logger.error(f"Error writing NMEA dataframe to {ofn}")
        rprint(f"Error writing NMEA dataframe to {ofn}")


def main():
    # get the name of this script for naming the logger
    script_name = os.path.basename(__file__).split(".")[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_nmea_reader(
        args=sys.argv[1:], script_name=script_name
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # call nmea_reader to read NMEA data and return a dataframe
    nmea_df, _ = nmea_reader(parsed_args=args_parsed, logger=logger)


if __name__ == "__main__":
    main()
