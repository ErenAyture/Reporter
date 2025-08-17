import os, pyproj.datadir
os.environ["PROJ_LIB"] = pyproj.datadir.get_data_dir()
os.environ["PROJ_NETWORK"] = "ON"

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Patch, Rectangle
import contextily as ctx
from pyproj import Transformer

# ---- RSRP color ranges (RangeDict) ----


class SpatialKPIDensityPlot:
    def __init__(
        self,
        bs_lat, bs_lon,
        azimuth,
        beamwidth,
        radius=100,
        grid_size=50,
        data_points=None,  # [(lon, lat, rsrp), ...]
        extent_km=2.0
    ):
        """
        Parameters:
            bs_lat, bs_lon   : base station lat/lon (WGS84)
            azimuth, beamwidth, radius : antenna sector params (deg, deg, m)
            grid_size        : grid square size in meters (default 50)
            data_points      : list of (lon, lat, rsrp)
            extent_km        : plot width/height in kilometers (default 2km x 2km)
        """
        self.bs_lat = bs_lat
        self.bs_lon = bs_lon
        self.azimuth = azimuth
        self.beamwidth = beamwidth
        self.radius = radius
        self.grid_size = grid_size
        self.data_points = data_points or []
        self.extent_km = extent_km

        self.proj = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        self.bs_x, self.bs_y = self.proj.transform(bs_lon, bs_lat)
        self.points_proj = [
            self.proj.transform(lon, lat) + (rsrp,) for lon, lat, rsrp in self.data_points
        ]

    def plot(self, out=None):
        fig, ax = plt.subplots(figsize=(8, 8))

        # Extent is always 2km x 2km (centered on BS)
        km = self.extent_km
        bs_x, bs_y = self.bs_x, self.bs_y
        extent = (bs_x - 1000*km/2, bs_x + 1000*km/2, bs_y - 1000*km/2, bs_y + 1000*km/2)
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

        # Draw grid squares
        for px, py, rsrp in self.points_proj:
            grid_x = bs_x + self.grid_size * round((px - bs_x) / self.grid_size)
            grid_y = bs_y + self.grid_size * round((py - bs_y) / self.grid_size)
            color = SSV4G_COVERAGE_RSRP[rsrp]
            rect = Rectangle((grid_x - self.grid_size / 2, grid_y - self.grid_size / 2),
                             self.grid_size, self.grid_size, facecolor=color, edgecolor="none", alpha=0.7)
            ax.add_patch(rect)

        # Draw antenna sector
        wedge = Wedge(
            center=(bs_x, bs_y),
            r=self.radius,
            theta1=90 - (self.azimuth + self.beamwidth / 2),
            theta2=90 - (self.azimuth - self.beamwidth / 2),
            facecolor=(1, 0, 0, 0.15),
            edgecolor="red",
            lw=2,
            label="Sector"
        )
        ax.add_patch(wedge)

        # Add OSM basemap (no attribution)
        ctx.add_basemap(ax, crs="EPSG:3857",
                        source=ctx.providers.OpenStreetMap.Mapnik,
                        alpha=0.8,
                        attribution=False)

        # Legend
        import matplotlib.patches as mpatches
        legend_patches = [
            mpatches.Patch(color=col, label=label)
            for label, col in zip(
                [
                    "-70 to -44", "-80 to -70", "-90 to -80", "-95 to -90",
                    "-100 to -95", "-110 to -100", "-120 to -110", "-141 to -120"
                ],
                [
                    '#008000', '#71b800', '#aad500', '#dfe300',
                    '#ffaa00', '#ff7300', '#e13900', '#e30000'
                ]
            )
        ]
        sector_patch = Patch(facecolor='none', edgecolor='red', lw=2, label="Sector")
        legend_patches.append(sector_patch)
        ax.legend(handles=legend_patches, title="RSRP [dBm]", loc="lower left")

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
        plt.tight_layout()
        if out:
            plt.savefig(out, bbox_inches="tight", dpi=300)
        plt.show()

# ---- USAGE EXAMPLE ----
if __name__ == "__main__":
    bs_lat, bs_lon = 40.387434, 31.934643   # Your site
    azimuth = 40
    beamwidth = 60
    radius = 100    # meters
    data_points = [
        (31.9350, 40.3875, -65),
        (31.9340, 40.3870, -80),
        (31.9360, 40.3880, -90),
        (31.9345, 40.3885, -105),
        # ... more
    ]

    plotter = SpatialKPIDensityPlot(
        bs_lat, bs_lon, azimuth, beamwidth,
        radius=radius, grid_size=50,
        data_points=data_points,
        extent_km=2
    )
    plotter.plot(out=None)  # Set filename to save as PNG
