#!/usr/bin/env python

# Standard library imports
import argparse
import os
import logging
import sys

# Third party imports
import polars as pl
from rich import print

# Local application imports
from analysegnss.nmea import nmea_constants as nmeac
from analysegnss.nmea.nmea_class import NMEA
from analysegnss.utils import argument_parser, init_logger


def nmeaReader(parsed_args: argparse.Namespace, logger: logging.Logger) -> pl.DataFrame:
    """Read the ascii file with NMEA data and return a dataframe with extracted NMEA data
    and optionally write the dataframe to a csv file

    Args:
        parsed_args (argparse.Namespace):   .nmea_ifn: input file name
                                            .verbose: verbosity level
                                            .log_dest: destination for log files
        logger (logging.Logger): logger object

    Returns:
        pl.DataFrame: NMEA dataframe
    """
    # Create NMEA object    
    nmea_data = NMEA(nmea_ifn=parsed_args.nmea_ifn, logger=logger)

    # get the NMEA dataframe
    nmea_df = nmea_data.get_nmea_dataframe()
    
    # print the NMEA dataframe
    print(nmea_df)
    
    return nmea_df

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
    else:
        logger.error(f"Error writing NMEA dataframe to {ofn}")

def main():
    # get the name of this script for naming the logger
    script_name = os.path.basename(__file__).split(".")[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_nmeaReader(args=sys.argv[1:], script_name=script_name)

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # call nmeaReader to read NMEA data and return a dataframe
    nmea_df = nmeaReader(parsed_args=args_parsed, logger=logger)
   
    # write the NMEA dataframe to a csv file
    if args_parsed.csv_out:
        ofn = args_parsed.nmea_ifn + "_nmea.csv"
        write_nmea_df(nmea_df=nmea_df, ofn=ofn, logger=logger)    
    

if __name__ == "__main__":
    main()