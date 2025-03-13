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
from analysegnss.plots import plot_utm
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_plot_coords
from analysegnss.pnt.pnt_data_collector import get_source_df, standardize_df


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


def plot_coords(args_parsed: argparse.Namespace, logger: logging.Logger):
    """Plots the coordinates from multiple PNT sources [PPK, RTK, GLABNG, NMEA, PNT_CSV]

    Args:
            argv (list): CLI arguments
    """

    matplotlib.use("TkAgg")


    # get the source of the coordinates
    source = get_source(parsed_args=args_parsed)

    # get the source dataframe and standardize it
    df_source = get_source_df(source=source, args_parsed=args_parsed, logger=logger)
    df_utm = standardize_df(df=df_source, source=source, args_parsed=args_parsed, logger=logger)

    logger.debug(f"df_utm = \n{df_utm}")

    # find filename and directory from the position file
    # ifn_full = args_parsed.pos_ifn if args_parsed.pos_ifn else args_parsed.sbf_ifn
    ifn_full = next(
        ifn
        for ifn in [args_parsed.pos_ifn, args_parsed.sbf_ifn, args_parsed.glab_ifn, args_parsed.nmea_ifn, args_parsed.csv_ifn]
        if ifn is not None
    )

    # separate the filename from the path
    filename_in = os.path.basename(ifn_full)
    dir_fn = os.path.dirname(ifn_full)

    print(f"creating plot for {source} position file {filename_in}")

    # plot the UTM and orthoH coordinates
    if args_parsed.mpl == False:
        with rich_console.status(f"Creating UTM scatter plot.\t", spinner="aesthetic"):
            # use plotly for creating html plots
            plot_utm.plot_utm_scatter(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                logger=logger,
                display=args_parsed.display,
            )

        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_height(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                sd=args_parsed.sd,
                logger=logger,
                display=args_parsed.display,
            )
    else:
        with rich_console.status(f"Creating UTM scatter plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_scatter_mpl(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                logger=logger,
                display=args_parsed.display,
            )
        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
            plot_utm.plot_utm_height_mpl(
                utm_df=df_utm,
                source=source,
                ifn=filename_in,
                dir_fn=dir_fn,
                sd=args_parsed.sd,
                logger=logger,
                display=args_parsed.display,
            )

        if args_parsed.display:
            with rich_console.status(f"Displaying plots.\t", spinner="aesthetic"):
                plt.show(block=True)


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
    plot_coords(args_parsed=args_parsed, logger=logger)  # type: ignore


if __name__ == "__main__":
    main()
