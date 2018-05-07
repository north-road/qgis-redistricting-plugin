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

from qgis.PyQt.QtCore import QCoreApplication


class RedistrictGuiHandler:
    """
    Base class for redistrict handling GUI operations.
    """

    def __init__(self, redistrict_dock,
                 district_registry):
        """
        Constructor for RedistrictGuiHandler
        :param redistrict_dock: linked redistricting dock
        :param district_registry: associated district registry
        """
        self._redistrict_dock = redistrict_dock
        self._district_registry = district_registry

    def redistrict_dock(self):
        """
        Returns the linked redistricting dock
        """
        return self._redistrict_dock

    def show_stats_for_district(self, district):
        """
        Displays the statistics for a district in the dock
        :param district: id/code for district to show
        """
        # Base class method just shows district name
        self._redistrict_dock.show_message(QCoreApplication.translate('LinzRedistrict', '<h1>Statistics for {}</h1>').format(
            self._district_registry.get_district_title(district)))
