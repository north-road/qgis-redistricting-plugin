# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Scenario registry

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

from collections import OrderedDict
from typing import Optional
from qgis.PyQt.QtCore import (QCoreApplication,
                              QDateTime)
from qgis.core import (QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsApplication,
                       QgsFeatureIterator,
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

    def get_scenario_name(self, scenario) -> str:
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

    def get_scenario(self, scenario) -> QgsFeature:
        """
        Returns the feature corresponding to the given scenario
        :param scenario: scenario id to get feature for
        """

        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.id_field, scenario))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f

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

    def next_scenario_id(self) -> int:
        """
        Returns the next available scenario ID
        """
        return max(self.source_layer.maximumValue(self.id_field_index), 0) + 1

    def __insert_new_scenario(self, new_scenario_name: str, created_datetime: QDateTime = None, created_by: str = None):
        """
        Inserts a scenario into the registry
        :param new_scenario_name: name for new scenario
        :param created_datetime: optional datetime for scenario, if not set will be set to current date time
        :param created_by: creator user name, if not set will be set to current user name
        :return: scenario id if successful, and error message
        """
        next_id = self.next_scenario_id()

        scenario_feature = QgsFeature()
        scenario_feature.initAttributes(self.source_layer.fields().count())
        scenario_feature[self.id_field_index] = next_id
        scenario_feature[self.name_field_index] = new_scenario_name
        scenario_feature[
            self.created_field_index] = QDateTime.currentDateTime() if created_datetime is None else created_datetime
        scenario_feature[
            self.created_by_field_index] = QgsApplication.userFullName() if created_by is None else created_by

        if not self.source_layer.dataProvider().addFeatures([scenario_feature]):
            return False, QCoreApplication.translate('LinzRedistrict', 'Could not create scenario')

        return next_id, None

    @staticmethod
    def __copy_records_from_scenario(source_meshblock_electorate_layer: QgsVectorLayer,
                                     source_scenario_id,
                                     dest_meshblock_electorate_layer: QgsVectorLayer,
                                     new_scenario_id):
        """
        Copies the records associated with a scenario from one table to
        another
        :param source_meshblock_electorate_layer: layer containing source meshblock->electorate mappings
        :param source_scenario_id: source scenario id
        :param dest_meshblock_electorate_layer: destination layer for copied meshblock->electorate mappings
        :param new_scenario_id: new scenario id for copied records
        """
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('scenario_id', source_scenario_id))
        current_meshblocks = source_meshblock_electorate_layer.getFeatures(request)
        scenario_id_idx = source_meshblock_electorate_layer.fields().lookupField('scenario_id')
        fid_idx = source_meshblock_electorate_layer.fields().lookupField('fid')
        new_features = []
        for f in current_meshblocks:
            f[scenario_id_idx] = new_scenario_id
            if fid_idx >= 0:
                f[fid_idx] = NULL
            new_features.append(f)

        dest_meshblock_electorate_layer.startEditing()
        dest_meshblock_electorate_layer.addFeatures(new_features)
        dest_meshblock_electorate_layer.commitChanges()

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
        new_id, error = self.__insert_new_scenario(new_scenario_name=new_scenario_name)
        if not new_id:
            return False, error

        ScenarioRegistry.__copy_records_from_scenario(source_meshblock_electorate_layer=self.meshblock_electorate_layer,
                                                      source_scenario_id=scenario_id,
                                                      dest_meshblock_electorate_layer=self.meshblock_electorate_layer,
                                                      new_scenario_id=new_id)
        return new_id, None

    def import_scenario_from_other_registry(self, source_registry: 'ScenarioRegistry', source_scenario_id,
                                            new_scenario_name: str) -> (bool, str):
        """
        Imports a scenario from another ScenarioRegistry
        :param source_registry: registry to import scenario from
        :param source_scenario_id: source scenario id
        :param new_scenario_name: name from imported scenario
        :returns boolean for success, and error message if error encountered
        """
        if self.scenario_name_exists(new_scenario_name):
            return False, QCoreApplication.translate('LinzRedistrict', '{} already exists').format(new_scenario_name)
        if not source_registry.scenario_exists(source_scenario_id):
            return False, QCoreApplication.translate('LinzRedistrict', 'Scenario {} does not exist in database').format(
                source_scenario_id)

        source_scenario = source_registry.get_scenario(source_scenario_id)

        # all good to go
        new_id, error = self.__insert_new_scenario(new_scenario_name=new_scenario_name,
                                                   created_datetime=source_scenario['created'],
                                                   created_by=source_scenario['created_by'])
        if not new_id:
            return False, error

        ScenarioRegistry.__copy_records_from_scenario(
            source_meshblock_electorate_layer=source_registry.meshblock_electorate_layer,
            source_scenario_id=source_scenario_id,
            dest_meshblock_electorate_layer=self.meshblock_electorate_layer,
            new_scenario_id=new_id)
        return new_id, None

    def electorate_meshblocks(self, electorate_id, electorate_type: str, scenario_id) -> QgsFeatureIterator:
        """
        Returns meshblock features currently assigned to an electorate in a
        given scenario
        :param electorate_id: electorate id
        :param electorate_type: electorate type, e.g. 'GN','GS','M'
        :param scenario_id: scenario id
        """
        request = QgsFeatureRequest()

        type_field = '{}_id'.format(electorate_type.lower())
        type_field_index = self.meshblock_electorate_layer.fields().lookupField(type_field)
        assert type_field_index >= 0

        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('scenario_id', scenario_id))
        request.combineFilterExpression(QgsExpression.createFieldEqualityExpression(type_field, electorate_id))

        return self.meshblock_electorate_layer.getFeatures(request)

    def electorate_has_meshblocks(self, electorate_id, electorate_type: str, scenario_id) -> bool:
        """
        Returns true if the given electorate has meshblocks within the specified scenario
        :param electorate_id: electorate id
        :param electorate_type: electorate type, e.g. 'GN','GS','M'
        :param scenario_id: scenario id
        """
        try:
            next(self.electorate_meshblocks(electorate_id=electorate_id, electorate_type=electorate_type,
                                            scenario_id=scenario_id))
        except StopIteration:
            return False

        return True
