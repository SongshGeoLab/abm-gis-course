"""QGIS Processing tool: rivers from a DEM, without GRASS.

The same three steps as on the slides, in plain NumPy:
fill sinks → flow direction (D8) → flow accumulation → threshold.

Install once: Processing Toolbox ▸ Python icon ▸ "Add Script to Toolbox…" ▸
pick this file. The tool then appears under Scripts ▸ GIS and Modelling.
Tested in QGIS 4.2 and written to run in QGIS 3 as well; it only needs NumPy and
GDAL, which come with QGIS.

The DEM must be in a projected CRS with metres (for example EPSG:25832),
so that cell sizes and slopes are in the same unit.
"""

import heapq

import numpy as np
from osgeo import gdal
from qgis.core import (QgsProcessingAlgorithm, QgsProcessingException,
                       QgsProcessingParameterNumber, QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterRasterLayer, QgsUnitTypes)

# The 8 neighbours (row offset, column offset) of a cell.
NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

try:                                            # QGIS ≥ 3.36 and QGIS 4
    from qgis.core import Qgis
    DOUBLE = Qgis.ProcessingNumberParameterType.Double
    METRES = Qgis.DistanceUnit.Meters
except AttributeError:                          # older QGIS 3
    DOUBLE = QgsProcessingParameterNumber.Double
    METRES = QgsUnitTypes.DistanceMeters


def fill_sinks(dem, outlet, feedback):
    """Raise every pit until water can flow out of the map (priority flood).

    `outlet` marks where water may leave: the map edge and cells next to no-data.
    """
    nrows, ncols = dem.shape
    filled = dem.copy()
    done = outlet.copy()
    queue = [(filled[r, c], r, c) for r, c in zip(*np.nonzero(outlet))]
    heapq.heapify(queue)
    processed, total = 0, dem.size
    while queue:
        z, r, c = heapq.heappop(queue)
        for dr, dc in NEIGHBOURS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < nrows and 0 <= cc < ncols and not done[rr, cc]:
                # a tiny slope so flat filled areas still drain
                filled[rr, cc] = max(filled[rr, cc], z + 1e-4)
                done[rr, cc] = True
                heapq.heappush(queue, (filled[rr, cc], rr, cc))
        processed += 1
        if processed % 50000 == 0:
            if feedback.isCanceled():
                raise QgsProcessingException("Cancelled")
            feedback.setProgress(10 + 50 * processed / total)
    return filled


def flow_direction(filled, cell_x, cell_y):
    """D8: index of the steepest-downhill neighbour of each cell, or -1 (no way down)."""
    nrows, ncols = filled.shape
    padded = np.pad(filled, 1, constant_values=np.inf)      # outside the map: never downhill
    best_slope = np.zeros(filled.shape)
    direction = np.full(filled.shape, -1, dtype=np.int8)
    for k, (dr, dc) in enumerate(NEIGHBOURS):
        neighbour = padded[1 + dr:1 + dr + nrows, 1 + dc:1 + dc + ncols]
        distance = np.hypot(dr * cell_y, dc * cell_x)
        with np.errstate(invalid="ignore"):         # no-data next to no-data: -inf - -inf
            slope = (filled - neighbour) / distance
        steeper = slope > best_slope
        best_slope[steeper] = slope[steeper]
        direction[steeper] = k
    return direction


def flow_accumulation(filled, direction, feedback):
    """Count how many cells drain through each cell (each cell counts itself)."""
    accumulation = np.ones(filled.shape)
    ncols = filled.shape[1]
    order = np.argsort(filled, axis=None)[::-1]               # highest cell first
    total = len(order)
    for i, index in enumerate(order):
        r, c = divmod(int(index), ncols)
        k = direction[r, c]
        if k >= 0:
            dr, dc = NEIGHBOURS[k]
            accumulation[r + dr, c + dc] += accumulation[r, c]
        if i % 100000 == 0:
            if feedback.isCanceled():
                raise QgsProcessingException("Cancelled")
            feedback.setProgress(65 + 35 * i / total)
    return accumulation


