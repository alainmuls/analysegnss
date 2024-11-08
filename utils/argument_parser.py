import argparse
import os
import argcomplete

from utils.utilities import str_yellow


def argument_parser_rtk(args: list) -> argparse.Namespace:
    """parses the arguments

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
        "--sbf_fn",
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

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_ppk(args: list) -> argparse.Namespace:
    """parses the arguments

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


def argument_parser_ppk_plot(args: list) -> argparse.Namespace:
    """(Deprecated. Use ppk_rnx2rtkp instead.)
    Parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = (
        baseName + " Plot PPK (from ppk_rnx2rtkp.py) or RTK (from rtk_pvtgeod.py) data"
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
    )

    parser.add_argument(
        "--title",
        help="title for plot",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "--plot",
        help="display plots (default False)",
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
    """parses the arguments

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
        help="input ebh lines timing filename. One of the keys needs to be called CL.\n"
        " The other keys of each track can be freely chosen. e.g. key: Wnc TOWstart, Wnc TOWend",
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


def argument_parser_rnxobs_csv(args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = (
        baseName
        + " Convert RINEX observation file to CSV file similar to those created by rtcm3_parser.py"
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
    )

    parser.add_argument(
        "--rnx_fn",
        help="RINEX observation filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--csv_fn",
        help="CSV observation filename (defaults to extension csv instead of rnx)",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems to convert (default: GE, select between G, R, E, C)",
        type=str,
        required=False,
        default="GE",
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args
