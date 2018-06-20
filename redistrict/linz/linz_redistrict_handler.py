# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ Specific Redistrict Handler

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

from qgis.PyQt.QtCore import (QDateTime,
                              QVariant)
from qgis.core import (QgsApplication,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsFeatureIterator,
                       QgsGeometry,
                       QgsVectorLayer,
                       QgsAggregateCalculator,
                       QgsExpression,
                       NULL)
from redistrict.core.redistrict_handler import RedistrictHandler
from redistrict.linz.electorate_changes_queue import ElectorateEditQueue


class LinzRedistrictHandler(RedistrictHandler):
    """
    LINZ specific class for redistrict handling operations. Pushes
    redistricting operations into the target layer's
    edit buffer, and stages changes for dissolving electorate
    layer boundaries
    """

    def __init__(self, meshblock_layer: QgsVectorLayer, meshblock_number_field_name: str, target_field: str,
                 electorate_changes_queue: ElectorateEditQueue,
                 electorate_layer: QgsVectorLayer,
                 electorate_layer_field: str, task: str, user_log_layer: QgsVectorLayer, scenario):
        """
        Constructor
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: field name for "meshblock number" field
        :param target_field: target field for districts
        :param electorate_changes_queue: queue for staged electorate changes
        :param electorate_layer: electoral district layer
        :param electorate_layer_field: matching field from electorate layer
        :param task: current task
        :param user_log_layer: user log layer
        :param scenario: current scenario
        """
        super().__init__(target_layer=meshblock_layer, target_field=target_field)
        self.electorate_changes_queue = electorate_changes_queue
        self.electorate_layer = electorate_layer
        self.electorate_layer_field = electorate_layer_field
        self.pending_affected_districts = {}
        self.pending_log_entries = []
        self.task = task
        self.user_log_layer = user_log_layer
        self.scenario = scenario
        self.stats_nz_pop_field = 'stats_nz_pop'
        self.stats_nz_var_20_field = 'stats_nz_var_20'
        self.stats_nz_var_23_field = 'stats_nz_var_23'

        self.estimated_pop_idx = self.electorate_layer.fields().lookupField('estimated_pop')
        assert self.estimated_pop_idx >= 0
        self.meshblock_number_idx = self.target_layer.fields().lookupField(meshblock_number_field_name)
        assert self.meshblock_number_idx >= 0
        self.offline_pop_field = 'offline_pop_{}'.format(self.task.lower())
        assert meshblock_layer.fields().lookupField(self.offline_pop_field) >= 0

        self.user_log_timestamp_idx = self.user_log_layer.fields().lookupField('timestamp')
        assert self.user_log_timestamp_idx >= 0
        self.user_log_username_idx = self.user_log_layer.fields().lookupField('username')
        assert self.user_log_username_idx >= 0
        self.user_log_scenario_idx = self.user_log_layer.fields().lookupField('scenario_id')
        assert self.user_log_scenario_idx >= 0
        self.user_log_mb_number_idx = self.user_log_layer.fields().lookupField('meshblock_number')
        assert self.user_log_mb_number_idx >= 0
        self.user_log_type_idx = self.user_log_layer.fields().lookupField('type')
        assert self.user_log_type_idx >= 0
        self.user_log_from_idx = self.user_log_layer.fields().lookupField('from_electorate_id')
        assert self.user_log_from_idx >= 0
        self.user_log_to_idx = self.user_log_layer.fields().lookupField('to_electorate_id')
        assert self.user_log_to_idx >= 0

        self.stats_nz_pop_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_pop_field)
        assert self.stats_nz_pop_field_index >= 0
        self.stats_nz_var_20_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_var_20_field)
        assert self.stats_nz_var_20_field_index >= 0
        self.stats_nz_var_23_field_index = self.electorate_layer.fields().lookupField(self.stats_nz_var_23_field)
        assert self.stats_nz_var_23_field_index >= 0

        self.invalid_field_index = self.electorate_layer.fields().lookupField('invalid')
        assert self.invalid_field_index >= 0
        self.invalid_reason_field_index = self.electorate_layer.fields().lookupField('invalid_reason')
        assert self.invalid_reason_field_index >= 0

    def create_affected_district_filter(self):
        """
        Returns a QgsExpression filter corresponding to all pending affected
        electorates
        """
        if not self.pending_affected_districts:
            return ''

        field_index = self.electorate_layer.fields().lookupField(self.electorate_layer_field)
        if self.electorate_layer.fields().at(field_index).type() == QVariant.String:
            district_filter = "{} IN ('{}')".format(self.electorate_layer_field,
                                                    "','".join(sorted([str(k) for k in
                                                                       self.pending_affected_districts.keys()])))  # pylint: disable=consider-iterating-dictionary
        else:
            district_filter = "{} IN ({})".format(self.electorate_layer_field,
                                                  ",".join(sorted([str(k) for k in
                                                                   self.pending_affected_districts.keys()])))  # pylint: disable=consider-iterating-dictionary
        return district_filter

    def get_affected_districts(self, attributes_required=None):
        """
        Returns an iterator over features for all pending affected
        electorates
        :param attributes_required: optional list of field names required. If
        not set than all attributes are fetched
        """
        request = QgsFeatureRequest().setFilterExpression(self.create_affected_district_filter())
        if attributes_required is not None:
            request.setSubsetOfAttributes(attributes_required, self.electorate_layer.fields())
        return self.electorate_layer.getFeatures(request)

    def get_added_meshblocks(self, district):
        """
        Returns the meshblock features which were added to a district
        :param district: district affected
        """
        if district not in self.pending_affected_districts:
            return QgsFeatureIterator()

        added = self.pending_affected_districts[district]['ADD']
        if added:
            request = QgsFeatureRequest().setFilterFids(added).setSubsetOfAttributes([])
            return self.target_layer.getFeatures(request)

        return QgsFeatureIterator()

    def grow_district_with_added_meshblocks(self, district, original_district_geometry):
        """
        Grows an electorate district by adding the meshblocks newly
        assigned to this district
        :param district: district to grow
        :param original_district_geometry: original geometry for district
        """
        parts = [f.geometry() for f in self.get_added_meshblocks(district)]
        if parts:
            parts.append(original_district_geometry)
            return QgsGeometry.unaryUnion(parts)

        return original_district_geometry

    def get_removed_meshblocks(self, district):
        """
        Returns the meshblock features which were removed from a district
        :param district: district affected
        """
        if district not in self.pending_affected_districts:
            return QgsFeatureIterator()

        removed = self.pending_affected_districts[district]['REMOVE']
        if removed:
            request = QgsFeatureRequest().setFilterFids(removed).setSubsetOfAttributes([])
            return self.target_layer.getFeatures(request)

        return QgsFeatureIterator()

    def shrink_district_by_removed_meshblocks(self, district, original_district_geometry):
        """
        Shrinks an electorate district by removing the meshblocks newly
        removed from this district
        :param district: district to shrink
        :param original_district_geometry: original geometry for district
        """
        parts = [f.geometry() for f in self.get_removed_meshblocks(district)]
        if parts:
            to_remove = QgsGeometry.unaryUnion(parts)
            return original_district_geometry.difference(to_remove)

        return original_district_geometry

    def end_edit_group(self):
        super().end_edit_group()
        if not self.pending_affected_districts:
            return

        # step 1: get all electorate features corresponding to affected electorates
        electorate_features = {f[self.electorate_layer_field]: f for f in
                               self.get_affected_districts([self.electorate_layer_field])}

        # and update the electorate boundaries based on these changes.
        # Ideally we'd redissolve the whole boundary from meshblocks, but that's too
        # slow. So instead we adjust piece-by-piece by adding or chomping away
        # the affected meshblocks only.
        new_geometries = {}
        new_attributes = {}
        for district in self.pending_affected_districts.keys():  # pylint: disable=consider-iterating-dictionary
            district_geometry = electorate_features[district].geometry()
            # add new bits
            district_geometry = self.grow_district_with_added_meshblocks(district, district_geometry)
            # minus lost bits
            district_geometry = self.shrink_district_by_removed_meshblocks(district, district_geometry)

            new_geometries[electorate_features[district].id()] = district_geometry

            calc = QgsAggregateCalculator(self.target_layer)
            calc.setFilter(QgsExpression.createFieldEqualityExpression(self.target_field, district))
            estimated_pop, ok = calc.calculate(QgsAggregateCalculator.Sum,  # pylint: disable=unused-variable
                                               self.offline_pop_field)

            new_attributes[electorate_features[district].id()] = {self.estimated_pop_idx: estimated_pop,
                                                                  self.stats_nz_pop_field_index: NULL,
                                                                  self.stats_nz_var_20_field_index: NULL,
                                                                  self.stats_nz_var_23_field_index: NULL,
                                                                  self.invalid_field_index: NULL,
                                                                  self.invalid_reason_field_index: NULL}
        self.electorate_changes_queue.push_changes(new_attributes, new_geometries)

        self.user_log_layer.dataProvider().addFeatures(self.pending_log_entries)

        self.pending_affected_districts = {}
        self.pending_log_entries = []
        self.redistrict_occured.emit()

    def discard_edit_group(self):
        super().discard_edit_group()
        self.pending_affected_districts = {}
        self.pending_log_entries = []

    def assign_district(self, target_ids, new_district):
        """
        Queue up changes
        :param target_ids:
        :param new_district:
        :return:
        """
        staged_log_entries = []
        # first, record the previous districts, before they get changed by the super method
        request = QgsFeatureRequest().setFilterFids(target_ids)
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes(
            [self.target_layer.fields().lookupField(self.target_field), self.meshblock_number_idx])
        for f in self.target_layer.getFeatures(request):
            district = f[self.target_field]
            if district == NULL:
                continue
            meshblock_number = f[self.meshblock_number_idx]

            if district not in self.pending_affected_districts:
                self.pending_affected_districts[district] = {'ADD': [], 'REMOVE': []}
            self.pending_affected_districts[district]['REMOVE'].append(f.id())

            staged_log_entries.append(self.create_log_entry(meshblock_number=meshblock_number, old_district=district,
                                                            new_district=new_district))

        if not super().assign_district(target_ids, new_district):
            return False

        self.pending_log_entries.extend(staged_log_entries)

        # if assign was successful, then record all districts affected by this operation
        # (that includes the new district and all old districts)

        if new_district not in self.pending_affected_districts:
            self.pending_affected_districts[new_district] = {'ADD': [], 'REMOVE': []}

        self.pending_affected_districts[new_district]['ADD'].extend(target_ids)
        return True

    def create_log_entry(self, meshblock_number, old_district, new_district) -> QgsFeature:
        """
        Returns a feature corresponding to a new log entry
        :param meshblock_number: meshblock number
        :param old_district: previous district
        :param new_district: new district
        """
        f = QgsFeature(self.user_log_layer.fields())
        f.initAttributes(len(self.user_log_layer.fields()))

        f[self.user_log_timestamp_idx] = QDateTime.currentDateTime()
        f[self.user_log_username_idx] = QgsApplication.userFullName()
        f[self.user_log_scenario_idx] = self.scenario
        f[self.user_log_mb_number_idx] = meshblock_number
        f[self.user_log_type_idx] = self.task
        f[self.user_log_from_idx] = old_district
        f[self.user_log_to_idx] = new_district

        return f
