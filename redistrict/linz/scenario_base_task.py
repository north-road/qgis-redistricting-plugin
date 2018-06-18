# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Scenario base task

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

from typing import Optional
from qgis.core import (QgsTask,
                       QgsFeatureRequest,
                       QgsVectorLayer,
                       QgsGeometry)
from redistrict.linz.scenario_registry import ScenarioRegistry


class ScenarioBaseTask(QgsTask):
    """
    Base class for scenario related tasks
    """

    ELECTORATE_FEATURE_ID = 'ELECTORATE_FEATURE_ID'
    ELECTORATE_ID = 'ELECTORATE_ID'
    ELECTORATE_TYPE = 'ELECTORATE_TYPE'
    ELECTORATE_CODE = 'ELECTORATE_CODE'
    ELECTORATE_NAME = 'ELECTORATE_NAME'
    MESHBLOCKS = 'MESHBLOCKS'
    ESTIMATED_POP = 'ESTIMATED_POP'

    def __init__(self, task_name: str, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer,  # pylint: disable=too-many-locals
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario,
                 task: Optional[str] = None):
        """
        Constructor for ScenarioSwitchTask
        :param task_name: user-visible, translated name for task
        :param electorate_layer: electorate layer
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        :param task: current redistricting task
        """
        super().__init__(task_name)

        self.scenario = scenario
        self.electorate_layer = electorate_layer
        self.task = task

        self.type_idx = electorate_layer.fields().lookupField('type')
        assert self.type_idx >= 0
        self.scenario_id_idx = electorate_layer.fields().lookupField('scenario_id')
        assert self.scenario_id_idx >= 0
        self.estimated_pop_idx = electorate_layer.fields().lookupField('estimated_pop')
        assert self.estimated_pop_idx >= 0
        self.mb_number_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField('meshblock_number')
        assert self.mb_number_idx >= 0
        self.mb_off_pop_m_idx = meshblock_layer.fields().lookupField('offline_pop_m')
        assert self.mb_off_pop_m_idx >= 0
        self.mb_off_pop_ni_idx = meshblock_layer.fields().lookupField('offline_pop_gn')
        assert self.mb_off_pop_ni_idx >= 0
        self.mb_off_pop_si_idx = meshblock_layer.fields().lookupField('offline_pop_gs')
        assert self.mb_off_pop_si_idx >= 0

        self.invalid_reason_idx = self.electorate_layer.fields().lookupField('invalid_reason')
        assert self.invalid_reason_idx >= 0
        self.invalid_idx = self.electorate_layer.fields().lookupField('invalid')
        assert self.invalid_idx >= 0

        electorate_id_idx = electorate_layer.fields().lookupField('electorate_id')
        assert electorate_id_idx >= 0
        self.code_idx = electorate_layer.fields().lookupField('code')
        assert self.code_idx >= 0
        self.name_idx = electorate_layer.fields().lookupField('name')
        assert self.name_idx >= 0
        self.meshblock_number_idx = meshblock_layer.fields().lookupField(meshblock_number_field_name)
        assert self.meshblock_number_idx >= 0

        # do a bit of preparatory processing on the main thread for safety

        # dict of meshblock number to feature
        meshblocks = {}
        for m in meshblock_layer.getFeatures():
            meshblocks[int(m[self.meshblock_number_idx])] = m

        # dict of electorates to process (by id)
        self.electorates_to_process = {}
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([electorate_id_idx, self.type_idx, self.code_idx, self.name_idx])
        for electorate in electorate_layer.getFeatures(request):
            # get meshblocks for this electorate in the target scenario
            electorate_id = electorate[electorate_id_idx]
            electorate_type = electorate[self.type_idx]
            electorate_code = electorate[self.code_idx]
            electorate_name = electorate[self.name_idx]
            if self.task and electorate_type != self.task:
                continue

            electorate_meshblocks = scenario_registry.electorate_meshblocks(electorate_id=electorate_id,
                                                                            electorate_type=electorate_type,
                                                                            scenario_id=scenario)
            assigned_meshblock_numbers = [m[self.mb_number_idx] for m in electorate_meshblocks]
            matching_meshblocks = [meshblocks[m] for m in assigned_meshblock_numbers]

            self.electorates_to_process[electorate_id] = {self.ELECTORATE_FEATURE_ID: electorate.id(),
                                                          self.ELECTORATE_TYPE: electorate_type,
                                                          self.ELECTORATE_CODE: electorate_code,
                                                          self.ELECTORATE_NAME: electorate_name,
                                                          self.MESHBLOCKS: matching_meshblocks}

        self.setDependentLayers([electorate_layer])

    def calculate_new_electorates(self):
        """
        Calculates the new electorate geometry and populations for the associated scenario
        """
        electorate_geometries = {}
        electorate_attributes = {}
        i = 0
        for electorate_id, params in self.electorates_to_process.items():
            self.setProgress(100 * i / len(self.electorates_to_process))

            electorate_feature_id = params[self.ELECTORATE_FEATURE_ID]
            electorate_type = params[self.ELECTORATE_TYPE]
            matching_meshblocks = params[self.MESHBLOCKS]

            if electorate_type == 'M':
                estimated_pop = sum(
                    [mbf[self.mb_off_pop_m_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_m_idx]])
            elif electorate_type == 'GN':
                estimated_pop = sum(
                    [mbf[self.mb_off_pop_ni_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_ni_idx]])
            else:
                estimated_pop = sum(
                    [mbf[self.mb_off_pop_si_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_si_idx]])

            electorate_attributes[electorate_feature_id] = {self.ESTIMATED_POP: estimated_pop,
                                                            self.ELECTORATE_ID: electorate_id,
                                                            self.ELECTORATE_TYPE: electorate_type,
                                                            self.ELECTORATE_NAME: params[self.ELECTORATE_NAME],
                                                            self.ELECTORATE_CODE: params[self.ELECTORATE_CODE],
                                                            self.MESHBLOCKS: matching_meshblocks}

            meshblock_parts = [m.geometry() for m in matching_meshblocks]
            electorate_geometry = QgsGeometry.unaryUnion(meshblock_parts)
            electorate_geometry = electorate_geometry.makeValid()
            electorate_geometries[electorate_feature_id] = electorate_geometry
            i += 1

        return electorate_geometries, electorate_attributes
