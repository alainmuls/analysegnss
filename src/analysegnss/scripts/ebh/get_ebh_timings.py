#! /usr/bin/env python

# Standard library imports
import argparse
import os
import re
import sys
from logging import Logger

# Third-party imports
import polars as pl
from rich import print as rprint

# Local application imports
from analysegnss.gnss import gnss_dt
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import argument_parser, init_logger


def get_ebh_timings(parsed_args: argparse.Namespace, logger: Logger) -> dict:
    """Getting ebh timings from sbf Comment block or ASCII file.
    The timings are formatted for each ebh line as follows:
    ebh_line_key: wnc tow, wnc tow
    which corresponds to format used by ebh_lines.py

    Args:
        parsed_args (argparse.Namespace): parsed arguments
                                            - sbf_ifn: path to sbf file
                                            - ebh_timings_ifn: path to ascii file
                                            - timing_ofn: path to output file
                                            - log_dest: path to log file
        logger (Logger): logger object

    Returns:
        ebh_timings(dict): dict with ebh keys and timestamps (week number and t of week) correctly formatted for ebh_lines.py
    """

    # ******************************************************* #
    # To ensure compatibility when passing on parsed_args     #
    # from a higher level scripti                             #
    # ******************************************************* #
    parsed_args = argument_parser.auto_populate_args_namespace(
        parsed_args,
        argument_parser.argument_parser_get_ebh_timings,
        os.path.splitext(os.path.basename(__file__))[0],
    )
    # ******************************************************* # 

    logger.debug(f"parsed_args: {parsed_args}")
    
    # it first checks if the ebh_timings_ifn is provided. If not, it checks if the sbf_ifn is provided.
    if parsed_args.ebh_timings_ifn is not None:
        # convert ascii file name to absolute path
        parsed_args.ebh_timings_ifn = os.path.abspath(parsed_args.ebh_timings_ifn)
        logger.info(f"Reading EBH comments from text file: {parsed_args.ebh_timings_ifn}")
        # Get EBH comments with EBH timestamps from ASCII file
        df_EBH_comments = get_EBH_comments_from_text(
            parsed_args=parsed_args, logger=logger
        )
    elif parsed_args.sbf_ifn is not None:
        # convert sbf file name to absolute path
        parsed_args.sbf_ifn = os.path.abspath(parsed_args.sbf_ifn)
        logger.info(f"Reading EBH comments from SBF file: {parsed_args.sbf_ifn}")
        # Get SBF comments
        df_EBH_comments = get_EBH_comments_from_sbf(
            parsed_args=parsed_args, logger=logger
        )
    else:
        logger.error("No SBF or text file provided")
        sys.exit()

    # Get EBH timestamps
    df_ebh_timestamps = parseEBHComments(df_EBH_comments=df_EBH_comments, logger=logger)
    # reformat EBH timestamps
    ebh_timings_ebhlinefmt, ebh_timings = reformat_timestamps_for_ebh(
        df_ebh_timestamps=df_ebh_timestamps, logger=logger
    )
    # Write EBH timings to file for ebh_lines.py usage
    # Using hasattr here to check if the argument exists (this fixes argparse.namespace errors across different python scripts)
    if parsed_args.timing_ofn is not None:
        ebh_timings_to_file(
            ebh_timings=ebh_timings_ebhlinefmt,
            dest_path=parsed_args.timing_ofn,
            logger=logger,
        )
    else:  # if no output file is provided, write to default file name
        if parsed_args.ebh_timings_ifn is not None:
            ebh_timings_to_file(
                ebh_timings=ebh_timings_ebhlinefmt,
                dest_path=f"{parsed_args.ebh_timings_ifn}_ebh_timings.txt",
                logger=logger,
            )
        elif parsed_args.sbf_ifn is not None:
            ebh_timings_to_file(
                ebh_timings=ebh_timings_ebhlinefmt,
                dest_path=f"{parsed_args.sbf_ifn}_ebh_timings.txt",
                logger=logger,
            )
        else:
            pass

    return ebh_timings



def get_EBH_comments_from_sbf(
    parsed_args: argparse.Namespace, logger: Logger
) -> pl.DataFrame:
    """
    Extract EBH time stamps from SBF file

    args:
    parsed_args (argparse.Namespace): Parsed arguments
        - sbf_ifn: path to SBF file
    logger (Logger): Logger object

    returns:
        pl.DataFrame: EBH comments with EBH timestamps [written in column "Comment"]
    """
    logger.info("Creating SBF object from SBF file")
    if parsed_args.sbf_ifn is not None:
        # create a SBF class object
        try:
            sbf = SBF(sbf_fn=parsed_args.sbf_ifn, logger=logger)
        except Exception as e:
            logger.error(f"Error creating SBF object: {e}")
    else:
        logger.error(f"No SBF file provided")
        sys.exit()

    # extract the SBF comment block(s) from SBF file
    df_EBH_comments = sbf.bin2asc_dataframe(
        lst_sbfblocks=["Comment1"], archive=parsed_args.archive
    )["Comment1"]
    logger.debug(f"Extracted EBH comments from SBF file.\n{df_EBH_comments}")

    return df_EBH_comments


