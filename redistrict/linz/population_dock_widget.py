"""
LINZ Redistricting Plugin - Selected population dock widget
"""

from collections import defaultdict
from qgis.PyQt.QtWidgets import (QWidget,
                                 QGridLayout,
                                 QTextBrowser)
from qgis.core import (
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsExpression,
    NULL
)
from qgis.gui import (QgsDockWidget,
                      QgisInterface)
from qgis.utils import iface
from redistrict.gui.district_selection_dialog import DistrictPicker
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry


class SelectedPopulationDockWidget(QgsDockWidget):
    """
    Dock widget for display of population of selected meshblocks
    """

    def __init__(self, _iface: QgisInterface = None, meshblock_layer: QgsVectorLayer = None):
        super().__init__()
        self.setObjectName('SelectedPopulationDockWidget')
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
        self.frame.anchorClicked.connect(self.anchor_clicked)
        grid.addWidget(self.frame, 1, 0, 1, 1)

        self.setWidget(dock_contents)

        self.meshblock_layer.selectionChanged.connect(self.selection_changed)
        self.task = None
        self.district_registry = None
        self.target_electorate = None
        self.quota = 0

    def reset(self):
        """
        Clears the current results shown in the dock
        """
        self.target_electorate = None
        self.frame.setHtml('')

    def update(self):
        """
        Refreshes the stats shown in the dock
        """
        self.selection_changed()

    def set_task(self, task: str):
        """
        Sets the current task to use when showing populations
        """
        self.task = task
        if self.district_registry:
            self.quota = self.district_registry.get_quota_for_district_type(self.task)

        self.target_electorate = None
        self.selection_changed()

    def set_district_registry(self, registry):
        """
        Sets the associated district registry
        """
        self.district_registry = registry

        if self.task:
            self.quota = self.district_registry.get_quota_for_district_type(self.task)

        self.selection_changed()

    def selection_changed(self):
        """
        Triggered when the selection in the meshblock layer changes
        """
        if not self.task or not self.district_registry:
            return

        request = QgsFeatureRequest().setFilterFids(self.meshblock_layer.selectedFeatureIds()).setFlags(
            QgsFeatureRequest.NoGeometry)

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

        district_title = self.district_registry.get_district_title(
            self.target_electorate)
        html = f"""<h3>Target Electorate: <a href="#">{district_title}</a></h3><p>"""

        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('type', self.task))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes(['electorate_id', 'estimated_pop', 'stats_nz_pop'],
                                      self.district_registry.source_layer.fields())
        original_populations = {}
        for f in self.district_registry.source_layer.getFeatures(request):
            estimated_pop = f['stats_nz_pop']
            if estimated_pop is None or estimated_pop == NULL:
                # otherwise just use existing estimated pop as starting point
                estimated_pop = f['estimated_pop']
            original_populations[f['electorate_id']] = estimated_pop

        overall = 0
        for electorate, pop in counts.items():
            if self.target_electorate:
                if electorate != self.target_electorate:
                    overall += pop

                    # use stats nz pop as initial estimate, if available
                    estimated_pop = original_populations[electorate]

                    estimated_pop -= pop
                    variance = LinzElectoralDistrictRegistry.get_variation_from_quota_percent(self.quota, estimated_pop)

                    change_dir_str = '+' if variance > 0 else ''
                    
                    source_district_title = self.district_registry.get_district_title(electorate)
                    
                    html += f"""\n{source_district_title}: <span style="font-weight:bold">-{pop}</span> (after: {int(estimated_pop)}, {change_dir_str}{variance}%)<br>"""
            else:
                html += f"""\n{district_title}: <span style="font-weight:bold">{pop}</span><br>"""
        if self.target_electorate:
            estimated_pop = original_populations[self.target_electorate]

            estimated_pop += overall
            variance = LinzElectoralDistrictRegistry.get_variation_from_quota_percent(self.quota, estimated_pop)

            change_dir_str = '+' if variance > 0 else ''
            html += f"""\n{district_title}: <span style="font-weight:bold">+{overall}</span> (after: {int(estimated_pop)}, {change_dir_str}{variance}%)<br>"""

        html += '</p>'

        self.frame.setHtml(html)

    def anchor_clicked(self):
        """
        Allows choice of "target" electorate
        """
        dlg = DistrictPicker(district_registry=self.district_registry,
                             parent=self.iface.mainWindow())
        if dlg.selected_district is None:
            return

        self.target_electorate = dlg.selected_district
        self.selection_changed()
