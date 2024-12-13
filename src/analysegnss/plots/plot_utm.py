import logging as logging
import os

import plotly.graph_objects as go
import polars as pl
from matplotlib import cm
from plotly.subplots import make_subplots
from rich import print
from rich.console import Console

from analysegnss.plots import discrete_colors as dc
from analysegnss.rtkpos import rtk_constants as rtkc
from analysegnss.sbf import sbf_constants as sbfc


def plot_utm_scatter(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    logger: logging.Logger = None,
) -> None:
    """
    Plots the UTM (North vs East) coordinates from a Polars DataFrame.

    Args:
        utm_df (pl.DataFrame): Polars DataFrame containing the UTM coordinates.
        origin (str): Origin of the plot ('RTK' or 'PPK').
        fn (str): name of file used
        dir_fn (str): directory of the file
        logger (logging.Logger): Logger object for logging.
    Returns:
        None
    """
    if logger is not None:
        logger.info(f"utm_df = \n{utm_df}")

    fig = go.Figure()

    if origin == "RTK":
        for pvtmode, pvtdata in utm_df.groupby("Type"):
            fig.add_trace(
                go.Scatter(
                    x=pvtdata["UTM.E"],
                    y=pvtdata["UTM.N"],
                    mode="markers",
                    name=f"{sbfc.dict_sbf_pvtmode[pvtmode]['desc']}",
                    marker=dict(color=sbfc.dict_sbf_pvtmode[pvtmode]["color"], size=1),
                )
            )

    elif origin == "PPK":
        for qual, qual_data in utm_df.groupby("Q"):
            fig.add_trace(
                go.Scatter(
                    x=qual_data["UTM.E"],
                    y=qual_data["UTM.N"],
                    mode="markers",
                    name=f"{rtkc.dict_rtk_pvtmode[qual]['desc']}",
                    marker=dict(color=rtkc.dict_rtk_pvtmode[qual]["color"], size=1),
                )
            )

    fig.update_layout(
        plot_bgcolor="white",
        font=dict(color="#909497", size=18),
        title=dict(text=fn, font=dict(size=22)),
        xaxis=dict(title="UTM.E", linecolor="#909497"),
        yaxis=dict(title="UTM.N", tickformat=",", linecolor="#909497"),
        margin=dict(t=100, r=80, b=80, l=120),
        height=720,
        width=1280,
        legend=dict(itemsizing="constant", itemwidth=30),
    )

    # fig.show()

    # get from the title the name of the station and its directory
    # and save the plot in the sub-directory 'plots'
    # if the directory does not exist, create it
    if not os.path.exists(os.path.join(dir_fn, "plots")):
        os.makedirs(os.path.join(dir_fn, "plots"))

    # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}.svg")
    # fig.write_image(fn_plot, width=1280, height=720)

    fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_scatter.png")
    # create a console logger
    console = Console()
    with console.status(f"Saving plot to {fn_plot}", spinner="point"):
        fig.write_image(fn_plot, width=1280, height=720)
    print(f"Plot saved to {fn_plot}")


def plot_utm_height(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    sd: bool = False,
    logger: logging.Logger = None,
) -> None:
    """plot the UTM.N,UTM.E and height vs time with display of standard deviation

    Args:
        utm_df (pl.DataFrame): df with coordinates, standard deviation and time
        origin (str): origin of the plot ('RTK' or 'PPK' or 'gLAB').
        fn (str): name of file used
        dir_fn (str): directory of the file
        sd (bool): display the standard deviation if true
        logger (logging.Logger, optional): logger. Defaults to None.
    """
    if logger is not None:
        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            logger.info(f"utm_df = \n{utm_df}")

    # create the colors used for the coordinates
    colors = dc.plotly_discrete_colors(n_colors=3)
    # Convert to Plotly color format
    enu_colors = [
        f"rgb({int(255*r)}, {int(255*g)}, {int(255*b)})" for r, g, b, _ in colors
    ]
    alpha = 0.15
    enu_colors_transparent = [
        f"rgba({int(255*r)}, {int(255*g)}, {int(255*b)}, {alpha})"
        for r, g, b, _ in colors
    ]

    # Create the subplot structure
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

    # Add traces to each subplot and add error bars when asked for
    if not sd:
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["UTM.N"],
                mode="markers",
                marker=dict(color=enu_colors[0], size=1),
                name="UTM.N",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["UTM.E"],
                mode="markers",
                marker=dict(color=enu_colors[1], size=1),
                name="UTM.E",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["orthoH"],
                mode="markers",
                marker=dict(color=enu_colors[2], size=1),
                name="orthoH",
            ),
            row=3,
            col=1,
        )
    else:  # display the standard deviation
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["UTM.N"],
                mode="markers+lines",
                marker=dict(color=enu_colors[0], size=1),
                line=dict(color=enu_colors[0]),
                name="UTM.N",
                error_y=dict(
                    type="data",
                    array=utm_df["sdn(m)"],
                    visible=True,
                    color=enu_colors_transparent[0],
                ),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["UTM.E"],
                mode="markers+lines",
                marker=dict(color=enu_colors[1], size=1),
                line=dict(color=enu_colors[1]),
                name="UTM.E",
                error_y=dict(
                    type="data",
                    array=utm_df["sde(m)"],
                    visible=True,
                    color=enu_colors_transparent[1],
                ),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=utm_df["DT"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=utm_df["orthoH"],
                mode="markers+lines",
                marker=dict(color=enu_colors[2], size=1),
                line=dict(color=enu_colors[2]),
                name="H",
                error_y=dict(
                    type="data",
                    array=utm_df["sdu(m)"],
                    visible=True,
                    color=enu_colors_transparent[2],
                ),
            ),
            row=3,
            col=1,
        )

    # Update layout for better visualization
    fig.update_layout(
        height=720,  # Taller figure to accommodate 3 subplots
        width=1280,
        showlegend=True,
        plot_bgcolor="white",
        title=dict(text=fn, font=dict(size=22)),
    )

    # Update axes labels
    fig.update_yaxes(title_text="UTM.N", row=1, col=1)
    fig.update_yaxes(title_text="UTM.E", row=2, col=1)
    fig.update_yaxes(title_text="Height", row=3, col=1)
    fig.update_xaxes(title_text="Time", row=3, col=1)

    # fig.show()

    # get from the title the name of the station and its directory
    # and save the plot in the sub-directory 'plots'
    # if the directory does not exist, create it
    if not os.path.exists(os.path.join(dir_fn, "plots")):
        os.makedirs(os.path.join(dir_fn, "plots"))

    # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}.svg")
    # fig.write_image(fn_plot, width=1280, height=720)

    if not sd:
        fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu.png")
    else:
        fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu_sd.png")

    # create a console logger
    console = Console()
    with console.status(f"Saving plot to {fn_plot}", spinner="point"):
        fig.write_image(fn_plot, width=1280, height=720)
    print(f"Plot saved to {fn_plot}")
