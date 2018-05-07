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
                 gui_handler):
        """
        Constructor for map tool
        :param canvas: linked map canvas
        :param gui_handler: redistrict gui handler
        """
        super().__init__(canvas, district_registry=gui_handler.district_registry())
        self.gui_handler = gui_handler

    def canvasReleaseEvent(self, e):  # pylint: disable=missing-docstring
        if e.button() != Qt.LeftButton:
            return

        district = self.get_clicked_district()
        self.gui_handler.show_stats_for_district(district)
