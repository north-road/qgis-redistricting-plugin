# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Redistricting GUI handler

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '30/04/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import (QCoreApplication,
                              QObject,
                              pyqtSignal)
from redistrict.core.district_registry import DistrictRegistry


class RedistrictGuiHandler(QObject):
    """
    Base class for redistrict handling GUI operations.
    """

    current_district_changed = pyqtSignal(int)

    def __init__(self, redistrict_dock,
                 district_registry):
        """
        Constructor for RedistrictGuiHandler
        :param redistrict_dock: linked redistricting dock
        :param district_registry: associated district registry
        """
        super().__init__()
        self._redistrict_dock = redistrict_dock
        self._district_registry = district_registry

    def redistrict_dock(self):
        """
        Returns the linked redistricting dock
        """
        return self._redistrict_dock

    def district_registry(self) -> DistrictRegistry:
        """
        Returns the linked district registry
        """
        return self._district_registry

    def show_stats_for_district(self, district):
        """
        Displays the statistics for a district in the dock
        :param district: id/code for district to show
        """
        # Base class method just shows district name
        if district is not None:
            message = QCoreApplication.translate('LinzRedistrict', '<h1>Statistics for {}</h1>').format(
                self._district_registry.get_district_title(district))
        else:
            message = ''
        self._redistrict_dock.show_message(message)
        self.current_district_changed.emit(district)
