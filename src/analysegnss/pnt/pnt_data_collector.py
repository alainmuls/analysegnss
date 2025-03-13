#!/usr/bin/env python

# Standard library imports
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# Third-party imports
import polars as pl
from rich import print as rprint

# Local application imports
import analysegnss.nmea.nmea_reader as nmea_reader
import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
import analysegnss.glabng.glab_parser as glab_parser
from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_pnt_data_collector



def pnt_data_collector(parsed_args: argparse.Namespace, logger: logging.Logger) -> dict:
    """Collects PNT data from given sources and constructs standardized PNT dataframes
    The function will return a dictionary with the source type as key and the standardized pnt dataframe as value.
    
    Args:
        parsed_args: Parsed arguments

    Returns:
        dict: Dictionary with source type as key and standardized pnt dataframe as value
    """
    # dictionary to map source type to argparse argument name
    file_handlers = {
        "pos_ifn": "PPK",
        "sbf_ifn": "RTK",
        "glab_ifn": "GLABNG",
        "nmea_ifn": "NMEA",
        "csv_ifn": "PNT_CSV",
    }

    # Initialize dictionary to store PNT dataframes
    standard_pnt_dfs = {}

    # Iterate over the input filenames and collect PNT data sources [PPK, RTK, GLABNG, NMEA, PNT_CSV]
    for source_type in ["pos_ifn", "sbf_ifn", "glab_ifn", "nmea_ifn", "csv_ifn"]:
        for source_ifn in getattr(parsed_args, source_type) if getattr(parsed_args, source_type) is not None else []:
            
            logger.debug(f"Detected source_ifn: {source_ifn}")
            if source_ifn is None:
                logger.debug(f"source_ifn is None, skipping")
                continue
            
           
            # get absolute path and basename from filename
            source_ifn_abs = os.path.abspath(source_ifn)
            source_ifn_dir = os.path.dirname(source_ifn_abs)
            source_ifn_base = os.path.basename(source_ifn_abs)
            logger.debug(f"source_ifn_abs: {source_ifn_abs} / source_ifn_dir: {source_ifn_dir} / source_ifn_base: {source_ifn_base}")
            
            # get source type [PPK, RTK, GLABNG, NMEA, PNT_CSV]
            source = file_handlers.get(source_type, "Source not found")
            logger.debug(f"Detected source: {source}")
            
            # Get pnt source dataframe
            df_source = get_source_df(source=source, source_ifn=source_ifn_abs, parsed_args=parsed_args, logger=logger)

            # Standardize PNT dataframe
            df_source_standardized = standardize_pnt_df(df_source=df_source, source=source, parsed_args=parsed_args, logger=logger)

            if parsed_args.output_csv:
                # get output filename
                output_dest = os.path.join(source_ifn_dir, os.path.splitext(source_ifn_base)[0] + "_" + source + "_pnt_standard.csv")
                # write to csv
                df_source_standardized.write_csv(output_dest)
                if os.path.exists(output_dest):
                    logger.info(f"Successfully wrote {source} PNT dataframe to {output_dest}")
                    rprint(f"Successfully wrote {source} PNT dataframe to {output_dest}")
                else:
                    logger.error(f"Failed to write {source} PNT dataframe to {output_dest}")
                    rprint(f"Failed to write {source} PNT dataframe to {output_dest}")
            
            # Add standardized PNT dataframe to dictionary
            standard_pnt_dfs[source] = df_source_standardized

    # print the standard_pnt_dfs
    for source, pnt_df in standard_pnt_dfs.items():
        logger.info(f"PNT source: {source}")
        logger.info(f"PNT dataframe:\n{pnt_df}")

    # Merge PNT dataframes if requested
    if parsed_args.merge:
        merged_pnt_df = merge_pnt_sources(standard_pnt_dfs=standard_pnt_dfs, logger=logger)
        # add merged pnt dataframe to dictionary
        standard_pnt_dfs["merged_pnt"] = merged_pnt_df
        logger.info(f"Merged PNT dataframe:\n{merged_pnt_df}")
        
        if parsed_args.output_csv:
            # get output filename
            output_dest = os.path.join(source_ifn_dir, "merged_PNTs_standard.csv")
            # write to csv
            merged_pnt_df.write_csv(output_dest)
            if os.path.exists(output_dest):
                logger.info(f"Successfully wrote merged PNT dataframe to {output_dest}")
                rprint(f"Successfully wrote merged PNT dataframe to {output_dest}")
            else:
                logger.error(f"Failed to write merged PNT dataframe to {output_dest}")
                rprint(f"Failed to write merged PNT dataframe to {output_dest}")
    

    return standard_pnt_dfs
    



