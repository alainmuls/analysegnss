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
from analysegnss.pnt.pnt_columns import get_pnt_columns, get_column_mapping_source_to_csv, get_required_columns_from_pnt_source
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_pnt_data_collector


def pnt_data_collector(parsed_args: argparse.Namespace, logger: logging.Logger) -> dict:
    """Collects PNT data from given sources and constructs standardized PNT dataframes
    The function will return a dictionary with the source type as key and the standardized pnt dataframe as value.
    The standardized pnt dataframe will have the following columns:
    - DT: datetime
    - UTM.E: east coordinate
    - UTM.N: north coordinate
    - orthoH: orthometric height
    (- sdn: standard deviation of north coordinate)
    (- sde: standard deviation of east coordinate)
    (- sdu: standard deviation of orthometric height)
    - pvt_qual: quality of the PVT solution
    - nrSVN: number of satellites used in the fix
    - source: source type
    
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

    ### COLLECT PNT DATA AND STANDARDIZE ###

    # Initialize dictionary to store PNT dataframes
    standard_pnt_dfs = {}

    # Iterate over the input filenames and collect PNT data sources [PPK, RTK, GLABNG, NMEA, PNT_CSV]
    for source_type in ["pos_ifn", "sbf_ifn", "glab_ifn", "nmea_ifn", "csv_ifn"]:
        for source_ifn in (
            getattr(parsed_args, source_type)
            if getattr(parsed_args, source_type) is not None
            else []
        ):

            logger.debug(f"Detected source_ifn: {source_ifn}")
            if source_ifn is None:
                logger.debug(f"source_ifn is None, skipping")
                continue

            # get absolute path
            source_pnt_dest = os.path.abspath(source_ifn)
            logger.debug(
                f"source_pnt_dest: {source_pnt_dest}"
            )

            # get source type [PPK, RTK, GLABNG, NMEA, PNT_CSV]
            source = file_handlers.get(source_type, "Source not found")
            logger.debug(f"Detected source: {source}")

            # Get pnt source dataframe
            df_source = get_source_df(
                source=source,
                source_ifn=source_pnt_dest,
                parsed_args=parsed_args,
                logger=logger,
            )

            # Standardize PNT dataframe
            df_source_standardized = standardize_pnt_df(
                df_source=df_source,
                source=source,
                parsed_args=parsed_args,
                logger=logger,
            )

            # Add standardized PNT dataframe to dictionary
            standard_pnt_dfs[source_pnt_dest] = df_source_standardized


    ### MERGE PNT DATAFRAMES ###

    # Merge PNT dataframes if requested
    if parsed_args.merge:
        merged_pnt_df = merge_pnt_sources(
            standard_pnt_dfs=standard_pnt_dfs, logger=logger
        )
        
        if parsed_args.merge_dest is not None:
            # get destination directory of merged pnt dataframe
            merged_pnt_odir = os.path.dirname(os.path.abspath(parsed_args.merge_dest))
            merged_pnt_dest = os.path.join(merged_pnt_odir, "merged.csv")
            logger.info(f"Merged PNT dataframe will be written to: {merged_pnt_dest}")
        else:
            merged_pnt_dest = "merged.csv"
            logger.warning(f"No destination directory provided for merged PNT dataframe. Not writing to file.")
        
        # add merged pnt dataframe to dictionary
        standard_pnt_dfs[merged_pnt_dest] = merged_pnt_df
        logger.info(f"Merged PNT dataframe:\n{merged_pnt_df}")


    ### PRINT STANDARDIZED PNT DATAFRAMES ###
    for source, pnt_df in standard_pnt_dfs.items():
        logger.info(f"PNT source: {source}")
        logger.info(f"PNT dataframe:\n{pnt_df}")
        rprint(f"\nPNT source: {source}")
        rprint(f"\nPNT dataframe:\n{pnt_df}")


    ### WRITE STANDARDIZED PNT DATAFRAMES TO CSV ###
    if parsed_args.csv_out:
        write_standardized_pnt_df_to_csv(
            standard_pnt_dfs=standard_pnt_dfs,
            logger=logger
        )
    
    return standard_pnt_dfs


def get_source_df(
    source: str,
    source_ifn: str | None,
    parsed_args: argparse.Namespace,
    logger: logging.Logger,
) -> pl.DataFrame:
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
            if source_ifn is not None: # otherwise use the parsed_args.pos_ifn
                parsed_args.pos_ifn = source_ifn
            df_source = ppk_rnx2rtkp.rtkp_pos(parsed_args=parsed_args, logger=logger)

        case "RTK":
            # Create RTK position dataframe
            logger.debug(f"Creating RTK position dataframe")
            if source_ifn is not None: # otherwise use the parsed_args.sbf_ifn
                parsed_args.sbf_ifn = source_ifn
            df_source = rtk_pvtgeod.rtk_pvtgeod(parsed_args=parsed_args, logger=logger)

        case "GLABNG":
            # Create GLAB position dataframe
            logger.debug(f"Creating GLAB position dataframe")
            if source_ifn is not None: # otherwise use the parsed_args.glab_ifn
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
            if source_ifn is not None: # otherwise use the parsed_args.nmea_ifn
                parsed_args.nmea_ifn = source_ifn
            df_source, _ = nmea_reader.nmea_reader(
                parsed_args=parsed_args, logger=logger
            )

        case "PNT_CSV":
            try:
                # Read PNT CSV file
                logger.debug(f"Creating PNT_CSV dataframe")
                if source_ifn is not None: # otherwise use the parsed_args.csv_ifn / source_ifn points to the source key when multiple PNT_CSV files are provided
                    parsed_args.csv_ifn = source_ifn
                logger.debug(f"Parsed arguments: {parsed_args}")
                
                # first check if parsed_args.header is True. Then use the columns defined in the header.
                # Otherwise, use the columns defined in the parsed_args.columns_csv
                # TODO: maybe work with wildcards to select the correct columns?
                if parsed_args.no_header:
                    # If no header, use the specified column names
                    logger.debug(f"No header, using columns: {parsed_args.columns_csv}")
                    df_source = pl.read_csv(
                        parsed_args.csv_ifn,
                        separator=parsed_args.sep,
                        has_header=False,
                        new_columns=parsed_args.columns_csv, # import columns names defined by the user
                        comment_prefix=parsed_args.comment_prefix,
                        skip_rows_after_header=parsed_args.skip_rows_after_header,
                    )
                else:
                    logger.debug(f"Using CSV header for column names and dtypes")
                    # Read the CSV with existing column names from header # default mode when importing CSV files generated by analysegnss repo
                    df_source = pl.read_csv(
                        parsed_args.csv_ifn,
                        separator=parsed_args.sep,
                        comment_prefix=parsed_args.comment_prefix,
                        has_header=True,
                        skip_rows_after_header=parsed_args.skip_rows_after_header,
                        # schema_overrides=PNT_DTYPE_SCHEMA,
                    )
            except Exception as e:
                logger.error(f"Error creating PNT_CSV dataframe: {str(e)}")
                raise

        case _:
            logger.error(f"Invalid source: {source}")
            sys.exit(ERROR_CODES["E_INVALID_SOURCE"])

    return df_source


def standardize_pnt_df(
    df_source: pl.DataFrame,
    source: str,
    parsed_args: argparse.Namespace,
    logger: logging.Logger,
) -> pl.DataFrame:
    """Standardize PNT dataframes to a common format which is used for plotting and further processing
        The function will return a dataframe with the following columns with the correct dtypes defined in pnt_columns.py:
        - UTM.E: east coordinate
        - UTM.N: north coordinate
        - orthoH: orthometric height
        - DT: datetime
        - pnt_qual: quality of the PVT solution
        - num_sats: number of satellites used in the fix
        (- sdn: standard deviation of north coordinate)
        (- sde: standard deviation of east coordinate)
        (- sdu: standard deviation of orthometric height)
        - source: source type
    
    Args:
        df_source (pl.DataFrame): Input dataframe
        source (str): Source type [RTK, PPK, GLABNG, NMEA, PNT_CSV]
        parsed_args: Parsed arguments [following args are required: sd, datetime_start]
            - sd: add standard deviation to the plot (boolean)
            - datetime_start: start datetime for CSV files if no DT column is present (str)
        logger: Logger object

    Returns:
        pl.DataFrame: Standardized dataframe
    """
    # Get column mappings and required columns for this source
    pnt_columns = get_pnt_columns(source=source)
    required_columns = get_required_columns_from_pnt_source(source=source, include_sd=parsed_args.sd)
    column_mapping_source_to_csv = get_column_mapping_source_to_csv(source=source, include_sd=parsed_args.sd)
    
    # Add pnt source column to required columns
    required_columns.append("source")

    # Check for missing columns and add dummy data if needed
    existing_cols = df_source.columns
    missing_cols = [col for col in required_columns if col not in existing_cols]
    
    if missing_cols:
        logger.debug(f"Missing columns in {source}: {missing_cols}. Creating dummy columns.")
        
        # Create dummy data for missing columns
        dummy_data = []
        for col in missing_cols:
            if col == pnt_columns.time:
                # create datetime series from user argument datetime_start or default which is GPS epoch
                dummy_data.append(
                    pl.Series(
                        [datetime.strptime(parsed_args.datetime_start, "%Y-%m-%d %H:%M:%S") + 
                         timedelta(seconds=i) for i in range(len(df_source))]
                    ).alias(col)
                )
            elif col == pnt_columns.nrSVN:
                dummy_data.append(pl.lit(0).alias(col))
            elif col == pnt_columns.quality_mapping.quality_column:
                dummy_data.append(pl.lit("MANUAL").alias(col))
            elif col == "source":
                dummy_data.append(pl.lit("UNKNOWN").alias(col))
            else:
                dummy_data.append(pl.lit(None).alias(col))
        
        # Add all missing columns
        if dummy_data:
            df_source = df_source.with_columns(dummy_data)
    
    # Select and rename columns for CSV output and cast to correct dtypes according to pnt_columns.py
    standard_pnt_cols_for_csv = []
    for source_col, csv_col_info in column_mapping_source_to_csv.items():
        if source_col in df_source.columns:
            # Extract the column name and data type from the dict
            csv_col_name = csv_col_info.get("column_name")
            csv_col_dtype = csv_col_info.get("dtype")
            
            # Add renamed and casted column
            standard_pnt_cols_for_csv.append(
                pl.col(source_col).alias(csv_col_name).cast(csv_col_dtype)
            )
    
    # Add source column
    standard_pnt_cols_for_csv.append(pl.lit(source).alias("source"))
    
    # Apply selection, renaming, and casting in one operation
    df_source_standardized = df_source.select(standard_pnt_cols_for_csv)
    
    # Filter out null values in coordinates
    std_cols = get_pnt_columns("PNT_CSV")
    df_source_standardized = df_source_standardized.filter(
        pl.col(std_cols.east).is_not_null()
        & pl.col(std_cols.north).is_not_null()
        & pl.col(std_cols.height).is_not_null()
    )
    
    return df_source_standardized


def merge_pnt_sources(standard_pnt_dfs: dict, logger: logging.Logger) -> pl.DataFrame:
    """Merge multiple PNT sources into a single dataframe

    Args:
        standard_pnt_dfs (dict): Dictionary of standardized PNT dataframes
        logger: Logger object

    Returns:
        pl.DataFrame: Merged dataframe sorted by timestamp
    """
    if not standard_pnt_dfs:
        logger.warning("No PNT dataframes to merge")
        return pl.DataFrame(), None

    logger.info(
        f"Collected PNT dataframes from the following sources are ready for merging: {standard_pnt_dfs.keys()}"
    )

    # Get list of pnt dataframes to merge
    dfs_to_merge = list(standard_pnt_dfs.values())


    # Merge all dataframes at once and sort by DT in one operation
    merged_df = pl.concat(dfs_to_merge, how="vertical").sort("DT")

    logger.info(
        f"Successfully merged {len(standard_pnt_dfs)} PNT dataframes into a single dataframe with {len(merged_df)} rows"
    )

    return merged_df



def write_standardized_pnt_df_to_csv(standard_pnt_dfs: dict, logger: logging.Logger):
    """Write standardized PNT dataframe to CSV
    
    Args:
        standard_pnt_dfs (dict): Dictionary of standardized PNT dataframes
        logger: Logger object
        
    """
    
    ### WRITE STANDARDIZED PNT DATAFRAMES TO CSV ###

    for source_ifn_abs, standard_pnt_df in standard_pnt_dfs.items():
        
        
        # get destination directory for merged pnt dataframe
        output_dest = os.path.splitext(source_ifn_abs)[0] + "_pnt_standard.csv"
        
        standard_pnt_df.write_csv(output_dest)
        
        # check if file was written successfully
        if os.path.exists(output_dest):
            source = os.path.basename(source_ifn_abs)
            logger.info(f"Successfully wrote {source} PNT dataframe to {output_dest}")
            rprint(
                f"Successfully wrote {source} PNT dataframe to {output_dest}"
            )
        else:
            source = os.path.basename(source_ifn_abs)
            logger.error(
                f"Failed to write {source} PNT dataframe to {output_dest}"
            )
            rprint(f"Failed to write {source} PNT dataframe to {output_dest}")


def main():

    # get the script name for passing to argument_parser
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_pnt_data_collector(
        script_name=script_name, args=sys.argv[1:]
    )

    # initialize logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)

    # merge pnt sources
    pnt_data_collector(parsed_args=args_parsed, logger=logger)


if __name__ == "__main__":
    main()
