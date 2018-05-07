# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District Statistics Tool

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

from qgis.PyQt.QtCore import Qt
from redistrict.gui.district_selection_map_tool import DistrictSelectionMapTool


class DistrictStatisticsTool(DistrictSelectionMapTool):
    """
    A map tool for showing district statistics
    """

    def __init__(self, canvas,
                 district_registry):
        """
        Constructor for map tool
        :param canvas: linked map canvas
        :param district_registry: associated district registry
        """
        super().__init__(canvas, district_registry)

    def canvasReleaseEvent(self, e):  # pylint: disable=missing-docstring
        if e.button() != Qt.LeftButton:
            return
