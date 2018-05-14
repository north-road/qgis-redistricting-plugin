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
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext


class LinzRedistrictingDockWidget(RedistrictingDockWidget):
    """
    LINZ Specific redistricting dock widget
    """

    def __init__(self, context: LinzRedistrictingContext, iface=None):
        """
        Constructor for LINZ redistricting dock
        :param context: initial dock context
        :param iface: QGIS interface
        """
        super().__init__(iface)
        self.update_dock_title(context=context)

    def update_dock_title(self, context: LinzRedistrictingContext):
        """
        Refreshes the dock title text, using the settings from a supplied
        context.
        :param context: redistricting context
        """
        self.setWindowTitle(self.tr('Redistricting - {} - Scenario {}').format(context.get_name_for_current_task(),
                                                                               context.scenario))
