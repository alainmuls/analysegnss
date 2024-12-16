#!/usr/bin/env python

import os
import sys

import polars as pl
from tabulate import tabulate

from analysegnss.config import ERROR_CODES
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.sbf.sbf_class import SBF
from analysegnss.utils import argument_parser, init_logger
from analysegnss.utils.utilities import combine_dfs


def quality_analysis(geod_df: pl.DataFrame, logger) -> None:
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
                    f"{qual_data.shape[0]/total_obs*100:.2f}",
                ]
            )

    qual_tabular = tabulate(
        qual_analysis,
        headers=["PNT Mode", "Count", "Percentage"],
        tablefmt="fancy_outline",
    )
    print(f"\nAnalysis of the quality of the position data\n{qual_tabular}")

    if logger is not None:
        logger.warning(f"Quality analysis:\n{qual_tabular}")


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

    args_parsed = argument_parser.argument_parser_rtk(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(
            sbf_fn=args_parsed.sbf_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(ERROR_CODES["E_SBF_OBJECT"])

    if not args_parsed.sbf2asc:
        if args_parsed.sd:
            # extract the PVT Geodetic2 block from SBF file and its covariance elements
            dfs_pvt = sbf.bin2asc_dataframe(
                lst_sbfblocks=["PVTGeodetic2", "PosCovGeodetic1"]
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
            # with pl.Config(
            #     tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
            # ):
            #     print(f"[bold green]{df_pvt}")

        else:  # only use the PVTGeodetic, no StdDev required
            # extract the PVT Geodetic2 block from SBF file
            df_pvt = sbf.bin2asc_dataframe(lst_sbfblocks=["PVTGeodetic2"])[
                "PVTGeodetic2"
            ]

        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            logger.info(f"  df_pvt: \n{df_pvt}")

        # analyse the quality of the solution
        quality_analysis(geod_df=df_pvt, logger=logger)

        return df_pvt

    else:  # conversion using sbf2asc
        df_poscov = sbf.sbf2asc_dataframe(lst_sbfblocks=["PosCovGeodetic1"])[
            "PosCovGeodetic1"
        ]
        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            print(f"df_poscov: \n{df_poscov}")
            logger.info(f"df_poscov: \n{df_poscov}")

        return None


def main():
    geod_df = rtk_pvtgeod(argv=sys.argv)


if __name__ == "__main__":
    main()
