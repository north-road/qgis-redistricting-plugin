"""
Common functionality used by regression tests.
"""

import sys
import logging
import os

from qgis.utils import iface
from qgis.core import QgsGeometry

LOGGER = logging.getLogger('QGIS')
QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None


def get_qgis_app(cleanup=True):
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    global QGIS_APP, PARENT, IFACE, CANVAS  # pylint: disable=W0603

    if iface:
        from qgis.core import QgsApplication  # pylint: disable=import-outside-toplevel
        QGIS_APP = QgsApplication
        CANVAS = iface.mapCanvas()
        PARENT = iface.mainWindow()
        IFACE = iface
        return QGIS_APP, CANVAS, IFACE, PARENT

    from qgis.core import QgsApplication  # pylint: disable=import-outside-toplevel
    from qgis.gui import QgsMapCanvas  # pylint: disable=import-outside-toplevel
    from qgis.PyQt.QtCore import QSize  # pylint: disable=import-outside-toplevel
    from qgis.PyQt.QtWidgets import QWidget  # pylint: disable=import-outside-toplevel
    from .qgis_interface import QgisInterface  # pylint: disable=import-outside-toplevel

    global QGISAPP  # pylint: disable=global-variable-undefined,used-before-assignment

    try:
        QGISAPP  # pylint: disable=used-before-assignment
    except NameError:
        myGuiFlag = True  # All test will run qgis in gui mode

        # In python3 we need to convert to a bytes object (or should
        # QgsApplication accept a QString instead of const char* ?)
        try:
            argvb = list(map(os.fsencode, sys.argv))
        except AttributeError:
            argvb = sys.argv

        # Note: QGIS_PREFIX_PATH is evaluated in QgsApplication -
        # no need to mess with it here.
        QGISAPP = QgsApplication(argvb, myGuiFlag)

        QGISAPP.initQgis()
        s = QGISAPP.showSettings()
        LOGGER.debug(s)

        def debug_log_message(message, tag, level):
            """
            Prints a debug message to a log
            :param message: message to print
            :param tag: log tag
            :param level: log message level (severity)
            :return:
            """
            print(f'{tag}({level}): {message}')

        QgsApplication.instance().messageLog().messageReceived.connect(
            debug_log_message)

        if cleanup:
            import atexit  # pylint: disable=import-outside-toplevel

            @atexit.register
            def exitQgis():  # pylint: disable=unused-variable
                """
                Gracefully closes the QgsApplication instance
                """
                try:
                    QGISAPP.exitQgis()  # pylint: disable=used-before-assignment
                    QGISAPP = None  # pylint: disable=redefined-outer-name
                except NameError:
                    pass

    if PARENT is None:
        # noinspection PyPep8Naming
        PARENT = QWidget()

    if CANVAS is None:
        # noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QSize(400, 400))

    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        # noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGISAPP, CANVAS, IFACE, PARENT


def normalized_wkt(geometry: QgsGeometry, precision: int = 17) -> str:
    """
    Returns the WKT of a normalized geometry
    """
    normalized = QgsGeometry(geometry)
    normalized.normalize()
    return normalized.asWkt(precision)
