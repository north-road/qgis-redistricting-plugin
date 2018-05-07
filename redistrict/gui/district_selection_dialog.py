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

from qgis.PyQt.QtCore import Qt, QObject, QCoreApplication
from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QLabel,
                                 QListWidget,
                                 QListWidgetItem,
                                 QVBoxLayout)
from qgis.gui import QgsFilterLineEdit
from qgis.utils import iface
from redistrict.core.district_registry import DistrictRegistry
from redistrict.gui.district_selection_map_tool import DistrictSelectionMapTool


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
        layout = QVBoxLayout()
        self.recent_label = QLabel(self.tr('Recently used {}').format(
            district_registry.type_string_sentence_plural()))
        layout.addWidget(self.recent_label)

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(100)
        for d in district_registry.recent_districts_list():
            item = QListWidgetItem(self.district_registry.get_district_title(d))
            item.setData(Qt.UserRole, d)
            self.recent_list.addItem(item)
        layout.addWidget(self.recent_list, 0)

        self.available_label = QLabel(self.tr('Available {}').format(
            district_registry.type_string_sentence_plural()
        ))
        layout.addWidget(self.available_label)
        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for {}').format(
            district_registry.type_string_sentence()))
        self.search.textChanged.connect(self.filter_changed)
        layout.addWidget(self.search)

        self.list = QListWidget()
        for title, code in district_registry.district_titles().items():
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, code)
            self.list.addItem(item)

        layout.addWidget(self.list, 10)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        if self.district_registry.flags() & DistrictRegistry.FLAG_ALLOWS_SPATIAL_SELECT:
            self.select_from_map_button = button_box.addButton(
                self.tr("Select from Map"), QDialogButtonBox.ActionRole)
            self.select_from_map_button.clicked.connect(self.pick_from_map)
        else:
            self.select_from_map_button = None
        self.chose_pick_from_map = False

        self.setLayout(layout)

        self.recent_list.itemSelectionChanged.connect(
            self.recent_list_item_selected)
        self.list.itemSelectionChanged.connect(
            self.list_item_selected)
        self.recent_list.itemDoubleClicked.connect(
            self.accept)
        self.list.itemDoubleClicked.connect(
            self.accept)

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
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == district:
                self.list.item(i).setSelected(True)
                return

    def selected_district(self):
        """
        Returns the district selected in the dialog
        """
        if self.recent_list.selectedItems():
            return self.recent_list.selectedItems()[0].data(Qt.UserRole)
        elif self.list.selectedItems():
            return self.list.selectedItems()[0].data(Qt.UserRole)

        return None

    def accept(self):  # pylint: disable=missing-docstring
        self.district_registry.push_recent_district(self.selected_district())
        super().accept()

    def filter_changed(self, filter_text):
        """
        Handles search filter changes
        """
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(filter_text.upper() not in item.text().upper())

    def pick_from_map(self):
        """
        Triggered when a user selects the "Select from Map" option
        """
        self.chose_pick_from_map = True
        self.reject()


class DistrictPicker(QObject):
    """
    Handles district selection, via dialog or map selection, in a blocking
    manner
    """

    def __init__(self, district_registry, parent=None):
        super().__init__(parent)
        self.district_registry = district_registry

        dlg = DistrictSelectionDialog(district_registry, parent)

        self.selected_district = None
        self.requires_confirmation = False
        res = dlg.exec_()
        iface.mainWindow().raise_()
        iface.mainWindow().activateWindow()

        if res:
            self.selected_district = dlg.selected_district()
        elif dlg.chose_pick_from_map:
            del dlg
            self.picked = False
            self.requires_confirmation = True
            self.pick_from_map()
            while not self.picked:
                QCoreApplication.processEvents()

    def pick_from_map(self):
        """
        Triggered when a user selects the "Select from Map" option
        """
        canvas = iface.mapCanvas()
        self.previous_map_tool = canvas.mapTool()
        self.picker_tool = DistrictSelectionMapTool(canvas, district_registry=self.district_registry)
        self.picker_tool.districtPicked.connect(self.picked_from_map)
        self.picker_tool.canceled.connect(self.picker_canceled)
        canvas.setFocus()
        canvas.setMapTool(self.picker_tool)

    def picked_from_map(self):
        """
        Triggered after a user has picked a point from the map
        using the map tool
        """
        canvas = iface.mapCanvas()
        canvas.setMapTool(self.previous_map_tool)

        self.selected_district = self.picker_tool.get_clicked_district()
        self.picked = True

    def picker_canceled(self):
        """
        Triggered if the district selection map tool was canceled
        """
        canvas = iface.mapCanvas()
        canvas.setMapTool(self.previous_map_tool)
        self.selected_district = None
        self.picked = True
