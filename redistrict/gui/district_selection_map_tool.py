# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District selection map tool

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import QgsRectangle
from qgis.gui import QgsMapTool


class DistrictSelectionMapTool(QgsMapTool):
    """
    Map tool for selecting a district from the map
    """

    districtPicked = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, canvas, district_registry):
        """
        Constructor for DistrictSelectionMapTool
        :param canvas: map canvas for tool
        :param district_registry: associated district registry
        """
        super().__init__(canvas)
        self.district_registry = district_registry
        self.rectangle = None

    def flags(self):  # pylint: disable=missing-docstring
        return QgsMapTool.Transient | QgsMapTool.AllowZoomRect

    def keyReleaseEvent(self, e):  # pylint: disable=missing-docstring
        if e.key() == Qt.Key_Escape:
            self.canceled.emit()

    def canvasReleaseEvent(self, e):  # pylint: disable=missing-docstring
        if e.button() != Qt.LeftButton:
            return

        self.districtPicked.emit()

    def canvasPressEvent(self, e):
        """
        Handle canvas click and build search rectangle
        """
        if e.button() != Qt.LeftButton:
            return

        search_radius = self.searchRadiusMU(self.canvas())
        self.rectangle = QgsRectangle(e.mapPoint().x() - search_radius,
                                      e.mapPoint().y() - search_radius,
                                      e.mapPoint().x() + search_radius,
                                      e.mapPoint().y() + search_radius)

    def search_rectangle(self):
        """
        Returns the canvas search rectangle
        """
        return self.rectangle

    def get_clicked_district(self):
        """
        Gets the district most recently clicked using the tool
        """
        return self.district_registry.get_district_at_point(self.rectangle,
                                                            self.canvas().mapSettings().destinationCrs())
