"""Run a small Mesa-Geo Rainfall model and export its state as GIS files.

The model follows the Rainfall example used in py4abm Chapter 8 (originally
from mesa-examples/gis/rainfall and the ABMGIS book): raindrops fall on an
elevation raster, move to the lowest neighbouring cell (elevation + water),
and flow out when they reach row 0 or column 0.

Outputs (in ../outputs/python/):
    water_level.tif   raster, one band, water per cell
    raindrops.gpkg    points, one row per raindrop still on the map
    raindrops.csv     the same points as a plain x, y table

Run with the py4abm environment:
    ../../../py4abm/.venv/bin/python export_rainfall.py
"""

from __future__ import annotations

import json
from pathlib import Path

import mesa
import mesa_geo as mg
import numpy as np
from shapely.geometry import Point

HERE = Path(__file__).resolve().parent
ELEVATION = HERE.parent / "netlogo" / "elevation.asc"
OUTPUTS = HERE.parent / "outputs" / "python"

SEED = 202408
RAIN_RATE = 500
WATER_HEIGHT = 5
STEPS = 12
CRS = "EPSG:4326"  # assumed: elevation.asc ships without a .prj


class LakeCell(mg.Cell):
    def __init__(self, model, pos=None, indices=None):
        super().__init__(model, pos, indices)
        self.elevation = None
        self.water_level = None


class Raindrop(mg.GeoAgent):
    def __init__(self, model, cell):
        super().__init__(model, geometry=Point(cell.xy), crs=model.space.crs)
        self.cell = cell
        self.created_step = model.steps
        self.moves = 0

    def step(self):
        neighbors = self.model.layer.get_neighboring_cells(
            self.cell.pos, moore=True, include_center=True
        )
        destination = min(neighbors, key=lambda c: c.elevation + c.water_level)
        if destination is self.cell:
            return
        self.cell.water_level -= WATER_HEIGHT
        self.moves += 1
        if self.model.is_outlet(destination):
            self.model.outflow += 1
            self.model.space.remove_agent(self)
            self.remove()
            return
        destination.water_level += WATER_HEIGHT
        self.cell = destination
        self.geometry = Point(destination.xy)


class Rainfall(mesa.Model):
    def __init__(self, elevation_file=ELEVATION, seed=SEED):
        super().__init__(rng=seed)
        self.space = mg.GeoSpace(crs=CRS, warn_crs_conversion=False)

        # Step 1: load the elevation raster into cells
        self.layer = mg.RasterLayer.from_file(
            str(elevation_file),
            model=self,
            cell_cls=LakeCell,
            attr_name="elevation",
        )
        self.layer.crs = CRS
        self.layer.apply_raster(
            np.zeros((1, self.layer.height, self.layer.width)),
            attr_name="water_level",
        )
        self.space.add_layer(self.layer)
        self.outflow = 0

    def is_outlet(self, cell):
        row, col = cell.rowcol
        return row == 0 or col == 0

    def step(self):
        for _ in range(RAIN_RATE):
            x = int(self.rng.integers(self.layer.width))
            y = int(self.rng.integers(self.layer.height))
            cell = self.layer.cells[x][y]
            if self.is_outlet(cell):
                self.outflow += 1
                continue
            cell.water_level += WATER_HEIGHT
            self.space.add_agents(Raindrop(self, cell))
        self.agents_by_type[Raindrop].shuffle_do("step")

    @property
    def contained(self):
        return len(self.agents_by_type[Raindrop])


def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    model = Rainfall()
    for _ in range(STEPS):
        model.step()
        print(f"step {model.steps:2d}: contained={model.contained:5d} outflow={model.outflow:4d}")

    # Step 4a: export a raster (cells -> GeoTIFF)
    model.layer.to_file(
        str(OUTPUTS / "water_level.tif"), attr_name="water_level", driver="GTiff"
    )

    # Step 4b: export agents as points (GeoAgents -> GeoPackage)
    drops = model.space.get_agents_as_GeoDataFrame(Raindrop)
    drops = drops[["unique_id", "created_step", "moves", "geometry"]]
    drops.to_file(OUTPUTS / "raindrops.gpkg", layer="raindrops", driver="GPKG")

    # Plan B: a plain CSV with x, y columns
    table = drops.assign(x=drops.geometry.x, y=drops.geometry.y).drop(columns="geometry")
    table.to_csv(OUTPUTS / "raindrops.csv", index=False)

    # Record what was exported
    metadata = {
        "model": "Rainfall (Mesa-Geo)",
        "input": "elevation.asc (ABMGIS, CC BY-SA 4.0)",
        "crs": CRS + " (assumed, not embedded in elevation.asc)",
        "seed": SEED,
        "rain_rate": RAIN_RATE,
        "water_height": WATER_HEIGHT,
        "steps": STEPS,
        "contained": model.contained,
        "outflow": model.outflow,
        "fields": {
            "water_level.tif": "water per cell = retained raindrops x water_height (model units)",
            "raindrops.*": "unique_id, created_step, moves; point at the cell centre",
        },
        "versions": {"mesa": mesa.__version__, "mesa_geo": mg.__version__},
    }
    (OUTPUTS / "rainfall_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"wrote {len(drops)} raindrops and water_level.tif to {OUTPUTS}")


if __name__ == "__main__":
    main()
