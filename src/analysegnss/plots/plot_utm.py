import logging as logging
import os

import numpy as np
import plotly.graph_objects as go
import polars as pl
from matplotlib import cm
from plotly.subplots import make_subplots
from rich import print
from rich.console import Console

from analysegnss.plots import discrete_colors as dc
from analysegnss.plots.plot_columns import get_utm_columns
from analysegnss.plots.plot_fonts import PlotlyFonts, MatplotlibFonts
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

# def plot_utm_scatter_mpl(
#     utm_df: pl.DataFrame,
#     origin: str,
#     fn: str,
#     dir_fn: str,
#     logger: logging.Logger = None,
#     display: bool = False,
# ) -> None:

#     # Get the correct column names according to the origin
#     cols = get_utm_columns(origin)

#     # Set the style
#     # plt.style.use("seaborn")
#     plt.style.use("tableau-colorblind10")

#     # Create figure and axis
#     fig, ax = plt.subplots(figsize=(12, 8))

#     # Plot each quality group
#     for qual, qual_data in utm_df.groupby(cols.quality_mapping.columns):
#         ax.scatter(
#             qual_data[cols.east],
#             qual_data[cols.north],
#             s=0.3,  # marker size
#             c=[cols.quality_mapping.quality_dict[qual]["color"]],
#             label=f"{cols.quality_mapping.quality_dict[qual]['desc']}",
#             alpha=0.6,
#         )

#     # Calculate grid spacing based on data range
#     x_range = utm_df[cols.east].max() - utm_df[cols.east].min()
#     y_range = utm_df[cols.north].max() - utm_df[cols.north].min()
#     grid_spacing = min(x_range, y_range) / 5  # 5 grid lines in the smaller dimension

#     # Set grid with equal spacing
#     ax.set_xticks(
#         np.arange(utm_df[cols.east].min(), utm_df[cols.east].max(), grid_spacing)
#     )
#     ax.set_yticks(
#         np.arange(utm_df[cols.north].min(), utm_df[cols.north].max(), grid_spacing)
#     )

#     # Customize the plot
#     ax.set_xlabel(cols.east)
#     ax.set_ylabel(cols.north)
#     ax.set_title(f"{fn} - {origin}")
#     ax.grid(True, linestyle="--", alpha=0.7)
#     ax.set_aspect("equal")

#     # Format axis with scientific notation
#     ax.ticklabel_format(style="plain", useOffset=False)

#     # Add legend
#     ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", markerscale=8)

#     # Adjust layout to prevent label cutoff
#     plt.tight_layout()

#     if display:
#         plt.show()

#     # Create plots directory if it doesn't exist
#     plots_dir = os.path.join(dir_fn, "plots")
#     os.makedirs(plots_dir, exist_ok=True)

#     # Save the plot
#     fn_plot = os.path.join(plots_dir, f"{fn.replace('.', '_')}_scatter_mpl.png")
#     fig.savefig(fn_plot, bbox_inches="tight", dpi=300)
#     print(f"Plot saved to {fn_plot}")

#     # Close the figure to free memory
#     plt.close(fig)


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
