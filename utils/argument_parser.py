import argparse
import os

import argcomplete

from utils.utilities import str_yellow


def argument_parser_sbf(args: list) -> argparse.Namespace:
    """parses the arguments and creates console/file logger

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = baseName + " analysis of SBF data"

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_txt)
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.2")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="verbose level... repeat up to three times.",
    )
    parser.add_argument(
        "--sbf_fn",
        help="input SBF filename",
        type=str,
        required=True,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_pos(args: list) -> argparse.Namespace:
    """parses the arguments and creates console/file logger

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = baseName + " analysis of rnx2rtkp position file"

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_txt)
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.2")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="verbose level... repeat up to three times.",
    )
    parser.add_argument(
        "--pos_fn",
        help="input rnx2rtkp pos filename",
        type=str,
        required=True,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args
