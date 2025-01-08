#!/usr/bin/env python

import os
import sys

import polars as pl
from rich import print

import analysegnss.glabng.glab_parser as glab_parser
import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
from analysegnss.config import ERROR_CODES
from analysegnss.plots import plot_utm
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.utils import argument_parser, init_logger


def get_origin(parsed_args: list) -> str:
    """determines the origin  of the coordinates

    Args:
        parsed_args (list): list of parsed arguments

    Returns:
        tuple[str, str]: origin and filename
    """
    # set the origin of the coordinates
    file_handlers = {"pos_fn": "PPK", "sbf_fn": "RTK", "glab_fn": "GLABNG"}

    # Get the first non-None filename and its attribute name
    file_attr = next(
        attr
        for attr in ["pos_fn", "sbf_fn", "glab_fn"]
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
    args_parsed = argument_parser.argument_parser_plot_coords(
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
            pos_fn_index = argv.index("--pos_fn")
            pos_fn_value = argv[pos_fn_index + 1]

            ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_fn", pos_fn_value]
            df_origin = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

        case "RTK":
            # create the RTK position dataframe by calling rtk_pvtgeod.py
            sbf_fn_index = argv.index("--sbf_fn")
            sbf_fn_value = argv[sbf_fn_index + 1]

            rtk_pvtgeod_args = (
                ["rtk_pvtgeod.py", "--sbf_fn", sbf_fn_value]
                if not args_parsed.sd
                else [
                    "rtk_pvtgeod.py",
                    "--sbf_fn",
                    sbf_fn_value,
                    "--sd",
                ]
            )

            df_origin = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

        case "GLABNG":
            # create the GLAB position dataframe by calling glab_parser
            glab_fn_index = argv.index("--glab_fn")
            glab_fn_value = argv[glab_fn_index + 1]

            glab_parser_args = [
                "glab_parser",
                "--glab_fn",
                glab_fn_value,
                "--section",
                "OUTPUT",
            ]
            dfs_glab = glab_parser.glab_parser(argv=glab_parser_args)

            with pl.Config(
                tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
            ):
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
    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        print(f"=====================\ndf_utm = \n{df_utm}\n=====================")

    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        if logger is not None:
            logger.info(f"df_utm = \n{df_utm}")

    # find filename and directory from the position file
    # fn_full = args_parsed.pos_fn if args_parsed.pos_fn else args_parsed.sbf_fn
    fn_full = next(
        fn
        for fn in [args_parsed.pos_fn, args_parsed.sbf_fn, args_parsed.glab_fn]
        if fn is not None
    )

    # separate the filename from the path
    filename = os.path.basename(fn_full)
    dir_fn = os.path.dirname(fn_full)

    # origin = "PPK" if args_parsed.pos_fn else "RTK"
    print(f"creating plot for {origin} position file {filename}")

    # plot the UTM and orthoH coordinates
    if args_parsed.mpl == False:
        # use plotly for creating html plots
        plot_utm.plot_utm_scatter(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            logger=logger,
            display=args_parsed.display,
        )

        plot_utm.plot_utm_height(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            sd=args_parsed.sd,
            logger=logger,
            display=args_parsed.display,
        )
    else:
        plot_utm.plot_utm_scatter_mpl(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            logger=logger,
            display=args_parsed.display,
        )

        plot_utm.plot_utm_height_mpl(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            sd=args_parsed.sd,
            logger=logger,
            display=args_parsed.display,
        )


def main():
    df_utm = plot_coords(argv=sys.argv)  # type: ignore


if __name__ == "__main__":
    main()
