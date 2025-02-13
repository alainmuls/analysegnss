# Standard library imports
import argparse
import os

# Third party imports
import argcomplete
from rich import print

# Local application imports
from analysegnss.utils.utilities import str_yellow


def argument_parser_rtk(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

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

    parser.add_argument(
        "--sd",
        help="add standard deviation",
        action="store_true",
        required=False,
        default=False,
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
        help="Archives extracted sbf blocks to specified archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default=None,
        type=str,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_ppk(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments and creates console/file logger

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

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
        help="Specify archive's directory name which archives the extracted rnx2rtkp pos file",
        required=False,
        default=None,
        type=str,
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_plot_coords(script_name: str, args: list) -> argparse.Namespace:
    """Parses the arguments for plotting the UTM coordinates (evt with standard deviation)

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = (
        baseName
        + """: Plot UTM scatter and line plots from data files.

        Note: The plotting options --sbf_fn, --pos_fn, and --glib_fn are mutually exclusive.
        You must choose exactly one of these options."""
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

    # Create a mutually exclusive group
    group = parser.add_mutually_exclusive_group(required=True)
    group.description = "Specify origin (POS, SBF or gLABng) (required)"
    # parser.add_argument(
    #     "--mutually-exclusive",
    #     action="store_true",
    #     help="One of the following options is required:",
    # )

    group.add_argument(
        "--sbf_ifn",
        help="input SBF filename",
        type=str,
    )
    group.add_argument(
        "--pos_ifn",
        help="input rnx2rtkp pos filename",
        type=str,
    )
    group.add_argument(
        "--glab_ifn",
        help="input gLABng filename",
        type=str,
    )

    parser.add_argument(
        "--sd",
        help="add standard deviation to the plot",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "--title",
        help="title for plot",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--display",
        help="display plots (default False)",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "--mpl",
        help="use matplotlib for plotting (default plotly)",
        action="store_true",
        required=False,
        default=False,
    )
    parser.add_argument(
        "--archive",
        help="Archives extracted sbf blocks to specified archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default=None,
        type=str,
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)
    # print(f"Parsed arguments: {vars(args)}")

    return args


def argument_parser_ebh_lines(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

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
        "-odir",
        "--ebh_dest_dir",
        help="Destination directory of ebh assur files (default: EBH_ASSUR directory in directory of the input sbf or pos file)",
        type=str,
        required=False,
        default=None,
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


def argument_parser_rnxobs_csv(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

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
        "--obs_fn",
        help="RINEX observation filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--csv_fn",
        help="CSV observation filename (defaults to filename with extension csv)",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems to convert (default: GE, select between GREC)",
        type=str,
        required=False,
        default="GE",
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_rnxnav_csv(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = (
        baseName
        + " Convert RINEX navigation file to CSV file similar to those created by rtcm3_parser.py"
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
        "--nav_fn",
        help="RINEX navigation filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems to convert (default: GE, select between GREC)",
        type=str,
        required=False,
        default="GE",
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_rnx_csv(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = (
        baseName
        + " Convert RINEX Obs & Nav file to CSV file similar to those created by rtcm3_parser.py"
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
        "--obs_fn",
        help="RINEX observation filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--nav_fn",
        help="RINEX navigation filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems to convert (default: GE, select between GREC)",
        type=str,
        required=False,
        default="GE",
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_glab_parser(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = baseName + " parses the gLAB file."

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
        "--glab_ifn",
        help="gLAB produced file",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--section",
        type=lambda x: [str(item).strip() for item in x.split(",")],
        help="Comma-separated gLAB sections to parse (default: OUTPUT) (e.g. OUTPUT,SATSEL,INFO)",
        required=False,
        default="OUTPUT",
    )

    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args


def argument_parser_cn0_daily(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments for cn0_analyse
    Args:
        argv (list): list of arguments
    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = baseName + " analyses the CN0 values from a CSV observation file."

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
        "--obs_fn",
        help="CSV observation file",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems (select one of GREC)",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--sigtype",
        help="signal type (e.g. 1C, 2W, ...)",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--interval",
        help="interval in seconds (default=10s, can be fractional)",
        type=float,
        required=False,
        default=10.0,
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
        default=None,
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
        help="Date time instance of the base station coordinates in YYYY-MM-DD_HH:MM:SS(.s)",
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
    """Launches the appropriate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings,
    decides whether the RTK or PPK solution has a sufficient quality,
    and finally outputs correct ASSUR formatted files for each ebh line.
    """
    baseName = str_yellow(os.path.basename(__file__))

    help_text = (
        baseName
        + """
        Launches the appropriate functions to calculate the ebh_lines from the sbf_ifn file
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
        help="input sbf file name. This sbf file not only contains the RTK/obs/nav data but also the ebh line timestamps",
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
        "-cfg",
        "--config_ppk",
        help="File name of config file used for RTKLib rnx2rtkp calculation. Default: rtkpos/rnx2rtkp_config/rnx2rtkp_EBH_PPK_default.conf",
        type=str,
        required=False,
        default="rtkpos/rnx2rtkp_config/rnx2rtkp_EBH_PPK_default.conf",
    )
    # TODO add sbf2asc compatibility (check if sbf2asc can extract sbf comments, ...)
    """
    parser.add_argument(
        "--sbf2asc",
        help="Using sbf2asc instead of bin2asc as sbf converter. Use sbf2asc if environment is ran on a ARM processor.",
        action="store_true",
        required=False,
    )
    """
    parser.add_argument(
        "--desc",
        help="description of EBH lines project",
        type=str,
        required=False,
        default="ebh_line",
    )
    parser.add_argument(
        "-odir",
        "--ebh_dest_dir",
        help="Destination directory of ebh assur files (default: EBH_ASSUR directory in directory of the input sbf or pos file)",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--archive",
        help="Archives extracted sbf blocks to specified archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default=None,
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
        required=True,
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
        required=True,
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


def argument_parser_get_rnx_files(args: list, script_name: str) -> argparse.Namespace:
    """
    Extracts rinex files from binary files such as Septentrio SBF files
    (Future work: extend this to other file formats such as rtcm3, ubx, etc.)
    """

    baseName = str_yellow(script_name)

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
        required=True,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    args = parser.parse_args(args)


def argument_parser_gradient_ebhlines(
    args: list, script_name: str
) -> argparse.Namespace:
    """
    Parses the arguments and creates console/file logger for gradient_ebhlines.py
    """

    baseName = str_yellow(script_name)

    help_text = (
        baseName
        + """
        Calculates the transversal and longitudinal gradient of the runway according to the DATM team
        and saves the output to a text file.
        The output contains:
            - the transversal and longitudinal gradient of the runway
            - the coordinates of the highest point on the CLine
            - the centerline coordinates on the lowest threshold
            - the distance from the lowest threshold to the highest point on the CLine
            - the slope from the lowest threshold to the highest point on the CLine
        from the ebh lines csv files
    """
    )

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
        "-id",
        "--input_dir",
        help="Directory containing the ebh lines csv files",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-od",
        "--output_dir",
        help="Directory to save the output file. (default: input_dir)",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "-ofn",
        "--output_filename",
        help="Output filename containing the runway gradient and other information. (default: runway_gradient_information.txt)",
        type=str,
        required=False,
        default="runway_gradient_information.txt",
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). (Default is /tmp/logs/)",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    args = parser.parse_args(args)

    return args


def argument_parser_reformat_sbf_rnx_for_opus(
    args: list, script_name: str
) -> argparse.Namespace:
    """
    This script checks and reformats rnx files for OPUS processing.
    Default is 01D duration and 30 seconds epoch interval for gnss systems GPS and Galileo.
    The scripts accepts sbf and rnx files.
    """
    baseName = str_yellow(script_name)

    help_txt = baseName + " checks and reformats rnx files for OPUS processing."

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
        "--log_dest",
        help="Specify log destination directory (full path). Default is /tmp/logs/",
        type=str,
        required=False,
        default="/tmp/logs/",
    )

    # Create mutually exclusive group for rnx_ifn and sbf_ifn (RINEX and SBF Septentrio respectively)
    group_sbfrnx = parser.add_mutually_exclusive_group(required=True)
    group_sbfrnx.description = (
        "Specify either a SBF file (Septentrio) or a RINEX file [required]"
    )
    group_sbfrnx.add_argument(
        "--rnx_ifn",
        help="input RINEX OBS filename. A RNX OBS file for OPUS processing is automatically created.",
        type=str,
    )
    group_sbfrnx.add_argument(
        "--sbf_ifn",
        help="input SBF (Septentrio) filename",
        type=str,
    )
    parser.add_argument(
        "--OPUS",
        help="Create additional rnx file for OPUS processing.",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "--gnss",
        help="OPUS configuration: select which GNSS constellation. GPS = G, Galileo=E, Beidou = C and Glonass = R. Default is GE",
        required=False,
        default="GE",
    )
    parser.add_argument(
        "--duration",
        help="Duration or time span of rinex dataset in seconds. default: 86400",
        required=False,
        default=86400,
    )
    parser.add_argument(
        "--epoch_interval",
        help="Epoch interval. Default: 30 seconds",
        required=False,
        default=30,
    )

    args = parser.parse_args(args[1:])

    return args


def argument_parser_sbfmeas2csv(script_name: str, args: list) -> argparse.Namespace:
    """parses the arguments

    Args:
        argv (list): list of arguments

    Returns:
        argparse.Namespace: parsed arguments
    """
    baseName = str_yellow(script_name)

    help_txt = (
        baseName
        + " Convert SBF file to CSV file similar to those created by rtcm3_parser.py"
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
        "--sbf_ifn",
        help="SBF filename",
        type=str,
        required=True,
        default=None,
    )

    parser.add_argument(
        "--csv_ofn",
        help="CSV observation filename (defaults to filename with extension csv)",
        type=str,
        required=False,
        default=None,
    )

    parser.add_argument(
        "--gnss",
        help="GNSS systems to convert (default: GE, select between GREC)",
        type=str,
        required=False,
        default="GE",
    )

    parser.add_argument(
        "--archive",
        help="Archives extracted sbf blocks to specified archive's directory name. (full or relative (@sbf_ifn) path) \
            Default is no archiving.",
        required=False,
        default=None,
        type=str,
    )
    # allow argument completion
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    return args
