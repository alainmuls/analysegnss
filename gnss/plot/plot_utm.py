import matplotlib.pyplot as plt
import plotly.graph_objects as go
import polars as pl

from sbf import sbf_constants as sbfc
from rtkpos import rtk_constants as rtkc


def plot_utm_coords(utm_df: pl.DataFrame, origin: str, title: str) -> None:
    """plots the UTM (North vs East) coordinates

    Args:
        utm_df (pl.Dataframe): polar dataframe containing the UTM coordinates
        origin (str): Origin of the plot ('PVTGeodetic' or 'RTKPos')
        title (str): Title of the plot
    """
    print(f"utm_df = \n{utm_df}")

    fig = go.Figure()

    if origin == "PVTGeodetic":
        for pvtmode, pvtdata in utm_df:
            fig.add_trace(
                go.Scatter(
                    x=pvtdata["UTM.E"],
                    y=pvtdata["UTM.N"],
                    mode="markers",
                    name=f"{sbfc.dict_sbf_pvtmode[pvtmode]['desc']}",
                    marker=dict(color=sbfc.dict_sbf_pvtmode[pvtmode]["color"], size=1),
                )
            )
    elif origin == "RTKPos":
        for qual, qual_data in utm_df.groupby("Q"):
            fig.add_trace(
                go.Scatter(
                    x=qual_data["UTM.E(m)"],
                    y=qual_data["UTM.N(m)"],
                    mode="markers",
                    name=f"{rtkc.dict_rtk_pvtmode[qual]['desc']}",
                    marker=dict(color=rtkc.dict_rtk_pvtmode[qual]["color"], size=1),
                )
            )

    fig.update_layout(
        plot_bgcolor="white",
        font=dict(color="#909497", size=18),
        title=dict(text=title, font=dict(size=26)),
        xaxis=dict(title="UTM.E", linecolor="#909497"),
        yaxis=dict(title="UTM.N", tickformat=",", linecolor="#909497"),
        margin=dict(t=100, r=80, b=80, l=120),
        height=720,
        width=1280,
    )

    fig.show()
