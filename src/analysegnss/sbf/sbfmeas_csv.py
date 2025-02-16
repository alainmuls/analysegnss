#!/usr/bin:env python3

import argparse
import logging
import os
import sys

import polars as pl
from polars.exceptions import ComputeError, SchemaError, ColumnNotFoundError
from rich import print

from analysegnss.config import DICT_GNSS, DICT_SIGNAL_TYPES, ERROR_CODES
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_sbfmeas_csv
from analysegnss.utils.utilities import str_red, str_green


def convert_meas3_csv(
    df_meas: dict,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    """converts the Meas3 dataframe to CSV file similar to those created by rtcm3_parser.py

    Args:
        df_meas (dict): dict with key=sbf_block, and value the dataframe
        parsed_args (argparse.Namespace): parsed arguments
        logger (Logging.logger): logger object

    # Returns:
    #     pl.DataFrame: converted dataframe
    """
    # check that Key "Meas3Ranges" is in the dictionary
    if "Meas3Ranges" not in df_meas.keys():
        raise ValueError("Key 'Meas3Ranges' not in dataframe dictionary")

    # Create mapping dictionary from the 3-letter abbrev to single letter key
    gnss_mapping = {v["abbrev"]: k for k, v in DICT_GNSS.items()}
    # Create mapping dictionary from signal type to code
    signal_mapping = {v["type"].upper(): v["code"] for v in DICT_SIGNAL_TYPES.values()}
    # Convert parsed_args.gnss string into a list of characters to match
    gnss_list = list(parsed_args.gnss)

    # create the CSV dataframe
    df_csv = (
        df_meas["Meas3Ranges"]
        .filter(pl.col("Antenna ID").str.to_lowercase() == "main")
        .with_columns(
            [
                pl.col("SignalType")
                .str.slice(0, 3)
                .map_dict(gnss_mapping)
                .alias("GNSS"),
                pl.col("SignalType").str.extract("_(.{2})").alias("cfreq"),
                pl.col("SignalType")
                .str.extract("_(.+)$")
                .str.to_uppercase()
                .map_dict(signal_mapping)
                .alias("sigt"),
                pl.col("PRN").str.slice(-2).alias("PRN"),
                (pl.col("TOW [s]") * 1000).cast(pl.UInt32).alias("TOW"),
            ]
        )
        .filter(pl.col("GNSS").is_in(gnss_list))
        .rename(
            {
                "WNc [w]": "WKNR",
                "PR [m]": "C",
                "L [cyc]": "L",
                "Doppler [Hz]": "D",
                "C/N0 [dB-Hz]": "S",
                "LockTime [s]": "locktime",
            }
        )
        .drop(["TOW [s]", "Antenna ID", "DT"])
        .select(
            [
                "GNSS",
                "WKNR",
                "TOW",
                "PRN",
                "cfreq",
                "sigt",
                "C",
                "L",
                "D",
                "S",
                "locktime",
                "SignalType",
            ]
        )
        .lazy()
    ).collect()

    # check whether the selected GNSS are in the sbf_block
    if df_csv.height == 0:
        raise ValueError(
            f"{str_red(parsed_args.sbf_ifn)} contains no data for selected GNSS {str_red(parsed_args.gnss)}"
        )

    if logger is not None:
        logger.debug("Intermediate dataframe 'df_csv'")
        logger.debug(df_csv)

        # these are checks on the correspondence of SignalType and the derived gnss, cfreq and sigt
        # Then get the unique mappings
        logger.debug("Unique SignalTypes:")
        logger.debug(df_csv.select("SignalType").unique())

        logger.debug("\nUnique sigt values:")
        logger.debug(df_csv.select("sigt").unique())

        logger.debug("Mapping between SignalType, frequency and sigt:")
        logger.debug(
            df_csv.select(["SignalType", "GNSS", "cfreq", "sigt"])
            .unique()
            .sort("SignalType")
        )

    # TODO: strange that we have to add the space after SignalType!!!!
    try:
        df_csv = df_csv.drop("SignalType")
    except ColumnNotFoundError:
        df_csv = df_csv.drop("SignalType ")

    convert_dataframe_csv(
        df_csv=df_csv, parsed_args=parsed_args, origin=origin, logger=logger
    )


def convert_meas_epoch2_csv(
    df_meas: dict,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    """converts the MeasEpoch2 dataframe to CSV file similar to those created by rtcm3_parser.py

    Args:
        df_meas (dict): dict with key=sbf_block, and value the dataframe
        parsed_args (argparse.Namespace): parsed arguments
        logger (Logging.logger): logger object

    # Returns:
    #     pl.DataFrame: converted dataframe
    """
    # check that Key "MeasEpoch2" is in the dictionary
    if "MeasEpoch2" not in df_meas.keys():
        raise ValueError("Key 'MeasEpoch2' not in dataframe dictionary")

    print(df_meas)

    # Create mapping dictionary from MeasType to code
    sigtype_mapping = {k: v["code"] for k, v in DICT_SIGNAL_TYPES.items()}
    # Create mapping dictionary from MeasType to code
    signal_mapping = {k: v["type"][:2] for k, v in DICT_SIGNAL_TYPES.items()}
    # Convert parsed_args.gnss string into a list of characters to match
    gnss_list = list(parsed_args.gnss)

    # Add the mapping in the DataFrame operations and perform filter and rename operations
    df_csv = (
        df_meas["MeasEpoch2"]
        .filter(pl.col("Antenna ID") == 0)
        .with_columns(
            [
                pl.col("MeasType").map_dict(sigtype_mapping).alias("sigt"),
                pl.col("SignalType").map_dict(signal_mapping).alias("cfreq"),
                pl.col("PRN")
                .str.slice(length=1, offset=0)
                .cast(pl.String)
                .alias("GNSS"),
                pl.col("PRN").str.slice(-2).alias("PRN"),
            ],
        )
        .filter(pl.col("GNSS").is_in(gnss_list))
        .rename(
            {
                "WNc [w]": "WKNR",
                "PR_m [m]": "C",
                "L_cycles [cyc]": "L",
                "Doppler_Hz": "D",
                "CN0_dBHz [dB-Hz]": "S",
                "LockTime [s]": "locktime",
                "TOW [0.001 s]": "TOW",
            }
        )
        .drop(["MeasType", "Antenna ID", "SignalType"])
        .select(
            [
                "GNSS",
                "WKNR",
                "TOW",
                "PRN",
                "cfreq",
                "sigt",
                "C",
                "L",
                "D",
                "S",
                "locktime",
            ]
        )
        .lazy()
    ).collect()

    convert_dataframe_csv(
        df_csv=df_csv, parsed_args=parsed_args, origin=origin, logger=logger
    )


def convert_dataframe_csv(
    df_csv: pl.DataFrame,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    # sort the entries based on WKNR and TOW
    df_csv = df_csv.sort(["WKNR", "TOW"])

    if logger is not None:
        logger.info("Intermediate dataframe 'df_csv'")
        logger.info(df_csv)

    if parsed_args.verbose is not None and parsed_args.verbose > 0:
        print("Intermediate dataframe 'df_csv':")
        print(df_csv)

    try:
        if parsed_args.csv_ofn is not None:
            df_csv.write_csv(parsed_args.csv_ofn)
            if logger is not None:
                logger.info(f"CSV file written to {str_green(parsed_args.csv_ofn)}")

            print(f"CSV file written to [bold green]{parsed_args.csv_ofn}[/bold green]")
        else:
            # change the "." into "_" and add _meas.csv to sbf_ifn
            csv_ofn = parsed_args.sbf_ifn.replace(".", "_") + f"_{origin}.csv"
            df_csv.write_csv(csv_ofn)
            if logger is not None:
                logger.info(f"CSV file written to {str_green(csv_ofn)}")

            print(f"CSV file written to [bold green]{csv_ofn}[/bold green]")
    except IOError as e:
        raise IOError(f"Failed to write CSV file {csv_ofn}: {e}")
    except (ComputeError, SchemaError, ValueError) as e:
        raise RuntimeError(f"Error during CSV writing: {e}")


def convert_meas3_csv(
    df_meas: dict,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    """converts the Meas3 dataframe to CSV file similar to those created by rtcm3_parser.py

    Args:
        df_meas (dict): dict with key=sbf_block, and value the dataframe
        parsed_args (argparse.Namespace): parsed arguments
        logger (Logging.logger): logger object

    # Returns:
    #     pl.DataFrame: converted dataframe
    """
    # check that Key "Meas3Ranges" is in the dictionary
    if "Meas3Ranges" not in df_meas.keys():
        raise ValueError("Key 'Meas3Ranges' not in dataframe dictionary")

    # Create mapping dictionary from the 3-letter abbrev to single letter key
    gnss_mapping = {v["abbrev"]: k for k, v in DICT_GNSS.items()}
    # Create mapping dictionary from signal type to code
    signal_mapping = {v["type"].upper(): v["code"] for v in DICT_SIGNAL_TYPES.values()}
    # Convert parsed_args.gnss string into a list of characters to match
    gnss_list = list(parsed_args.gnss)

    # create the CSV dataframe
    df_csv = (
        df_meas["Meas3Ranges"]
        .filter(pl.col("Antenna ID").str.to_lowercase() == "main")
        .with_columns(
            [
                pl.col("SignalType")
                .str.slice(0, 3)
                .map_dict(gnss_mapping)
                .alias("GNSS"),
                pl.col("SignalType").str.extract("_(.{2})").alias("cfreq"),
                pl.col("SignalType")
                .str.extract("_(.+)$")
                .str.to_uppercase()
                .map_dict(signal_mapping)
                .alias("sigt"),
                pl.col("PRN").str.slice(-2).alias("PRN"),
                (pl.col("TOW [s]") * 1000).cast(pl.UInt32).alias("TOW"),
            ]
        )
        .filter(pl.col("GNSS").is_in(gnss_list))
        .rename(
            {
                "WNc [w]": "WKNR",
                "PR [m]": "C",
                "L [cyc]": "L",
                "Doppler [Hz]": "D",
                "C/N0 [dB-Hz]": "S",
                "LockTime [s]": "locktime",
            }
        )
        .drop(["TOW [s]", "Antenna ID", "DT"])
        .select(
            [
                "GNSS",
                "WKNR",
                "TOW",
                "PRN",
                "cfreq",
                "sigt",
                "C",
                "L",
                "D",
                "S",
                "locktime",
                "SignalType",
            ]
        )
        .lazy()
    ).collect()

    # check whether the selected GNSS are in the sbf_block
    if df_csv.height == 0:
        raise ValueError(
            f"{str_red(parsed_args.sbf_ifn)} contains no data for selected GNSS {str_red(parsed_args.gnss)}"
        )

    if logger is not None:
        logger.debug("Intermediate dataframe 'df_csv'")
        logger.debug(df_csv)

        # these are checks on the correspondence of SignalType and the derived gnss, cfreq and sigt
        # Then get the unique mappings
        logger.debug("Unique SignalTypes:")
        logger.debug(df_csv.select("SignalType").unique())

        logger.debug("\nUnique sigt values:")
        logger.debug(df_csv.select("sigt").unique())

        logger.debug("Mapping between SignalType, frequency and sigt:")
        logger.debug(
            df_csv.select(["SignalType", "GNSS", "cfreq", "sigt"])
            .unique()
            .sort("SignalType")
        )

    # TODO: strange that we have to add the space after SignalType!!!!
    try:
        df_csv = df_csv.drop("SignalType")
    except ColumnNotFoundError:
        df_csv = df_csv.drop("SignalType ")

    convert_dataframe_csv(
        df_csv=df_csv, parsed_args=parsed_args, origin=origin, logger=logger
    )


def convert_meas_epoch2_csv(
    df_meas: dict,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    """converts the MeasEpoch2 dataframe to CSV file similar to those created by rtcm3_parser.py

    Args:
        df_meas (dict): dict with key=sbf_block, and value the dataframe
        parsed_args (argparse.Namespace): parsed arguments
        logger (Logging.logger): logger object

    # Returns:
    #     pl.DataFrame: converted dataframe
    """
    # check that Key "MeasEpoch2" is in the dictionary
    if "MeasEpoch2" not in df_meas.keys():
        raise ValueError("Key 'MeasEpoch2' not in dataframe dictionary")

    print(df_meas)

    # Create mapping dictionary from MeasType to code
    sigtype_mapping = {k: v["code"] for k, v in DICT_SIGNAL_TYPES.items()}
    # Create mapping dictionary from MeasType to code
    signal_mapping = {k: v["type"][:2] for k, v in DICT_SIGNAL_TYPES.items()}
    # Convert parsed_args.gnss string into a list of characters to match
    gnss_list = list(parsed_args.gnss)

    # Add the mapping in the DataFrame operations and perform filter and rename operations
    df_csv = (
        df_meas["MeasEpoch2"]
        .filter(pl.col("Antenna ID") == 0)
        .with_columns(
            [
                pl.col("MeasType").map_dict(sigtype_mapping).alias("sigt"),
                pl.col("SignalType").map_dict(signal_mapping).alias("cfreq"),
                pl.col("PRN")
                .str.slice(length=1, offset=0)
                .cast(pl.String)
                .alias("GNSS"),
                pl.col("PRN").str.slice(-2).alias("PRN"),
            ],
        )
        .filter(pl.col("GNSS").is_in(gnss_list))
        .rename(
            {
                "WNc [w]": "WKNR",
                "PR_m [m]": "C",
                "L_cycles [cyc]": "L",
                "Doppler_Hz": "D",
                "CN0_dBHz [dB-Hz]": "S",
                "LockTime [s]": "locktime",
                "TOW [0.001 s]": "TOW",
            }
        )
        .drop(["MeasType", "Antenna ID", "SignalType"])
        .select(
            [
                "GNSS",
                "WKNR",
                "TOW",
                "PRN",
                "cfreq",
                "sigt",
                "C",
                "L",
                "D",
                "S",
                "locktime",
            ]
        )
        .lazy()
    ).collect()

    convert_dataframe_csv(
        df_csv=df_csv, parsed_args=parsed_args, origin=origin, logger=logger
    )


def convert_dataframe_csv(
    df_csv: pl.DataFrame,
    parsed_args: argparse.Namespace,
    origin: str,
    logger: logging.Logger = None,
) -> None:
    # sort the entries based on WKNR and TOW
    df_csv = df_csv.sort(["WKNR", "TOW"])

    if logger is not None:
        logger.info("Intermediate dataframe 'df_csv'")
        logger.info(df_csv)

    if parsed_args.verbose is not None and parsed_args.verbose > 0:
        print("Intermediate dataframe 'df_csv':")
        print(df_csv)

    try:
        if parsed_args.csv_ofn is not None:
            df_csv.write_csv(parsed_args.csv_ofn)
            if logger is not None:
                logger.info(f"CSV file written to {str_green(parsed_args.csv_ofn)}")

            print(f"CSV file written to [bold green]{parsed_args.csv_ofn}[/bold green]")
        else:
            # change the "." into "_" and add _meas.csv to sbf_ifn
            csv_ofn = parsed_args.sbf_ifn.replace(".", "_") + f"_{origin}.csv"
            df_csv.write_csv(csv_ofn)
            if logger is not None:
                logger.info(f"CSV file written to {str_green(csv_ofn)}")

            print(f"CSV file written to [bold green]{csv_ofn}[/bold green]")
    except IOError as e:
        raise IOError(f"Failed to write CSV file {csv_ofn}: {e}")
    except (ComputeError, SchemaError, ValueError) as e:
        raise RuntimeError(f"Error during CSV writing: {e}")


def sbfmeas_csv(argv: list):
    """reads SBF file and converts Measurement blocks to CSV file similar
    to those created by rtcm3_parser.py

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_sbfmeas_csv(
        args=argv[1:], script_name=os.path.basename(__file__)
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed} | {type(args_parsed)}")

    # create a SBF class object
    try:
        sbf = SBF(sbf_fn=args_parsed.sbf_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])
    logger.info(f"sbf object: {sbf}")

    # check which SBFBlock for measurements are available in the SBF file
    sbf_blocks = sbf.get_sbf_blocks()
    logger.debug(f"Available SBF blocks: {sbf_blocks}")
    if not sbf_blocks:
        logger.error(f"No SBF blocks found in {args_parsed.sbf_ifn}")
        sys.exit(ERROR_CODES["E_SBF_BLOCKS"])

    # check if Meas3Ranges, Meas3CN0HiRes and Meas3Doppler are available
    required_blocks = [
        "Meas3Ranges",
        "Meas3CN0HiRes",
        "Meas3Doppler",
    ]
    # Check if all required blocks are present
    meas3_present = all(block in sbf_blocks for block in required_blocks)
    # print(f"meas3_present: {meas3_present}")
    if meas3_present:
        logger.debug("Converting measurements using Meas3 blocks")
        meas_df = sbf.bin2asc_dataframe(
            lst_sbfblocks=["Meas3Ranges"], archive=args_parsed.archive
        )
        try:
            convert_meas3_csv(
                df_meas=meas_df, parsed_args=args_parsed, origin="meas3", logger=logger
            )
        except ValueError as e:
            logger.error(e)
            sys.exit(ERROR_CODES["E_FAILURE"])

    elif "MeasEpoch2" in sbf_blocks:
        logger.debug("Converting measurements using MeasEpoch2 block")
        meas_df = sbf.bin2asc_dataframe(
            lst_sbfblocks=["MeasEpoch2"], archive=args_parsed.archive
        )
        try:
            convert_meas_epoch2_csv(
                df_meas=meas_df,
                parsed_args=args_parsed,
                origin="measepoch2",
                logger=logger,
            )
        except ValueError as e:
            logger.error(e)
            sys.exit(ERROR_CODES["E_FAILURE"])

    else:
        logger.error("No Meas3 or MeasEpoch2 blocks found in SBF file. Exiting.")
        sys.exit(ERROR_CODES["E_SBF_BLOCKS"])


def main():
    sbfmeas_csv(argv=sys.argv)


if __name__ == "__main__":
    main()
