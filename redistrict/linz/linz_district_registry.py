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
from qgis.core import (QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer)
from redistrict.core.district_registry import VectorLayerDistrictRegistry


class LinzElectoralDistrictRegistry(VectorLayerDistrictRegistry):
    """
    A LINZ specific registry for NZ electora; districts based off field
    values from a vector layer
    """

    def __init__(self, source_layer,
                 source_field,
                 title_field,
                 quota_layer: QgsVectorLayer,
                 name='districts',
                 type_string_title='Electorate'):
        """
        Constructor for District Registry
        :param source_layer: vector layer to retrieve districts from
        :param source_field: source field (name) to retrieve districts
        from
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
        self.type_field = 'type'
        self.estimated_population_field = 'estimated_pop'

        self.source_field_index = self.source_layer.fields().lookupField(self.source_field)
        assert self.source_field_index >= 0
        self.type_field_index = self.source_layer.fields().lookupField(self.type_field)
        assert self.type_field_index >= 0
        self.estimated_pop_field_index = self.source_layer.fields().lookupField(self.estimated_population_field)
        assert self.estimated_pop_field_index >= 0

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
        f = next(self.source_layer.getFeatures(request))
        return f[self.type_field_index]

    @staticmethod
    def district_type_title(district_type: str) -> str:
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

        assert False  # should never happen

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
        f = next(self.quota_layer.getFeatures(request))
        return f[quota_field_index]

    def get_quota_for_district(self, district) -> int:
        """
        Returns the quota for the given district
        :param district: district code/id
        """
        district_type = self.get_district_type(district)
        return self.get_quota_for_district_type(district_type)

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
        f = next(self.source_layer.getFeatures(request))
        return f[self.estimated_pop_field_index]