def get_source_df(source: str, source_ifn: str, parsed_args: argparse.Namespace, logger: logging.Logger) -> pl.DataFrame:
    """Get dataframe from a specific source

    Args:
        source (str): Source type (RTK, PPK, GLABNG, NMEA, PNT_CSV)
        parsed_args: Parsed arguments
        logger: Logger object

    Returns:
        pl.DataFrame: DataFrame with standardized columns
    """
    match source:
        case "PPK":
            # Create PPK position dataframe
            logger.debug(f"Creating PPK position dataframe")
            parsed_args.pos_ifn = source_ifn
            df_source = ppk_rnx2rtkp.rtkp_pos(parsed_args=parsed_args, logger=logger)

        case "RTK":
            # Create RTK position dataframe
            logger.debug(f"Creating RTK position dataframe")
            parsed_args.sbf_ifn = source_ifn
            df_source = rtk_pvtgeod.rtk_pvtgeod(parsed_args=parsed_args, logger=logger)

        case "GLABNG":
            # Create GLAB position dataframe
            logger.debug(f"Creating GLAB position dataframe")
            parsed_args.glab_ifn = source_ifn
            glab_parser_args = [
                "glab_parser",
                "--glab_ifn",
                parsed_args.glab_ifn,
                "--section",
                "OUTPUT",
            ]
            dfs_glab = glab_parser.glab_parser(argv=glab_parser_args)
            df_source = dfs_glab["OUTPUT"]
            if logger:
                logger.debug(f"GLAB OUTPUT dataframe:\n{df_source}")

        case "NMEA":
            # Create NMEA dataframe
            logger.debug(f"Creating NMEA dataframe")
            parsed_args.nmea_ifn = source_ifn
            df_source, _ = nmea_reader.nmea_reader(
                parsed_args=parsed_args, logger=logger
            )

        case "PNT_CSV":
            try:
                # Read PNT CSV file
                logger.debug(f"Creating PNT_CSV dataframe")
                parsed_args.csv_ifn = source_ifn
                logger.debug(f"Parsed arguments: {parsed_args}")
                df_source = pl.read_csv(
                    parsed_args.csv_ifn,
                    separator=parsed_args.sep,
                    new_columns=parsed_args.columns_csv,
                    comment_prefix=parsed_args.comment_prefix,
                    has_header=parsed_args.header,
                    skip_rows_after_header=parsed_args.skip_rows_after_header,
                )
            except Exception as e:
                logger.error(f"Error creating PNT_CSV dataframe: {str(e)}")
                raise

        case _:
            logger.error(f"Invalid source: {source}")
            sys.exit(ERROR_CODES["E_INVALID_SOURCE"])

    return df_source


