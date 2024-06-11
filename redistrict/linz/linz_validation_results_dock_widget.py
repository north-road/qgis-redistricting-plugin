# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Validation results dock widget

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

from functools import partial
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QGridLayout,
                                 QWidget,
                                 QTableWidget,
                                 QTableWidgetItem,
                                 QToolButton)
from qgis.core import QgsGeometry
from qgis.gui import QgsDockWidget
from qgis.utils import iface
from redistrict.gui.gui_utils import GuiUtils
from redistrict.linz.validation_task import ValidationTask


class LinzValidationResultsDockWidget(QgsDockWidget):
    """
    LINZ Specific validation results dock widget
    """

    def __init__(self, _iface=None):
        """
        Constructor for LINZ redistricting dock
        :param context: initial dock context
        :param iface: QGIS interface
        """
        super().__init__()
        self.setObjectName('LinzValidationResultsDockWidget')

        if _iface is not None:
            self.iface = _iface
        else:
            self.iface = iface

        dock_contents = QWidget()
        grid = QGridLayout(dock_contents)
        grid.setContentsMargins(0, 0, 0, 0)

        self.setWidget(dock_contents)

        self.setObjectName('LinzValidationResultsDock')
        self.setWindowTitle(self.tr('Validation Results'))
        self.table = None

    def zoom_to_extent(self, geom: QgsGeometry):
        """
        Zooms the canvas to the given extent
        :param geom: extent to zoom to
        """
        self.iface.mapCanvas().zoomToFeatureExtent(geom.boundingBox())

    def clear(self):
        """
        Clears existing validation results from the dock
        """
        if self.table is not None:
            self.table.deleteLater()
            self.table = None

    def show_validation_results(self, results):
        """
        Shows the results of a validation run
        :param results: validation results
        """
        self.clear()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['', 'Electorate', 'Error'])

        def create_zoom_button(geom: QgsGeometry):
            """
            Creates a zoom to electorate button
            :param geom: extent to zoom to
            """
            button = QToolButton()
            if geom.isEmpty():
                button.setEnabled(False)
                button.setToolTip('Electorate has no meshblocks assigned')
            else:
                button.setToolTip('Zoom to Electorate')
            button.setIcon(GuiUtils.get_icon('zoom_selected.svg'))
            button.clicked.connect(partial(self.zoom_to_extent, geom))
            return button

        self.table.setRowCount(0)

        def add_electorate(electorate_id, name: str, error: str,  # pylint: disable=unused-argument
                           geom: QgsGeometry):
            """
            Adds an electorate to the results table
            :param electorate_id: electorate ID
            :param name: electorate name
            :param error: error string
            :param geom: electorate geometry
            """
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
            name_item = QTableWidgetItem(name)
            name_item.setFlags(flags)
            error_item = QTableWidgetItem(error)
            error_item.setFlags(flags)

            row = self.table.rowCount()
            self.table.setRowCount(row + 1)

            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, error_item)
            self.table.setCellWidget(row, 0, create_zoom_button(geom))

        for result in results:
            add_electorate(electorate_id=result[ValidationTask.ELECTORATE_ID],
                           name=result[ValidationTask.ELECTORATE_NAME],
                           error=result[ValidationTask.ERROR],
                           geom=result[ValidationTask.ELECTORATE_GEOMETRY])

        self.table.setColumnWidth(0, 30)
        self.widget().layout().addWidget(self.table, 1, 0, 1, 1)
