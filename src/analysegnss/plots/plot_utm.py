import logging as logging
import os

import numpy as np
import plotly.graph_objects as go
import polars as pl
from matplotlib import cm
from matplotlib.ticker import ScalarFormatter
from plotly.subplots import make_subplots
from rich import print
from rich.console import Console

from analysegnss.plots import discrete_colors as dc
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.plots.plot_fonts import MatplotlibFonts, PlotlyFonts
from analysegnss.rtkpos import rtk_constants as rtkc
from analysegnss.sbf import sbf_constants as sbfc


def plot_utm_scatter(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    logger: logging.Logger = None,
    display: bool = False,
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
        with pl.Config(
            tbl_cols=-1, float_precision=3, tbl_cell_numeric_alignment="RIGHT"
        ):
            logger.info(f"utm_df = \n{utm_df}")

    # get the correct column names according to the origin
    cols = get_utm_columns(origin)

    # get the common fonts to use in the plot
    plot_fonts = PlotlyFonts()

    # create a figure
    fig = go.Figure()

    for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
        fig.add_trace(
            go.Scatter(
                x=qual_data[cols.east],
                y=qual_data[cols.north],
                mode="markers",
                name=f"{cols.quality_mapping.quality_dict[qual]['desc']}",
                marker=dict(
                    color=cols.quality_mapping.quality_dict[qual]["color"], size=1
                ),
            )
        )

    fig.update_layout(
        plot_bgcolor="white",
        font=dict(color="#909497"),  # , size=14),
        title=dict(text=f"{fn} - {origin}"),  # , font=dict(size=18)),
        xaxis=dict(
            title=cols.east,
            linecolor="#909497",
            # tickfont=dict(size=8),
            tickformat=",.2f",
            showgrid=True,
            gridwidth=0.5,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            title=cols.north,
            linecolor="#909497",
            # tickfont=dict(size=8),
            tickformat=",.2f",
            showgrid=True,
            gridwidth=0.5,
            gridcolor="lightgray",
        ),
        # margin=dict(t=100, r=80, b=80, l=120),
        height=600,
        width=1024,
        legend=dict(itemsizing="constant", itemwidth=30),  # , font=dict(size=8)),
    )

    # Apply standard fonts
    plot_fonts.apply_fonts(fig)

    if display:
        fig.show()

    # get from the title the name of the station and its directory
    # and save the plot in the sub-directory 'plots'
    # if the directory does not exist, create it
    if not os.path.exists(os.path.join(dir_fn, "plots")):
        os.makedirs(os.path.join(dir_fn, "plots"))

    fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_scatter.pdf")
    # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_scatter.html")
    # create a console logger
    console = Console()
    with console.status(f"Saving plot to {fn_plot}", spinner="point"):
        fig.write_image(fn_plot, width=1024, height=600)
        # fig.write_html(fn_plot)
    print(f"Plot saved to {fn_plot}")


def plot_utm_height(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    sd: bool = False,
    logger: logging.Logger = None,
    display: bool = False,
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

    # get the correct column names according to the origin
    cols = get_utm_columns(origin)

    # get the common fonts to use in the plot
    plot_fonts = PlotlyFonts()

    # create the colors used for the coordinates
    colors = dc.plotly_discrete_colors(n_colors=3)
    # Convert to Plotly color format
    enu_colors = [
        f"rgb({int(255*r)}, {int(255*g)}, {int(255*b)})" for r, g, b, _ in colors
    ]
    alpha = 0.75
    enu_colors_transparent = [
        f"rgba({int(255*r)}, {int(255*g)}, {int(255*b)}, {alpha})"
        for r, g, b, _ in colors
    ]

    # Create the subplot structure
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
    # Add traces for each column
    for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):

        fig.add_trace(
            go.Scatter(
                x=qual_data[cols.time].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=qual_data[cols.north],
                mode="markers",
                marker=dict(
                    color=cols.quality_mapping.quality_dict[qual]["color"], size=1
                ),
                name=f"{cols.quality_mapping.quality_dict[qual]['desc']}",
                showlegend=True,
                error_y=(
                    dict(
                        type="data",
                        array=qual_data[cols.sdn],
                        visible=True,
                        color=cols.quality_mapping.quality_dict[qual]["color"],
                        thickness=0,
                        width=0.5,
                    )
                    if sd
                    else None
                ),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=qual_data[cols.time].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=qual_data[cols.east],
                mode="markers",
                marker=dict(
                    color=cols.quality_mapping.quality_dict[qual]["color"], size=1
                ),
                showlegend=False,
                error_y=(
                    dict(
                        type="data",
                        array=qual_data[cols.sde],
                        visible=True,
                        color=cols.quality_mapping.quality_dict[qual]["color"],
                        thickness=0,
                        width=0.5,
                    )
                    if sd
                    else None
                ),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=qual_data[cols.time].dt.strftime("%Y-%m-%d %H:%M:%S"),
                y=qual_data[cols.height],
                mode="markers",
                marker=dict(
                    color=cols.quality_mapping.quality_dict[qual]["color"], size=1
                ),
                showlegend=False,
                error_y=(
                    dict(
                        type="data",
                        array=qual_data[cols.sdu],
                        visible=True,
                        color=cols.quality_mapping.quality_dict[qual]["color"],
                        thickness=0,
                        width=0.5,
                    )
                    if sd
                    else None
                ),
            ),
            row=3,
            col=1,
        )

    # Update layout for better visualization
    fig.update_layout(
        height=600,  # Taller figure to accommodate 3 subplots
        width=1024,
        showlegend=True,
        plot_bgcolor="white",
        title=dict(text=f"{fn} - {origin}"),  # , font=dict(size=18)),
        yaxis_tickformat=",.2f",
        yaxis2_tickformat=",.2f",
        yaxis3_tickformat=",.2f",
        xaxis_showgrid=True,
        xaxis2_showgrid=True,
        xaxis3_showgrid=True,
        yaxis_showgrid=True,
        yaxis2_showgrid=True,
        yaxis3_showgrid=True,
        xaxis_gridwidth=0.5,
        xaxis2_gridwidth=0.5,
        xaxis3_gridwidth=0.5,
        yaxis_gridwidth=0.5,
        yaxis2_gridwidth=0.5,
        yaxis3_gridwidth=0.5,
        xaxis_gridcolor="lightgray",
        xaxis2_gridcolor="lightgray",
        xaxis3_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        yaxis2_gridcolor="lightgray",
        yaxis3_gridcolor="lightgray",
        legend=dict(itemsizing="constant", itemwidth=30),
    )

    # Update axes labels
    fig.update_yaxes(title_text=cols.north, row=1, col=1)  # , tickfont=dict(size=8))
    fig.update_yaxes(title_text=cols.east, row=2, col=1)  # , tickfont=dict(size=8))
    fig.update_yaxes(title_text=cols.height, row=3, col=1)  # , tickfont=dict(size=8))
    fig.update_xaxes(title_text=cols.time, row=3, col=1)  # , tickfont=dict(size=8))

    # Apply standard fonts
    plot_fonts.apply_fonts(fig)

    if display:
        fig.show()

    # get from the title the name of the station and its directory
    # and save the plot in the sub-directory 'plots'
    # if the directory does not exist, create it
    if not os.path.exists(os.path.join(dir_fn, "plots")):
        os.makedirs(os.path.join(dir_fn, "plots"))

    # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}.svg")
    # fig.write_image(fn_plot, width=1024, height=600)

    if not sd:
        fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu.pdf")
        # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu.html")
        # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu.svg")
    else:
        fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu_sd.pdf")
        # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu_sd.html")
        # fn_plot = os.path.join(dir_fn, "plots", f"{fn.replace('.', '_')}_enu_sd.svg")

    # create a console logger
    console = Console()
    with console.status(f"Saving plot to {fn_plot}", spinner="point"):
        fig.write_image(fn_plot, width=1024, height=600)
        # fig.write_html(fn_plot)
    print(f"Plot saved to {fn_plot}")


import os

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns


def plot_utm_scatter_mpl(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    logger: logging.Logger = None,
    display: bool = False,
) -> None:

    # get the columns used in the UTM dataframe
    cols = get_utm_columns(origin)

    plt.style.use("tableau-colorblind10")

    fig, ax = plt.subplots(figsize=(12, 8))

    # get the custom used fonts
    plot_fonts = MatplotlibFonts()

    # Calculate the range of data
    x_min, x_max = utm_df[cols.east].min(), utm_df[cols.east].max()
    y_min, y_max = utm_df[cols.north].min(), utm_df[cols.north].max()
    plot_range = max(x_max - x_min, y_max - y_min)

    # Define base intervals for tick values
    base_intervals = [
        0.1,
        0.2,
        0.5,
        1,
        2,
        5,
        10,
        20,
        50,
        100,
        200,
        500,
        1000,
        2000,
        5000,
    ]

    # Find appropriate interval that gives about 5-7 grid lines
    target_lines = 7
    tick_spacing = min(base_intervals, key=lambda x: abs(plot_range / x - target_lines))

    # Calculate ticks using the selected base interval
    x_start = np.floor(x_min / tick_spacing) * tick_spacing
    x_end = np.ceil(x_max / tick_spacing) * tick_spacing
    y_start = np.floor(y_min / tick_spacing) * tick_spacing
    y_end = np.ceil(y_max / tick_spacing) * tick_spacing

    x_ticks = np.arange(x_start, x_end + tick_spacing, tick_spacing)
    y_ticks = np.arange(y_start, y_end + tick_spacing, tick_spacing)

    for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
        ax.scatter(
            qual_data[cols.east],
            qual_data[cols.north],
            s=0.2,
            c=[cols.quality_mapping.quality_dict[qual]["color"]],
            label=f"{cols.quality_mapping.quality_dict[qual]['desc']}",
            alpha=0.6,
        )

    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)

    # Lock in the exact limits
    ax.set_xlim(x_ticks[0], x_ticks[-1])
    ax.set_ylim(y_ticks[0], y_ticks[-1])

    # Ensure autoscaling is off
    ax.autoscale(enable=False)

    ax.set_xlabel(cols.east)
    ax.set_ylabel(cols.north)
    ax.set_title(f"{fn} - {origin}")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.set_aspect("equal")

    ax.ticklabel_format(style="plain", useOffset=False)

    legend = ax.legend(markerscale=8, loc="best")

    # apply the MatplotlibFonts to the figure and axes
    plot_fonts.apply_fonts(fig, ax)

    plt.tight_layout()

    if display:
        plt.show()

    plots_dir = os.path.join(dir_fn, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    fn_plot = os.path.join(plots_dir, f"{fn.replace('.', '_')}_scatter_mpl.png")
    fig.savefig(fn_plot, bbox_inches="tight", dpi=300)
    print(f"Plot saved to {fn_plot}")

    plt.close(fig)


def plot_utm_height_mpl(
    utm_df: pl.DataFrame,
    origin: str,
    fn: str,
    dir_fn: str,
    sd: bool = False,
    logger: logging.Logger = None,
    display: bool = False,
) -> None:
    """Plot UTM North, East and height vs time using matplotlib

    Args:
        utm_df (pl.DataFrame): df with coordinates, standard deviation and time
        origin (str): origin of the plot ('RTK' or 'PPK' or 'gLAB')
        fn (str): name of file used
        dir_fn (str): directory of the file
        sd (bool): display the standard deviation if true
        logger (logging.Logger, optional): logger. Defaults to None.
        display (bool, optional): show plot. Defaults to False.
    """
    # Get the correct column names according to the origin
    cols = get_utm_columns(origin)

    # Get the custom fonts
    plot_fonts = MatplotlibFonts()

    # Create figure with three subplots sharing x-axis
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Plot data for each quality level
    for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
        color = cols.quality_mapping.quality_dict[qual]["color"]
        label = cols.quality_mapping.quality_dict[qual]["desc"]

        times = qual_data[cols.time].to_list()
        north = qual_data[cols.north].to_list()
        east = qual_data[cols.east].to_list()
        height = qual_data[cols.height].to_list()

        if sd:
            # Standard deviation bands
            sdn = qual_data[cols.sdn].to_list()
            sde = qual_data[cols.sde].to_list()
            if qual == 1:
                sdu = (qual_data[cols.sdu] * 100).to_list()
            else:
                sdu = (qual_data[cols.sdu]).to_list()

            # Plot error bars instead of fill_between
            ax1.errorbar(
                times, north, yerr=sdn, fmt="none", c="gray", alpha=0.05, capsize=0.1
            )
            ax2.errorbar(
                times, east, yerr=sde, fmt="none", c="gray", alpha=0.05, capsize=0.1
            )
            ax3.errorbar(
                times, height, yerr=sdu, fmt="none", c="gray", alpha=0.05, capsize=0.1
            )

        # Plot points only for each component
        ax1.plot(
            times,
            north,
            marker=".",
            c=color,
            ms=3,
            label=label,
            alpha=1,
            linestyle="None",
        )
        ax2.plot(times, east, marker=".", c=color, ms=3, alpha=1, linestyle="None")
        ax3.plot(times, height, marker=".", c=color, ms=3, alpha=1, linestyle="None")

        # ax1.fill_between(
        #     times,
        #     [n - s for n, s in zip(north, sdn)],
        #     [n + s for n, s in zip(north, sdn)],
        #     color=color,
        #     alpha=0.2,
        # )
        # ax2.fill_between(
        #     times,
        #     [e - s for e, s in zip(east, sde)],
        #     [e + s for e, s in zip(east, sde)],
        #     color=color,
        #     alpha=0.2,
        # )
        # ax3.fill_between(
        #     times,
        #     [h - s for h, s in zip(height, sdu)],
        #     [h + s for h, s in zip(height, sdu)],
        #     color=color,
        #     alpha=0.2,
        # )
    # for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
    #     color = cols.quality_mapping.quality_dict[qual]["color"]
    #     label = cols.quality_mapping.quality_dict[qual]["desc"]

    #     times = qual_data[cols.time].to_list()
    #     north = qual_data[cols.north].to_list()
    #     east = qual_data[cols.east].to_list()
    #     height = qual_data[cols.height].to_list()

    #     # Plot North component with SD
    #     ax1.scatter(times, north, c=color, s=1, label=label, alpha=0.6)
    #     if sd:
    #         sdn = qual_data[cols.sdn].to_list()
    #         ax1.fill_between(
    #             times,
    #             [n - s for n, s in zip(north, sdn)],
    #             [n + s for n, s in zip(north, sdn)],
    #             color=color,
    #             alpha=0.2,
    #         )

    #     # Plot East component with SD
    #     ax2.scatter(times, east, c=color, s=1, alpha=0.6)
    #     if sd:
    #         sde = qual_data[cols.sde].to_list()
    #         ax2.fill_between(
    #             times,
    #             [e - s for e, s in zip(east, sde)],
    #             [e + s for e, s in zip(east, sde)],
    #             color=color,
    #             alpha=0.2,
    #         )

    #     # Plot Height component with SD
    #     ax3.scatter(times, height, c=color, s=1, alpha=0.6)
    #     if sd:
    #         sdu = qual_data[cols.sdu].to_list() * 10000
    #         ax3.fill_between(
    #             times,
    #             [h - s for h, s in zip(height, sdu)],
    #             [h + s for h, s in zip(height, sdu)],
    #             color=color,
    #             alpha=0.2,
    #         )

    # for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
    #     color = cols.quality_mapping.quality_dict[qual]["color"]
    #     label = cols.quality_mapping.quality_dict[qual]["desc"]

    #     print(f"Data shape before conversion: {qual_data.shape}")
    #     print(f"Columns available: {qual_data.columns}")

    #     # Convert to list first for safer handling
    #     times = qual_data[cols.time].to_list()
    #     north = qual_data[cols.north].to_list()

    #     ax1.scatter(times, north, c=color, s=1, label=label, alpha=0.6)

    #     # times = qual_data[cols.time].to_numpy()
    #     # north = qual_data[cols.north].to_numpy()

    #     # print(
    #     #     f"Processing North - times shape: {times.shape}, north shape: {north.shape}"
    #     # )
    #     # try:
    #     #     ax1.scatter(times, north, c=color, s=1, label=label, alpha=0.6)
    #     #     print("North scatter completed successfully")
    #     # except Exception as e:
    #     #     print(f"Error in North scatter: {e}")
    #     #     raise

    #     # # North plot
    #     # ax1.scatter(times, qual_data[cols.north], c=color, s=1, label=label, alpha=0.6)
    #     # if sd:
    #     #     ax1.fill_between(
    #     #         times,
    #     #         qual_data[cols.north] - qual_data[cols.sdn],
    #     #         qual_data[cols.north] + qual_data[cols.sdn],
    #     #         color=color,
    #     #         alpha=0.2,
    #     #     )

    #     # Convert to list first for safer handling
    #     times = qual_data[cols.time].to_list()
    #     east = qual_data[cols.east].to_list()

    #     ax2.scatter(times, east, c=color, s=1, label=label, alpha=0.6)

    #     # print(f"type(times) = {type(times)}")
    #     # print(f"times = {times}")
    #     # print(f"qual_data[cols.east] = {qual_data[cols.east]}")
    #     # print(f"East data: times={len(times)}, east={len(qual_data[cols.east])}")
    #     # # East plot
    #     # ax2.scatter(times, qual_data[cols.east], c=color, s=1, alpha=0.6)
    #     # if sd:
    #     #     ax2.fill_between(
    #     #         times,
    #     #         qual_data[cols.east] - qual_data[cols.sde],
    #     #         qual_data[cols.east] + qual_data[cols.sde],
    #     #         color=color,
    #     #         alpha=0.2,
    #     #     )

    #     # Convert to list first for safer handling
    #     times = qual_data[cols.time].to_list()
    #     height = qual_data[cols.height].to_list()

    #     ax3.scatter(times, height, c=color, s=1, label=label, alpha=0.6)

    #     # print(f"type(times) = {type(times)}")
    #     # print(f"times = {times}")
    #     # print(f"qual_data[cols.height] = {qual_data[cols.height]}")
    #     # print(f"Height data: times={len(times)}, height={len(qual_data[cols.height])}")
    #     # # Height plot
    #     # ax3.scatter(times, qual_data[cols.height], c=color, s=1, alpha=0.6)
    #     # if sd:
    #     #     ax3.fill_between(
    #     #         times,
    #     #         qual_data[cols.height] - qual_data[cols.sdu],
    #     #         qual_data[cols.height] + qual_data[cols.sdu],
    #     #         color=color,
    #     #         alpha=0.2,
    #     # )

    # Configure axes
    ax1.set_ylabel(cols.north)
    ax2.set_ylabel(cols.east)
    ax3.set_ylabel(cols.height)
    ax3.set_xlabel(cols.time)

    # Add grid to all subplots
    for ax in [ax1, ax2, ax3]:
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))

    # Add legend only to first subplot
    ax1.legend(markerscale=8, loc="best")

    # Set title for entire figure
    fig.suptitle(f"{fn} - {origin}")

    # Apply custom fonts
    plot_fonts.apply_fonts(fig, ax1)
    plot_fonts.apply_fonts(fig, ax2)
    plot_fonts.apply_fonts(fig, ax3)

    plt.tight_layout()

    if display:
        plt.show()

    # Create plots directory if it doesn't exist
    plots_dir = os.path.join(dir_fn, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # Save plot
    suffix = "_enu_sd" if sd else "_enu"
    fn_plot = os.path.join(plots_dir, f"{fn.replace('.', '_')}{suffix}_mpl.png")
    fig.savefig(fn_plot, bbox_inches="tight", dpi=300)
    print(f"Plot saved to {fn_plot}")

    plt.close(fig)
