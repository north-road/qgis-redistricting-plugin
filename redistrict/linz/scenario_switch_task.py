# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Scenario switching task

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

from qgis.core import (QgsVectorLayer,
                       NULL)
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_base_task import ScenarioBaseTask


class ScenarioSwitchTask(ScenarioBaseTask):
    """
    A background task for handling scenario switches
    """

    ELECTORATE_FEATURE_ID = 'ELECTORATE_FEATURE_ID'
    ELECTORATE_TYPE = 'ELECTORATE_TYPE '
    MESHBLOCKS = 'MESHBLOCKS'

    def __init__(self, task_name: str, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer,
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario):
        """
        Constructor for ScenarioSwitchTask
        :param task_name: user-visible, translated name for task
        :param electorate_layer: electorate layer
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        """
        super().__init__(task_name=task_name, electorate_layer=electorate_layer, meshblock_layer=meshblock_layer,
                         meshblock_number_field_name=meshblock_number_field_name, scenario_registry=scenario_registry,
                         scenario=scenario, task=None)

        self.stats_nz_pop_field = 'stats_nz_pop'
        self.stats_nz_var_20_field = 'stats_nz_var_20'
        self.stats_nz_var_23_field = 'stats_nz_var_23'

        self.stats_nz_pop_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_pop_field)
        assert self.stats_nz_pop_field_index >= 0
        self.stats_nz_var_20_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_var_20_field)
        assert self.stats_nz_var_20_field_index >= 0
        self.stats_nz_var_23_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_var_23_field)
        assert self.stats_nz_var_23_field_index >= 0

    def run(self):  # pylint: disable=missing-docstring
        electorate_geometries, electorate_attributes = self.calculate_new_electorates()

        attribute_change_map = {}
        geometry_change_map = {}
        for params in self.electorates_to_process.values():
            electorate_feature_id = params[self.ELECTORATE_FEATURE_ID]

            attribute_change_map[electorate_feature_id] = {self.scenario_id_idx: self.scenario,
                                                           self.estimated_pop_idx:
                                                               electorate_attributes[electorate_feature_id][
                                                                   self.ESTIMATED_POP],
                                                           self.invalid_idx: 0,
                                                           self.invalid_reason_idx: None,
                                                           self.stats_nz_pop_field_index: NULL,
                                                           self.stats_nz_var_20_field_index: NULL,
                                                           self.stats_nz_var_23_field_index: NULL}

            electorate_geometry = electorate_geometries[electorate_feature_id]
            geometry_change_map[electorate_feature_id] = electorate_geometry

        # commit changes
        if not self.electorate_layer.dataProvider().changeAttributeValues(attribute_change_map):
            return False
        if not self.electorate_layer.dataProvider().changeGeometryValues(geometry_change_map):
            return False

        return True
