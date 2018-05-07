# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Redistricting dock widget

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

from qgis.PyQt.QtWidgets import (QWidget,
                                 QGridLayout,
                                 QToolBar)
from qgis.gui import QgsDockWidget
from qgis.utils import iface


class RedistrictingDockWidget(QgsDockWidget):
    """
    Dock widget for display of redistricting statistics and operations
    """

    def __init__(self, _iface=None):
        super().__init__()

        if _iface is not None:
            self.iface = _iface
        else:
            self.iface = iface

        dock_contents = QWidget()
        grid = QGridLayout(dock_contents)
        grid.setContentsMargins(0, 0, 0, 0)

        self._dock_toolbar = QToolBar(dock_contents)
        self._dock_toolbar.setFloatable(False)
        grid.addWidget(self._dock_toolbar, 0, 0, 1, 1)

        self._dock_toolbar.setIconSize(self.iface.iconSize(True))

    def dock_toolbar(self):
        """
        Returns the dock toolbar
        """
        return self._dock_toolbar
