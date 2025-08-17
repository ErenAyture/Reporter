import json
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.patches import Rectangle, Wedge, Patch
from openpyxl.drawing.image import Image as XLImage
from pyproj import Transformer


# ---------------------------------------------------------------------------
#  Core map helper – now paints ONE rect per 50 m grid cell (white outline)
# ---------------------------------------------------------------------------
class Grid50Plot:
    """Self‑contained plotter; identical signature to SpatialKPIDensityPlot
    from *SpatialKPIDensity.py* but with an all‑new ``plot`` method that
    aggregates samples into fixed 50‑metre squares and draws **one**
    rectangle per square with a thin white outline so the grid is obvious.
    """
    def __init__(self, *, bs_lat, bs_lon, azimuth, beamwidth, data_points,
                 kpi_col, kpi_name, kpi_range_dict, extent_km,
                 grid_size: int = 50, radius: int = 100,
                 lon_col: str = "longitude", lat_col: str = "latitude"):
        self.bs_lat = float(bs_lat); self.bs_lon = float(bs_lon)
        self.azimuth = float(azimuth); self.beamwidth = float(beamwidth)
        self.data_points = data_points
        self.kpi_col = kpi_col; self.kpi_name = kpi_name
        self.kpi_range_dict = kpi_range_dict
        self.extent_km = extent_km
        self.grid_size = grid_size; self.radius = radius
        self.lon_col = lon_col; self.lat_col = lat_col

        # project once
        self.proj = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        self.bs_x, self.bs_y = self.proj.transform(self.bs_lon, self.bs_lat)
        xs, ys = self.proj.transform(self.data_points[self.lon_col].values,
                                     self.data_points[self.lat_col].values)
        self.points_proj = list(zip(xs, ys, self.data_points[self.kpi_col].values))

    # .....................................................................
    def plot(self, out: str | None = None):
        """Return an *openpyxl* Image ready for ``ws.add_image``."""
        # aggregate samples → grid dict
        grid: dict[tuple[int,int], list[float]] = {}
        for px, py, kpi_val in self.points_proj:
            if pd.isna(kpi_val):
                continue
            gx = int(self.grid_size * round((px - self.bs_x) / self.grid_size))
            gy = int(self.grid_size * round((py - self.bs_y) / self.grid_size))
            grid.setdefault((gx, gy), []).append(float(kpi_val))

        # ------------------------------------------------------------------
        #  figure base
        # ------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(8, 8))
        km = self.extent_km
        ax.set_xlim(self.bs_x - 500 * km, self.bs_x + 500 * km)
        ax.set_ylim(self.bs_y - 500 * km, self.bs_y + 500 * km)

        # draw grid squares – white outline so they *look like* a grid
        for (gx, gy), vals in grid.items():
            centre_x = self.bs_x + gx
            centre_y = self.bs_y + gy
            median_val = float(np.median(vals))
            colour = self.kpi_range_dict[median_val]
            rect = Rectangle((centre_x - self.grid_size/2,
                               centre_y - self.grid_size/2),
                              self.grid_size, self.grid_size,
                              facecolor=colour, edgecolor="white",
                              linewidth=0.4, alpha=0.75, zorder=3)
            ax.add_patch(rect)

        # antenna sector wedge (above grid, under legend)
        wedge = Wedge((self.bs_x, self.bs_y), self.radius,
                      90 - (self.azimuth + self.beamwidth/2),
                      90 - (self.azimuth - self.beamwidth/2),
                      facecolor=(1, 0, 0, 0.15), edgecolor="red",
                      lw=2, zorder=4, label="Sector")
        ax.add_patch(wedge)

        # basemap at the very bottom
        ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik,
                        alpha=0.8, attribution=False, zorder=0)

        # legend (colour swatches + sector)
        legend_items = [Patch(color=c, label=l.replace(":", " to "))
                        for l, c in self.kpi_range_dict.items()]
        legend_items.append(Patch(facecolor='none', edgecolor='red', lw=2, label="Sector"))
        ax.legend(handles=legend_items, title=self.kpi_name, loc="lower left")

        ax.set_xticks([]); ax.set_yticks([]); plt.tight_layout()

        buf = BytesIO(); plt.savefig(buf, format="png", dpi=300, bbox_inches="tight"); plt.close(fig)
        buf.seek(0)
        img = XLImage(buf); img.width = 500; img.height = 500
        return img
