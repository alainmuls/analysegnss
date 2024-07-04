#!/usr/bin/env python

# Import the required modules
import datetime
import os
import sys

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import polars as pl
import seaborn as sns

import globalvars
from sbf.sbf_class import SBF
from utils import argument_parser, init_logger
from utils.utilities import bin_nibble
from sbf import sbf_constants as sbfc


def pvtgeod_analyse(argv: list):
    """
    Convert PVT Geodetic2 SBF block to dataframe and analyse quality of data
    """
    # init the global variables
    globalvars.initialize()

    # parse the CLI arguments
    script_name = os.path.splitext(os.path.basename(__file__))[0]

    args_parsed = argument_parser.argument_parser_sbf(args=argv[1:])
    # print(f"\nParsed arguments: {args_parsed}")

    # create the file/console logger
    logger = init_logger.logger_setup(args=args_parsed, base_name=script_name)
    # # test logger
    # logger.warning(f"Parsed arguments: {args_parsed}")
    # logger.debug(f"program arguments: {args_parsed}")

    # create a SBF class object
    try:
        sbf = SBF(
            sbf_fn=args_parsed.sbf_fn, logger=logger
        )  # start_time=datetime.time(12, 30),
    except Exception as e:
        logger.error(f"Error creating SBF object: {e}")
        sys.exit(1)

    df_geod = sbf.extract_pvtgeodetic2()
    print(f"df_geod.columns = \n{df_geod.columns}")
    print(f"df_geod = \n{df_geod}")
    # print(f"df_geod[1000:1015] = \n{df_geod[1000:1015]}")
    print(
        f"bin_nibble(df_geod[1000]['SignalInfo'][0]) = {bin_nibble(df_geod[1000]['SignalInfo'][0])}"
    )

    # # Create Plotly scatter plot
    # # fig = px.scatter(df_geod, x="UTM.E", y="UTM.N", color="Type")
    # # Show the plot
    # fig.show()

    # create a grouping based on the Type of the positioning
    df = df_geod.groupby("Type")
    print(f"df = \n{df}")
    for pvtmode, pvtdata in df:
        print(f"pvtmode = {pvtmode}, pvtdata = \n{pvtdata}")

    # create a plot
    sns.set_theme()
    # sns.set_style("whitegrid")
    # plot the data
    # fig = df_geod.plot(x="UTM.E", y="UTM.N", kind="scatter", color="Type")
    sns.scatterplot(data=df_geod, x="UTM.E", y="UTM.N", hue="Type")
    # show the plot
    # plt.show()

    # print(f'sbfc.dict_sbf_pvtmode[3]["color"] = {sbfc.dict_sbf_pvtmode[3]}')
    plot = go.Figure(
        data=[
            go.Scatter(
                x=df_geod["UTM.E"],
                y=df_geod["UTM.N"],
                # color=,
                mode="markers",
            )
        ],
    )
    plot.show()

    fig = go.Figure()
    for pvtmode, pvtdata in df:
        fig.add_trace(
            go.Scatter(
                x=pvtdata["UTM.E"],
                y=pvtdata["UTM.N"],
                mode="markers",
                name=f"{sbfc.dict_sbf_pvtmode[pvtmode]['desc']}",
                marker=dict(color=sbfc.dict_sbf_pvtmode[pvtmode]["color"], size=1),
            )
        )

    fig.update_layout(
        plot_bgcolor="white",
        font=dict(color="#909497", size=18),
        title=dict(text="Ocotillo RWY1", font=dict(size=26)),
        xaxis=dict(title="UTM.E", linecolor="#909497"),
        yaxis=dict(title="UTM.N", tickformat=",", linecolor="#909497"),
        margin=dict(t=100, r=80, b=80, l=120),
        height=720,
        width=1280,
    )

    fig.show()


if __name__ == "__main__":
    pvtgeod_analyse(argv=sys.argv)
