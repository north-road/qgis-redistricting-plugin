# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District selection dialog

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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QLabel,
                                 QListWidget,
                                 QVBoxLayout)
from qgis.gui import QgsFilterLineEdit


class DistrictSelectionDialog(QDialog):
    """
    A dialog used for selecting from available districts
    :param district_registry: associated registry of available
    districts to show
    """

    def __init__(self, district_registry, parent=None):
        super().__init__(parent)

        self.district_registry = district_registry

        self.setWindowTitle(self.tr('Select New {}').format(
            district_registry.type_string_title()))
        l = QVBoxLayout()
        self.recent_label = QLabel(self.tr('Recently used {}').format(
            district_registry.type_string_sentence_plural()))
        l.addWidget(self.recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(100)
        for d in district_registry.recent_districts_list():
            self.recent_list.addItem(d)
        l.addWidget(self.recent_list, 0)

        self.available_label = QLabel(self.tr('Available {}').format(
            district_registry.type_string_sentence_plural()
        ))
        l.addWidget(self.available_label)
        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for {}').format(
            district_registry.type_string_sentence()))
        self.search.textChanged.connect(self.filter_changed)
        l.addWidget(self.search)

        self.list = QListWidget()
        for d in district_registry.district_list():
            self.list.addItem(d)

        l.addWidget(self.list, 10)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        l.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.select_from_map_button = button_box.addButton(
            self.tr("Select from Map"), QDialogButtonBox.ActionRole)

        self.setLayout(l)

        self.recent_list.itemSelectionChanged.connect(
            self.recent_list_item_selected)
        self.list.itemSelectionChanged.connect(
            self.list_item_selected)

        # select most recently used district by default
        if self.recent_list.count() > 0:
            self.recent_list.item(0).setSelected(True)

    def recent_list_item_selected(self):
        """
        Handles a selection made in the recent district list
        """
        if self.recent_list.selectedItems():
            self.list.clearSelection()

    def list_item_selected(self):
        """
        Handles a selection made in the complete district list
        """
        if self.list.selectedItems():
            self.recent_list.clearSelection()

    def set_selected_district(self, district):
        """
        Sets the district selected in the dialog
        :param district: district to select
        """
        matches = self.list.findItems(district, Qt.MatchExactly)
        if matches:
            matches[0].setSelected(True)

    def selected_district(self):
        """
        Returns the district selected in the dialog
        """
        if self.recent_list.selectedItems():
            return self.recent_list.selectedItems()[0].text()
        elif self.list.selectedItems():
            return self.list.selectedItems()[0].text()

        return None

    def accept(self):  # pylint: disable=missing-docstring
        self.district_registry.push_recent_district(self.selected_district())
        super().accept()

    def filter_changed(self, filter):
        """
        Handles search filter changes
        """
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(filter.upper() not in item.text().upper())