def write_raster(path, array, source, dtype, nodata):
    driver = gdal.GetDriverByName("GTiff")
    out = driver.Create(path, source.RasterXSize, source.RasterYSize, 1, dtype,
                        options=["COMPRESS=DEFLATE"])
    out.SetGeoTransform(source.GetGeoTransform())
    out.SetProjection(source.GetProjection())
    band = out.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(array)
    out.FlushCache()


class RiversFromDem(QgsProcessingAlgorithm):
    INPUT, THRESHOLD, ACCUMULATION, STREAMS = "INPUT", "THRESHOLD", "ACCUMULATION", "STREAMS"

    def name(self):
        return "riversfromdem"

    def displayName(self):
        return "Rivers from a DEM (no GRASS)"

    def group(self):
        return "GIS and Modelling"

    def groupId(self):
        return "gismodelling"

    def shortHelpString(self):
        return ("Fill sinks → flow direction (D8) → flow accumulation → streams.\n\n"
                "A cell is a river if at least the threshold area (km²) drains through it.\n"
                "Use a DEM in a projected CRS with metres.")

    def createInstance(self):
        return RiversFromDem()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, "Elevation (DEM)"))
        self.addParameter(QgsProcessingParameterNumber(
            self.THRESHOLD, "River threshold: area draining through a cell (km²)",
            type=DOUBLE, defaultValue=1.0, minValue=0.0001))
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.ACCUMULATION, "Flow accumulation (km²)"))
        self.addParameter(QgsProcessingParameterRasterDestination(self.STREAMS, "Streams"))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        threshold_km2 = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        accumulation_path = self.parameterAsOutputLayer(parameters, self.ACCUMULATION, context)
        streams_path = self.parameterAsOutputLayer(parameters, self.STREAMS, context)
        if layer.providerType() != "gdal":
            raise QgsProcessingException("Please use a DEM file (for example a GeoTIFF), "
                                         "not a web or database layer.")
        if layer.crs().isGeographic():
            raise QgsProcessingException(
                "The DEM is in degrees. Reproject it to a CRS in metres first "
                "(Raster ▸ Projections ▸ Warp).")
        if layer.crs().mapUnits() != METRES:
            raise QgsProcessingException("The DEM's CRS must use metres, so that areas come out in km².")

        source = gdal.Open(layer.source())
        band = source.GetRasterBand(1)
        dem = band.ReadAsArray().astype("float64")
        nodata = band.GetNoDataValue()
        missing = np.isnan(dem) if nodata is None else (dem == nodata) | np.isnan(dem)
        cell_x, cell_y = layer.rasterUnitsPerPixelX(), layer.rasterUnitsPerPixelY()
        cell_km2 = cell_x * cell_y / 1e6
        feedback.pushInfo(f"{dem.shape[1]} × {dem.shape[0]} cells of {cell_x:g} × {cell_y:g} m")

        # Water may leave the map at the edge and where the DEM has no data.
        edge = np.zeros(dem.shape, dtype=bool)
        edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
        near_missing = np.zeros(dem.shape, dtype=bool)
        if missing.any():
            padded = np.pad(missing, 1)
            for dr, dc in NEIGHBOURS:
                near_missing |= padded[1 + dr:1 + dr + dem.shape[0], 1 + dc:1 + dc + dem.shape[1]]
        dem[missing] = -np.inf                  # never raised, never flows anywhere
        outlet = (edge | near_missing) & ~missing

        feedback.setProgressText("1/3 Filling sinks")
        filled = fill_sinks(dem, outlet | missing, feedback)
        feedback.setProgressText("2/3 Flow direction (D8)")
        direction = flow_direction(filled, cell_x, cell_y)
        direction[outlet | missing] = -1        # water leaves the map here
        feedback.setProgress(65)
        feedback.setProgressText("3/3 Flow accumulation")
        area_km2 = flow_accumulation(filled, direction, feedback) * cell_km2
        streams = (area_km2 >= threshold_km2).astype("uint8")

        area_km2[missing] = -1
        streams[missing] = 255
        write_raster(accumulation_path, area_km2, source, gdal.GDT_Float32, -1)
        write_raster(streams_path, streams, source, gdal.GDT_Byte, 255)
        feedback.pushInfo(f"Largest catchment in view: {area_km2.max():.0f} km²; "
                          f"river cells: {int((streams == 1).sum()):,}")
        return {self.ACCUMULATION: accumulation_path, self.STREAMS: streams_path}
