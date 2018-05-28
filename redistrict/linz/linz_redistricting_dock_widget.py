# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ specific redistricting dock widget

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

from functools import partial
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QTableWidget,
                                 QTableWidgetItem,
                                 QToolButton)
from qgis.core import QgsRectangle
from redistrict.gui.gui_utils import GuiUtils
from redistrict.gui.redistricting_dock_widget import RedistrictingDockWidget
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext
from redistrict.linz.validation_task import ValidationTask


class LinzRedistrictingDockWidget(RedistrictingDockWidget):
    """
    LINZ Specific redistricting dock widget
    """

    def __init__(self, context: LinzRedistrictingContext, iface=None):
        """
        Constructor for LINZ redistricting dock
        :param context: initial dock context
        :param iface: QGIS interface
        """
        super().__init__(iface)
        self.update_dock_title(context=context)
        self.table = None

    def update_dock_title(self, context: LinzRedistrictingContext):
        """
        Refreshes the dock title text, using the settings from a supplied
        context.
        :param context: redistricting context
        """
        self.setWindowTitle(self.tr('Redistricting - {} - {}').format(context.get_name_for_current_task(),
                                                                      context.get_name_for_current_scenario()))

    def show_message(self, html):
        """
        Shows a HTML formatted message in the dock, replacing
        its current contents
        :param html: HTML to show
        """
        if self.table is not None:
            self.table.deleteLater()
            self.table = None

        super().show_message(html)

    def zoom_to_extent(self, extent: QgsRectangle):
        """
        Zooms the canvas to the given extent
        :param extent: extent to zoom to
        """
        self.iface.mapCanvas().zoomToFeatureExtent(extent)

    def show_validation_results(self, results):
        """
        Shows the results of a validation run
        :param results: validation results
        """
        if self.table is not None:
            self.table.deleteLater()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['', 'Electorate', 'Error'])

        def create_zoom_button(extent: QgsRectangle):
            """
            Creates a zoom to electorate button
            :param extent: extent to zoom to
            """
            button = QToolButton()
            button.setToolTip('Zoom to Electorate')
            button.setIcon(GuiUtils.get_icon('zoom_selected.svg'))
            button.clicked.connect(partial(self.zoom_to_extent, extent))
            return button

        self.table.setRowCount(0)

        def add_electorate(electorate_id, name: str, error: str, extent: QgsRectangle):  # pylint: disable=unused-argument
            """
            Adds an electorate to the results table
            :param electorate_id: electorate ID
            :param name: electorate name
            :param error: error string
            :param extent: extent of electorate geometry
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
            self.table.setCellWidget(row, 0, create_zoom_button(extent))

        for result in results:
            add_electorate(electorate_id=result[ValidationTask.ELECTORATE_ID],
                           name=result[ValidationTask.ELECTORATE_NAME],
                           error=result[ValidationTask.ERROR],
                           extent=result[ValidationTask.ELECTORATE_GEOMETRY].boundingBox())

        self.table.setColumnWidth(0, 30)
        self.widget().layout().addWidget(self.table, 1, 0, 1, 1)
