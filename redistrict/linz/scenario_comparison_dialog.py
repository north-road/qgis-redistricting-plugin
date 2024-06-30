"""
Scenario comparison dialog
"""

from typing import Optional

from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel
)

from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_selection_widget import ScenarioSelectionWidget


class ScenarioComparisonDialog(QDialog):
    """
    A dialog used for selecting from available scenarios in order to diff
    two scenarios
    """

    def __init__(self, scenario_registry: ScenarioRegistry, parent=None):
        """
        Constructor for ScenarioComparisonDialog
        :param scenario_registry: linked scenario registry
        :param parent: parent widget
        """
        super().__init__(parent)

        self.scenario_registry = scenario_registry

        self.setWindowTitle(self.tr('Select Scenarios to Compare'))

        layout = QGridLayout()

        layout.addWidget(QLabel('Base scenario'), 0, 0)
        layout.addWidget(QLabel('Secondary scenario'), 0, 1)

        self.base_selection_widget = ScenarioSelectionWidget(scenario_registry)
        layout.addWidget(self.base_selection_widget, 1, 0)

        self.secondary_selection_widget = ScenarioSelectionWidget(scenario_registry)
        layout.addWidget(self.secondary_selection_widget, 1, 1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box, 2, 0, 1, 2)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)

        self.base_selection_widget.selected_scenario_changed.connect(self._validate)
        self.secondary_selection_widget.selected_scenario_changed.connect(self._validate)

        self._validate()

        self.setLayout(layout)

    def _validate(self):
        """
        Validates the current dialog configuration
        """
        is_valid = (
                self.base_selection_widget.selected_scenario() is not None and
                self.secondary_selection_widget.selected_scenario() is not None and
                (self.base_selection_widget.selected_scenario() !=
                 self.secondary_selection_widget.selected_scenario())
        )
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(is_valid)

    def set_base_scenario(self, scenario: int):
        """
        Sets the base scenario selected in the dialog
        :param scenario: scenario to select
        """
        self.base_selection_widget.set_selected_scenario(scenario)

    def set_secondary_scenario(self, scenario: int):
        """
        Sets the secondary scenario selected in the dialog
        :param scenario: scenario to select
        """
        self.secondary_selection_widget.set_selected_scenario(scenario)

    def selected_base_scenario(self) -> Optional[int]:
        """
        Returns the base scenario selected in the dialog
        """
        return self.base_selection_widget.selected_scenario()

    def selected_secondary_scenario(self) -> Optional[int]:
        """
        Returns the secondary scenario selected in the dialog
        """
        return self.secondary_selection_widget.selected_scenario()
