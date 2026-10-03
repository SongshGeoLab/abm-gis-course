# From Model to Map: demo files

Files for the lecture *From Model to Map: bringing agent-based model outputs into GIS and QGIS*.

```
_demo/
├── netlogo/
│   ├── rainfall_gis.nlogo   the Rainfall model with export buttons (NetLogo 6.4)
│   ├── elevation.asc        input elevation raster (no CRS inside)
│   └── wgs84.prj            the CRS we assume for elevation.asc (EPSG:4326)
├── python/
│   ├── export_rainfall.py       Mesa-Geo Rainfall → GeoTIFF, GeoPackage, CSV
│   └── export_geoschelling.py   py4abm GeoSchelling → GeoPackage (4 layers)
└── outputs/
    ├── netlogo/   files written by the NetLogo model at tick 12
    └── python/    files written by the two Python scripts
```

## 1. Run the model

**NetLogo (no programming needed)**

1. Open `netlogo/rainfall_gis.nlogo` in NetLogo 6.4. Keep `elevation.asc` and `wgs84.prj` in the same folder.
2. Press **setup**, then **go**. Press **go** again to stop at about tick 12.
3. Press the three export buttons. The files are written next to the model:

| Button | File | Type |
|---|---|---|
| 4a water -> raster | `water_tick12.asc` + `.prj` | raster |
| 4b raindrops -> points | `raindrops_tick12.geojson`, `raindrops_tick12.shp` (+ .dbf .shx .prj) | points |
| Plan B: raindrops -> CSV | `raindrops_tick12.csv` (columns `x`, `y` in EPSG:4326) | table |

**Python / Mesa-Geo**

Use the environment of the [py4abm](https://github.com/abmind-community/py4abm) book (mesa 3.5, mesa-geo 0.9):

```bash
cd _demo/python
../../../py4abm/.venv/bin/python export_rainfall.py
../../../py4abm/.venv/bin/python export_geoschelling.py
```

| File | Type | CRS |
|---|---|---|
| `water_level.tif` | raster, water per cell | EPSG:4326 |
| `raindrops.gpkg`, `raindrops.csv` | points | EPSG:4326 |
| `geoschelling.gpkg` (`regions_step00`, `regions_final`, `people_step00`, `people_final`) | polygons and points | EPSG:32618 |
| `*_metadata.json` | seed, parameters, versions, field meanings | |

## 2. Open the files in QGIS

1. **Load.** Drag `.tif`, `.asc`, `.gpkg`, `.geojson` or `.shp` files into the map. For a CSV, use *Layer ▸ Add Layer ▸ Add Delimited Text Layer…*, set X field = `x`, Y field = `y`, and Geometry CRS = `EPSG:4326`.
2. **Check the CRS.** Look under *Layer Properties ▸ Information*. NetLogo's Shapefile `.prj` may appear as a custom CRS. If so, right-click ▸ *Layer CRS ▸ Set Layer CRS* → `EPSG:4326`. Add a basemap under *Browser ▸ XYZ Tiles ▸ OpenStreetMap*.
3. **Style.**
   - Elevation: *Hillshade*.
   - Water: *Singleband pseudocolor*, with `0` set as no data under *Transparency*.
   - Raindrops: small markers, or the *Heatmap* renderer.
4. **Analyse.**
   - Wet area: use *Raster Calculator* with `"water_level@1" > 0`. For areas in m², reproject to EPSG:32610, then run *Raster layer unique values report*.
   - GeoSchelling: use *Graduated* symbology on `a_share`, and compare `regions_step00` with `regions_final`.
5. **Share.** In *Project ▸ New Print Layout…*, add a title, legend, scale bar, north arrow and credits.

## Things to notice

- NetLogo exports **every** turtle variable (`COLOR`, `HEADING`, `PEN-MODE`…) as a field. Remove the ones you don't need with *Refactor fields*.
- NetLogo's `xcor` and `ycor` are **patch coordinates**, not map coordinates. The CSV export converts them with the GIS extension (`gis:envelope-of`).
- NetLogo writes `.asc` with the cell size rounded to 6 decimals, so the grid can be shifted by up to about 3 m. You won't see this on a map.
- The two tools use different random number generators, so their drop counts differ slightly. The lakes form in the same places.

## Credits

- Elevation data and the original Rainfall model: Crooks, Malleson, Manley & Heppenstall (2019), *Agent-Based Modelling and Geographical Information Systems*, CC BY-SA 4.0.
- Mesa-Geo Rainfall example: <https://github.com/mesa/mesa-examples/tree/main/gis/rainfall>
- GeoSchelling model and DC tracts: py4abm Chapter 8. Tracts are from the U.S. Census Bureau TIGER/Line 2025.
