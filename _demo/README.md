# GIS and Modelling Approaches: demo files

Files for the lecture *GIS and Modelling Approaches* (`gis_modelling.qmd`).

```
_demo/
├── dem/
│   ├── jena_dem.tif                 DEM around Jena, 30 m, EPSG:25832 (Part 1)
│   ├── crater_lake_elevation.asc    elevation for the raindrop model (Part 2)
│   └── crater_lake_elevation.prj    its CRS (EPSG:4326)
├── outputs/
│   ├── dem/   flow_accumulation_km2.tif, streams.tif   (ready-made Part 1 results)
│   └── abm/   water_level.tif, raindrops.gpkg           (raindrop model after 12 steps)
└── python/
    ├── river_network.py    fill sinks → flow direction → flow accumulation → streams
    ├── d8_diagram.py       the 4×4 flow-direction figure on the slides
    └── export_rainfall.py  Mesa-Geo raindrop model → GeoTIFF + GeoPackage
```

## Exercise A · Rivers from a DEM (QGIS only)

1. Drag `dem/jena_dem.tif` into QGIS. Make a hillshade: *Raster ▸ Analysis ▸ Hillshade*.
2. Open *Processing ▸ Toolbox* and search for **r.watershed**.
   - *Elevation*: `jena_dem.tif`
   - *Minimum size of exterior watershed basin*: `1111` (cells; 1111 × 30 m × 30 m ≈ 1 km²)
   - Outputs: *Number of cells that drain through each cell*, *Stream segments*, *Unique label for each watershed basin*
3. Run it again with `11111` (≈ 10 km²) and compare the two stream networks.
4. Add an OpenStreetMap basemap (*Browser ▸ XYZ Tiles ▸ OpenStreetMap*) and compare the modelled rivers with real ones.

If r.watershed is not in the Toolbox, open the ready-made results in `outputs/dem/` instead.

Things to notice: accumulation cells with **negative values** receive water from outside the map (edge effect), and the DEM is a surface model, so buildings and bridges in Jena change the flow paths.

## Exercise B · Output of an agent-based model

1. Open `outputs/abm/water_level.tif` and `outputs/abm/raindrops.gpkg`. Both are in EPSG:4326.
2. Style the water with *Singleband pseudocolor*. Under *Transparency*, set `0` as no data.
3. Where did lakes form? Compare with `dem/crater_lake_elevation.asc`.

## Python (optional)

```bash
pip install mesa-geo rasterio matplotlib
cd _demo/python
python river_network.py     # writes outputs/dem/ and the slide figures
python export_rainfall.py   # writes outputs/abm/
```

## Data

- Jena DEM: Copernicus DEM GLO-30, clipped to 11.44–11.74° E, 50.83–50.99° N and reprojected to EPSG:25832.
  © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA.
- Crater Lake elevation: from Crooks, Malleson, Manley & Heppenstall (2019), *Agent-Based Modelling and Geographical Information Systems*, CC BY-SA 4.0.
  The raindrop model follows the Rainfall example in *Python for Agent-Based Modeling*, Chapter 8 (<https://github.com/abmind-community/py4abm>).
