#!/usr/bin/env python

# Standard library imports
import os
import sys
from datetime import datetime, timedelta

# Third-party imports
import polars as pl
from rich import print as rprint

# Local application imports
import analysegnss.nmea.nmea_reader as nmea_reader
import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_plot_coords

def get_source_df(source: str, args_parsed, logger) -> pl.DataFrame:
    """Get dataframe from a specific source

    Args:
        source (str): Source type (RTK, PPK, NMEA, PNT_CSV)
        args_parsed: Parsed arguments
        logger: Logger object

    Returns:
        pl.DataFrame: DataFrame with standardized columns
    """
    match source:
        case "PPK":
            # Create PPK position dataframe
            ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_ifn", args_parsed.pos_ifn]
            df_source = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

        case "RTK":
            # Create RTK position dataframe
            rtk_pvtgeod_args = (
                ["rtk_pvtgeod.py", "--sbf_ifn", args_parsed.sbf_ifn]
                if not args_parsed.sd
                else ["rtk_pvtgeod.py", "--sbf_ifn", args_parsed.sbf_ifn, "--sd"]
            )
            df_source = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

        case "NMEA":
            # Create NMEA dataframe
            df_source, _ = nmea_reader.nmea_reader(parsed_args=args_parsed, logger=logger)

        case "PNT_CSV":
            try:
                # Read PNT CSV file
                df_source = pl.read_csv(
                    args_parsed.csv_ifn,
                    separator=args_parsed.sep,
                    new_columns=args_parsed.columns_csv,
                    comment_prefix=args_parsed.comment_prefix,
                    has_header=args_parsed.header,
                    skip_rows_after_header=args_parsed.skip_rows_after_header,
                )
            except Exception as e:
                logger.error(f"Error creating PNT_CSV dataframe: {str(e)}")
                raise

        case _:
            logger.error(f"Invalid source: {source}")
            sys.exit(ERROR_CODES["E_INVALID_SOURCE"])

    return df_source

def standardize_df(df: pl.DataFrame, source: str, args_parsed, logger) -> pl.DataFrame:
    """Standardize dataframe columns based on source type

    Args:
        df (pl.DataFrame): Input dataframe
        source (str): Source type
        args_parsed: Parsed arguments
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
    if args_parsed.sd:
        required_columns.extend([
            utm_columns.sdn,
            utm_columns.sde,
            utm_columns.sdu,
        ])

    # Check for missing columns
    existing_cols = df.columns
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
        logger.debug(f"Missing columns in {source}: {missing_cols}. Creating dummy columns.")
        dummy_data = {}
        for col in missing_cols:
            if col == utm_columns.time:
                dummy_data[col] = pl.Series(
                    name=col,
                    values=[datetime.strptime(args_parsed.datetime_start, "%Y-%m-%d %H:%M:%S")+timedelta(seconds=i) for i in range(len(df))]
                )
            elif col == utm_columns.nrSVN:
                dummy_data[col] = pl.Series(name=col, values=[0] * len(df))
            elif col == utm_columns.quality_mapping.quality_column:
                dummy_data[col] = pl.Series(name=col, values=["MANUAL"] * len(df))
            else:
                dummy_data[col] = pl.Series(name=col, values=[None] * len(df))

        # Add dummy columns
        for col_name, col_data in dummy_data.items():
            df = df.with_columns(col_data)

    # Select required columns
    if not args_parsed.sd:
        df = df.select(required_columns[:6])
    else:
        df = df.select(required_columns)

    # Filter out null values in coordinates
    df = df.filter(
        pl.col(utm_columns.east).is_not_null()
        & pl.col(utm_columns.north).is_not_null()
        & pl.col(utm_columns.height).is_not_null()
    )

    # Add source identifier
    df = df.with_columns(pl.lit(source).alias("source"))

    return df

def merge_pnt_sources(argv: list) -> pl.DataFrame:
    """Merge multiple PNT sources into a single dataframe

    Args:
        argv (list): Command line arguments

    Returns:
        pl.DataFrame: Merged dataframe
    """
    # Get script name for logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # Parse arguments
    args_parsed = argument_parser_plot_coords(args=argv[1:], script_name=script_name)

    # Create logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # Initialize list for dataframes
    dfs = []

    # Process each source type
    source_files = {
        "PPK": args_parsed.pos_ifn,
        "RTK": args_parsed.sbf_ifn,
        "NMEA": args_parsed.nmea_ifn,
        "PNT_CSV": args_parsed.csv_ifn
    }

    for source, file_path in source_files.items():
        if file_path is not None:
            logger.info(f"Processing {source} source from {file_path}")
            try:
                # Get source dataframe
                df_source = get_source_df(source, args_parsed, logger)
                
                # Standardize columns
                df_standardized = standardize_df(df_source, source, args_parsed, logger)
                
                dfs.append(df_standardized)
                logger.info(f"Successfully processed {source} source")
            except Exception as e:
                logger.error(f"Error processing {source} source: {e}")
                continue

    if not dfs:
        logger.error("No valid PNT sources found")
        sys.exit(ERROR_CODES["E_NO_DATA"])

    # Merge all dataframes
    merged_df = pl.concat(dfs, how="diagonal")
    logger.info(f"Successfully merged {len(dfs)} PNT sources")
    
    # Sort by time if available
    if "DT" in merged_df.columns:
        merged_df = merged_df.sort("DT")

    return merged_df

def main():
    merged_df = merge_pnt_sources(argv=sys.argv)
    rprint(f"Merged PNT sources dataframe:\n{merged_df}")

if __name__ == "__main__":
    main() 