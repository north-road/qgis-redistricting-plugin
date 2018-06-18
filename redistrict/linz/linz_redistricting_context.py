# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ Redistricting Context

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

from qgis.PyQt.QtCore import QCoreApplication, QObject, pyqtSignal
from redistrict.linz.scenario_registry import ScenarioRegistry


class LinzRedistrictingContext(QObject):
    """
    Contains settings relating to the general context of a LINZ redistricting
    operation
    """

    TASK_GN = 'GN'
    TASK_GS = 'GS'
    TASK_M = 'M'

    scenario_changed = pyqtSignal()

    def __init__(self, scenario_registry: ScenarioRegistry):
        """
        Constructor for redistricting context
        :param scenario_registry: linked scenario registry
        """
        super().__init__()
        self.scenario = 1
        self.scenario_registry = scenario_registry
        self.task = self.TASK_GN

    @staticmethod
    def get_name_for_task(task: str) -> str:
        """
        Returns a friendly name for a task
        """
        if task == LinzRedistrictingContext.TASK_GN:
            return QCoreApplication.translate('LinzRedistrict', 'General (North Island)')
        elif task == LinzRedistrictingContext.TASK_GS:
            return QCoreApplication.translate('LinzRedistrict', 'General (South Island)')
        return QCoreApplication.translate('LinzRedistrict', 'Māori')

    def get_name_for_current_task(self) -> str:
        """
        Returns the friendly name corresponding to the current task
        """
        return LinzRedistrictingContext.get_name_for_task(self.task)

    def get_name_for_current_scenario(self) -> str:
        """
        Returns the friendly name corresponding to the current scenario
        """
        return self.scenario_registry.get_scenario_name(self.scenario)

    def set_scenario(self, scenario: int):
        """
        Changes to current scenario
        :param scenario: new scenario
        """
        self.scenario = scenario
        self.scenario_changed.emit()
