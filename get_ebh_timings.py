#! /usr/bin/env python

import argparse
import os
import sys
from logging import Logger
import polars as pl
from datetime import datetime

import globalvars
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


def get_ebh_timestamps(df_sbfComments: pl.DataFrame, logger: Logger) -> pl.DataFrame:
    """
    Extract EBH time stamps from SBF comments

    args:
    df_sfbComments (pl.DataFrame): SBF comments
    logger (Logger): Logger object

    returns:
        pl.DataFrame: EBH time stamps
    """
    logger.info("Extracting EBH timestamps from SBF comments")

    df_ebh_timestamps = df_sbfComments.select(
        [
            # Create a new column with the timestamp key
            pl.col("Comment")
            .str.extract(r"(?:[^_]*_){2}(.+)").alias("key"),
            
            # For comment format: 20241001_10-34-51_Start_l1
            pl.col("Comment")
            .str.extract(r"(\d{8}_\d{2}-\d{2}-\d{2})")
            .alias("EBH_Timestamps"),
        ]
    )

    print(df_ebh_timestamps)
    """
    # for Comment format: sCL_20241001_10-34-51
    df_ebh_timestamps = df_sfbComments.select(
        pl.col("Comment").str.extract(r"_+").alias("EBH_Timestamps")
    )
    df_timestamps_key = df_sfbComments.select(
        pl.col("Comment")
        .str.extract(r"(\s+[^_])").alias("key")
    """

    # Convert EBH timestamps to GPS week number and Time of week format and store them in dict
    df_ebh_timestamps = df_ebh_timestamps.with_columns(
        pl.struct(["key", "EBH_Timestamps"])
        .map_elements(
            lambda x: gnss_dt.dt2gnss(x["EBH_Timestamps"], "%Y%m%d_%H-%M-%S"),
            #return_dtype=pl.struct([pl.Float32, pl.Float32])
        )
        .alias("Wnc-Tow")
    )
        
    logger.info(f"EBH timings: {df_ebh_timestamps}")
    sys.exit()


def main(argv: list[str]) -> None:
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # Parse arguments
    parsed_args = argument_parser.argument_parser_sbf_timestamps(args=argv[1:])
    # Initialize logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name, log_dest="/tmp/logs/")

    # Get SBF comments
    df_sbfComments = get_SBFcomments(parsed_args=parsed_args, logger=logger)
    # Get EBH timestamps
    get_ebh_timestamps(df_sbfComments=df_sbfComments, logger=logger)


if __name__ == "__main__":
    main(sys.argv)
