import os, pyproj.datadir
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_NETWORK"] = "ON"

#!/usr/bin/env python
# ── SpatialKPIDensity.py ──────────────────────────────────────────────
"""50 m-grid KPI heat-map over an OpenStreetMap basemap."""

import os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge, Patch

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import contextily as ctx
from pyproj import Transformer, datadir as _pd
from io import BytesIO
from openpyxl.drawing.image import Image as XLImage
# from threading import Lock

os.environ["MPLBACKEND"] = "Agg"   # <- 100 % non-GUI backend

import matplotlib                  # happens AFTER the env var
matplotlib.use("Agg", force=True)  # belt-and-suspenders
plt.ioff()                         # disable interactive state
# -- enable online tiles for PROJ 6+
os.environ["PROJ_LIB"]     = _pd.get_data_dir()
os.environ["PROJ_NETWORK"] = "ON"



# ──────────────────────────────────────────────────────────────────────
class SpatialKPIDensityPlot:
    """Draw a 50 m KPI heat-map around a base-station location."""

    # ------------------------------------------------------------------
    def __init__(
        self,
        bs_lat: float, bs_lon: float,
        azimuth: float, beamwidth: float,
        # lock: Lock,
        *,
        radius: float      = 100,          # sector wedge (m)
        grid_size: float   = 50,           # always 50 m
        data_points: pd.DataFrame | None = None,
        lon_col: str       = "longitude",
        lat_col: str       = "latitude",
        kpi_col: str       = "rsrp",
        kpi_name: str      = "KPI",
        kpi_range_dict:    dict = None,
        extent_km: float   = 2.0,
        sector_frac: float = 0.05,
        
    ):
        self.bs_lat, self.bs_lon = bs_lat, bs_lon
        self.azimuth, self.beamwidth = azimuth, beamwidth
        # self.lock = lock
        self.radius, self.grid_size  = sector_frac * extent_km * 1000, grid_size
        self.lon_col, self.lat_col   = lon_col, lat_col
        self.kpi_col, self.kpi_name  = kpi_col, kpi_name
        self.kpi_range_dict          = kpi_range_dict or {}
        self.extent_km               = float(extent_km)

        # WGS84 → Web-Mercator
        self._proj    = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        self.bs_x, self.bs_y = self._proj.transform(bs_lon, bs_lat)

        self.data_points = data_points if data_points is not None else \
            pd.DataFrame(columns=[lon_col, lat_col, kpi_col])
        self.points_proj = self._project_points()
        # print(self.data_points)
        # print(self.points_proj)

    # ------------------------------------------------------------------
    def _project_points(self):
        lon = self.data_points[self.lon_col].values
        lat = self.data_points[self.lat_col].values
        kpi = self.data_points[self.kpi_col].values
        xs, ys = self._proj.transform(lon, lat)

        return list(zip(xs, ys, kpi))

    # ------------------------------------------------------------------
    def plot(self, out: str | None = None):
        """Return an openpyxl Image (for Excel) or save PNG if *out* is given."""

        fig = Figure(figsize=(8, 8))
        FigureCanvasAgg(fig)              # attaches a canvas
        ax = fig.add_subplot(111)
        # fig, ax = plt.subplots(figsize=(8, 8))

        # -- frame extents
        km = self.extent_km
        ax.set_xlim(self.bs_x - 500 * km, self.bs_x + 500 * km)
        ax.set_ylim(self.bs_y - 500 * km, self.bs_y + 500 * km)

        # -- basemap (z 0)
        ctx.add_basemap(ax, crs="EPSG:3857",
                        source=ctx.providers.OpenStreetMap.Mapnik,
                        alpha=0.8, attribution=False, zorder=0)

        # -- 50 m squares (z 3)
        for px, py, val in self.points_proj:
            # print(f'{px} {py} {val}')
            
            if pd.isna(val):
                #print("continued")
                continue
            # RangeDict.__getitem__ handles the “find-the-bin” logic
            try:
                colour = self.kpi_range_dict[val]
                # print(colour)
            except KeyError:
                continue    # value outside all bins → skip

            gx = self.bs_x + self.grid_size * round((px - self.bs_x) / self.grid_size)
            gy = self.bs_y + self.grid_size * round((py - self.bs_y) / self.grid_size)
            # print(f'gx: {gx} gy: {gy}')
            ax.add_patch(Rectangle(
                (gx - self.grid_size / 2, gy - self.grid_size / 2),
                self.grid_size, self.grid_size,
                facecolor=colour, edgecolor="none", alpha=0.7, zorder=3))

        # -- antenna sector (z 2)
        ax.add_patch(Wedge(
            (self.bs_x, self.bs_y), self.radius,
            90 - (self.azimuth + self.beamwidth / 2),
            90 - (self.azimuth - self.beamwidth / 2),
            facecolor=(1, 0, 0, .15), edgecolor="red", lw=2,
            label="Sector", zorder=2))

        # -- legend
        leg_patches = [Patch(color=c, label=l.replace(":", " to "))
                       for l, c in self.kpi_range_dict.items()]
        leg_patches.append(Patch(facecolor="none", edgecolor="red", lw=2, label="Sector"))
        ax.legend(handles=leg_patches, title=self.kpi_name, loc="lower left")

        ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
        plt.tight_layout()

        # -- output
        if out:
            fig.savefig(out, dpi=300, bbox_inches="tight")
            fig.clear()
            return out
        else:
            # show window for manual inspection
            # plt.show()                       # << interactive window
            # with self.lock:
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            fig.clear()
            img = XLImage(buf); img.width = 500; img.height = 500
            return img

