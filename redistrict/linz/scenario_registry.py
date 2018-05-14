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
from qgis.core import (QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer,
                       NULL)


class ScenarioRegistry():
    """
    A registry for handling available scenarios
    """

    def __init__(self, source_layer: QgsVectorLayer,
                 id_field: str,
                 name_field: str):
        """
        Constructor for ScenarioRegistry
        :param source_layer: source layer for registry
        :param id_field: name of scenario id field
        :param name_field: name of scenario name field
        """
        self.source_layer = source_layer
        self.id_field = id_field
        self.id_field_index = source_layer.fields().lookupField(self.id_field)
        assert self.id_field_index >= 0
        self.name_field = name_field
        self.name_field_index = source_layer.fields().lookupField(self.name_field)
        assert self.name_field_index >= 0

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

    def branch_scenario(self, new_scenario_name: str):
        """
        Branches the current scenario to a new scenario
        :param new_scenario_name: name for new scenario
        """
        pass
