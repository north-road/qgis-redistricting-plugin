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

from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QCheckBox,
    QPushButton,
    QMessageBox,
    QLineEdit,
    QSpinBox,
    QGroupBox,
    QGridLayout
)

from qgis.core import QgsSettings
from qgis.gui import (QgsAuthConfigSelect,
                      QgsFileWidget)

from redistrict.linz.nz_electoral_api import get_api_connector
from redistrict.gui.playsound import playsound

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

    def __init__(self, parent=None):  # pylint: disable=too-many-statements
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

        g_layout = QGridLayout()
        g_layout.addWidget(QLabel(self.tr('Check for completed requests every')), 0, 0)
        self.check_every_spin = QSpinBox()
        self.check_every_spin.setMinimum(10)
        self.check_every_spin.setMaximum(600)
        self.check_every_spin.setSuffix(' ' + self.tr('s'))
        self.check_every_spin.setValue(QgsSettings().value('redistrict/check_every', '30', int, QgsSettings.Plugins))
        g_layout.addWidget(self.check_every_spin, 0, 1)

        g_layout.addWidget(QLabel(self.tr('GMS version')), 1, 0)
        self.gms_version_combo = QComboBox()
        self.gms_version_combo.setEditable(True)
        self.gms_version_combo.addItem('GMS_TEST_VERSION')
        self.gms_version_combo.addItem('StatsNZ_MB_V1_01_20190808_1410')
        self.gms_version_combo.setCurrentText(
            QgsSettings().value('redistrict/gms_version', 'GMS_TEST_VERSION', str,
                                QgsSettings.Plugins))
        g_layout.addWidget(self.gms_version_combo, 1, 1)

        layout.addLayout(g_layout)

        self.use_mock_checkbox = QCheckBox(self.tr('Use mock Statistics NZ API'))
        self.use_mock_checkbox.setChecked(get_use_mock_api())
        layout.addWidget(self.use_mock_checkbox)

        self.test_button = QPushButton(self.tr('Test API connection'))
        self.test_button.clicked.connect(self.test_api)
        layout.addWidget(self.test_button)

        self.use_overlays_checkbox = QCheckBox(self.tr('Show updated populations during interactive redistricting'))
        self.use_overlays_checkbox.setChecked(
            QgsSettings().value('redistrict/show_overlays', False, bool, QgsSettings.Plugins))
        layout.addWidget(self.use_overlays_checkbox)

        self.use_sound_group_box = QGroupBox(self.tr('Use audio feedback'))
        self.use_sound_group_box.setCheckable(True)
        self.use_sound_group_box.setChecked(
            QgsSettings().value('redistrict/use_audio_feedback', False, bool, QgsSettings.Plugins))

        sound_layout = QGridLayout()
        sound_layout.addWidget(QLabel(self.tr('When meshblock redistricted')), 0, 0)
        self.on_redistrict_file_widget = QgsFileWidget()
        self.on_redistrict_file_widget.setDialogTitle(self.tr('Select Audio File'))
        self.on_redistrict_file_widget.setStorageMode(QgsFileWidget.GetFile)
        self.on_redistrict_file_widget.setFilePath(
            QgsSettings().value('redistrict/on_redistrict', '', str, QgsSettings.Plugins))
        self.on_redistrict_file_widget.setFilter(self.tr('Wave files (*.wav *.WAV)'))
        sound_layout.addWidget(self.on_redistrict_file_widget, 0, 1)
        self.play_on_redistrict_sound_button = QPushButton(self.tr('Test'))
        self.play_on_redistrict_sound_button.clicked.connect(self.play_on_redistrict_sound)
        sound_layout.addWidget(self.play_on_redistrict_sound_button, 0, 2)

        self.use_sound_group_box.setLayout(sound_layout)
        layout.addWidget(self.use_sound_group_box)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.setLayout(layout)

    def base_url(self) -> str:
        """
        Returns the current configured base URL
        """
        base_url = self.base_url_edit.text().strip()
        if base_url and base_url[-1] == '/':
            base_url = base_url[:-1]

        if base_url and base_url.endswith('/status'):
            base_url = base_url[:-len('/status')]

        return base_url

    def accept(self):  # pylint: disable=missing-docstring
        super().accept()
        QgsSettings().setValue('redistrict/auth_config_id', self.auth_value.configId(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/use_mock_api', self.use_mock_checkbox.isChecked(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/base_url', self.base_url(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/check_every', self.check_every_spin.value(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/show_overlays', self.use_overlays_checkbox.isChecked(), QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/use_audio_feedback', self.use_sound_group_box.isChecked(),
                               QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/on_redistrict', self.on_redistrict_file_widget.filePath(),
                               QgsSettings.Plugins)
        QgsSettings().setValue('redistrict/gms_version',
                               self.gms_version_combo.currentText(),
                               QgsSettings.Plugins)

    def test_api(self):
        """
        Tests the API connection (real or mock!)
        """
        connector = get_api_connector(use_mock=self.use_mock_checkbox.isChecked(),
                                      authcfg=self.auth_value.configId(),
                                      base_url=self.base_url())
        if connector.check():
            QMessageBox.information(self, self.tr('Test API Connection'),
                                    self.tr('API responded OK!'), QMessageBox.Ok)
        else:
            QMessageBox.critical(self, self.tr('Test API Connection'),
                                 self.tr('Could not connect to API!'), QMessageBox.Ok)

    def play_on_redistrict_sound(self):
        """
        Plays the 'on redistrict' sound
        """
        try:
            playsound(self.on_redistrict_file_widget.filePath(), block=False)
        except FileNotFoundError:
            pass
