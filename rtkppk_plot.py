#!/usr/bin/env python

import os
import sys

import polars as pl

import ppk_rnx2rtkp
import rtk_pvtgeod
from config import ERROR_CODES
from plots import plot_utm
from utils import argument_parser, init_logger


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
        df_utm = df_pos.select(["DT", "Q", "ns", "UTM.E", "UTM.N", "orthoH"])

        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            if logger is not None:
                logger.info(f"df_pos = \n{df_pos}")
                logger.info(f"df_utm = \n{df_utm}")

        origin = "PPK"
        if args_parsed.title is not None:
            title = args_parsed.title
        else:
            title = args_parsed.pos_fn + " (" + origin + ")"

    elif args_parsed.sbf_fn is not None:
        # create the RTK position dataframe by calling rtk_pvtgeod.py
        # create the PPK position dataframe by calling ppk_rnx2rtkp.py
        sbf_fn_index = argv.index("--sbf_fn")
        sbf_fn_value = argv[sbf_fn_index + 1]

        rtk_pvtgeod_args = ["rtk_pvtgeod.py", "--sbf_fn", sbf_fn_value]
        df_rtk = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

        # select the columns needed for the plot
        df_utm = df_rtk.select(["DT", "Type", "NrSV", "UTM.E", "UTM.N", "orthoH"])

        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            if logger is not None:
                logger.info(f"df_rtk = \n{df_rtk}")
                logger.info(f"df_utm = \n{df_utm}")

        origin = "RTK"
        if args_parsed.title is not None:
            title = args_parsed.title
        else:
            title = args_parsed.sbf_fn + " (" + origin + ")"

    else:
        if logger is not None:
            logger.error("No position file specified")
        print("No position file specified")
        sys.exit(ERROR_CODES["E_INVALID_ARGS"])

    # plot the UTM and orthoH coordinates
    if args_parsed.plot:
        plot_utm.plot_utm_coords(
            utm_df=df_utm,
            origin=origin,
            title=title,
            logger=logger,
        )


if __name__ == "__main__":
    df_rtkpos = rtkppk_plot(argv=sys.argv)  # type: ignore