def get_EBH_comments_from_text(
    parsed_args: argparse.Namespace, logger: Logger
) -> pl.DataFrame:
    """
    Get EBH comments with EBH timestamps from text file

    Args:
        parsed_args (argparse.Namespace): parsed arguments.
            - ebh_timings_ifn: path to text file
        logger (Logger): logger object

    Returns:
        pl.DataFrame: EBH comments with timestamps [written in column "Comment"]
    """
    logger.info("Getting EBH comments with EBH timestamps from ASCII file")

    try:
        # Read the ASCII file
        df_EBH_comments = pl.read_csv(
            parsed_args.ebh_timings_ifn,
            separator="\n",
            has_header=False,
            new_columns=["Comment"],
            dtypes={"Comment": pl.Utf8},
        )
    except Exception as e:
        logger.error(f"Error reading text file: {e}")
        logger.warning(f"Fallingback to SBF file")
        return get_EBH_comments_from_sbf(parsed_args=parsed_args, logger=logger)
        
    if df_EBH_comments.is_empty():
        logger.warning(f"No EBH comments found in text file: {parsed_args.ebh_timings_ifn}")
        logger.warning(f"Fallingback to SBF file")
        return get_EBH_comments_from_sbf(parsed_args=parsed_args, logger=logger)

    logger.debug(f"EBH comments extracted from text file: {df_EBH_comments}")

    return df_EBH_comments


def parseEBHComments(df_EBH_comments: pl.DataFrame, logger: Logger) -> pl.DataFrame:
    """
    Parse SBF comments dataframe to return correct formatted EBH timestamps

    args:
    df_EBH_comments (pl.DataFrame): EBH comments
    logger (Logger): Logger object

    returns:
        pl.DataFrame: EBH time stamps
    """
    logger.info(
        "Extracting EBH timestamps from SBF comments and parsing the key,time and misc values"
    )

    df_ebh_timestamps = df_EBH_comments.select(
        [
            # Create a new column with the timestamp key
            pl.col("Comment").str.extract(r"(?:[^_]*_){2}(.+)").alias("key"),
            # For comment format: 20241001_10-34-51_Start_0m
            # For comment format: 20241001_10-34-51_Finished
            pl.col("Comment")
            .str.extract(r"(\d{8}_\d{2}-\d{2}-\d{2})")
            .alias("EBH_timestamps"),
        ]
    )

    logger.debug(f"The extracted EBH timestamps are:{df_ebh_timestamps}")

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

    logger.debug(f"EBH timings with WN and TOW: {df_ebh_timestamps}")

    return df_ebh_timestamps


def reformat_timestamps_for_ebh(
    df_ebh_timestamps: pl.DataFrame, logger: Logger
) -> dict:
    """
    Reformat timestamps for ebh_lines.py
    ebh_line_key: wnc tow, wnc tow

    args:
        df_ebh_timestamps (pl.DataFrame): EBH timestamps
        logger (Logger): Logger object

    returns:
        ebh_timings_ebhlinefmt (dict): dict with ebh keys and timestamps correctly formatted for ebh_lines.py
        ebh_timings (dict): dict with ebh keys and timestamps formaated as tuples
    """
    # TODO make the following lazy?

    logger.info("Reformatting EBH timestamps")

    # An EBH measurement is only initiated once
    # if a measurements fails, the web applications requests the user to rename the survey
    # This resolves the issue of having duplicate stop/finish commands for one survey

    logger.info("Grouping EBH timestamp dataframe for each found measurement")

    # Key that identifies the end of a measurement
    key_stop = "Finish"

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
        logger.debug(df_ebh_timestamps)

    else:
        logger.warning(f"No key {key_stop} found in SBF comments. Using all timestamps")

    # Search for patterns "Start_l" and "End_l", and group them by index
    ebh_timings_ebhlinefmt = {}
    ebh_timings = {}
    # using regex to extract the index (last digit after '_' which can be "0m" or "-5m", ...)
    # Regex pattern to match 'Start_'
    start_pattern = r"Start_([+-]?)(\d+)m"

    # Iterate over all keys to find matching pairs
    for start_key in df_ebh_timestamps["key"]:
        match = re.match(start_pattern, start_key)
        if match:

            logger.debug(f"found match for {start_key}: {match}")
            # in the used regex pattern the capturing groups are ([+-]?) which is the sign and  (\d+) which is the line number
            sign = match.group(1)  # this capture the group with + or - sign
            line_number = match.group(
                2
            )  # this capture the group with the line number [string]

            # Find the corresponding "End_l" key using the same index
            end_key = f"End_{sign}{line_number}m"

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
                sign == ""
            ):  # Special case for 0m: Change the key name to CL for compatibility reasons with ebh_lines.py

                # ebh_lines.py format
                ebh_timings_ebhlinefmt["CL"] = (
                    f"{int(start_data[0])} {start_data[1]}, {int(end_data[0])} {(end_data[1])}"
                )

                # genal format using tuples
                ebh_timings[f"CL"] = [
                    (start_data[0], start_data[1]),
                    (end_data[0], end_data[1]),
                ]
            else:

                # ebh_lines.py format
                ebh_timings_ebhlinefmt[f"{sign}{line_number}"] = (
                    f"{int(start_data[0])} {start_data[1]}, {int(end_data[0])} {end_data[1]}"
                )

                # general format using tuples
                ebh_timings[f"{sign}{line_number}"] = [
                    (start_data[0], start_data[1]),
                    (end_data[0], end_data[1]),
                ]
        else:
            logger.debug(
                f"{start_key} does not match sbf comment timestamp with pattern {start_pattern}"
            )

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

    # check if the file is empty
    if os.path.getsize(dest_path) == 0:
        logger.warning(f"No ebh timings found in {dest_path}")
        rprint(f"No ebh timings found in [yellow]{dest_path}[/yellow]")
    else:
        logger.warning(f"Done writing timings file to {dest_path}")
        rprint(f"Done writing timings file to [yellow]{dest_path}[/yellow]")




def main():

    # fetch script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_get_ebh_timings(
        script_name=script_name, args=sys.argv[1:]
    )
    # Initialize logger
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest=parsed_args.log_dest
    )

    get_ebh_timings(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":
    main()
