# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ Specific District registry

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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (NULL,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsExpression,
                       QgsVectorLayer)
from redistrict.core.district_registry import VectorLayerDistrictRegistry


class LinzElectoralDistrictRegistry(VectorLayerDistrictRegistry):
    """
    A LINZ specific registry for NZ electora; districts based off field
    values from a vector layer
    """

    def __init__(self, source_layer: QgsVectorLayer,
                 source_field: str,
                 title_field: str,
                 electorate_type: str,
                 quota_layer: QgsVectorLayer,
                 name='districts',
                 type_string_title='Electorate'):
        """
        Constructor for District Registry
        :param source_layer: vector layer to retrieve districts from
        :param source_field: source field (name) to retrieve districts
        from
        :param title_field: field name for district titles
        :param electorate_type: electorate types to show, e.g. "GN"
        :param quota_layer: layer containing quota for district types
        :param name: unique identifying name for registry
        :param type_string_title: title case string for district
        types
        """
        super().__init__(source_layer=source_layer,
                         source_field=source_field,
                         title_field=title_field,
                         name=name,
                         type_string_title=type_string_title,
                         type_string_sentence='electorate',
                         type_string_sentence_plural='electorates')
        self.electorate_type = electorate_type
        self.type_field = 'type'
        self.estimated_population_field = 'estimated_pop'
        self.deprecated_field = 'deprecated'

        self.source_field_index = self.source_layer.fields().lookupField(self.source_field)
        assert self.source_field_index >= 0
        self.type_field_index = self.source_layer.fields().lookupField(self.type_field)
        assert self.type_field_index >= 0
        self.estimated_pop_field_index = self.source_layer.fields().lookupField(self.estimated_population_field)
        assert self.estimated_pop_field_index >= 0
        self.deprecated_field_index = self.source_layer.fields().lookupField(self.deprecated_field)
        assert self.deprecated_field_index >= 0

        self.quota_layer = quota_layer

    # noinspection PyMethodMayBeStatic
    def modify_district_request(self, request):
        """
        Allows subclasses to modify the request used to fetch available
        districts from the source layer, e.g. to add filtering
        or sorting to the request.
        :param request: base feature request to modify
        :return: modified feature request
        """
        request.addOrderBy(self.source_field)
        if self.electorate_type:
            request.setFilterExpression(
                QgsExpression.createFieldEqualityExpression(self.type_field, self.electorate_type))
        request.combineFilterExpression('"{}" is null or not "{}"'.format(self.deprecated_field, self.deprecated_field))
        return request

    def get_district_type(self, district) -> str:
        """
        Returns the district type (GN/GS/M) for the specified district
        :param district: district id
        """
        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, district))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.type_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[self.type_field_index]

    @staticmethod
    def district_type_title(district_type: str) -> str:  # pylint: disable=inconsistent-return-statements
        """
        Returns a user-friendly display title for the specified district type.
        :param district_type: district type to retrieve title for
        """
        if district_type == 'GN':
            return QCoreApplication.translate('LinzRedistrict', 'General North Island')
        elif district_type == 'GS':
            return QCoreApplication.translate('LinzRedistrict', 'General South Island')
        elif district_type == 'M':
            return QCoreApplication.translate('LinzRedistrict', 'Māori')

        # should never happen
        assert False

    def get_quota_for_district_type(self, district_type: str) -> int:
        """
        Returns the quota for the specified district type
        :param district_type: district type, e.g. "GS"
        """
        quota_field_index = self.quota_layer.fields().lookupField('quota')
        assert quota_field_index >= 0

        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('type', district_type))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([quota_field_index])
        request.setLimit(1)
        f = next(self.quota_layer.getFeatures(request))
        return f[quota_field_index]

    def get_quota_for_district(self, district) -> int:
        """
        Returns the quota for the given district
        :param district: district code/id
        """
        district_type = self.get_district_type(district)
        return self.get_quota_for_district_type(district_type)

    def get_code_for_electorate(self, electorate_id):
        """
        Returns the electorate code for a given electorate_id
        :param electorate_id: electorate id
        """
        code_field_index = self.source_layer.fields().lookupField('code')
        assert code_field_index >= 0

        request = QgsFeatureRequest()
        request.setFilterFid(electorate_id)
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([code_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[code_field_index]

    def get_estimated_population(self, district) -> int:
        """
        Returns the estimated (offline) population for the district
        :param district: district code/id
        """
        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, district))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.estimated_pop_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[self.estimated_pop_field_index]

    @staticmethod
    def get_variation_from_quota_percent(quota: int, population: int) -> int:
        """
        Returns the % variation from the quota for an electorate's population
        :param quota: electorate quota
        :param population: actual population
        :return: percentage as int (e.g. 4, -3, etc)
        """
        return round(100 * (population - quota) / quota)

    @staticmethod
    def variation_exceeds_allowance(quota: int, population: int) -> bool:
        """
        Returns true if a variation (in percent) exceeds the acceptable tolerance
        :param quota: electorate quota
        :param: population: actual population
        """
        return abs((population - quota) / quota) >= 0.05

    def create_electorate(self, new_electorate_code, new_electorate_name: str) -> (bool, str):
        """
        Creates a new electorate
        :param new_electorate_code: code for new electorate
        :param new_electorate_name: name for name electorate
        :return: boolean representing success or failure of creation, and error string
        """
        if self.district_name_exists(new_electorate_name):
            return False, QCoreApplication.translate('LinzRedistrict', 'An electorate with this name already exists')

        code_field_idx = self.source_layer.fields().lookupField('code')
        new_id = int(self.source_layer.maximumValue(self.source_field_index)) + 1

        f = QgsFeature()
        f.initAttributes(self.source_layer.fields().count())
        f[self.source_layer.fields().lookupField(self.title_field)] = new_electorate_name
        f[self.type_field_index] = self.electorate_type
        f[self.source_field_index] = new_id
        f[code_field_idx] = new_electorate_code

        if not self.source_layer.dataProvider().addFeatures([f]):
            return False, QCoreApplication.translate('LinzRedistrict', 'Could not create new electorate')

        return True, None

    def toggle_electorate_deprecation(self, electorate):
        """
        Toggles the deprecation flag for an electorate
        :param electorate: electorate id
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.deprecated_field_index])
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate))
        f = next(self.source_layer.getFeatures(request))

        is_deprecated = f[self.deprecated_field_index]
        if is_deprecated == NULL:
            is_deprecated = False

        new_status = 0 if is_deprecated else 1
        self.source_layer.dataProvider().changeAttributeValues({f.id(): {self.deprecated_field_index: new_status}})
