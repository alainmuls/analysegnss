#!/usr/bin/env python

# Standard library imports
from logging import Logger
import os
import sys

# Third-party imports
import polars as pl
from tabulate import tabulate

# Local application imports
from analysegnss.config import ERROR_CODES
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import init_logger
from analysegnss.utils.utilities import combine_dfs
from analysegnss.utils.argument_parser import argument_parser_rtk


def quality_analysis(geod_df: pl.DataFrame, logger: Logger = None) -> list:
    """display the quality analysis

    Args:
        df (pl.DataFrame): dataframe containing the RTK solution
        logger (_type_): logger object
    """
    # analysis of the quality of the position data
    qual_analysis = []
    total_obs = geod_df.shape[0]
    for qual, qual_data in geod_df.group_by("Type"):
        if qual in sbfc.DICT_SBF_PVTMODE:
            qual_analysis.append(
                [
                    sbfc.DICT_SBF_PVTMODE[qual]["desc"],
                    qual_data.shape[0],
                    round(qual_data.shape[0] / total_obs * 100, 2),
                ]
            )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "Count", "Percentage"],
        tablefmt="fancy_outline",
    )

    if logger is not None:
        logger.debug(f"Quality analysis:\n{qual_tabular}")

    return qual_analysis


def rtk_pvtgeod(argv: list) -> dict:
    """
    Convert PVT Geodetic2 SBF block to dataframe and analyse quality of data
    Args:
        argv (list): list of arguments
    Returns:
        dict: dict with dataframe for each selected SBF block
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    args_parsed = argument_parser_rtk(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.debug(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(sbf_fn=args_parsed.sbf_ifn, logger=logger)
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])

    if not args_parsed.sbf2asc:
        if args_parsed.sd:
            # extract the PVT Geodetic2 block from SBF file and its covariance elements
            dfs_pvt = sbf.bin2asc_dataframe(
                lst_sbfblocks=["PVTGeodetic2", "PosCovGeodetic1"],
                archive=args_parsed.archive,
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

        else:  # only use the PVTGeodetic, no StdDev required
            # extract the PVT Geodetic2 block from SBF file
            df_pvt = sbf.bin2asc_dataframe(
                lst_sbfblocks=["PVTGeodetic2"], archive=args_parsed.archive
            )["PVTGeodetic2"]

        # fill the null values with NaN
        df_pvt = df_pvt.fill_null(float('nan'))
        logger.info(f"  df_pvt: \n{df_pvt}")

        # analyse the quality of the solution
        quality_analysis(geod_df=df_pvt, logger=logger)

        return df_pvt

    else:  # conversion using sbf2asc
        df_pvt = sbf.sbf2asc_dataframe(
            lst_sbfblocks=["PVTGeodetic2"], archive=args_parsed.archive
        )["PVTGeodetic2"]

        # sbf2asc cant read the PosCovGeodetic1 block.Only PosCovCartesian1 is available.
        df_xyz = sbf.sbf2asc_dataframe(
            lst_sbfblocks=["PVTCartesian2"], archive=args_parsed.archive
        )["PVTCartesian2"]
        if args_parsed.sd:
            df_xyzcov = sbf.sbf2asc_dataframe(
                lst_sbfblocks=["PosCovCartesian1"], archive=args_parsed.archive
            )["PosCovCartesian1"]
        else:
            df_xyzcov = None

        logger.info(f"df_pvt: \n{df_pvt}")
        logger.info(f"df_xyz: \n{df_xyz}")
        if df_xyzcov is not None:
            logger.info(f"df_xyzcov: \n{df_xyzcov}")

        return df_pvt


def main():
    geod_df = rtk_pvtgeod(argv=sys.argv)


if __name__ == "__main__":
    main()
