#!/usr/bin/env python

import argparse
import os
import sys

import polars as pl
from tabulate import tabulate

import globalvars
import ppk_rnx2rtkp
import rtk_pvtgeod
from rtkpos import rtk_constants as rtkc
from rtkpos.rtkpos_class import Rtkpos
from utils import argument_parser, init_logger
from utils.utilities import str_yellow


def get_ppk_dataframe(parsed_args: argparse.Namespace) -> pl.DataFrame:
    """get the dataframe obtained from PPK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with PPK solution
    """
    ppk_rnx2rtkp_args = ["ppk_rnx2rtkp.py"]
    ppk_rnx2rtkp_args.append("--pos_fn")
    ppk_rnx2rtkp_args.append(parsed_args.ebh_fn)
    if parsed_args.verbose:
        match parsed_args.verbose:
            case 1:
                ppk_rnx2rtkp_args.append("-v")
            case 2:
                ppk_rnx2rtkp_args.append("-vv")
            case 3:
                ppk_rnx2rtkp_args.append("-vvv")

    print(f"ppk_rnx2rtkp_args = {ppk_rnx2rtkp_args}")

    df_pos = ppk_rnx2rtkp.rtkp_pos(argv=ppk_rnx2rtkp_args)

    return df_pos


def get_rtk_dataframe(parsed_args: argparse.Namespace) -> pl.DataFrame:
    """get the dataframe obtained from RTK processing

    Args:
        parsed_args (argparse.Namespace): CLI arguments

    Returns:
        pl.DataFrame: dataframe with RTK solution
    """
    rtk_pvtgeod_args = ["rtk_pvtgeod.py"]
    rtk_pvtgeod_args.append("--sbf_fn")
    rtk_pvtgeod_args.append(parsed_args.ebh_fn)
    if parsed_args.verbose:
        match parsed_args.verbose:
            case 1:
                rtk_pvtgeod_args.append("-v")
            case 2:
                rtk_pvtgeod_args.append("-vv")
            case 3:
                rtk_pvtgeod_args.append("-vvv")

    print(f"rtk_pvtgeod_args = {rtk_pvtgeod_args}")

    df_pos = rtk_pvtgeod.rtk_pvtgeod(argv=rtk_pvtgeod_args)

    return df_pos


def ebh_lines(argv: list):
    """get the ebh_lines from RTK or PPK processing

    Args:
        argv (list): CLI arguments
    """
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_ebh_lines(args=argv[1:])
    print(f"\nParsed arguments: {args_parsed}")
    print(f"\nParsed arguments: {type(args_parsed)}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    logger.info(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

    # get the dataframe according to the processing type (RTK or PPK)
    if args_parsed.ppk:
        # call ppp_rnx2rtkp to get the position dataframe
        pos_df = get_ppk_dataframe(parsed_args=args_parsed)

        logger.info(f"Dataframe obtained from PPK processing of {args_parsed.ebh_fn}")
        print(
            f"Dataframe obtained from {str_yellow('PPK')} processing of {str_yellow(args_parsed.ebh_fn)}"
        )
    elif args_parsed.rtk:
        # call rtk_pvtgeod to get the position dataframe
        pos_df = get_rtk_dataframe(parsed_args=args_parsed)

        logger.info(f"Dataframe obtained from RTK processing of {args_parsed.ebh_fn}")
        print(
            f"Dataframe obtained from {str_yellow('RTK')} processing of {str_yellow(args_parsed.ebh_fn)}"
        )
    else:
        logger.error("No processing type selected")
        sys.exit(1)

    with pl.Config(tbl_cols=-1):
        logger.info(pos_df)
        print(pos_df)


if __name__ == "__main__":
    ebh_lines(argv=sys.argv)
