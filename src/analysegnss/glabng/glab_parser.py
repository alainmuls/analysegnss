#!/usr/bin/env python3
import logging
import os
import sys

from analysegnss.glabng.glabng_class import GLABNG
from analysegnss.utils import argument_parser, init_logger


def glab_parser(
    glab_fn: str, glab_sections: list[str], logger: logging.Logger = None
) -> None:
    """parses specified section in a glab file

    Args:
        glab_fn (str): name of glab file
        glab_sections (list[str]): sections to parse
    """
    try:
        glab = GLABNG(glab_fn=glab_fn, logger=logger)
    except ValueError as e:
        print(f"Validation failed: {e}")

    # parse the OUTPUT section of glab file
    glab.glab_dataframe(lst_sections=glab_sections)


def main():
    """
    Parses a gLAB file.
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser.argument_parser_glab_parser(args=sys.argv[1:])

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    glab_parser(
        glab_fn=args_parsed.glab_fn,
        glab_sections=args_parsed.section,
        logger=logger,
    )


if __name__ == "__main__":
    main()
