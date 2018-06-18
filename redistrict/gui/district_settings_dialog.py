# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District settings dialog

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Alessandro Pasotti'
__date__ = '07/06/2018'
__copyright__ = 'Copyright 2018, LINZ'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QLabel,
                                 QVBoxLayout,
                                 QHBoxLayout,
                                 QCheckBox,
                                 QPushButton,
                                 QMessageBox,
                                 QLineEdit,
                                 QSpinBox)

from qgis.core import QgsSettings
from qgis.gui import QgsAuthConfigSelect

from redistrict.linz.nz_electoral_api import get_api_connector

SETTINGS_AUTH_CONFIG_KEY = 'redistrict/auth_config_id'


def get_auth_config_id() -> str:
    """Return the authentication configuration id from the settings, an empty string if not found.

    :return: authentication configuration id
    """
    return QgsSettings().value('redistrict/auth_config_id', None, str, QgsSettings.Plugins)


def get_use_mock_api() -> bool:
    """Returns True if the mock Stats NZ API should be used
    """
    return QgsSettings().value('redistrict/use_mock_api', False, bool, QgsSettings.Plugins)


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

        layout.addWidget(QLabel(self.tr('API base URL')))
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setText(QgsSettings().value('redistrict/base_url', '', str, QgsSettings.Plugins))
        layout.addWidget(self.base_url_edit)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(self.tr('Check for completed requests every')))
        self.check_every_spin = QSpinBox()
        self.check_every_spin.setMinimum(10)
        self.check_every_spin.setMaximum(600)
        self.check_every_spin.setSuffix(' ' + self.tr('s'))
        self.check_every_spin.setValue(QgsSettings().value('redistrict/check_every', '30', int, QgsSettings.Plugins))

        h_layout.addWidget(self.check_every_spin)
        layout.addLayout(h_layout)

        self.use_mock_checkbox = QCheckBox(self.tr('Use mock Statistics NZ API'))
        self.use_mock_checkbox.setChecked(get_use_mock_api())
        layout.addWidget(self.use_mock_checkbox)

        self.test_button = QPushButton(self.tr('Test API connection'))
        self.test_button.clicked.connect(self.test_api)
        layout.addWidget(self.test_button)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.setLayout(layout)

    def accept(self):  # pylint: disable=missing-docstring
        super().accept()
        QgsSettings().setValue('redistrict/auth_config_id', self.auth_value.configId(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/use_mock_api', self.use_mock_checkbox.isChecked(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/base_url', self.base_url_edit.text(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/check_every', self.check_every_spin.value(), QgsSettings.Plugins)

    def test_api(self):
        """
        Tests the API connection (real or mock!)
        """
        connector = get_api_connector(use_mock=self.use_mock_checkbox.isChecked(),
                                      authcfg=self.auth_value.configId(),
                                      base_url=self.base_url_edit.text())
        if connector.check():
            QMessageBox.information(self, self.tr('Test API Connection'),
                                    self.tr('API responded OK!'), QMessageBox.Ok)
        else:
            QMessageBox.critical(self, self.tr('Test API Connection'),
                                 self.tr('Could not connect to API!'), QMessageBox.Ok)
