#!/usr/bin/env python

import os
import sys

import polars as pl
from rich import print

import analysegnss.rtkpos.ppk_rnx2rtkp as ppk_rnx2rtkp
import analysegnss.sbf.rtk_pvtgeod as rtk_pvtgeod
from analysegnss.config import ERROR_CODES
from analysegnss.plots import plot_utm
from analysegnss.utils import argument_parser, init_logger


def rtkppk_plot(argv: list):
    """analyses the rnx2rtkp output file and extracts the position information

    Args:
        argv (list): CLI arguments
    """
    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ppk_plot(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {args_parsed}")

    if args_parsed.pos_fn is not None:
        # create the PPK position dataframe by calling ppk_rnx2rtkp.py
        pos_fn_index = argv.index("--pos_fn")
        pos_fn_value = argv[pos_fn_index + 1]

        ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py", "--pos_fn", pos_fn_value]
        df_pos = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

        # select the columns needed for the plot
        if not args_parsed.sd:
            df_utm = df_pos.select(["DT", "Q", "ns", "UTM.E", "UTM.N", "orthoH"])
        else:
            df_utm = df_pos.select(
                [
                    "DT",
                    "Q",
                    "ns",
                    "UTM.E",
                    "UTM.N",
                    "orthoH",
                    "sdn(m)",
                    "sde(m)",
                    "sdu(m)",
                ]
            )
        # df_utm = df_pos.select(["DT", "Q", "ns", "UTM.E", "UTM.N", "orthoH"])

    elif args_parsed.sbf_fn is not None:
        # create the RTK position dataframe by calling rtk_pvtgeod.py
        # create the PPK position dataframe by calling ppk_rnx2rtkp.py
        sbf_fn_index = argv.index("--sbf_fn")
        sbf_fn_value = argv[sbf_fn_index + 1]

        if args_parsed.sd:
            rtk_pvtgeod_args = [
                "rtk_pvtgeod.py",
                "--sbf_fn",
                sbf_fn_value,
                "--sd",
            ]
        else:
            rtk_pvtgeod_args = ["rtk_pvtgeod.py", "--sbf_fn", sbf_fn_value]

        df_rtk = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)
        # with pl.Config(
        #     tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        # ):
        #     for sbf_block, df_block in dfs_rtk.items():
        #         print(f"[bold green]df_{sbf_block}")
        #         print(df_block)

        # select the columns needed for the plot
        if not args_parsed.sd:
            df_utm = df_rtk.select(["DT", "Type", "NrSV", "UTM.E", "UTM.N", "orthoH"])
        else:
            df_utm = df_rtk.select(
                [
                    "DT",
                    "Type",
                    "NrSV",
                    "UTM.E",
                    "UTM.N",
                    "orthoH",
                    "SD_lat [m]",
                    "SD_lon [m]",
                    "SD_hgt [m]",
                ]
            )

    else:
        if logger is not None:
            logger.error("No position file specified")
        print("No position file specified")
        sys.exit(ERROR_CODES["E_INVALID_ARGS"])

    with pl.Config(tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"):
        if logger is not None:
            logger.info(f"df_utm = \n{df_utm}")

    # find filename and directory from the position file
    fn_full = args_parsed.pos_fn if args_parsed.pos_fn else args_parsed.sbf_fn
    # separate the filename from the path
    filename = os.path.basename(fn_full)
    dir_fn = os.path.dirname(fn_full)

    # set the origin of the coordinates
    origin = "PPK" if args_parsed.pos_fn else "RTK"
    print(f"creating plot for {origin} position file {filename}")

    # plot the UTM and orthoH coordinates
    if args_parsed.plot:
        plot_utm.plot_utm_scatter(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            logger=logger,
        )

        plot_utm.plot_utm_height(
            utm_df=df_utm,
            origin=origin,
            fn=filename,
            dir_fn=dir_fn,
            sd=args_parsed.sd,
            logger=logger,
        )


def main():
    df_rtkpos = rtkppk_plot(argv=sys.argv)  # type: ignore


if __name__ == "__main__":
    main()
