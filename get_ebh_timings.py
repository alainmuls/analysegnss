#! /usr/bin/env python

import argparse
import os
import sys
from logging import Logger
import polars as pl
from datetime import datetime
import re

from gnss import gnss_dt
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger, utilities


def get_SBFcomments(parsed_args: argparse.Namespace, logger: Logger) -> pl.DataFrame:
    """
    Extract EBH time stamps from SBF file

    args:
    parsed_args (argparse.Namespace): Parsed arguments
    logger (Logger): Logger object

    returns:
        pl.DataFrame: EBH time stamps
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
    df_sbfComments = sbf.bin2asc_dataframe(
        lst_sbfblocks=["Comment1"], archive=parsed_args.archive
    )["Comment1"]
    logger.info(f"Extracted sbf comment block from SBF file.\n{df_sbfComments}")

    return df_sbfComments


def parseSBFComments(df_sbfComments: pl.DataFrame, logger: Logger) -> pl.DataFrame:
    """
    Extract EBH time stamps from SBF comments

    args:
    df_sfbComments (pl.DataFrame): SBF comments
    logger (Logger): Logger object

    returns:
        pl.DataFrame: EBH time stamps
    """
    logger.info(
        "Extracting EBH timestamps from SBF comments and parsing the key,time and misc values"
    )

    df_ebh_timestamps = df_sbfComments.select(
        [
            # Create a new column with the timestamp key
            pl.col("Comment").str.extract(r"(?:[^_]*_){2}(.+)").alias("key"),
            # For comment format: 20241001_10-34-51_Start_l1
            pl.col("Comment")
            .str.extract(r"(\d{8}_\d{2}-\d{2}-\d{2})")
            .alias("EBH_timestamps"),
        ]
    )

    logger.info(f"The extracted EBH timestamps are:{df_ebh_timestamps}")

    # Convert EBH timestamps to GPS week number and Time of week format and store them in dict
    df_ebh_timestamps = df_ebh_timestamps.with_columns(
        pl.struct(["key", "EBH_timestamps"])
        .map_elements(
            lambda x: gnss_dt.dt2gnss(x["EBH_timestamps"], "%Y%m%d_%H-%M-%S"),
            return_dtype=pl.List(pl.Float64),
            # unable to define dtype for value in tuple seperately
        )
        .alias("wnc-tow")
    )

    logger.info(f"EBH timings with WN and TOW: {df_ebh_timestamps}")

    return df_ebh_timestamps


def reformat_ebh_timestamps(df_ebh_timestamps: pl.DataFrame, logger: Logger) -> dict:
    """
    Reformat EBH timestamps for ebh_lines.py
    ebh_line_key: wnc tow, wnc tow

    args:
        df_ebh_timestamps (pl.DataFrame): EBH timestamps
        logger (Logger): Logger object

    returns:
        ebh_timings (dict): dict with ebh keys and timestamps correctly formatted
    """
    #TODO make the following lazy

    logger.info("Reformatting EBH timestamps")

    # During an EBH measurement a new measurement can be started and ended multiple times.
    # Therefore, we need to group these measurements
    # Right now all the rows after the key Finished measurement are ignored
    # TODO group each measurement found in sbf comments
    logger.info("Grouping EBH timestamp dataframe for each found measurement")

    # Key that identifies the end of a measurement
    key_stop = "Finished measurement"

    # find index idx of the key_stop / we use series to serialize the boolean values
    key_stop_idx = (
        df_ebh_timestamps.select(pl.col("key") == key_stop).to_series().arg_true()
    )

    if len(key_stop_idx) > 0:
        stop_call = key_stop_idx[0]  # Index of the first stop measurement call
        logger.info(
            f"Found {len(key_stop_idx)} stop call . Finished measurement at index {stop_call}"
        )

        # slice dataframe to only include rows before the first stop measurement call
        df_ebh_timestamps = df_ebh_timestamps.slice(0, stop_call)
        logger.info(
            f"Sliced dataframe to only include rows before the first stop measurement call"
        )
        logger.info(df_ebh_timestamps)

        # Group the dataframe by the key column
        # TODO slice dataframe further per measurement
    else:
        logger.warning(
            "No key 'Finished measurement' found in SBF comments. Using all timestamps"
        )

    # Search for patterns "Start_l" and "End_l", and group them by index
    ebh_timings_ebhlinefmt = {}
    ebh_timings = {}
    # using regex to extract the index (last digit after '_l')
    # Regex pattern to match 'Start_l'
    start_pattern = r"Start_l(\d+)"

    # Iterate over all keys to find matching pairs
    for start_key in df_ebh_timestamps["key"]:
        match = re.match(start_pattern, start_key)
        if match:
            # in the used regex pattern the capturing group is (\d+) which is also our index
            index = match.group(1)

            # Find the corresponding "End_l" key using the same index
            end_key = f"End_l{index}"

            logger.debug(f"start_key {start_key}, end_key {end_key}")

            # Extract the timestamps for the matching start and end keys
            start_data = (
                df_ebh_timestamps.filter(pl.col("key") == start_key)
                .select("wnc-tow")
                .to_series()
                .item(0)
            )
            end_data = (
                df_ebh_timestamps.filter(pl.col("key") == end_key)
                .select("wnc-tow")
                .to_series()
                .item(0)
            )

            logger.debug(f"start_data {start_data}, end_data {end_data}")

            # Collect data and store in dictionary [ebh_line_key: wnc tow, wnc tow)
            # the following block stores the timings data using a dict in ebh_lines.py format and in another dict using a more general format
            # The latter uses tuples instead strings which facilitates easier conversion between wnc tow and time date formats using gnss_dt.py
            if (
                index == "1"
            ):  # Special case for l1: Change the key name to CL for compatibility reasons with ebh_lines.py
                
                # ebh_lines.py format
                ebh_timings_ebhlinefmt["CL"] = (
                    f"{int(start_data[0])} {start_data[1]}, {int(end_data[0])} {(end_data[1])}"
                )
                
                # genal format using tuples
                ebh_timings[f"CL"] = [(start_data[0],start_data[1]),(end_data[0],end_data[1])]
            else:
                
                # ebh_lines.py format
                ebh_timings_ebhlinefmt[f"l{index}"] = (
                    f"{int(start_data[0])} {start_data[1]}, {int(end_data[0])} {end_data[1]}"
                )
                
                # general format using tuples
                ebh_timings[f"l{index}"] = [(start_data[0],start_data[1]),(end_data[0],end_data[1])]
            

    logger.info(f"ebh line timings using ebh_lines format:\n{ebh_timings_ebhlinefmt}")

    return ebh_timings_ebhlinefmt, ebh_timings


def ebh_timings_to_file(ebh_timings: dict, dest_path: str, logger: Logger) -> None:
    """
    Write ebh timings to a file which ebh_lines.py imports to calculate the EBH lines

    args:
    ebh_timestamps (pl.DataFrame): EBH timestamps
    dest_path (str): Path to file
    logger (Logger): Logger object
    """

    logger.info(f"writing ebh timings to file")
    # write ebh timings to a file
    with open(dest_path, "w") as f:
        for key, value in ebh_timings.items():
            f.write(f"{key}: {value}\n")

    logger.info(f"Done writing timings file to {dest_path}")


def get_ebh_timings(parsed_args: argparse.Namespace, logger:Logger) -> None:
    """Getting ebh timings from sbf Comment block. 
        The timings are formatted for each ebh line with the following format 
        ebh_line_key: wnc tow, wnc tow 
        which corresponds to format used by ebh_lines.py
        
        returns:
        ebh_timings(dict): dict with ebh keys and timestamps (week number and t of week) correctly formatted for ebh_lines.py 
        """
    
    # Get SBF comments
    df_sbfComments = get_SBFcomments(parsed_args=parsed_args, logger=logger)
    # Get EBH timestamps
    df_ebh_timestamps = parseSBFComments(df_sbfComments=df_sbfComments, logger=logger)
    # reformat EBH timestamps
    ebh_timings_ebhlinefmt, ebh_timings = reformat_ebh_timestamps(
        df_ebh_timestamps=df_ebh_timestamps, logger=logger
    )
    # Write EBH timings to file for ebh_lines.py usage
    # Using hasattr here to check if the argument exists (this fixes argparse.namespace errors across different python scripts)
    if hasattr(parsed_args, "timing_ofn") and parsed_args.timing_ofn:
        ebh_timings_to_file(
            ebh_timings=ebh_timings_ebhlinefmt, dest_path=parsed_args.timing_ofn, logger=logger
        )
    else:  # if no output file is provided, write to default file name
        ebh_timings_to_file(
            ebh_timings=ebh_timings_ebhlinefmt,
            dest_path=f"{parsed_args.sbf_ifn}_ebh_timings.txt",
            logger=logger,
        )
    
    return ebh_timings


if __name__ == "__main__":
    
    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_ebh_timings(args=sys.argv[1:])
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )
    
    get_ebh_timings(parsed_args=parsed_args, logger=logger)