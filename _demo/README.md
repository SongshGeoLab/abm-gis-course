# GIS and Modelling Approaches: demo files

Files for the lecture *GIS and Modelling Approaches* (`gis_modelling.qmd`).

Students get these files as `gis-modelling-exercises.zip` from the repository's [*Exercise files* release](https://github.com/SongshGeoLab/abm-gis-course/releases/tag/exercises). It is rebuilt automatically whenever the files change (`make_exercise_zip.sh`, run by `.github/workflows/exercise-zip.yml`). The zip leaves out `python/` and `outputs/qgis/`, which only matter for making the slides.

```
_demo/
├── dem/
│   ├── jena_dem.tif                 DEM around Jena, 30 m, EPSG:25832 (Part 1)
│   ├── crater_lake_elevation.asc    elevation for the raindrop model (Part 2)
│   └── crater_lake_elevation.prj    its CRS (EPSG:4326, assumed: the source grid has none)
├── qgis/
│   └── rivers_from_dem.py           QGIS Processing tool: rivers from a DEM without GRASS
├── outputs/
│   ├── dem/   flow_accumulation_km2.tif, streams.tif   (ready-made Part 1 results)
│   ├── abm/   water_level.tif, raindrops.gpkg           (raindrop model after 12 steps)
│   └── qgis/  raw QGIS screenshots for the OpenStreetMap slide (repository only)
└── python/                          scripts that made the slide figures (repository only)
    ├── river_network.py             fill sinks → flow direction → flow accumulation → streams
    ├── dem_resolution.py            real terrain vs DEMs at 120 / 300 / 900 m cells (slide figure)
    ├── d8_diagram.py                the 4×4 flow-direction figure on the slides
    ├── flood_map.py                 official Jena flood hazard map for the first slide (needs internet)
    ├── qgis_tool_screenshots.py     runs inside QGIS: screenshots of our river tool
    ├── qgis_osm_screenshots.py      runs inside QGIS: screenshots of adding the OSM basemap
    ├── qgis_figures.py              numbered markers on those screenshots (slide figures)
    └── export_rainfall.py           Mesa-Geo raindrop model → GeoTIFF + GeoPackage
```

## Exercise A · Rivers from a DEM (QGIS only)

1. Drag `dem/jena_dem.tif` into QGIS. Make a hillshade: *Raster ▸ Analysis ▸ Hillshade*.
2. Add our river tool to QGIS (only once): *Processing ▸ Toolbox* ▸ Python icon ▸ *Add Script to Toolbox…* ▸ pick `qgis/rivers_from_dem.py`.
3. Double-click *Scripts ▸ GIS and Modelling ▸ Rivers from a DEM (no GRASS)*.
   - *Elevation (DEM)*: `jena_dem.tif`
   - *River threshold*: `1` (km²)
   - Run: you get two layers, *Flow accumulation (km²)* and *Streams*.
4. Run it again with `10` km² and compare the two stream networks.
5. Add an OpenStreetMap basemap and compare the modelled rivers with real ones. In the *Browser* panel, right-click *XYZ Tiles ▸ New Connection…*, name it `OpenStreetMap`, URL `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, then double-click it and drag it to the bottom of the *Layers* panel. (QGIS 3 often has *XYZ Tiles ▸ OpenStreetMap* already; QGIS 4 starts empty.)

The tool follows the slides step by step: fill sinks → flow direction (D8) → flow accumulation → threshold. Its results match the ready-made files in `outputs/dem/`.

**With GRASS:** the classic tool is *r.watershed* (threshold `1111` cells ≈ 1 km², tick *Enable Single Flow Direction (D8) flow*). On macOS, QGIS 4 often cannot run GRASS tools ([QGIS issue #65363](https://github.com/qgis/QGIS/issues/65363)); that is why we wrote our own tool. If GRASS is installed separately, starting QGIS from the Terminal like this can help (adjust the two app names to your versions):

```bash
export GISBASE=/Applications/GRASS-8.5.app/Contents/Resources GRASS_PREFIX=$GISBASE
open /Applications/QGIS-final-4_2_0.app
```

Things to notice: the Saale gets most of its water from outside the map, so the model underestimates it (edge effect; r.watershed marks such cells with **negative values**), and the DEM is a surface model, so buildings and bridges in Jena change the flow paths.

## Exercise B · Output of an agent-based model

1. Open `outputs/abm/water_level.tif` and `outputs/abm/raindrops.gpkg`. Both are in EPSG:4326.
2. Style the water with *Singleband pseudocolor*. Under *Transparency*, set `0` as no data.
3. Where did lakes form? Compare with `dem/crater_lake_elevation.asc`.

## Python (optional, repository only)

```bash
pip install mesa-geo rasterio matplotlib pillow requests
cd _demo/python
python river_network.py     # writes outputs/dem/ and the slide figures
python export_rainfall.py   # writes outputs/abm/
python dem_resolution.py    # slide figure: one DEM at three resolutions
python flood_map.py         # slide figure: Jena flood hazard map (needs internet)
python qgis_figures.py      # QGIS slide figures (take the screenshots first, see qgis_*_screenshots.py)
```

## Data

- Jena flood hazard map (first slide): national flood hazard maps of the German Federal Institute of Hydrology (BfG, <https://geoportal.bafg.de/karten/HWRM/>), data from TLUBN Thüringen; basemap © basemap.de / BKG (CC BY 4.0). The flood data licence was not checked; verify it before publishing the slides.
- Jena DEM: Copernicus DEM GLO-30, clipped to 11.44–11.74° E, 50.83–50.99° N and reprojected to EPSG:25832.
  © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- Crater Lake elevation: from Crooks, Malleson, Manley & Heppenstall (2019), *Agent-Based Modelling and Geographical Information Systems*, CC BY-SA 4.0.
  The raindrop model follows the Rainfall example in *Python for Agent-Based Modeling*, Chapter 8 (<https://github.com/abmind-community/py4abm>).
