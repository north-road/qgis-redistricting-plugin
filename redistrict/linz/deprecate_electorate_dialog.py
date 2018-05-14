# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Deprecate electorate dialog

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
                                 QListWidget,
                                 QListWidgetItem,
                                 QVBoxLayout)
from qgis.core import QgsFeatureRequest
from qgis.gui import QgsFilterLineEdit
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry


class DeprecateElectorateDialog(QDialog):
    """
    A dialog used for selecting electorates to deprecate (or un-deprecate)
    :param district_registry: associated registry of available
    districts to show
    """

    def __init__(self, electorate_registry: LinzElectoralDistrictRegistry, parent=None):
        super().__init__(parent)

        self.electorate_registry = electorate_registry

        self.setWindowTitle(self.tr('Deprecate Electorate'))

        layout = QVBoxLayout()

        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for {}').format(
            electorate_registry.type_string_sentence()))
        self.search.textChanged.connect(self.filter_changed)
        layout.addWidget(self.search)

        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([electorate_registry.source_field_index,
                                       electorate_registry.title_field_index,
                                       electorate_registry.deprecated_field_index])
        self.list = QListWidget()
        for f in electorate_registry.source_layer.getFeatures(request):
            title = f[electorate_registry.title_field_index]
            code = f[electorate_registry.source_field_index]
            deprecated = f[electorate_registry.deprecated_field_index]

            if deprecated:
                title = '*' + title
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, code)
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

    def selected_district(self):
        """
        Returns the electorate selected in the dialog
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
