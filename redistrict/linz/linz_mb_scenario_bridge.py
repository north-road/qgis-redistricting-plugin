# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ meshblock to scenario bridge

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

from typing import Dict, List
from qgis.PyQt.QtCore import QObject
from qgis.core import (QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer)


class LinzMeshblockScenarioBridge(QObject):
    """
    LINZ specific class for synchronizing changes between the meshblock layer
    and the meshblock-scenario table
    """

    def __init__(self, meshblock_layer: QgsVectorLayer, meshblock_scenario_layer: QgsVectorLayer):
        """
        Constructor
        :param meshblock_layer: meshblock layer
        :param meshblock_scenario_layer: meshblock-scenario table
        """
        super().__init__()
        self.meshblock_layer = meshblock_layer
        self.meshblock_scenario_layer = meshblock_scenario_layer

        self.staged_electorate_idx = self.meshblock_layer.fields().lookupField('staged_electorate')
        assert self.staged_electorate_idx >= 0
        self.meshblock_number_idx = self.meshblock_layer.fields().lookupField('MeshblockNumber')
        assert self.meshblock_number_idx >= 0

        self.target_scenario_idx = self.meshblock_scenario_layer.fields().lookupField('scenario_id')
        assert self.target_scenario_idx >= 0
        self.target_meshblock_number_idx = self.meshblock_scenario_layer.fields().lookupField('meshblock_number')
        assert self.target_meshblock_number_idx >= 0

        self.meshblock_layer.beforeCommitChanges.connect(self.meshblock_layer_saved)

        self.scenario = None
        self.task = None

    def get_new_electorates(self) -> Dict[int, int]:
        """
        Returns a dictionary of pending changes from meshblock number to new electorate id
        """
        assert self.task is not None

        electorate_field_name = '{}_id'.format(self.task)
        electorate_field_idx = self.meshblock_scenario_layer.fields().lookupField(electorate_field_name)
        assert electorate_field_idx >= 0

        if self.meshblock_layer.editBuffer() is None:
            return {}

        # get list of affected features
        changed_attribute_values = self.meshblock_layer.editBuffer().changedAttributeValues()

        request = QgsFeatureRequest()
        request.setSubsetOfAttributes([self.meshblock_number_idx])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setFilterFids(list(changed_attribute_values.keys()))
        meshblock_features = {f.id(): f for f in self.meshblock_layer.getFeatures(request)}

        # dict of meshblock number to new electorate
        new_electorates = {}
        for source_id, changes in changed_attribute_values.items():
            new_electorate = changes[self.staged_electorate_idx]
            meshblock_number = int(meshblock_features[source_id][self.meshblock_number_idx])
            new_electorates[meshblock_number] = new_electorate
        return new_electorates

    def get_target_meshblock_ids_from_numbers(self, meshblock_numbers: List[int]) -> Dict[int, int]:
        """
        Returns a dictionary of target meshblock feature IDs corresponding to the
        specified meshblock numbers
        :param meshblock_numbers: list of meshblock numbers to lookup
        """
        assert self.scenario is not None
        request = QgsFeatureRequest()
        request.setSubsetOfAttributes([self.target_meshblock_number_idx])
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('scenario_id', self.scenario))
        meshblock_filter = 'meshblock_number IN ({})'.format(','.join([str(mb) for mb in meshblock_numbers]))
        request.combineFilterExpression(meshblock_filter)
        # create dictionary of meshblock number to id
        mb_number_to_target_id = {}
        for f in self.meshblock_scenario_layer.getFeatures(request):
            mb_number_to_target_id[f[self.target_meshblock_number_idx]] = f.id()
        return mb_number_to_target_id

    def meshblock_layer_saved(self):
        """
        Triggered when the meshblock layer is about to be saved
        """
        assert self.task is not None

        electorate_field_name = '{}_id'.format(self.task)
        electorate_field_idx = self.meshblock_scenario_layer.fields().lookupField(electorate_field_name)
        assert electorate_field_idx >= 0, electorate_field_name

        # dict of meshblock number to new electorate
        new_electorates = self.get_new_electorates()

        # find feature ids of affected rows
        mb_number_to_target_id = self.get_target_meshblock_ids_from_numbers(list(new_electorates.keys()))

        # create map of changes attributes
        target_changed_attributes = {}
        for mb, electorate in new_electorates.items():
            mb_id = mb_number_to_target_id[mb]
            target_changed_attributes[mb_id] = {electorate_field_idx: electorate}

        self.meshblock_scenario_layer.dataProvider().changeAttributeValues(target_changed_attributes)
