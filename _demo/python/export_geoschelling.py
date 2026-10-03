"""Run the py4abm GeoSchelling model on Washington, DC tracts and export it.

This reuses the tested model in py4abm/code/ch08/geoschelling/model.py.
It writes one GeoPackage with the start and the end of the run, so students
can compare the two maps in QGIS.

Output (in ../outputs/python/geoschelling.gpkg), CRS EPSG:32618 (UTM 18N):
    regions_step00, regions_final   tract polygons with a_count, b_count, a_share
    people_step00,  people_final    person points with group and happy

Run with the py4abm environment:
    ../../../py4abm/.venv/bin/python export_geoschelling.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY4ABM = HERE.parents[2] / "py4abm"
sys.path.insert(0, str(PY4ABM / "code" / "ch08"))

import mesa  # noqa: E402
import mesa_geo  # noqa: E402
from geoschelling.model import DCSegregationModel  # noqa: E402

OUTPUT = HERE.parent / "outputs" / "python" / "geoschelling.gpkg"


def export_snapshot(snapshot, suffix):
    regions = snapshot.regions_geodataframe()
    regions["a_share"] = (regions["a_count"] / regions["occupancy"]).round(3)
    regions.to_file(OUTPUT, layer=f"regions_{suffix}", driver="GPKG")

    people = snapshot.people_geodataframe()
    people["happy"] = people["happy"].astype(int)
    people.to_file(OUTPUT, layer=f"people_{suffix}", driver="GPKG")


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.unlink(missing_ok=True)

    model = DCSegregationModel(PY4ABM / "data/ch08/geoschelling/dc_tracts_2025.gpkg")
    while model.running:
        model.step()
    final = model.latest_snapshot

    export_snapshot(model.snapshot_at(0), "step00")
    export_snapshot(final, "final")

    metadata = {
        "model": "GeoSchelling on DC census tracts (py4abm Chapter 8)",
        "input": "dc_tracts_2025.gpkg (U.S. Census Bureau TIGER/Line 2025)",
        "crs": "EPSG:32618",
        "seed": model.seed,
        "happiness_threshold": model.happiness_threshold,
        "people_per_tract": model.people_per_tract,
        "final_step": final.step,
        "fields": {
            "a_share": "a_count / occupancy (0-1)",
            "happy": "1 if the share of the person's own group in the tract >= threshold",
        },
        "versions": {"mesa": mesa.__version__, "mesa_geo": mesa_geo.__version__},
    }
    (OUTPUT.parent / "geoschelling_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"final step {final.step}; wrote 4 layers to {OUTPUT}")


if __name__ == "__main__":
    main()
