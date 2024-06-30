"""
Scenario selection dialog
"""

from typing import Optional

from qgis.PyQt.QtWidgets import (QDialog,
                                 QDialogButtonBox,
                                 QVBoxLayout)

from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_selection_widget import ScenarioSelectionWidget


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

        self.selection_widget = ScenarioSelectionWidget(scenario_registry)
        layout.addWidget(self.selection_widget, stretch=10)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)

        self.setLayout(layout)

        self.selection_widget.scenario_double_clicked.connect(
            self.accept)

    def set_selected_scenario(self, scenario: int):
        """
        Sets the scenario selected in the dialog
        :param scenario: scenario to select
        """
        self.selection_widget.set_selected_scenario(scenario)

    def selected_scenario(self) -> Optional[int]:
        """
        Returns the scenario selected in the dialog
        """
        return self.selection_widget.selected_scenario()