# ── self-test -- run “python SpatialKPIDensity.py” ───────────────────
# if __name__ == "__main__":

#     # ♦ sample KPI colour mapping (10 dB step RangeDict imitation)
#     # class RangeDict(dict):
#     #     """Key lookup that returns the colour for the first interval that
#     #     *contains* the numeric key.  Ex:  -85 → colours["-90:-80"]"""
#     #     def __getitem__(self, item):
#     #         for rng, col in self.items():
#     #             lo, hi = map(float, rng.split(":"))
#     #             if lo <= item < hi:
#     #                 return col
#     #         raise KeyError(item)

#     # LTE_RSRP_COLOURS = RangeDict({
#     #     "-INF:-141": "#4d4d4d",
#     #     "-141:-120": "#b2182b",
#     #     "-120:-110": "#ef8a62",
#     #     "-110:-100": "#fdae61",
#     #     "-100:-95" : "#fee08b",
#     #     "-95:-90"  : "#d9ef8b",
#     #     "-90:-80"  : "#a6d96a",
#     #     "-80:-70"  : "#66bd63",
#     #     "-70:-44"  : "#1a9850",
#     #     "-44:+INF" : "#006837",
#     # })
#     from RangeDict import LTE_Ranges,RangeDict
#     # ♦ fabricated drive-test
#     df = pd.DataFrame({
#         "longitude": [31.93500, 31.93400, 31.93600, 31.93450,
#                       31.93520, 31.93380, 31.93590, 31.93430],
#         "latitude" : [40.38750, 40.38700, 40.38800, 40.38850,
#                       40.38720, 40.38780, 40.38795, 40.38810],
#         "rsrp"     : [-65, -80, -90, -105, -95, -72, -99, -88],
#     })

#     plotter = SpatialKPIDensityPlot(
#         bs_lat=40.387434, bs_lon=31.934643, azimuth=40, beamwidth=60,
#         radius=100, grid_size=50,
#         data_points=df, lon_col="longitude", lat_col="latitude",
#         kpi_col="rsrp", kpi_name="RSRP",
#         kpi_range_dict=LTE_Ranges["rsrp"], extent_km=2)

#     # interactive window + exported PNG
#     img = plotter.plot(out="sample_rsrp3.png")
#     print("Saved PNG as sample_rsrp3.png and returned an openpyxl Image:", img)

# ──────────────────────────────────────────────────────────────────────
