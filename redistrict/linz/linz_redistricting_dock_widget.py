# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ specific redistricting dock widget

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

from redistrict.gui.redistricting_dock_widget import RedistrictingDockWidget


class LinzRedistrictingDockWidget(RedistrictingDockWidget):
    """
    LINZ Specific redistricting dock widget
    """

    def __init__(self, iface=None):
        """
        Constructor for LINZ redistricting dock
        :param iface: QGIS interface
        """
        super().__init__(iface)
        self.setWindowTitle(self.tr('Redistricting - Scenario 1'))
