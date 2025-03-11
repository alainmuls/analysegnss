#!/usr/bin/env python

import os
import sys
from datetime import datetime, timedelta

import matplotlib
import matplotlib.pyplot as plt
import polars as pl
from rich import print

import analysegnss.glabng.glab_parser as glab_parser
import analysegnss.nmea.nmea_reader as nmea_reader
import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.gnss.general_pvt_quality_dict import GENERAL_PVT_QUALITY_ID
from analysegnss.plots import plot_utm
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_plot_coords


def get_source(parsed_args: list) -> str:
    """determines the source  of the coordinates

    Args:
            parsed_args (list): list of parsed arguments

    Returns:
            tuple[str, str]: source and filename
    """
    # set the source of the coordinates
    # set the source of the coordinates
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
    # filename = getattr(parsed_args, file_attr)

    # Create instance and get source in one go
    source = file_handlers[file_attr]
    return source


def plot_coords(argv: list):
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
            argv (list): CLI arguments
    """

    matplotlib.use("TkAgg")

    # get the script name for passing to argument_parser
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_plot_coords(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {args_parsed}")

    # get the source of the coordinates
    source = get_source(parsed_args=args_parsed)

    # get the needed columns from the dataframe according to the source
 	# TODO: make the following compatible with argparse Namespace instead manually creating CL arguments. This will fix verbose output.
    match source:
        case "PPK":
            # create the PPK position dataframe by calling ppk_rnx2rtkp.py
            pos_ifn_index = argv.index("--pos_ifn")
            pos_ifn_value = argv[pos_ifn_index + 1]

            ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_ifn", pos_ifn_value]
            df_source = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)
            ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_ifn", pos_ifn_value]
            df_source = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

        case "RTK":
            # create the RTK position dataframe by calling rtk_pvtgeod.py
            sbf_ifn_index = argv.index("--sbf_ifn")
            sbf_ifn_value = argv[sbf_ifn_index + 1]

            rtk_pvtgeod_args = (
                ["rtk_pvtgeod.py", "--sbf_ifn", sbf_ifn_value]
                if not args_parsed.sd
                else [
                    "rtk_pvtgeod.py",
                    "--sbf_ifn",
                    sbf_ifn_value,
                    "--sd",
                ]
            )

            df_source = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

        case "GLABNG":
            # create the GLAB position dataframe by calling glab_parser
            glab_ifn_index = argv.index("--glab_ifn")
            glab_ifn_value = argv[glab_ifn_index + 1]

            glab_parser_args = [
                "glab_parser",
                "--glab_ifn",
                glab_ifn_value,
                "--section",
                "OUTPUT",
            ]
            dfs_glab = glab_parser.glab_parser(argv=glab_parser_args)

            for section, df_section in dfs_glab.items():
                if section == "OUTPUT":
                    print(
                        f"dataframe from [green][bold]{section}[/bold][/green] section"
                    )
                    print(df_section)

            df_source = dfs_glab["OUTPUT"]

        case "NMEA":
            # create the NMEA dataframe by calling nmea_reader.py
            df_source, qual_analysis = nmea_reader.nmea_reader(
                parsed_args=args_parsed, logger=logger
            )

        case "PNT_CSV":
            try:
                # create a PNT_CSV dataframe by reading PNT_CSV file written by nmeaReader.py, rtk_pvtgeod.py, ppk_rnx2rtkp.py or glab_parser.py
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

    logger.debug(f"print source dataframe:\n{df_source}")

    # get the utm columns names according to the source
    utm_columns = get_utm_columns(source=source)
    # print(f"utm_columns: {utm_columns}")
    # print(f"type(utm_columns): {type(utm_columns)}")
    logger.debug(f"print source dataframe:\n{df_source}")

    # create the df_utm dataframe from the dataframe obtained according to each source
    try:
        required_columns = [
            utm_columns.time,
            utm_columns.quality_mapping.quality_column,
            utm_columns.nrSVN,
            utm_columns.east,
            utm_columns.north,
            utm_columns.height,
        ]
        if args_parsed.sd:
            required_columns.extend(
                [
                    utm_columns.sdn,
                    utm_columns.sde,
                    utm_columns.sdu,
                ]
            )

        # Check which columns are missing
        existing_cols = df_source.columns
        missing_cols = []

        for col in required_columns:
            if isinstance(col, list):  # Handle quality_mapping.columns which is a list
                if not any(qcol in existing_cols for qcol in col):
                    missing_cols.extend(col)
                    logger.debug(
                        f"Missing {col} in input source. Adding to missing columns"
                    )
            elif col not in existing_cols:
                missing_cols.append(col)
                logger.debug(
                    f"Missing {col} in input source. Adding to missing columns"
                )

        # Create dummy columns for missing ones
        if missing_cols:
            logger.debug(f"Missing columns: {missing_cols}. Creating dummy columns.")
            dummy_data = {}

            for col in missing_cols:
                if col == utm_columns.time:
                    dummy_data[col] = pl.Series(
                        name=col,
                        values=[datetime.strptime(args_parsed.datetime_start, "%Y-%m-%d %H:%M:%S")+timedelta(seconds=i) for i in range(len(df_source))],
                    )
                    logger.warning(
                        f"Missing {col} in input source. Created dummy column {col} with start datetime {args_parsed.datetime_start}"
                    )
                    logger.debug(f"DT dummy_data: {dummy_data[col]}")
                elif col == utm_columns.nrSVN:
                    dummy_data[col] = pl.Series(name=col, values=[0] * len(df_source))
                    logger.warning(
                        f"Missing {col} in input source. Created dummy column {col} with 0"
                    )
                    logger.debug(f"NRSVN dummy_data: {dummy_data[col]}")
                elif col == utm_columns.quality_mapping.quality_column:
                    dummy_data[col] = pl.Series(
                        name=col,
                        values=["MANUAL"] * len(df_source),
                    )
                    logger.warning(
                        f"Missing {col} in input source. Created dummy column {col} with MANUAL quality"
                    )
                    logger.debug(f"pvt qual dummy_data: {dummy_data[col]}")
                else:
                    dummy_data[col] = pl.Series(
                        name=col, values=[None] * len(df_source)
                    )
                    logger.warning(
                        f"Missing {col} in input source. Created dummy column {col} with None"
                    )
                    logger.debug(f"{col} dummy_data: {dummy_data[col]}")
            # Add dummy columns to dataframe
            for col_name, col_data in dummy_data.items():
                df_source = df_source.with_columns(col_data)

        # Now create df_utm with all required columns
        if not args_parsed.sd:
            df_utm = df_source.select(
                required_columns[:6]
            )  # First 6 columns without SD
        else:
            df_utm = df_source.select(required_columns)  # All columns including SD

    except Exception as e:
        logger.error(f"Error creating UTM dataframe: {str(e)}")
        raise

    # Filter out rows with null/nan values in UTM coordinates and height
    df_utm = df_utm.filter(
        pl.col(utm_columns.east).is_not_null()
        & pl.col(utm_columns.north).is_not_null()
        & pl.col(utm_columns.height).is_not_null()
    )

    if logger is not None:
        logger.info(f"df_utm = \n{df_utm}")

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

    # source = "PPK" if args_parsed.pos_ifn else "RTK"
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
    df_utm = plot_coords(argv=sys.argv)  # type: ignore


if __name__ == "__main__":
    main()
