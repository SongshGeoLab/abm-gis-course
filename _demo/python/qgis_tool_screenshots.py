"""Screenshots for the slide "In QGIS: rivers from a DEM".

Runs *inside* QGIS: adds ../qgis/rivers_from_dem.py to the Processing Toolbox
(what "Add Script to Toolbox…" does), searches for it, and opens its dialog
with the Jena DEM. Uses a fresh, throw-away QGIS profile, so your own
settings stay untouched. Afterwards run qgis_figures.py.

Run from this folder (macOS example, QGIS 4.2; QGIS closes by itself):
    /Applications/QGIS-final-4_2_0.app/Contents/MacOS/QGIS-final-4_2_0 \\
        --nologo --profiles-path /tmp/qgis-course-tool-profile \\
        --code qgis_tool_screenshots.py

(No --noplugins here: the Toolbox's Scripts section comes from the Processing plugin.)

Needs: QGIS 4 (3.x should work too).
"""

import shutil
import traceback
from pathlib import Path

from qgis.core import QgsApplication, QgsProject, QgsRasterLayer
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QDockWidget, QLineEdit
from qgis.utils import iface

# QGIS runs this file with exec(), so __file__ is not always set.
HERE = Path(globals().get("__file__", Path.cwd() / "qgis_tool_screenshots.py")).resolve().parent
TOOL = HERE.parent / "qgis" / "rivers_from_dem.py"
DEM = HERE.parent / "dem" / "jena_dem.tif"
OUT_DIR = HERE.parent / "outputs" / "qgis"


def report_errors(step):
    """Write errors to a log file: inside QGIS they would otherwise vanish."""
    def wrapped(*args):
        try:
            step(*args)
        except Exception:
            (OUT_DIR / "error.log").write_text(traceback.format_exc())
            QgsApplication.instance().exit(1)
    return wrapped


@report_errors
def add_tool():
    """Same as Toolbox ▸ Python icon ▸ Add Script to Toolbox…: copy + refresh."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    window = iface.mainWindow()
    window.showNormal()
    window.resize(1600, 960)
    scripts = Path(QgsApplication.qgisSettingsDirPath()) / "processing" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy(TOOL, scripts / TOOL.name)
    QgsApplication.processingRegistry().providerById("script").refreshAlgorithms()

    QgsProject.instance().addMapLayer(QgsRasterLayer(str(DEM), "jena_dem"))
    iface.mapCanvas().refresh()
    toolbox = next(d for d in window.findChildren(QDockWidget) if d.objectName() == "ProcessingToolbox")
    toolbox.show()
    toolbox.raise_()
    search = toolbox.findChild(QLineEdit)
    search.setText("rivers")
    QTimer.singleShot(3000, open_dialog)


@report_errors
def open_dialog():
    import processing
    window = iface.mainWindow()
    iface.messageBar().clearWidgets()
    window.grab().save(str(OUT_DIR / "tool_window.png"))
    layer = QgsProject.instance().mapLayersByName("jena_dem")[0]
    dialog = processing.createAlgorithmDialog("script:riversfromdem",
                                              {"INPUT": layer, "THRESHOLD": 1.0})
    dialog.setMinimumSize(820, 560)             # big enough to show all outputs
    dialog.show()
    QTimer.singleShot(2500, lambda: save_dialog(dialog))


@report_errors
def save_dialog(dialog):
    dialog.grab().save(str(OUT_DIR / "tool_dialog.png"))
    QgsApplication.instance().exit(0)


QTimer.singleShot(3000, add_tool)
