# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - GUI Utilities

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

from qgis.PyQt.QtCore import (Qt,
                              QPoint)


class GuiUtils:
    """
    Utilities for GUI plugin components
    """

    @staticmethod
    def float_toolbar_over_widget(toolbar, widget, offset_x=30, offset_y=50):
        """
        Moves a QToolbar so that it floats over a QWidget
        :param toolbar: toolbar to float. Call this method before showing
        the toolbar.
        :param widget: target widget
        :param offset_x: x offset from top left of widget, in pixels
        :param offset_y: y offset from top left of widget, in pixels
        :return:
        """

        global_point = widget.mapToGlobal(QPoint(0, 0))
        toolbar.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        toolbar.move(global_point.x() + offset_x, global_point.y() + offset_y)
        toolbar.adjustSize()
        toolbar.show()
