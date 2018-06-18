# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - GUI Utilities

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

import time
import os
from qgis.PyQt.QtCore import (QCoreApplication,
                              Qt,
                              QPoint)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QProgressDialog,
                                 QDialogButtonBox)
from qgis.gui import QgsNewNameDialog


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

    @staticmethod
    def get_icon(icon: str):
        """
        Returns a plugin icon
        :param icon: icon name (svg file name)
        :return: QIcon
        """
        path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'images',
            icon)
        if not os.path.exists(path):
            return QIcon()

        return QIcon(path)


class BlockingDialog(QProgressDialog):
    """
    Mega-hacky workaround around QProgressDialog delayed painting.
    Avoids black dialogs.
    """

    def __init__(self, title, text, parent=None):
        """
        :param title: Dialog title
        :param text: Dialog text
        :param parent: Parent widget
        """
        super().__init__(text, 'Cancel', 0, 0, parent)
        self.setWindowTitle(title)
        self.setMinimumDuration(1)

    def force_show_and_paint(self):
        """
        Forces the dialog to show and be painted at least once - no more black dialogs!
        """
        self.show()
        for i in range(10):  # pylint: disable=unused-variable
            time.sleep(0.01)
            self.setValue(0)
            self.forceShow()
            QCoreApplication.processEvents()


class ConfirmationDialog(QgsNewNameDialog):
    """
    A blocking dialog which requires users to enter a preset confirmation string
    in order to proceed
    """

    def __init__(self, title='', hint='', confirm_string='', parent=None):
        """
        Constructor for ConfirmationDialog
        :param title: dialog title
        :param hint: dialog text (hint)
        :param confirm_string: string which must be entered for OK to be enabled
        :param parent: parent widget
        """
        super().__init__('', '', parent=parent)
        self.setWindowTitle(title)
        self.setHintString(hint)
        self.confirm_string = confirm_string
        self.newNameChanged.connect(self.on_name_changed)

    def on_name_changed(self):
        """
        Triggered when the name is changed
        """
        new_name = self.name()
        self.buttonBox().button(QDialogButtonBox.Ok).setEnabled(new_name == self.confirm_string)
