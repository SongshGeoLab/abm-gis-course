"""Put numbered markers on the QGIS screenshots for the OpenStreetMap slide.

Run qgis_osm_screenshots.py (inside QGIS) first. Then, from this folder:
    python qgis_osm_figure.py

Needs: matplotlib, pillow.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

HERE = Path(__file__).resolve().parent
SHOTS = HERE.parent / "outputs" / "qgis"
FIG = HERE.parents[1] / "assets" / "abm-gis" / "img" / "qgis_osm_basemap.png"
TEAL = "#006c66"

# Pixel positions in the 1600 × 960 QGIS window (fresh profile, default layout).
MARKERS = {
    "1": (170, 418),   # Browser ▸ XYZ Tiles (right-click here)
    "2": (1052, 540),  # the New Connection dialog (pasted in at DIALOG_AT)
    "3": (232, 445),   # the new OpenStreetMap connection
    "4": (190, 636),   # Layers: OpenStreetMap at the bottom
}
DIALOG_AT = (1075, 515)   # bottom right, so Jena stays visible
DIALOG_SCALE = 0.8


def marker(ax, xy, text):
    ax.annotate(text, xy, ha="center", va="center", fontsize=14, fontweight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=0.3", facecolor=TEAL, edgecolor="white", lw=2))


def main():
    window = Image.open(SHOTS / "qgis_window.png").convert("RGB")
    dialog = Image.open(SHOTS / "xyz_dialog.png").convert("RGB")
    dialog = dialog.resize((round(dialog.width * DIALOG_SCALE), round(dialog.height * DIALOG_SCALE)))
    x, y = DIALOG_AT
    framed = Image.new("RGB", (dialog.width + 6, dialog.height + 6), TEAL)
    framed.paste(dialog, (3, 3))
    window.paste(framed, (x, y))

    fig, ax = plt.subplots(figsize=(window.width / 100, window.height / 100), dpi=100)
    ax.imshow(window)
    ax.set_axis_off()
    for text, xy in MARKERS.items():
        marker(ax, xy, text)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(FIG, dpi=100)
    print(f"wrote {FIG}")


if __name__ == "__main__":
    main()
