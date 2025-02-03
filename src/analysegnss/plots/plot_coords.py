#!/usr/bin/env python

import os
import sys

import polars as pl
from rich import print

import analysegnss.glabng.glab_parser as glab_parser
import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.plots import plot_utm
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_plot_coords


def get_origin(parsed_args: list) -> str:
    """determines the origin  of the coordinates

    Args:
        parsed_args (list): list of parsed arguments

    Returns:
        tuple[str, str]: origin and filename
    """
    # set the origin of the coordinates
    file_handlers = {"pos_ifn": "PPK", "sbf_ifn": "RTK", "glab_ifn": "GLABNG"}

    # Get the first non-None filename and its attribute name
    file_attr = next(
        attr
        for attr in ["pos_ifn", "sbf_ifn", "glab_ifn"]
        if getattr(parsed_args, attr) is not None
    )
    # filename = getattr(parsed_args, file_attr)

    # Create instance and get origin in one go
    origin = file_handlers[file_attr]
    return origin


def plot_coords(argv: list):
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments
    """
    # parse the CLI arguments
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

    # get the origin of the coordinates
    origin = get_origin(parsed_args=args_parsed)

    # get the needed columns from the dataframe according to the origin
    match origin:
        case "PPK":
            # create the PPK position dataframe by calling ppk_rnx2rtkp.py
            pos_ifn_index = argv.index("--pos_ifn")
            pos_ifn_value = argv[pos_ifn_index + 1]

            ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_ifn", pos_ifn_value]
            df_origin = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

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

            df_origin = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

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

            df_origin = dfs_glab["OUTPUT"]

        case _:
            logger.error(f"Invalid origin: {origin}")
            sys.exit(ERROR_CODES["E_INVALID_ORIGIN"])

    # get the utm columns names according to the origin
    utm_columns = get_utm_columns(origin=origin)
    print(f"utm_columns: {utm_columns}")
    print(f"type(utm_columns): {type(utm_columns)}")

    print(
        f"{utm_columns.east} {utm_columns.north} {utm_columns.quality_mapping.columns}"
    )

    # create the df_utm dataframe from the dataframe obtained according to each origin
    if not args_parsed.sd:
        df_utm = df_origin.select(
            [
                utm_columns.time,
                utm_columns.quality_mapping.columns,
                utm_columns.nrSVN,
                utm_columns.east,
                utm_columns.north,
                utm_columns.height,
            ]
        )
    else:
        df_utm = df_origin.select(
            [
                utm_columns.time,
                utm_columns.quality_mapping.columns,
                utm_columns.nrSVN,
                utm_columns.east,
                utm_columns.north,
                utm_columns.height,
                utm_columns.sdn,
                utm_columns.sde,
                utm_columns.sdu,
            ]
        )
    # select the columns needed for the plot
    print(f"=====================\ndf_utm = \n{df_utm}\n=====================")
    if logger is not None:
        logger.info(f"df_utm = \n{df_utm}")

    # find filename and directory from the position file
    # ifn_full = args_parsed.pos_ifn if args_parsed.pos_ifn else args_parsed.sbf_ifn
    ifn_full = next(
        ifn
        for ifn in [args_parsed.pos_ifn, args_parsed.sbf_ifn, args_parsed.glab_ifn]
        if ifn is not None
    )

    # separate the filename from the path
    filename_in = os.path.basename(ifn_full)
    dir_fn = os.path.dirname(ifn_full)

    # origin = "PPK" if args_parsed.pos_ifn else "RTK"
    print(f"creating plot for {origin} position file {filename_in}")

    # plot the UTM and orthoH coordinates
    if args_parsed.mpl == False:
        with rich_console.status(f"Creating UTM scatter plot.\t", spinner="aesthetic"):
		    # use plotly for creating html plots
		    plot_utm.plot_utm_scatter(
		        utm_df=df_utm,
		        origin=origin,
		        ifn=filename_in,
		        dir_fn=dir_fn,
		        logger=logger,
		        display=args_parsed.display,
		    )

        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
		    plot_utm.plot_utm_height(
		        utm_df=df_utm,
		        origin=origin,
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
		        origin=origin,
		        ifn=filename_in,
		        dir_fn=dir_fn,
		        logger=logger,
		        display=args_parsed.display,
		    )

        with rich_console.status(f"Creating NEU vs DT plot.\t", spinner="aesthetic"):
		    plot_utm.plot_utm_height_mpl(
		        utm_df=df_utm,
		        origin=origin,
		        ifn=filename_in,
		        dir_fn=dir_fn,
		        sd=args_parsed.sd,
		        logger=logger,
		        display=args_parsed.display,
		    )


def main():
    df_utm = plot_coords(argv=sys.argv)  # type: ignore


if __name__ == "__main__":
    main()
