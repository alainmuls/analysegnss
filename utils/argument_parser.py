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
        default="",
        type=str,
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
        "--pos_ifn",
        help="input rnx2rtkp pos filename",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name",
        required=False,
        default="",
        type=str,
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
        "--plot",
        help="display plots (default False)",
        action="store_true",
        required=False,
        default=False,
    )

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.description = "Specify either a POS file or an SBF file (required)"

    group.add_argument(
        "--pos_ifn",
        help="input rnx2rtkp pos filename",
        type=str,
    )
    group.add_argument(
        "--sbf_ifn",
        help="input SBF filename",
        type=str,
    )
    parser.add_argument(
        "--title",
        help="Plot title",
        default=None,
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
    # Create mutually exclusive group for pos_ifn and sbf_ifn (PPK and RTK respectively)
    group_rtkppk = parser.add_mutually_exclusive_group(required=True)
    group_rtkppk.description = (
        "Specify either a POS file (PPK) or an SBF file (RTK) [required]"
    )
    group_rtkppk.add_argument(
        "--pos_ifn",
        help="input rnx2rtkp pos (PPK) filename",
        type=str,
    )
    group_rtkppk.add_argument(
        "--sbf_ifn",
        help="input SBF (RTK) filename",
        type=str,
    )

    parser.add_argument(
        "--desc",
        help="description of EBH lines project",
        type=str,
        required=False,
    )

    parser.add_argument(
        "--timing_ifn",
        help="input ebh lines timing filename. One of the keys needs to be called CL. The other keys of each track can be freely chosen. e.g. key: Wnc TOWstart, Wnc TOWend",
        type=str,
        required=True,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_get_ebh_timings(args: list) -> argparse.Namespace:
    """
    Extracts the timestamps from the SBF file and saves them to a file.
    This file is formatted for ebh_lines.py
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_txt = (
        baseName
        + """
        Extracts the timestamps from the SBF file and saves them to a file.
        This file is formatted for ebh_lines.py
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
        help="input sbf filename with sbf comments holding timestamp info",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--timing_ofn",
        help="output EBH line timings filename (use full path). This file \
            is required by ebh_lines.py (default: {sbf_ifn}_ebh_timings.txt)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default="",
        type=str,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_get_base_coord(args: list) -> argparse.Namespace:
    "Gets the base coordinates from a SBF file using the sbf_class"
    baseName = str_yellow(os.path.basename(__file__))
    help_text = (
        baseName
        + """
        Gets the base coordinates from a SBF file in XYZ using the sbf_class
    """
    )

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_text)
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
        "--sbf_ifn",
        help="input sbf filename with sbf BaseStation1 block.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--datetime",
        help="Date time instance of the base station coordinates in YYYY-MM-DD_HH:MM:SS(.%f)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    args = parser.parse_args(args)

    return args


def argument_parser_ebh_process_launcher(args: list) -> argparse.Namespace:
    """Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings,
    decides whether the RTK or PPK solution has a sufficient quality,
    and finally outputs correct ASSUR formatted files for each ebh line.
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_text = (
        baseName
        + """
        Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
        from which it retrievers the correct timings, 
        decides whether the RTK or PPK solution has a sufficient quality, 
        and finally outputs correct ASSUR formatted files for each ebh line.
        """
    )

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_text)
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
        "--sbf_ifn",
        help="input sbf file. This sbf file not only contains the RTK/obs/nav data but also the timestamps",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--base_corr",
        help="base correction filename. RNX OBS or SBF file obtained from GNSS base station. If provided, a PPK solution is calculated \
            for each RTK solution that is not of sufficient quality.",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-cfg_ppk",
        "--config_ppk",
        help="file name of config file used for RTKLib rnx2rtkp calculation.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--desc",
        help="description of EBH lines project",
        type=str,
        required=False,
        default="ebh_line",
    )
    parser.add_argument(
        "--archive",
        help="Specify archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default="",
        type=str,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_rnx2rtkp_launcher(args: list) -> argparse.Namespace:
    """
    Parses the arguments and creates console/file logger for launch_ppk_rnx2rtkp.py
    """

    baseName = str_yellow(os.path.basename(__file__))

    help_text = (
        baseName
        + """
        This program post-processes RINEX observations and navigation files 
        and base correction data (RTCM or RNX obs) to obtain PPK, PPP, and SPP solutions using RTKLib.
        At the moment it only supports PPK calculations.
        """
    )
    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_text)
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
        "--obs",
        help="input RINEX observation filename",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--nav",
        nargs="+",
        help="input (multiple) RINEX navigation filename. If more than one leave space between the different filenames",
        type=str, 
        required=True
    )
    parser.add_argument(
        "--base_corr",
        help="input RINEX observation filename or sbf filename obtained from GNSS base station (working on RTCM3).",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-X",
        "--base_coord_X",
        help="Reference coordinates of base station in ECEF XYZ format.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-Y",
        "--base_coord_Y",
        help="Reference coordinates of base station in ECEF XYZ format.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-Z",
        "--base_coord_Z",
        help="Reference coordinates of base station in ECEF XYZ format",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-cfg_ppk",
        "--config_ppk",
        help="RTKlib configuration file",
        type=str,
        required=True
    )
    parser.add_argument(
        "-dts",
        "--datetime_start",
        help="obs start time in the format YYYY-MM-DD_HH:MM:SS(.s)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-dte",
        "--datetime_end",
        help="obs end time in the format YYYY-MM-DD_HH:MM:SS(.s)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--pos_ofn",
        help="output filename of position file (default is obs filename + _PPK.pos)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    args = parser.parse_args(args)

    return args


def argument_parser_get_rnx_files(args: list) -> argparse.Namespace:
    """
    Extracts rinex files from binary files such as Septentrio SBF files 
    (Future work: extend this to other file formats such as rtcm3, ubx, etc.)
    """

    baseName = str_yellow(os.path.basename(__file__))

    help_text = (
        baseName
        + """
            Extracts rinex files from Septentrio SBF files 
            (Future work: extend this to other file formats such as rtcm3, ubx, etc.)
        """
    )
    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=help_text)
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
        "--sbf_ifn",
        help="input filename of binary file (e.g. SBF file)",
        type=str,
        required=True
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    args = parser.parse_args(args)

    return args


