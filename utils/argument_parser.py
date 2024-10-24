import argparse
import os

import argcomplete

from utils.utilities import str_yellow


def argument_parser_rtk(args: list) -> argparse.Namespace:
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
    parser.add_argument(
        "--sbf_ifn",
        help="input SBF filename",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--sbf2asc",
        help="Using sbf2asc instead of bin2asc as sbf converter.",
        action="store_true",
        required=False,
    )

    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.2")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="verbose level... repeat up to three times.",
    )
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name",
        required=False,
        default='',
        type=str
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_ppk(args: list) -> argparse.Namespace:
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
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name",
        required=False,
        default='',
        type=str
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_ppk_plot(args: list) -> argparse.Namespace:
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
    parser.add_argument(
        "--plot",
        help="displays plots (default False)",
        action="store_true",
        required=False,
        default=False,
    )

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.description = "Specify either a POS file or an SBF file (required)"
    # parser.add_argument(
    #     "--mutually-exclusive",
    #     action="store_true",
    #     help="One of the following options is required:",
    # )

    group.add_argument(
        "--pos_fn",
        help="input rnx2rtkp pos filename",
        type=str,
    )
    group.add_argument(
        "--sbf_fn",
        help="input SBF filename",
        type=str,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)
    print(f"Parsed arguments: {vars(args)}")

    return args


def argument_parser_ebh_lines(args: list) -> argparse.Namespace:
    """parses the arguments and creates console/file logger

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = baseName + " extracts the EBH lines from RTK or PPK created dataframe"

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
    # Create the first mutually exclusive group
    group_rtkppk = parser.add_mutually_exclusive_group(required=True)
    group_rtkppk.add_argument(
        "--rtk", action="store_true", help="extract lines from RTK solution"
    )
    group_rtkppk.add_argument(
        "--ppk", action="store_true", help="extract lines from PPK solution"
    )

    parser.add_argument(
        "--desc",
        help="description of EBH lines project",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--ebh_fn",
        help="input RTK/PPK filename",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--timing_fn",
        help="input ebh lines timing filename",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--plot",
        help="displays plots (default False)",
        action="store_true",
        required=False,
        default=False,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args

def argument_parser_ebh_timestamps(args: list) -> argparse.Namespace:
    """
    
    
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = (
        baseName
        + """
        Extracts the timestamps from the SBF file and saves them in a yaml/desc file.
        The description file is used to calculate the EBH lines
    """
    )

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_txt)
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.2")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="verbose level... repeat up to three times.",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--sbf_ifn",
        help="input sbf file with sbf comments holding timestamp info",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--out_ebh_fn",
        help="Creates EBH lines description file (use full path!). This description file \
            is required by ebh_lines.py (default: ebh_timings_desc.txt)",
        type=str,
        required=False,
        default="ebh_timings_desc.txt"
    )
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name",
        required=False,
        default='',
        type=str
    )
    parser.add_argument(
        "--log",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/"
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args