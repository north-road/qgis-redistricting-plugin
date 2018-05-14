# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - District registry

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
from qgis.core import (QgsCoordinateTransform,
                       QgsProject,
                       QgsSettings,
                       QgsFeatureRequest,
                       QgsExpression,
                       NULL)

MAX_RECENT_DISTRICTS = 5


class DistrictRegistry():
    """
    A registry for handling available districts
    """

    FLAG_ALLOWS_SPATIAL_SELECT = 1

    def __init__(self, name='districts', districts=None,
                 type_string_title='District',
                 type_string_sentence='district',
                 type_string_sentence_plural='districts'):
        """
        Constructor for District Registry
        :param name: unique identifying name for registry
        :param districts: list of districts to include in registry
        :param type_string_title: title case string for district
        types
        :param type_string_sentence: sentence case string for district
        types
        :param type_string_sentence_plural: sentence case string for district
        types (plural)
        """
        self.name = name
        if districts is None:
            districts = []
        self.districts = districts
        self._type_string_title = type_string_title
        self._type_string_sentence = type_string_sentence
        self._type_string_sentence_plural = type_string_sentence_plural

    def flags(self):
        """
        Returns flags indicating registry behavior
        """
        return 0

    def type_string_title(self):
        """
        Returns the title case district type identifier, e.g. "District'
        """
        return self._type_string_title

    def type_string_sentence(self):
        """
        Returns the sentence case district type identifier (singular),
        e.g. "district"
        """
        return self._type_string_sentence

    def type_string_sentence_plural(self):
        """
        Returns the sentence case district type identifier (plural),
        e.g. "districts"
        """
        return self._type_string_sentence_plural

    # noinspection PyMethodMayBeStatic
    def get_district_title(self, district):
        """
        Returns a user-friendly title corresponding to the given district
        :param district: district code/id to get title for
        """
        return str(district)

    def settings_key(self):
        """
        Returns the QSettings key corresponding to this registry
        """
        return 'redistricting/{}'.format(self.name)

    def district_list(self):
        """
        Returns a complete list of districts available for
        redistricting to
        """
        return self.districts

    def district_titles(self):
        """
        Returns a dictionary of sorted district titles to corresponding district id/code
        """
        return {self.get_district_title(d): d for d in self.district_list()}

    def clear_recent_districts(self):
        """
        Clears the list of recent districts
        """
        QgsSettings().setValue('{}/recent_districts'.format(
            self.settings_key()), [])

    def push_recent_district(self, district):
        """
        Pushes a district to the top of the recent districts list
        :param district: district to push to list
        """
        recent_districts = self.recent_districts_list()
        recent_districts = [district] + \
                           [d for d in recent_districts
                            if d != district]
        recent_districts = recent_districts[:MAX_RECENT_DISTRICTS]
        QgsSettings().setValue('{}/recent_districts'.format(
            self.settings_key()), recent_districts)

    def recent_districts_list(self):
        """
        Returns a list of recently used districts
        """
        valid_districts = self.district_list()
        return [d for d in QgsSettings().value('{}/recent_districts'.format(
            self.settings_key()), []) if d in valid_districts]

    def get_district_at_point(self, rect, crs):  # pylint: disable=unused-argument
        """
        Returns the district corresponding to a map point. This
        is implemented only for registries which return the
        FLAG_ALLOWS_SPATIAL_SELECT flag.
        :param rect: rectangle to search within
        :param crs: crs for map point
        :return: district at map point, or None if not found
        """
        return None


class VectorLayerDistrictRegistry(DistrictRegistry):
    """
    A registry for districts based off field values from a vector layer
    """

    def __init__(self, source_layer,
                 source_field,
                 name='districts',
                 type_string_title='District',
                 type_string_sentence='district',
                 type_string_sentence_plural='districts',
                 title_field=None):
        """
        Constructor for District Registry
        :param source_layer: vector layer to retrieve districts from
        :param source_field: source field (name) to retrieve districts
        from
        :param name: unique identifying name for registry
        :param type_string_title: title case string for district
        types
        :param type_string_sentence: sentence case string for district
        types
        :param type_string_sentence_plural: sentence case string for district
        types (plural)
        :param title_field: optional field name for field to retrieve
        district titles from. If not set source_field will be used.
        """
        super().__init__(name=name,
                         type_string_title=type_string_title,
                         type_string_sentence=type_string_sentence,
                         type_string_sentence_plural=type_string_sentence_plural)
        self.source_layer = source_layer
        self.source_field = source_field
        if title_field is not None:
            self.title_field = title_field
        else:
            self.title_field = self.source_field

    def flags(self):
        """
        Returns flags indicating registry behavior
        """
        return self.FLAG_ALLOWS_SPATIAL_SELECT

    def get_district_title(self, district):
        if self.title_field == self.source_field:
            return super().get_district_title(district)

        # lookup matching feature
        title_field_index = self.source_layer.fields().lookupField(self.title_field)
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, district))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([title_field_index])
        request.setLimit(1)
        try:
            f = next(self.source_layer.getFeatures(request))
        except StopIteration:
            return super().get_district_title(district)
        return f[title_field_index]

    # noinspection PyMethodMayBeStatic
    def modify_district_request(self, request):
        """
        Allows subclasses to modify the request used to fetch available
        districts from the source layer, e.g. to add filtering
        or sorting to the request.
        :param request: base feature request to modify
        :return: modified feature request
        """
        return request

    def district_list(self):
        """
        Returns a complete list of districts available for redistricting to
        """
        field_index = self.source_layer.fields().lookupField(self.source_field)

        request = QgsFeatureRequest()
        self.modify_district_request(request)
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([field_index])

        districts = [f[field_index]
                     for f in self.source_layer.getFeatures(request)
                     if f[field_index] != NULL]
        # we want an ordered list of unique values!
        d = OrderedDict()
        for x in districts:
            d[x] = True
        return list(d.keys())

    def district_titles(self):
        """
        Returns a dictionary of sorted district titles to corresponding district id/code
        """
        field_index = self.source_layer.fields().lookupField(self.source_field)
        title_field_index = self.source_layer.fields().lookupField(self.title_field)
        request = QgsFeatureRequest()
        self.modify_district_request(request)
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([field_index, title_field_index])

        districts = {f[title_field_index]: f[field_index]
                     for f in self.source_layer.getFeatures(request)
                     if f[field_index] != NULL}
        result = OrderedDict()
        for d in sorted(districts.keys()):
            result[d] = districts[d]
        return result

    def get_district_at_point(self, rect, crs):
        """
        Returns the district corresponding to a map point. This
        is implemented only for registries which return the
        FLAG_ALLOWS_SPATIAL_SELECT flag.
        :param rect: rect to search within
        :param crs: crs for map point
        :return: district at map point, or None if not found
        """

        # first reproject point to layer crs
        transform = QgsCoordinateTransform(crs, self.source_layer.crs(), QgsProject.instance())
        try:
            rect = transform.transformBoundingBox(rect)
        except:  # noqa, pylint: disable=bare-except
            pass

        field_index = self.source_layer.fields().lookupField(self.source_field)
        request = QgsFeatureRequest().setFilterRect(rect)
        self.modify_district_request(request)
        request.setSubsetOfAttributes([field_index])
        for f in self.source_layer.getFeatures(request):
            return f[field_index]
        return None
