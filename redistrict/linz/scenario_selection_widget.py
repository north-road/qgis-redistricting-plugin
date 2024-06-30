"""
Scenario selection widget
"""

from typing import Optional

from qgis.PyQt.QtCore import (
    Qt,
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (QWidget,
                                 QListWidget,
                                 QListWidgetItem,
                                 QVBoxLayout)
from qgis.gui import QgsFilterLineEdit
from redistrict.linz.scenario_registry import ScenarioRegistry


class ScenarioSelectionWidget(QWidget):
    """
    A widget used for selecting from available scenarios
    """

    scenario_double_clicked = pyqtSignal()
    selected_scenario_changed = pyqtSignal()

    def __init__(self, scenario_registry: ScenarioRegistry, parent=None):
        """
        Constructor for ScenarioSelectionWidget
        :param scenario_registry: linked scenario registry
        :param parent: parent widget
        """
        super().__init__(parent)

        self.scenario_registry = scenario_registry

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.search = QgsFilterLineEdit()
        self.search.setShowSearchIcon(True)
        self.search.setPlaceholderText(self.tr('Search for scenario'))
        self.search.textChanged.connect(self.filter_changed)
        layout.addWidget(self.search)

        self.list = QListWidget()
        for title, scenario_id in scenario_registry.scenario_titles().items():
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, scenario_id)
            self.list.addItem(item)

        layout.addWidget(self.list, 10)

        self.setLayout(layout)

        self.list.itemDoubleClicked.connect(
            self.scenario_double_clicked)

        self.list.itemSelectionChanged.connect(
            self.selected_scenario_changed)

        # select last scenario by default
        if self.list.count() > 0:
            self.list.item(self.list.count() - 1).setSelected(True)

    def set_selected_scenario(self, scenario: int):
        """
        Sets the scenario selected in the widget
        :param scenario: scenario to select
        """
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == scenario:
                self.list.item(i).setSelected(True)
                return

    def selected_scenario(self) -> Optional[int]:
        """
        Returns the scenario selected in the widget
        """
        if self.list.selectedItems():
            return self.list.selectedItems()[0].data(Qt.UserRole)

        return None

    def filter_changed(self, filter_text: str):
        """
        Handles search filter changes
        """
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(filter_text.upper() not in item.text().upper())
