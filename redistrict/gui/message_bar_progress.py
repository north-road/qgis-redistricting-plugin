# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Progress reporting message bar item

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

from qgis.PyQt.QtCore import (Qt,
                              QObject)
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.core import Qgis
from qgis.gui import QgisInterface


class MessageBarProgressItem(QObject):
    """
    Message bar item which shows a progress report bar
    """

    def __init__(self, text, iface: QgisInterface, parent: QObject = None):
        """
        Constructor for MessageBarProgressItem
        :param text: text to show
        :param parent: parent object
        """
        super().__init__(parent)
        self.iface = iface
        self.progressMessageBar = \
            self.iface.messageBar().createMessage(text)
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.progressMessageBar.destroyed.connect(self.clear_progress)
        self.progressMessageBar.layout().addWidget(self.progress)
        self.iface.messageBar().pushWidget(self.progressMessageBar,
                                           Qgis.Info)

    def close(self):  # pylint disable=may-be-static
        """
        Closes the message bar item
        """
        if self.progressMessageBar is not None:
            self.iface.messageBar().popWidget(self.progressMessageBar)

    def clear_progress(self):
        """
        Called on deletion of the progress bar, e.g. by user closing the bar
        """
        self.progress = None
        self.progressMessageBar = None

    def set_progress(self, progress: float):
        """
        Sets the progress to show in the item
        :param progress: float for percent progress, 0 - 100
        """
        if self.progress is not None:
            self.progress.setValue(int(progress))
