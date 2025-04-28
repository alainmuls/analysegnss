#!/usr/bin/env python

# Standard library imports
import argparse
from logging import Logger
import os
import sys

# Third-party imports
from rich import print as rprint
import polars as pl
from tabulate import tabulate

# Local application imports
from analysegnss.config import ERROR_CODES
from analysegnss.gnss.standard_pnt_quality_dict import (
    sbf_to_standard_pntqual,
    get_pntquality_info,
)
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import init_logger
from analysegnss.utils.utilities import combine_dfs, print_df_in_chunks
from analysegnss.utils.argument_parser import (
    argument_parser_rtk,
    auto_populate_args_namespace,
)


def quality_analysis(geod_df: pl.DataFrame, logger: Logger = None) -> list:
    """display the quality analysis

    Args:
        geod_df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = geod_df.shape[0]
    for qual, qual_data in geod_df.group_by(["Type"]):
        qual_analysis.append(
            [
                get_pntquality_info(sbf_to_standard_pntqual(qual[0]))["desc"],
                qual_data.shape[0],
                round(qual_data.shape[0] / total_obs * 100, 2),
                total_obs,
            ]
        )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "PNT Mode Count", "Percentage", "Total Observations"],
        tablefmt="fancy_outline",
    )

    # print the quality analysis
    rprint(f"Quality analysis from sbf PVTGeodetic:\n{qual_tabular}")

    if logger is not None:
        logger.debug(f"Quality analysis:\n{qual_tabular}")

    return qual_analysis


def sbf_reader(parsed_args: argparse.Namespace, logger: Logger) -> dict:
    """
    Convert PVT Geodetic2 SBF block to dataframe and analyse quality of data
    Args:
        argv (list): list of arguments
    Returns:
        dict: dict with dataframe for each selected SBF block
    """
    # Ensure compatibility when passing on parsed_args from a higher level script.
    parsed_args = auto_populate_args_namespace(
        parsed_args,
        argument_parser_rtk,
        os.path.splitext(os.path.basename(__file__))[0],
    )

    logger.debug(f"auto-populated parsed arguments: {parsed_args}")

    # create a SBF class object
    try:
        sbf = SBF(sbf_fn=parsed_args.sbf_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])

    if not parsed_args.sbf2asc:
        if parsed_args.sd:
            # extract the PVT Geodetic2 block from SBF file and its covariance elements
            dfs_pvt = sbf.bin2asc_dataframe(
                lst_sbfblocks=["PVTGeodetic2", "PosCovGeodetic1"],
                archive=parsed_args.archive,
            )

            if "PosCovGeodetic1" in dfs_pvt:
                # drop the rows where the covariances "Cov_latlat [m²]" etc are not available
                dfs_pvt["PosCovGeodetic1"] = (
                    pl.DataFrame(dfs_pvt["PosCovGeodetic1"])
                    .lazy()
                    .filter(
                        ~pl.col("Cov_latlat [m²]").is_null()
                        & ~pl.col("Cov_lonlon [m²]").is_null()
                        & ~pl.col("Cov_hgthgt [m²]").is_null()
                    )
                    .collect()
                )

                dfs_pvt["PosSDgeodetic"] = sbf.convert_Cov2SD(
                    dfs_pvt["PosCovGeodetic1"]
                )
                # remove the covariance matrix from dfs_pvt
                dfs_pvt.pop("PosCovGeodetic1")

            # merge the RTK position dataframes on the DT column
            df_pvt = combine_dfs(dfs_pvt)
            # Drop the column
            if "DT_right" in df_pvt.columns:
                df_pvt = df_pvt.drop("DT_right")

            # return df_pvt, qual_analysis

        else:  # only use the PVTGeodetic, no StdDev required
            # extract the PVT Geodetic2 block from SBF file
            df_pvt = sbf.bin2asc_dataframe(
                lst_sbfblocks=["PVTGeodetic2"], archive=parsed_args.archive
            )["PVTGeodetic2"]

        # fill the null values with NaN
        # df_pvt = df_pvt.fill_null(float('nan')) # -- commented out because it changes the type of all columns to float

        logger.info(print_df_in_chunks(title="df_pvt from SBF", df=df_pvt))
        # analyse the quality of the solution
        qual_analysis = quality_analysis(geod_df=df_pvt, logger=logger)

        return df_pvt, qual_analysis

    else:  # conversion using sbf2asc # TODO: next part not yet finished
        df_pvt = sbf.sbf2asc_dataframe(
            lst_sbfblocks=["PVTGeodetic2"], archive=parsed_args.archive
        )["PVTGeodetic2"]

        # sbf2asc cant read the PosCovGeodetic1 block.Only PosCovCartesian1 is available.
        df_xyz = sbf.sbf2asc_dataframe(
            lst_sbfblocks=["PVTCartesian2"], archive=parsed_args.archive
        )["PVTCartesian2"]
        if parsed_args.sd:
            df_xyzcov = sbf.sbf2asc_dataframe(
                lst_sbfblocks=["PosCovCartesian1"], archive=parsed_args.archive
            )["PosCovCartesian1"]
        else:
            df_xyzcov = None

        if df_xyzcov is not None:
            logger.debug(f"df_xyzcov: \n{df_xyzcov}")

        logger.info(f"df_pvt from sbf2asc PVTGeodetic: \n{df_pvt}")
        logger.info(f"df_xyz from sbf2asc PVTCartesian: \n{df_xyz}")
        if df_xyzcov is not None:
            logger.info(f"df_xyzcov from sbf2asc PosCovCartesian: \n{df_xyzcov}")

        return df_pvt, None


def main():
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    args_parsed = argument_parser_rtk(
        args=sys.argv[1:], script_name=os.path.basename(__file__)
    )

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    df_pvt, qual_analysis = sbf_reader(parsed_args=args_parsed, logger=logger)
    # print the quality analysis
    print(print_df_in_chunks(title="df_pvt from SBF", df=df_pvt))
    if qual_analysis is not None:
        qual_tabular = tabulate(
            qual_analysis,
            headers=["PNT Mode", "Count", "Percentage", "Total Observations"],
            tablefmt="fancy_outline",
        )
        rprint(f"Analysis of the quality of SBF position data:\n{qual_tabular}")


if __name__ == "__main__":
    main()
