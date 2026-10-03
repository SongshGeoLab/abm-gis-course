"""River network from a DEM: fill sinks → flow direction (D8) → flow accumulation → streams.

This is what QGIS tools such as GRASS ``r.watershed`` do for you. It is written
out here in plain NumPy so the three ideas are visible, and to draw the
figures for the slides.

Run from this folder:
    python river_network.py

Needs: numpy, rasterio, matplotlib.
"""

import heapq
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import LightSource, LogNorm

HERE = Path(__file__).resolve().parent
DEM_FILE = HERE.parent / "dem" / "jena_dem.tif"
OUT_DIR = HERE.parent / "outputs" / "dem"
FIG_DIR = HERE.parents[1] / "assets" / "abm-gis" / "img"

# A cell is "river" when at least this much land drains through it.
STREAM_THRESHOLD_KM2 = 1.0

# The 8 neighbours (row offset, column offset) of a cell.
NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
DISTANCE = [np.hypot(dr, dc) for dr, dc in NEIGHBOURS]


def fill_sinks(dem):
    """Raise every pit until water can flow out to the map edge (priority flood)."""
    nrows, ncols = dem.shape
    filled = dem.copy()
    done = np.zeros(dem.shape, dtype=bool)
    queue = []
    for r in range(nrows):
        for c in range(ncols):
            if r in (0, nrows - 1) or c in (0, ncols - 1):
                heapq.heappush(queue, (filled[r, c], r, c))
                done[r, c] = True
    while queue:
        z, r, c = heapq.heappop(queue)
        for dr, dc in NEIGHBOURS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < nrows and 0 <= cc < ncols and not done[rr, cc]:
                # a tiny slope so flat filled areas still drain
                filled[rr, cc] = max(filled[rr, cc], z + 1e-4)
                done[rr, cc] = True
                heapq.heappush(queue, (filled[rr, cc], rr, cc))
    return filled


def flow_direction(filled):
    """D8: each cell sends its water to the steepest-downhill neighbour (-1 = edge)."""
    nrows, ncols = filled.shape
    direction = np.full(filled.shape, -1, dtype=np.int8)
    for r in range(1, nrows - 1):
        for c in range(1, ncols - 1):
            best_slope = 0.0
            for k, (dr, dc) in enumerate(NEIGHBOURS):
                slope = (filled[r, c] - filled[r + dr, c + dc]) / DISTANCE[k]
                if slope > best_slope:
                    best_slope, direction[r, c] = slope, k
    return direction


def flow_accumulation(filled, direction):
    """Count how many cells drain through each cell (each cell counts itself)."""
    accumulation = np.ones(filled.shape)
    ncols = filled.shape[1]
    for index in np.argsort(filled, axis=None)[::-1]:  # highest cell first
        r, c = divmod(index, ncols)
        k = direction[r, c]
        if k >= 0:
            dr, dc = NEIGHBOURS[k]
            accumulation[r + dr, c + dc] += accumulation[r, c]
    return accumulation


def thicken(array, times=1):
    """Draw lines thicker on the figure: each cell takes the max of its 3×3 window."""
    for _ in range(times):
        padded = np.pad(array, 1, mode="edge")
        rows, cols = array.shape
        array = np.max([padded[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols]
                        for dr, dc in NEIGHBOURS + [(0, 0)]], axis=0)
    return array


def save_raster(path, array, profile, dtype):
    profile = profile | {"dtype": dtype, "nodata": None, "compress": "deflate"}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array.astype(dtype), 1)


def plot_map(path, layers, extent, title):
    fig, ax = plt.subplots(figsize=(8, 6.8), dpi=150)
    for draw in layers:
        draw(ax)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=13)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(DEM_FILE) as src:
        dem = src.read(1).astype("float64")
        profile = src.profile
        cell_km2 = abs(src.res[0] * src.res[1]) / 1e6
        b = src.bounds
    extent = (b.left, b.right, b.bottom, b.top)

    filled = fill_sinks(dem)
    direction = flow_direction(filled)
    accumulation = flow_accumulation(filled, direction)
    area_km2 = accumulation * cell_km2
    streams = area_km2 >= STREAM_THRESHOLD_KM2

    save_raster(OUT_DIR / "flow_accumulation_km2.tif", area_km2, profile, "float32")
    save_raster(OUT_DIR / "streams.tif", streams, profile, "uint8")
    print(f"cells: {dem.size:,}  cell area: {cell_km2:.4f} km²")
    print(f"largest catchment in view: {area_km2.max():.0f} km²")
    print(f"river cells (≥ {STREAM_THRESHOLD_KM2} km²): {streams.sum():,}")

    hillshade = LightSource(azdeg=315, altdeg=45).hillshade(dem, vert_exag=3, dx=30, dy=30)

    def shade(ax, alpha=1.0):
        ax.imshow(hillshade, cmap="gray", extent=extent, alpha=alpha)

    def elevation(ax):
        shade(ax)
        im = ax.imshow(dem, cmap="terrain", extent=extent, alpha=0.55, vmin=100, vmax=520)
        cbar = ax.figure.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
        cbar.set_label("Elevation (m)")

    def accumulation_layer(ax):
        shade(ax, 0.35)
        shown = thicken(area_km2)
        im = ax.imshow(np.ma.masked_less(shown, 0.05), cmap="Blues", extent=extent,
                       norm=LogNorm(vmin=0.05, vmax=area_km2.max()))
        cbar = ax.figure.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
        cbar.set_label("Area draining through the cell (km², log scale)")

    def stream_layer(ax):
        shade(ax, 0.6)
        small = thicken(streams.astype(float))
        big = thicken((area_km2 >= 20).astype(float), times=2)
        ax.imshow(np.ma.masked_equal(small, 0), cmap="Blues", vmin=0, vmax=1.6, extent=extent)
        ax.imshow(np.ma.masked_equal(big, 0), cmap="Blues", vmin=0, vmax=1.05, extent=extent)

    plot_map(FIG_DIR / "dem_jena_elevation.png", [elevation], extent,
             "Elevation around Jena (Copernicus DEM, 30 m)")
    plot_map(FIG_DIR / "dem_jena_accumulation.png", [accumulation_layer], extent,
             "Flow accumulation")
    plot_map(FIG_DIR / "dem_jena_streams.png", [stream_layer], extent,
             f"River network: cells draining ≥ {STREAM_THRESHOLD_KM2:g} km²")


if __name__ == "__main__":
    main()
