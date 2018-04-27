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

    def __init__(self, name='districts', districts=None):
        """
        Constructor for District Registry
        :param name: unique identifying name for registry
        :param districts: list of districts to include in registry
        """
        self.name = name
        if districts is None:
            districts = []
        self.districts = districts

    def settings_key(self):
        """
        Returns the QSettings key corresponding to this registry
        """
        return 'redistricting/{}'.format(self.name)

    def district_list(self):
        """
        Returns a complete list of districts available for redistricting to
        """
        return self.districts

    def clear_recent_districts(self):
        """
        Clears the list of recent districts
        """
        QgsSettings().setValue('{}/recent_districts'.format(
            self.settings_key()), [])

    def push_recent_district(self, district):
        """
        Pushes a district to the top of the recent districts list
        :param district: district to push to list
        """
        recent_districts = self.recent_districts_list()
        recent_districts = [district] + \
                           [d for d in recent_districts
                            if d != district]
        recent_districts = recent_districts[:MAX_RECENT_DISTRICTS]
        QgsSettings().setValue('{}/recent_districts'.format(
            self.settings_key()), recent_districts)

    def recent_districts_list(self):
        """
        Returns a list of recently used districts
        """
        return QgsSettings().value('{}/recent_districts'.format(
            self.settings_key()), [])
