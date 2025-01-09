import random
from typing import Optional

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from matplotlib import cm, colors
from pydantic import BaseModel


class DiscreteColors(BaseModel):
    """
    DiscreteColors creates a color sequence which is consistently repeatable.
    The generated list of colors has maximum 'max_colors' of different values
    """

    cmap: Optional[colors.LinearSegmentedColormap] = cm.get_cmap(
        "hsv"
    )  # colormap, cfr https://matplotlib.org/3.5.0/tutorials/colors/colormaps.html (gist_rainbow, nipy_spectral)
    max_colors: Optional[int] = 37  # max (odd) number of colors in discrete series

    def discrete_color(self, value: int) -> tuple:
        """
        :param value: integer value number of SVs between 1 and 36 included
        """
        while value < 0:
            value = value + self.max_colors
        while value >= self.max_colors:
            value = value - self.max_colors

        # print(f"value = {value}")
        # print(f"max_colors = {self.max_colors}")

        color = self.cmap(value / self.max_colors)
        return color

    class Config:
        arbitrary_types_allowed = True


def plotly_discrete_colors(n_colors: int = 37) -> list:
    """
    plotly_discrete_colors creates a color sequence which is consistently repeatable for use in Plotly graphs.
    The generated list of colors has maximum 'max_colors' of different values
    """
    if n_colors > 3:
        return px.colors.sample_colorscale(
            "turbo", [n / (n_colors - 1) for n in range(n_colors)]
        )
    else:
        # return ["green", "blue", "purple"]
        return [(0, 1, 0, 1), (0, 0, 1, 1), (0.5, 0, 0.5, 1)]


def make_rgb_transparent(rgb, bg_rgb, alpha):
    """
    make a color transparent
    """
    return [alpha * c1 + (1 - alpha) * c2 for (c1, c2) in zip(rgb, bg_rgb)]


def main() -> None:
    my_colors = DiscreteColors()
    # my2_colors = DiscreteColors(cmap=cm.get_cmap('hsv'), max_colors=37)

    for prn in random.sample(range(1, 37), 20):
        print(
            f" my_colors.discrete_color(value={prn:02d}) = "
            f"{my_colors.discrete_color(value=prn)}"
        )
        # print(f"my2_colors.discrete_color(value={prn:02d}) = "
        #       f{my2_colors.discrete_color(value=prn)}")

    enu_colors = DiscreteColors(cmap=cm.get_cmap("gist_rainbow"), max_colors=3)
    for i in range(3):
        print(f"enu_color[{i}] = {enu_colors.discrete_color(i)}")

    # Plotly discrete colors, get a discrete list of colors
    n_colors = [37, 3]
    for i in n_colors:
        go_colors = plotly_discrete_colors(n_colors=i)
        fig = go.Figure()
        for j, c in enumerate(go_colors):
            print(f"c[{j}] = {c}")
            fig.add_bar(x=[j], y=[15], marker_color=c, showlegend=False)
        fig.show()


if __name__ == "__main__":
    main()
