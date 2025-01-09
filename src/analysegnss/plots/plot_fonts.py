from dataclasses import dataclass

import matplotlib.pyplot as plt


@dataclass
class PlotlyFonts:
    title_font = dict(family="sans-serif", size=12, color="black")

    axis_font = dict(family="sans-serif", size=10, color="black")

    tick_font = dict(family="sans-serif", size=8, color="black")

    legend_font = dict(family="sans-serif", size=8, color="black")

    def apply_fonts(self, fig):
        """Apply standard fonts to a plotly figure"""
        fig.update_layout(title_font=self.title_font, legend_font=self.legend_font)

        fig.update_xaxes(title_font=self.axis_font, tickfont=self.tick_font)

        fig.update_yaxes(title_font=self.axis_font, tickfont=self.tick_font)


class MatplotlibFonts:
    def __init__(self):
        self.font_family = "Arial"
        self.title_size = 14
        self.axis_label_size = 12
        self.tick_label_size = 10
        self.legend_size = 10
        self.font_color = "#909497"

    def apply_fonts(self, fig, ax):
        """Apply consistent fonts to matplotlib figure and axis"""
        # Title styling
        ax.set_title(
            ax.get_title(), fontsize=self.title_size, color="black", weight="bold"
        )

        # Axis labels styling
        ax.set_xlabel(
            ax.get_xlabel(),
            fontsize=self.axis_label_size,
            color=self.font_color,
            weight="bold",
        )

        ax.set_ylabel(
            ax.get_ylabel(),
            fontsize=self.axis_label_size,
            color=self.font_color,
            weight="bold",
        )

        # Tick labels styling
        ax.tick_params(
            axis="both", labelsize=self.tick_label_size, colors=self.font_color
        )

        # Legend styling
        if ax.get_legend():
            legend = ax.get_legend()
            plt.setp(
                legend.get_texts(), fontsize=self.legend_size, color=self.font_color
            )
