# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District registry

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

from qgis.core import QgsSettings

MAX_RECENT_DISTRICTS = 5


class DistrictRegistry():
    """
    A registry for handling available districts
    """

    def __init__(self, districts=None):
        """
        Constructor for District Registry
        :param districts: list of districts to include in registry
        """
        if districts is None:
            districts = []
        self.districts = districts

        s = QgsSettings()
        self.recent_districts = s.value('redistricting/recent_districts', [])

    def district_list(self):
        """
        Returns a complete list of districts available for redistricting to
        """
        return self.districts

    def push_recent_district(self, district):
        """
        Pushes a district to the top of the recent districts list
        :param district: district to push to list
        """
        self.recent_districts = [district] + \
                                [d for d in self.recent_districts
                                 if d != district]
        self.recent_districts = self.recent_districts[:MAX_RECENT_DISTRICTS]
        s = QgsSettings()
        s.setValue('redistricting/recent_districts', self.recent_districts)

    def recent_districts_list(self):
        """
        Returns a list of recently used districts
        """
        return self.recent_districts