def standardize_pnt_df(df_source: pl.DataFrame, source: str, parsed_args: argparse.Namespace, logger: logging.Logger) -> pl.DataFrame:
    """Standardize PNT dataframe columns

    Args:
        df_source (pl.DataFrame): Input dataframe
        source (str): Source type
        parsed_args: Parsed arguments
        logger: Logger object

    Returns:
        pl.DataFrame: Standardized dataframe
    """
    # Get column mappings for this source
    utm_columns = get_utm_columns(source=source)

    # Define required columns
    required_columns = [
        utm_columns.time,
        utm_columns.quality_mapping.quality_column,
        utm_columns.nrSVN,
        utm_columns.east,
        utm_columns.north,
        utm_columns.height,
    ]
    if parsed_args.sd:
        required_columns.extend(
            [
                utm_columns.sdn,
                utm_columns.sde,
                utm_columns.sdu,
            ]
        )

    # Check for missing columns
    existing_cols = df_source.columns
    missing_cols = []
    for col in required_columns:
        if isinstance(col, list):
            if not any(qcol in existing_cols for qcol in col):
                missing_cols.extend(col)
        elif col not in existing_cols:
            missing_cols.append(col)
            logger.debug(f"Missing {col} in {source}. Adding to missing columns")

    # Add dummy columns for missing ones
    if missing_cols:
        logger.debug(
            f"Missing columns in {source}: {missing_cols}. Creating dummy columns."
        )
        dummy_data = {}
        for col in missing_cols:
            if col == utm_columns.time:
                dummy_data[col] = pl.Series(
                    name=col,
                    values=[
                        datetime.strptime(
                            parsed_args.datetime_start, "%Y-%m-%d %H:%M:%S"
                        )
                        + timedelta(seconds=i)
                        for i in range(len(df_source))
                    ],
                )
            elif col == utm_columns.nrSVN:
                dummy_data[col] = pl.Series(name=col, values=[0] * len(df_source))
            elif col == utm_columns.quality_mapping.quality_column:
                dummy_data[col] = pl.Series(name=col, values=["MANUAL"] * len(df_source))
            else:
                dummy_data[col] = pl.Series(name=col, values=[None] * len(df_source))

        # Add dummy columns
        for col_name, col_data in dummy_data.items():
            df_source = df_source.with_columns(col_data)

    # Select required columns
    if not parsed_args.sd:
        df_source = df_source.select(required_columns[:6])
    else:
        df_source = df_source.select(required_columns)

    # Filter out null values in coordinates
    df_source = df_source.filter(
        pl.col(utm_columns.east).is_not_null()
        & pl.col(utm_columns.north).is_not_null()
        & pl.col(utm_columns.height).is_not_null()
    )

    # Add source identifier
    df_source_standardized = df_source.with_columns(pl.lit(source).alias("source"))

    return df_source_standardized


def merge_pnt_sources(standard_pnt_dfs: dict, logger: logging.Logger) -> pl.DataFrame:
    """Merge multiple PNT sources into a single dataframe

    Args:
        pnt_standard_dfs (dict): Dictionary of standardized PNT dataframes
        logger: Logger object

    Returns:
        pl.DataFrame: Merged dataframe
    """

    merged_df = pl.DataFrame()
    
    for source, pnt_df in standard_pnt_dfs.items():
       
        logger.info(f"Merging pnt dataframe from {source} with\n{pnt_df}\ninto merged pnt dataframe with\n{merged_df}\n")
        merged_df = pl.concat([merged_df, pnt_df], how="diagonal")
        logger.info(f"Successfully merged pnt dataframe with {len(pnt_df)} rows from {source} into merged pnt dataframe with {len(merged_df)} rows")

    # Sort by time if available
    if "DT" in merged_df.columns:
        merged_df = merged_df.sort("DT")

    return merged_df

    
def main():

    # get the script name for passing to argument_parser
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_pnt_data_collector(
        script_name=script_name,
        args=sys.argv[1:]
    )
    
    # initialize logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
   
    # merge pnt sources
    pnt_dfs = pnt_data_collector(parsed_args=args_parsed, logger=logger)
    
    for source, pnt_df in pnt_dfs.items():
        rprint(f"PNT source: {source}")
        rprint(f"PNT dataframe:\n{pnt_df}")


if __name__ == "__main__":
    main()
