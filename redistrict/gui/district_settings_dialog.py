# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District settings dialog

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Alessandro Pasotti'
__date__ = '07/06/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import Qt, QObject, QCoreApplication
from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QLabel,
                                 QListWidget,
                                 QListWidgetItem,
                                 QVBoxLayout)
from qgis.gui import QgsFilterLineEdit
from qgis.utils import iface

from qgis.core import QgsSettings
from qgis.gui import QgsAuthConfigSelect

SETTINGS_AUTH_CONFIG_KEY = 'redistrict/auth_config_id'


def get_auth_config_id():
    """Return the authentication configuration id from the settings, an empty string if not found.

    :return: authentication configuration id
    :rtype: str
    """
    return QgsSettings().value('redistrict/auth_config_id', None, str, QgsSettings.Plugins)


class DistrictSettingsDialog(QDialog):
    """
    A dialog used for plugin settings
    """

    def __init__(self, parent=None):
        super().__init__(parent)


        self.setWindowTitle(self.tr('Redistrict Plugin | Settings'))
        layout = QVBoxLayout()
        self.auth_label = QLabel(self.tr('Authentication configuration'))
        layout.addWidget(self.auth_label)
        self.auth_value = QgsAuthConfigSelect()
        layout.addWidget(self.auth_value)
        auth_id = get_auth_config_id()
        if auth_id:
            self.auth_value.setConfigId(auth_id)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.setLayout(layout)


    def accept(self):  # pylint: disable=missing-docstring
        super().accept()
        QgsSettings().setValue('redistrict/auth_config_id', self.auth_value.configId(), QgsSettings.Plugins)
