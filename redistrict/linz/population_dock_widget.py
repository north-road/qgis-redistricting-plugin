# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Selected population dock widget

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

from collections import defaultdict
from qgis.PyQt.QtWidgets import (QWidget,
                                 QGridLayout,
                                 QTextBrowser)
from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest
)
from qgis.gui import (QgsDockWidget,
                      QgisInterface)
from qgis.utils import iface


class SelectedPopulationDockWidget(QgsDockWidget):
    """
    Dock widget for display of population of selected meshblocks
    """

    def __init__(self, _iface: QgisInterface = None, meshblock_layer: QgsVectorLayer = None):
        super().__init__()
        self.setWindowTitle(self.tr('Selected Meshblock Population'))
        self.meshblock_layer = meshblock_layer

        if _iface is not None:
            self.iface = _iface
        else:
            self.iface = iface

        dock_contents = QWidget()
        grid = QGridLayout(dock_contents)
        grid.setContentsMargins(0, 0, 0, 0)

        self.frame = QTextBrowser()
        self.frame.setOpenLinks(False)
        # self.frame.anchorClicked.connect(self.anchor_clicked)
        grid.addWidget(self.frame, 1, 0, 1, 1)

        self.setWidget(dock_contents)

        self.meshblock_layer.selectionChanged.connect(self.selection_changed)
        self.task = None
        self.district_registry = None

    def set_task(self, task: str):
        """
        Sets the current task to use when showing populations
        """
        self.task = task
        self.selection_changed()

    def set_district_registry(self, registry):
        """
        Sets the associated district registry
        """
        self.district_registry = registry
        self.selection_changed()

    def selection_changed(self):
        """
        Triggered when the selection in the meshblock layer changes
        """
        if not self.task or not self.district_registry:
            return

        request = QgsFeatureRequest().setFilterFids(self.meshblock_layer.selectedFeatureIds()).setFlags(QgsFeatureRequest.NoGeometry)

        counts = defaultdict(int)
        for f in self.meshblock_layer.getFeatures(request):
            electorate = f['staged_electorate']
            if self.task == 'GN':
                pop = f['offline_pop_gn']
            elif self.task == 'GS':
                pop = f['offline_pop_gs']
            else:
                pop = f['offline_pop_m']
            counts[electorate] += pop

        html = '<p>'
        for electorate, pop in counts.items():
            html += """\n{}: <span style="font-weight:bold">{}</span><br>""".format(self.district_registry.get_district_title(electorate), pop)
        html += '</p>'

        self.frame.setHtml(html)
