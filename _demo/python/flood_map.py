"""Official flood hazard map for Jena, drawn for the opening slide.

The flood layers come from the national flood hazard maps of the German
Federal Institute of Hydrology (BfG), which collects the maps the federal
states made for the EU Floods Directive. Thuringia computed them with
hydraulic models of the Saale: the map is itself the output of a model.

Run from this folder (needs internet):
    python flood_map.py

Needs: numpy, matplotlib, pillow, requests.
"""

import io
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import requests
from matplotlib.patches import Patch
from PIL import Image

HERE = Path(__file__).resolve().parent
FIG = HERE.parents[1] / "assets" / "abm-gis" / "img" / "flood_jena.png"
FLOOD_SERVICE = "https://geoportal.bafg.de/arcgis3/rest/services/nHWGK_HWRK_live"
BASEMAP_WMS = "https://sgx.geodatenzentrum.de/wms_basemapde"

# Jena, west-east 11.53–11.65° E, south-north 50.885–50.965° N.
WEST, SOUTH, EAST, NORTH = 11.53, 50.885, 11.65, 50.965
WIDTH = 1600                            # pixels; the height follows from the map shape

# Water depth classes of the BfG map (colours as the service draws them).
DEPTH_CLASSES = [("0–0.5 m", (204, 236, 255)), ("0.5–1 m", (153, 204, 255)),
                 ("1–2 m", (101, 153, 255)), ("2–4 m", (61, 102, 255)),
                 ("> 4 m", (0, 51, 204))]
EXTREME_COLOUR = (240, 140, 60)


def web_mercator(lon, lat):
    """Longitude/latitude in degrees → web-map coordinates (EPSG:3857) in metres."""
    earth_radius = 6378137
    x = earth_radius * math.radians(lon)
    y = earth_radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def fetch_rgba(url, params):
    """Download a map image and return it as an RGBA array."""
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return np.array(Image.open(io.BytesIO(response.content)).convert("RGBA"))


def flood_layer(service, bbox, size):
    """One BfG flood layer as a transparent image for the bounding box."""
    return fetch_rgba(f"{FLOOD_SERVICE}/{service}/MapServer/export", {
        "bbox": ",".join(map(str, bbox)), "bboxSR": 3857, "imageSR": 3857,
        "size": f"{size[0]},{size[1]}", "format": "png32", "transparent": "true", "f": "image"})


def basemap(bbox, size):
    """The grey official German basemap (basemap.de, BKG) for the bounding box."""
    return fetch_rgba(BASEMAP_WMS, {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": "de_basemapde_web_raster_grau", "STYLES": "", "CRS": "EPSG:3857",
        "BBOX": ",".join(map(str, bbox)), "WIDTH": size[0], "HEIGHT": size[1],
        "FORMAT": "image/png"})


def main():
    x0, y0 = web_mercator(WEST, SOUTH)
    x1, y1 = web_mercator(EAST, NORTH)
    bbox = (x0, y0, x1, y1)
    extent = (x0, x1, y0, y1)           # the order matplotlib wants
    size = (WIDTH, round(WIDTH * (y1 - y0) / (x1 - x0)))   # same shape as the map: no stretching

    extreme = flood_layer("Wassertiefen_RW_L_live", bbox, size)   # rare, extreme flood
    hq100 = flood_layer("Wassertiefen_RW_M_live", bbox, size)     # 1% chance each year
    extreme_rgba = np.zeros_like(extreme)
    extreme_rgba[extreme[..., 3] > 0] = (*EXTREME_COLOUR, 150)      # orange, see-through

    fig, ax = plt.subplots(figsize=(8, 8 * size[1] / size[0]), dpi=150)
    ax.imshow(basemap(bbox, size), extent=extent)
    ax.imshow(extreme_rgba, extent=extent)
    ax.imshow(hq100, extent=extent)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_axis_off()

    handles = [Patch(color=np.array(rgb) / 255, label=label) for label, rgb in DEPTH_CLASSES]
    handles.append(Patch(color=np.array(EXTREME_COLOUR) / 255, alpha=0.6,
                         label="only in an extreme flood"))
    ax.legend(handles=handles, loc="lower left", fontsize=9.5, framealpha=0.92,
              title="Water depth, 1% chance each year (HQ100)", title_fontsize=10,
              alignment="left")
    fig.savefig(FIG, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    print(f"wrote {FIG}")


if __name__ == "__main__":
    main()
