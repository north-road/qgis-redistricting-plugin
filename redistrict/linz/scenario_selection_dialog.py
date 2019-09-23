# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Scenario selection dialog

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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QListWidget,
                                 QListWidgetItem,
                                 QVBoxLayout)
from qgis.gui import QgsFilterLineEdit
from redistrict.linz.scenario_registry import ScenarioRegistry


class ScenarioSelectionDialog(QDialog):
    """
    A dialog used for selecting from available scenarios
    """

    def __init__(self, scenario_registry: ScenarioRegistry, parent=None):
        """
        Constructor for ScenarioSelectionDialog
        :param scenario_registry: linked scenario registry
        :param parent: parent widget
        """
        super().__init__(parent)

        self.scenario_registry = scenario_registry

        self.setWindowTitle(self.tr('Select Active Scenario'))

        layout = QVBoxLayout()

        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for scenario'))
        self.search.textChanged.connect(self.filter_changed)
        layout.addWidget(self.search)

        self.list = QListWidget()
        for title, scenario_id in scenario_registry.scenario_titles().items():
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, scenario_id)
            self.list.addItem(item)

        layout.addWidget(self.list, 10)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.setLayout(layout)

        self.list.itemDoubleClicked.connect(
            self.accept)

        # select last scenario by default
        if self.list.count() > 0:
            self.list.item(self.list.count() - 1).setSelected(True)

    def set_selected_scenario(self, scenario):
        """
        Sets the scenario selected in the dialog
        :param scenario: scenario to select
        """
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == scenario:
                self.list.item(i).setSelected(True)
                return

    def selected_scenario(self):
        """
        Returns the scenario selected in the dialog
        """
        if self.list.selectedItems():
            return self.list.selectedItems()[0].data(Qt.UserRole)

        return None

    def filter_changed(self, filter_text):
        """
        Handles search filter changes
        """
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(filter_text.upper() not in item.text().upper())
