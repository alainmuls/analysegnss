#!/usr/bin/env python

# standard imports
import os
import sys
import argparse
import logging

# third party imports
import matplotlib
import matplotlib.pyplot as plt
import polars as pl
from rich import print

from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.glabng import glab_reader
from analysegnss.nmea import nmea_reader
from analysegnss.rtkpos import rtkpos_reader
from analysegnss.sbf import sbf_reader
from analysegnss.plots import plot_utm
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import (
    argument_parser_plot_coords,
    auto_populate_args_namespace,
)


def get_source(parsed_args: argparse.Namespace) -> str:
    """Determines the source of the coordinates

    Args:
        parsed_args: Parsed arguments containing file paths

    Returns:
        str: Source type (PPK, RTK, GLABNG, NMEA, PNT_CSV)
    """

    # dictionary to map source type to argparse argument name
    file_handlers = {
        "pos_ifn": "PPK",
        "sbf_ifn": "RTK",
        "glab_ifn": "GLABNG",
        "nmea_ifn": "NMEA",
        "csv_ifn": "PNT_CSV",
    }

    # Get the first non-None filename and its attribute name
    file_attr = next(
        attr
        for attr in ["pos_ifn", "sbf_ifn", "glab_ifn", "nmea_ifn", "csv_ifn"]
        if getattr(parsed_args, attr) is not None
    )

    # Create instance and get source in one go
    source = file_handlers.get(file_attr, "Source not found")

    return source


def plot_coords(parsed_args: argparse.Namespace, logger: logging.Logger):
    """Plots the coordinates from multiple PNT sources [PPK, RTK, GLABNG, NMEA, PNT_CSV]

    Args:
            argv (list): CLI arguments
    """

    # auto populate argparse Namespace
    parsed_args = auto_populate_args_namespace(
        parsed_args,
        argument_parser_plot_coords,
        os.path.splitext(os.path.basename(__file__))[0],
    )

    logger.debug(f"Parsed arguments after auto-population: {parsed_args}")

    matplotlib.use("TkAgg")

    # get the source of the coordinates
    source = get_source(parsed_args=parsed_args)

    # get the source dataframe and standardize it
    df_source = get_source_df(source=source, parsed_args=parsed_args, logger=logger)

    # Get column mappings for this source
    utm_columns = get_utm_columns(source=source)
    logger.debug(f"utm_columns: {utm_columns}")

    # create the df_utm dataframe from the dataframe obtained according to each source
    try:
        if not parsed_args.sd:
            df_utm = df_source.select(
                [
                    utm_columns.time,
                    utm_columns.quality_mapping.quality_column,
                    utm_columns.nrSVN,
                    utm_columns.east,
                    utm_columns.north,
                    utm_columns.height,
                ]
            )
        else:
            df_utm = df_source.select(
                [
                    utm_columns.time,
                    utm_columns.quality_mapping.quality_column,
                    utm_columns.nrSVN,
                    utm_columns.east,
                    utm_columns.north,
                    utm_columns.height,
                    utm_columns.sdn,
                    utm_columns.sde,
                    utm_columns.sdu,
                ]
            )
    except pl.exceptions.ColumnNotFoundError as e:
        column_missing = e.args[0]
        logger.error(f"ERROR: Missing the column |{column_missing}| in the dataframe")
        sys.exit(1)

    # Filter out null values in coordinates
    df_utm = df_utm.filter(
        pl.col(utm_columns.east).is_not_null()
        & pl.col(utm_columns.north).is_not_null()
        & pl.col(utm_columns.height).is_not_null()
    )

    logger.debug(f"df_utm = \n{df_utm}")

    # find filename and directory from the position file
    # ifn_full = args_parsed.pos_ifn if args_parsed.pos_ifn else args_parsed.sbf_ifn
    ifn_full = next(
        ifn
        for ifn in [
            parsed_args.pos_ifn,
            parsed_args.sbf_ifn,
            parsed_args.glab_ifn,
            parsed_args.nmea_ifn,
            parsed_args.csv_ifn,
        ]
        if ifn is not None
    )

    # separate the filename from the path
    filename_in = os.path.basename(ifn_full)
    dir_fn = os.path.dirname(ifn_full)

    print(f"creating plot for {source} position file {filename_in}")

    # plot the UTM and orthoH coordinates
    if parsed_args.mpl == False:
        with rich_console.status(f"Creating UTM scatter plot.\t", spinner="aesthetic"):
            # use plotly for creating html plots
            plot_utm.plot_utm_scatter(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                logger=logger,
                display=parsed_args.display,
            )

        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_height(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                sd=parsed_args.sd,
                logger=logger,
                display=parsed_args.display,
            )
    else:
        with rich_console.status(f"Creating UTM scatter plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_scatter_mpl(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                logger=logger,
                display=parsed_args.display,
            )
        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_height_mpl(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                sd=parsed_args.sd,
                logger=logger,
                display=parsed_args.display,
            )

        if parsed_args.display:
            with rich_console.status(f"Displaying plots.\t", spinner="aesthetic"):
                plt.show(block=True)


def get_source_df(
    source: str,
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
            df_source, _ = rtkpos_reader.rtkp_pos(
                parsed_args=parsed_args, logger=logger
            )

        case "RTK":
            # Create RTK position dataframe
            logger.debug(f"Creating RTK position dataframe")
            df_source, _ = sbf_reader.sbf_reader(parsed_args=parsed_args, logger=logger)

        case "GLABNG":
            # Create GLAB position dataframe
            logger.debug(f"Creating GLAB position dataframe")
            glab_parser_args = [
                "glab_parser",
                "--glab_ifn",
                parsed_args.glab_ifn,
                "--section",
                "OUTPUT",
            ]
            dfs_glab = glab_reader.glab_parser(argv=glab_parser_args)
            df_source = dfs_glab["OUTPUT"]
            if logger:
                logger.debug(f"GLAB OUTPUT dataframe:\n{df_source}")

        case "NMEA":
            # Create NMEA dataframe
            df_source, _ = nmea_reader.nmea_reader(
                parsed_args=parsed_args, logger=logger
            )

        case "PNT_CSV":
            try:

                # Read PNT CSV file

                # first check if parsed_args.header is True. Then use the columns defined in the header.
                # Otherwise, use the columns defined in the parsed_args.columns_csv
                if parsed_args.no_header:
                    # If no header, use the specified column names
                    df_source = pl.read_csv(
                        parsed_args.csv_ifn,
                        separator=parsed_args.sep,
                        has_header=False,
                        new_columns=parsed_args.columns_csv,
                        comment_prefix=parsed_args.comment_prefix,
                        skip_rows_after_header=parsed_args.skip_rows_after_header,
                    )
                else:
                    # Read the CSV with existing column names from header
                    df_source = pl.read_csv(
                        parsed_args.csv_ifn,
                        separator=parsed_args.sep,
                        comment_prefix=parsed_args.comment_prefix,
                        has_header=True,
                        skip_rows_after_header=parsed_args.skip_rows_after_header,
                        schema_overrides={"DT": pl.Datetime()},
                    )
            except Exception as e:
                logger.error(f"Error creating PNT_CSV dataframe: {str(e)}")
                raise

        case _:
            logger.error(f"Invalid source: {source}")
            sys.exit(ERROR_CODES["E_INVALID_SOURCE"])

    return df_source


def main():

    # get the script name for passing to argument_parser
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_plot_coords(
        args=sys.argv[1:], script_name=script_name
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    # plot the coordinates
    plot_coords(parsed_args=args_parsed, logger=logger)  # type: ignore


if __name__ == "__main__":
    main()
