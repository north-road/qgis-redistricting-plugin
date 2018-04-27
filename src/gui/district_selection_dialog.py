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

        self.setWindowTitle(self.tr('Select New Electorate'))
        l = QVBoxLayout()
        l.addWidget(QLabel(self.tr('Recently used electorates')))

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(100)
        for i in range(5):
            self.recent_list.addItem('Electorate {}'.format(i))
        l.addWidget(self.recent_list, 0)

        l.addWidget(QLabel(self.tr('Available electorates')))
        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for electorate'))
        l.addWidget(self.search)

        self.list = QListWidget()
        for i in range(10):
            self.list.addItem('Electorate {}'.format(i))

        l.addWidget(self.list, 10)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        l.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.select_from_map_button = button_box.addButton(
            self.tr("Select from Map"), QDialogButtonBox.ActionRole)

        self.setLayout(l)
