"""Screenshots for the slide "Add an OpenStreetMap basemap in QGIS".

Runs *inside* QGIS and clicks through what students do: Browser ▸ XYZ Tiles ▸
New Connection…, fill in OpenStreetMap, then add it under the modelled
streams. Uses a fresh, throw-away QGIS profile, so your own settings stay
untouched. Afterwards run qgis_figures.py to add the numbered markers.

Run from this folder (macOS example, QGIS 4.2; QGIS closes by itself):
    /Applications/QGIS-final-4_2_0.app/Contents/MacOS/QGIS-final-4_2_0 \\
        --nologo --noplugins --profiles-path /tmp/qgis-course-profile \\
        --code qgis_osm_screenshots.py

Needs: QGIS 4 (3.x should work too) and internet for the map tiles.
"""

import traceback
from pathlib import Path

from qgis.core import (QgsApplication, QgsCoordinateTransform, QgsPalettedRasterRenderer,
                       QgsProject, QgsRasterLayer)
from qgis.gui import QgsBrowserTreeView, QgsDataItemGuiContext, QgsGui
from qgis.PyQt.QtCore import QModelIndex, QTimer
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication, QDialogButtonBox, QLineEdit, QMenu
from qgis.utils import iface

# QGIS runs this file with exec(), so __file__ is not always set.
HERE = Path(globals().get("__file__", Path.cwd() / "qgis_osm_screenshots.py")).resolve().parent
STREAMS = HERE.parent / "outputs" / "dem" / "streams.tif"
OUT_DIR = HERE.parent / "outputs" / "qgis"
OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def report_errors(step):
    """Write errors to a log file: inside QGIS they would otherwise vanish."""
    def wrapped(*args):
        try:
            step(*args)
        except Exception:
            (OUT_DIR / "error.log").write_text(traceback.format_exc())
            QgsApplication.instance().exit(1)
    return wrapped


def browser_view():
    return next(v for v in iface.mainWindow().findChildren(QgsBrowserTreeView)
                if v.model() is not None and v.isVisible())


def find_row(model, text, parent=QModelIndex()):
    for row in range(model.rowCount(parent)):
        index = model.index(row, 0, parent)
        if model.data(index) == text:
            return index
    return None


@report_errors
def open_new_connection():
    """Step 1: right-click XYZ Tiles ▸ New Connection…"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    window = iface.mainWindow()
    window.showNormal()
    window.resize(1600, 960)
    xyz = next(item for item in iface.browserModel().rootItems() if item.name() == "XYZ Tiles")
    menu = QMenu(window)
    for provider in QgsGui.dataItemGuiProviderRegistry().providers():
        provider.populateContextMenu(xyz, menu, [xyz], QgsDataItemGuiContext())
    new_connection = next(a for a in menu.actions() if a.text().startswith("New Connection"))
    QTimer.singleShot(3000, fill_dialog)        # the dialog blocks, so fill it from a timer
    new_connection.trigger()


@report_errors
def fill_dialog():
    """Step 2: name + URL, screenshot, OK."""
    dialog = QApplication.activeModalWidget()
    fields = {edit.objectName(): edit for edit in dialog.findChildren(QLineEdit)}
    fields["mEditName"].setText("OpenStreetMap")
    fields["mEditUrl"].setText(OSM_URL)
    QTimer.singleShot(800, lambda: save_dialog(dialog))


@report_errors
def save_dialog(dialog):
    dialog.grab().save(str(OUT_DIR / "xyz_dialog.png"))
    dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).click()
    QTimer.singleShot(2000, add_layers)


@report_errors
def add_layers():
    """Steps 3–4: select OpenStreetMap in the Browser, add it below the modelled streams."""
    view = browser_view()
    xyz = find_row(view.model(), "XYZ Tiles")
    view.expand(xyz)
    QTimer.singleShot(1500, lambda: view.setCurrentIndex(find_row(view.model(), "OpenStreetMap", xyz)))

    project = QgsProject.instance()
    project.addMapLayer(QgsRasterLayer(f"type=xyz&url={OSM_URL}&zmax=19&zmin=0", "OpenStreetMap", "wms"))
    streams = QgsRasterLayer(str(STREAMS), "streams (model)")
    classes = [QgsPalettedRasterRenderer.Class(0, QColor(0, 0, 0, 0), "land"),
               QgsPalettedRasterRenderer.Class(1, QColor(220, 30, 30), "modelled river")]
    streams.setRenderer(QgsPalettedRasterRenderer(streams.dataProvider(), 1, classes))
    project.addMapLayer(streams)
    to_project = QgsCoordinateTransform(streams.crs(), project.crs(), project)
    iface.mapCanvas().setExtent(to_project.transformBoundingBox(streams.extent()))
    iface.mapCanvas().refresh()
    QTimer.singleShot(15000, save_window)       # give the tiles time to load


@report_errors
def save_window():
    iface.messageBar().clearWidgets()
    iface.mainWindow().grab().save(str(OUT_DIR / "qgis_window.png"))
    QgsApplication.instance().exit(0)


QTimer.singleShot(3000, open_new_connection)
