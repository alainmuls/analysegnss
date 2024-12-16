from dataclasses import dataclass


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
