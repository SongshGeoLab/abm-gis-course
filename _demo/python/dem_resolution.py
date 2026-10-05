"""How a DEM turns real terrain into square cells, at three resolutions.

Takes a 3.6 × 3.6 km patch of the Jena DEM (Saale valley, south of the
centre). The 30 m data, drawn as a smooth surface, stands in for the real
terrain. Averaging blocks of cells gives coarser DEMs: each cell keeps only
one height, so the coarser the grid, the more of the valley disappears.

Run from this folder:
    python dem_resolution.py

Needs: numpy, rasterio, matplotlib, pillow.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import LightSource, Normalize
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
DEM_FILE = HERE.parent / "dem" / "jena_dem.tif"
FIG = HERE.parents[1] / "assets" / "abm-gis" / "img" / "dem_resolution.png"

ROW, COL, SIZE = 400, 260, 120          # 120 cells × 30 m = 3.6 km
CELL = 30                               # metres
RESOLUTIONS = [120, 300, 900]           # coarser cell sizes in metres
VERT_EXAG = 4                           # stretch heights so the relief is visible


def coarsen(dem, factor):
    """Average blocks of factor × factor cells into one cell."""
    n = dem.shape[0] // factor
    return dem[:n * factor, :n * factor].reshape(n, factor, n, factor).mean(axis=(1, 3))


def setup_3d(ax, title, zmin, zmax):
    ax.set_xlim(0, SIZE * CELL)
    ax.set_ylim(0, SIZE * CELL)
    ax.set_zlim(zmin, zmin + (zmax - zmin) * 1.05)
    ax.set_box_aspect((1, 1, VERT_EXAG * (zmax - zmin) / (SIZE * CELL)))
    ax.view_init(elev=32, azim=-60)
    ax.set_axis_off()
    ax.set_title(title, fontsize=20, pad=0, y=0.88)


def trim_white(path, margin=20):
    """Cut away the empty space that 3D axes leave around the picture."""
    image = Image.open(path).convert("RGB")
    box = ImageChops.difference(image, Image.new("RGB", image.size, "white")).getbbox()
    left, top, right, bottom = box
    image.crop((max(left - margin, 0), max(top - margin, 0),
                min(right + margin, image.width), min(bottom + margin, image.height))).save(path)


def main():
    with rasterio.open(DEM_FILE) as src:
        dem = src.read(1).astype("float64")[ROW:ROW + SIZE, COL:COL + SIZE]
    dem = dem[::-1]                     # row 0 = south, so the 3D view is not mirrored
    zmin, zmax = dem.min(), dem.max()
    norm = Normalize(zmin, zmax)
    cmap = plt.get_cmap("terrain")
    light = LightSource(azdeg=315, altdeg=45)

    fig = plt.figure(figsize=(18, 6.4), dpi=130)

    # Real terrain: the fine data as a smooth, continuous surface.
    ax = fig.add_subplot(1, 4, 1, projection="3d")
    x = (np.arange(SIZE) + 0.5) * CELL
    xx, yy = np.meshgrid(x, x)
    # shade in map orientation (north up), then flip like the heights
    colours = light.shade(dem[::-1], cmap=cmap, norm=norm, vert_exag=VERT_EXAG, blend_mode="soft")[::-1]
    ax.plot_surface(xx, yy, dem, facecolors=colours, rstride=1, cstride=1, linewidth=0,
                    antialiased=False, shade=False)
    setup_3d(ax, "≈ Real terrain\n(30 m DEM, drawn smooth)", zmin, zmax)

    # Coarser DEMs: one flat-topped block per cell.
    for i, res in enumerate(RESOLUTIONS, start=2):
        grid = coarsen(dem, res // CELL)
        n = grid.shape[0]
        ax = fig.add_subplot(1, 4, i, projection="3d")
        xs, ys = np.meshgrid(np.arange(n) * res, np.arange(n) * res)
        ax.bar3d(xs.ravel(), ys.ravel(), np.full(n * n, zmin), res, res,
                 grid.ravel() - zmin, color=cmap(norm(grid.ravel())),
                 edgecolor="#333", linewidth=0.25 if n > 20 else 0.6, shade=True)
        setup_3d(ax, f"DEM, {res} m cells\n{n} × {n} = {n * n:,} heights", zmin, zmax)

    fig.subplots_adjust(left=0, right=1, top=0.9, bottom=0, wspace=0)
    fig.savefig(FIG, bbox_inches="tight", facecolor="white")
    trim_white(FIG)
    print(f"wrote {FIG}  (heights {zmin:.0f}–{zmax:.0f} m)")


if __name__ == "__main__":
    main()
