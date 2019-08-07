# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Electorate validation task

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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsVectorLayer,
                       NULL)
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_base_task import (ScenarioBaseTask,
                                                CanceledException)


class ValidationTask(ScenarioBaseTask):
    """
    A background task for validating electorates
    """

    ELECTORATE_NAME = 'ELECTORATE_NAME'
    ELECTORATE_GEOMETRY = 'ELECTORATE_GEOMETRY'
    ERROR = 'ERROR'

    def __init__(self, task_name: str, electorate_registry: LinzElectoralDistrictRegistry,
                 meshblock_layer: QgsVectorLayer,
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario, task: str):
        """
        Constructor for ScenarioSwitchTask
        :param task_name: user-visible, translated name for task
        :param electorate_registry: electorate registry
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        :param task: current task
        """
        self.electorate_registry = electorate_registry
        super().__init__(task_name=task_name, electorate_layer=self.electorate_registry.source_layer,
                         meshblock_layer=meshblock_layer,
                         meshblock_number_field_name=meshblock_number_field_name, scenario_registry=scenario_registry,
                         scenario=scenario, task=task)
        self.results = []

        # immediately clear existing validation results
        attribute_change_map = {}
        for e in self.electorates_to_process.values():
            attribute_change_map[e[self.ELECTORATE_FEATURE_ID]] = {
                self.invalid_idx: NULL,
                self.invalid_reason_idx: NULL
            }
        self.electorate_layer.dataProvider().changeAttributeValues(attribute_change_map)

    def run(self):  # pylint: disable=missing-docstring, too-many-locals
        try:
            electorate_geometries, electorate_attributes = self.calculate_new_electorates()
        except CanceledException:
            return False

        attribute_change_map = {}
        for electorate_feature_id, attributes in electorate_attributes.items():
            if self.isCanceled():
                return False

            electorate_id = attributes[self.ELECTORATE_ID]
            pop = attributes[self.ESTIMATED_POP]
            electorate_type = attributes[self.ELECTORATE_TYPE]
            expected_regions = attributes[self.EXPECTED_REGIONS]

            quota = self.electorate_registry.get_quota_for_district_type(electorate_type)
            name = self.electorate_registry.get_district_title(electorate_id)
            geometry = electorate_geometries[electorate_feature_id]

            # clear any existing validation result
            attribute_change_map[electorate_feature_id] = {self.invalid_idx: 0,
                                                           self.invalid_reason_idx: NULL,
                                                           self.scenario_id_idx: self.scenario,
                                                           self.estimated_pop_idx: attributes[self.ESTIMATED_POP]}
            # quota check
            if self.electorate_registry.variation_exceeds_allowance(quota=quota, population=pop):
                error = QCoreApplication.translate('LinzRedistrict', 'Outside quota tolerance')
                self.results.append({self.ELECTORATE_ID: electorate_id,
                                     self.ELECTORATE_NAME: name,
                                     self.ELECTORATE_GEOMETRY: geometry,
                                     self.ERROR: error})
                attribute_change_map[electorate_feature_id] = {self.invalid_idx: 1,
                                                               self.invalid_reason_idx: error}

            # contiguity check
            if geometry.isMultipart() and geometry.constGet().numGeometries() > expected_regions:
                error = QCoreApplication.translate('LinzRedistrict', 'Electorate is non-contiguous')
                self.results.append({self.ELECTORATE_ID: electorate_id,
                                     self.ELECTORATE_NAME: name,
                                     self.ELECTORATE_GEOMETRY: geometry,
                                     self.ERROR: error})
                attribute_change_map[electorate_feature_id] = {self.invalid_idx: 1,
                                                               self.invalid_reason_idx: error}
            elif not geometry.isMultipart() and expected_regions > 1:
                error = QCoreApplication.translate('LinzRedistrict', 'Electorate has less parts than expected')
                self.results.append({self.ELECTORATE_ID: electorate_id,
                                     self.ELECTORATE_NAME: name,
                                     self.ELECTORATE_GEOMETRY: geometry,
                                     self.ERROR: error})
                attribute_change_map[electorate_feature_id] = {self.invalid_idx: 1,
                                                               self.invalid_reason_idx: error}

        if self.isCanceled():
            return False

        # commit changes
        if not self.electorate_layer.dataProvider().changeAttributeValues(attribute_change_map):
            return False

        return True
