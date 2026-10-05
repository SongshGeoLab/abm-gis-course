"""Put numbered markers on the QGIS screenshots for the slides.

Two figures, each a main-window screenshot with a dialog pasted in:
- qgis_rivers_tool.png: add our river tool to the Toolbox and run it
- qgis_osm_basemap.png: add an OpenStreetMap basemap

Take the screenshots first (inside QGIS): qgis_tool_screenshots.py and
qgis_osm_screenshots.py. Then, from this folder:
    python qgis_figures.py

Needs: matplotlib, pillow.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

HERE = Path(__file__).resolve().parent
SHOTS = HERE.parent / "outputs" / "qgis"
FIG_DIR = HERE.parents[1] / "assets" / "abm-gis" / "img"
TEAL = "#006c66"

# Pixel positions are in the 1600 × 960 QGIS window (fresh profile, default layout).
FIGURES = {
    "qgis_rivers_tool.png": {
        "window": "tool_window.png",
        "dialog": "tool_dialog.png",
        "dialog_at": (330, 495),
        "dialog_scale": 0.75,
        "markers": {
            # number: (where the number goes, what it points at or None)
            "1": ((1520, 111), (1343, 111)),    # Python icon ▸ Add Script to Toolbox…
            "2": ((1335, 248), None),           # Scripts ▸ GIS and Modelling ▸ our tool
            "3": ((975, 580), None),            # DEM and threshold in the dialog
            "4": ((975, 900), None),            # Run
        },
    },
    "qgis_osm_basemap.png": {
        "window": "qgis_window.png",
        "dialog": "xyz_dialog.png",
        "dialog_at": (1075, 515),               # bottom right, so Jena stays visible
        "dialog_scale": 0.8,
        "markers": {
            "1": ((170, 418), None),            # Browser ▸ XYZ Tiles (right-click here)
            "2": ((1052, 540), None),           # the New Connection dialog
            "3": ((232, 445), None),            # the new OpenStreetMap connection
            "4": ((190, 636), None),            # Layers: OpenStreetMap at the bottom
        },
    },
}


def marker(ax, xy, text, target=None):
    """A numbered circle; with a target, also ring the target and draw a line to it."""
    if target is not None:
        ax.add_patch(plt.Circle(target, 17, fill=False, edgecolor=TEAL, lw=3))
        ax.plot([target[0] + 17, xy[0] - 14], [target[1], xy[1]], color=TEAL, lw=2.5)
    ax.annotate(text, xy, ha="center", va="center", fontsize=14, fontweight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=0.3", facecolor=TEAL, edgecolor="white", lw=2))


def make_figure(name, spec):
    window = Image.open(SHOTS / spec["window"]).convert("RGB")
    dialog = Image.open(SHOTS / spec["dialog"]).convert("RGB")
    scale = spec["dialog_scale"]
    dialog = dialog.resize((round(dialog.width * scale), round(dialog.height * scale)))
    framed = Image.new("RGB", (dialog.width + 6, dialog.height + 6), TEAL)
    framed.paste(dialog, (3, 3))
    window.paste(framed, spec["dialog_at"])

    fig, ax = plt.subplots(figsize=(window.width / 100, window.height / 100), dpi=100)
    ax.imshow(window)
    ax.set_axis_off()
    for text, (xy, target) in spec["markers"].items():
        marker(ax, xy, text, target)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(FIG_DIR / name, dpi=100)
    plt.close(fig)
    print(f"wrote {FIG_DIR / name}")


def main():
    for name, spec in FIGURES.items():
        make_figure(name, spec)


if __name__ == "__main__":
    main()
