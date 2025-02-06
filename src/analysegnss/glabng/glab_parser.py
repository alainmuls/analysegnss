#!/usr/bin/env python3
import logging
import os
import sys

import polars as pl
from rich import print

from analysegnss.glabng.glabng_class import GLABNG
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import argument_parser_glab_parser


def parse_glab_section(
    glab_fn: str, section: list[str], logger: logging.Logger = None
) -> dict[str, pl.DataFrame]:
    """parses specified section in a glab file

    Args:
        glab_fn (str): name of glab file
        section (list[str]): sections to parse

    Returns:
        dict[str, pl.DataFrame]: dictionary of dataframes where the section name is the key and the dataframe is the value
    """
    try:
        glab = GLABNG(glab_fn=glab_fn, logger=logger)
    except ValueError as e:
        print(f"Validation failed: {e}")

    # parse the OUTPUT section of glab file
    glab_dfs = glab.glab_dataframe(lst_sections=section)

    #     for section, df_section in glab_dfs.items():
    #         print(f"dataframe from [green][bold]{section}[/bold][/green] section")
    #         print(df_section)

    return glab_dfs


def glab_parser(argv: list) -> dict[str, pl.DataFrame]:
    """
    Parses a gLAB file.

    Returns:
        dict[str, pl.DataFrame]: dictionary of dataframes where the section name is the key and the dataframe is the value
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_glab_parser(
        args=argv[1:], script_name=os.path.basename(__file__)
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    dfs_glabng = parse_glab_section(
        glab_fn=args_parsed.glab_fn,
        section=args_parsed.section,
        logger=logger,
    )

    return dfs_glabng


def main():
    dfs_glab = glab_parser(argv=sys.argv)

    for section, df_section in dfs_glab.items():
        print(f"dataframe from [green][bold]{section}[/bold][/green] section")
        print(df_section)


if __name__ == "__main__":
    main()
