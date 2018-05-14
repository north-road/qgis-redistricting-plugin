# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Scenario registry

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

from collections import OrderedDict
from typing import Optional
from qgis.PyQt.QtCore import (QCoreApplication,
                              QDateTime)
from qgis.core import (QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsApplication,
                       NULL)


class ScenarioRegistry():
    """
    A registry for handling available scenarios
    """

    def __init__(self, source_layer: QgsVectorLayer,
                 id_field: str,
                 name_field: str,
                 meshblock_electorate_layer: Optional[QgsVectorLayer]):
        """
        Constructor for ScenarioRegistry
        :param source_layer: source layer for registry
        :param id_field: name of scenario id field
        :param name_field: name of scenario name field
        :param meshblock_electorate_layer: layer containing meshblock to electorate mapping for each scenario
        """
        self.source_layer = source_layer
        self.id_field = id_field
        self.id_field_index = source_layer.fields().lookupField(self.id_field)
        assert self.id_field_index >= 0
        self.name_field = name_field
        self.name_field_index = source_layer.fields().lookupField(self.name_field)
        assert self.name_field_index >= 0
        self.created_field = 'created'
        self.created_field_index = source_layer.fields().lookupField(self.created_field)
        self.created_by_field = 'created_by'
        self.created_by_field_index = source_layer.fields().lookupField(self.created_by_field)
        self.meshblock_electorate_layer = meshblock_electorate_layer

    def get_scenario_name(self, scenario):
        """
        Returns a user-friendly name corresponding to the given scenario
        :param scenario: scenario id to get name for
        """

        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.id_field, scenario))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.name_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[self.name_field_index]

    def scenario_list(self):
        """
        Returns a complete list of available scenarios
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.id_field_index])

        districts = [f[self.id_field_index]
                     for f in self.source_layer.getFeatures(request)
                     if f[self.id_field_index] != NULL]
        # we want an ordered list of unique values!
        d = OrderedDict()
        for x in districts:
            d[x] = True
        return list(d.keys())

    def scenario_titles(self):
        """
        Returns a dictionary of sorted scenario titles to corresponding scenario id
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.id_field_index, self.name_field_index])

        districts = {f[self.name_field_index]: f[self.id_field_index]
                     for f in self.source_layer.getFeatures(request)
                     if f[self.id_field_index] != NULL}
        result = OrderedDict()
        for d in sorted(districts.keys()):
            result[d] = districts[d]
        return result

    def scenario_name_exists(self, new_scenario_name: str) -> bool:
        """
        Returns true if the given scenario name already exists
        :param new_scenario_name: name of scenario to test
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([])
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.name_field, new_scenario_name))
        request.setLimit(1)
        for f in self.source_layer.getFeatures(request):  # pylint: disable=unused-variable
            # found a matching feature
            return True
        return False

    def scenario_exists(self, scenario_id) -> bool:
        """
        Returns true if the given scenario exists
        :param scenario_id: ID for scenario
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([])
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.id_field, scenario_id))
        request.setLimit(1)
        for f in self.source_layer.getFeatures(request):  # pylint: disable=unused-variable
            # found a matching feature
            return True
        return False

    def branch_scenario(self, scenario_id, new_scenario_name: str):
        """
        Branches a scenario to a new scenario
        :param scenario_id: scenario to branch
        :param new_scenario_name: name for new scenario
        :returns New scenario ID if branch was successful, and error message if not
        """
        if self.scenario_name_exists(new_scenario_name):
            return False, QCoreApplication.translate('LinzRedistrict', '{} already exists').format(new_scenario_name)
        if not self.scenario_exists(scenario_id):
            return False, QCoreApplication.translate('LinzRedistrict', 'Scenario {} does not exist').format(scenario_id)

        # all good to go
        next_id = self.source_layer.maximumValue(self.id_field_index) + 1

        scenario_feature = QgsFeature()
        scenario_feature.initAttributes(self.source_layer.fields().count())
        scenario_feature[self.id_field_index] = next_id
        scenario_feature[self.name_field_index] = new_scenario_name
        scenario_feature[self.created_field_index] = QDateTime.currentDateTime()
        scenario_feature[self.created_by_field_index] = QgsApplication.userFullName()

        if not self.source_layer.dataProvider().addFeatures([scenario_feature]):
            return False, QCoreApplication.translate('LinzRedistrict', 'Could not create scenario')

        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('scenario_id', scenario_id))
        current_meshblocks = self.meshblock_electorate_layer.getFeatures(request)
        scenario_id_idx = self.meshblock_electorate_layer.fields().lookupField('scenario_id')
        new_features = []
        for f in current_meshblocks:
            f[scenario_id_idx] = next_id
            new_features.append(f)

        self.meshblock_electorate_layer.startEditing()
        self.meshblock_electorate_layer.addFeatures(new_features)

        return next_id, None
