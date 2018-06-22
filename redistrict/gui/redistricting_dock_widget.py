# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Redistricting dock widget

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, LINZ'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtWidgets import (QWidget,
                                 QGridLayout,
                                 QToolBar,
                                 QTextBrowser)
from qgis.gui import (QgsDockWidget,
                      QgisInterface)
from qgis.utils import iface


class RedistrictingDockWidget(QgsDockWidget):
    """
    Dock widget for display of redistricting statistics and operations
    """

    def __init__(self, _iface: QgisInterface = None):
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

        self.frame = QTextBrowser()
        self.frame.setOpenLinks(False)
        self.frame.anchorClicked.connect(self.anchor_clicked)
        grid.addWidget(self.frame, 1, 0, 1, 1)

        self.setWidget(dock_contents)

    def dock_toolbar(self):
        """
        Returns the dock toolbar
        """
        return self._dock_toolbar

    def show_message(self, html):
        """
        Shows a HTML formatted message in the dock, replacing
        its current contents
        :param html: HTML to show
        """
        self.frame.setHtml(html)
        self.setUserVisible(True)

    def anchor_clicked(self, link: QUrl):
        """
        Called on clicking an anchor link in the dock frame
        :param link: link clicked
        """
        pass
