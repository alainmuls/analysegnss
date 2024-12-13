from utils import discrete_colors

# get a discrete list of colors
n_colors = 37
prn_colors = discrete_colors.plotly_discrete_colors(n_colors=n_colors)

#                       paper_bgcolor='white', plot_bgcolor='white',
# from matplotlib import cm, colors
#     DiscreteColors creates a color sequence which is consistently repeatable.
#     The generated list of colors has maximum 'max_colors' of different values
#     cmap: Optional[colors.LinearSegmentedColormap] = cm.get_cmap('hsv')  # colormap, cfr https://matplotlib.org/3.5.0/tutorials/colors/colormaps.html (gist_rainbow, nipy_spectral)
#     max_colors: Optional[int] = 37   # max (odd) number of colors in discrete series
#     def discrete_color(self, value: int) -> tuple:
#             value = value + self.max_colors
#         while value >= self.max_colors:
#             value = value - self.max_colors
#         # print(f"max_colors = {self.max_colors}")
#         color = self.cmap(value / self.max_colors)
#         return color

#     enu_colors = DiscreteColors(cmap=cm.get_cmap('gist_rainbow'), max_colors=3)
#         print(f"enu_color[{i}] = {enu_colors.discrete_color(i)}")


def make_rgb_transparent(rgb, bg_rgb, alpha):
    """
    make a color transparent
    """
    return [alpha * c1 + (1 - alpha) * c2 for (c1, c2) in zip(rgb, bg_rgb)]


def make_rgb_transparent(rgb, bg_rgb, alpha):
    """
    make a color transparent
    """
    return [alpha * c1 + (1 - alpha) * c2 for (c1, c2) in zip(rgb, bg_rgb)]
