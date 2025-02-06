#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 10:46:52 2020
@author: amuls

Examine the CN0 values of a CSV observation file
"""


import logging
import os
import sys

import polars as pl
from rich import print

from analysegnss.config import ERROR_CODES, DICT_GNSS, rich_console
from analysegnss.csv.csv_class import GNSS_CSV
from analysegnss.utils import init_logger
from analysegnss.utils.utilities import str_red
from analysegnss.utils.argument_parser import argument_parser_cn0_daily


def cn0_analyse(argv: list):
    """reads from CSV observation file the CN0 for a selected GNSS and signal type
    at a specified interval and calculate the mean and standard deviation of the CN0 values.

    Args:
        argv (list): CLI arguments
    """
    # get the name of this script for naming the logger
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    # parse the CLI arguments
    args_parsed = argument_parser_cn0_daily(
        args=argv[1:], script_name=os.path.basename(__file__)
    )
    # print(args_parsed)

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    logger.info(f"Parsed arguments: {args_parsed}")

    # create the CSV_OBS object
    try:
        cvs_obs = GNSS_CSV(
            csv_fn=args_parsed.obs_fn,
            GNSS=args_parsed.gnss,
            interval=args_parsed.interval,
            signal_type=args_parsed.sigtype,
            logger=logger,
        )
    except ValueError as e:
        logger.error(f"Error: {str_red(e)}")
        sys.exit(ERROR_CODES["E_FAILURE"])

    # print(f"cvs_obs = {cvs_obs}")

    # read the CSV file in a polars DataFrame
    with rich_console.status("Reading CSV file...", spinner="aesthetic"):
        df_cn0 = cvs_obs.csv_gnss_sigt_df()
        # keep only the CN0 (S) column
        df_cn0 = df_cn0.lazy().drop(["C", "L", "D"]).collect()

    # print the DataFrame
    print(f"df_cn0 = {df_cn0}")

    # Group by epoch and calculate CN0 statistics
    df_mean_cn0 = (
        df_cn0.group_by(["WKNR", "TOW"])
        .agg(
            [
                pl.col("S").mean().alias("mean_cn0"),
                pl.col("PRN").count().alias("num_prns"),
            ]
        )
        .sort(["WKNR", "TOW"])
    )

    print((f"df_mean_cn0 = {df_mean_cn0}"))

    # # Ensure both dataframes have the same time columns
    # df_all_cn0 = df_cn0.join(
    #     df_mean_cn0,
    #     on=["WKNR", "TOW"],
    #     how="inner",  # This ensures we only keep matching rows
    # ).sort(
    #     ["WKNR", "TOW"]
    # )  # Keep everything nicely ordered
    # print((f"df_all_cn0 = {df_all_cn0}"))

    # TEST START
    import matplotlib

    matplotlib.use("TkAgg")  # or 'Agg' for non-interactive plots
    import matplotlib.pyplot as plt

    plt.style.use("tableau-colorblind10")

    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot CN0 data on primary axis
    ax1.scatter(
        df_cn0["TOW"], df_cn0["S"], alpha=0.3, label="Individual CN0", color="gray"
    )
    ax1.plot(
        df_mean_cn0["TOW"], df_mean_cn0["mean_cn0"], "r-", linewidth=2, label="Mean CN0"
    )
    ax1.set_xlabel("Time of Week (s)")
    ax1.set_ylabel("CN0 (dB-Hz)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Create secondary axis for number of PRNs
    ax2 = ax1.twinx()
    ax2.plot(
        df_mean_cn0["TOW"],
        df_mean_cn0["num_prns"],
        "b-",
        linewidth=2,
        label="Number of PRNs",
    )
    ax2.set_ylabel("Number of PRNs", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    # Add title and grid
    plt.title(
        f"CN0 Values and Number of PRNs Over Time - {DICT_GNSS[args_parsed.gnss]["name"]}"
        f" {args_parsed.sigtype}"
    )
    ax1.grid(True)

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    plt.show()
    # EOF TEST

    return df_cn0


def main():
    return cn0_analyse(argv=sys.argv)


if __name__ == "__main__":
    main()
