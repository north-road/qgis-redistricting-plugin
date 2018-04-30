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
                 type_string_sentence_plural='districts'):
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
        """
        super().__init__(name=name,
                         type_string_title=type_string_title,
                         type_string_sentence=type_string_sentence,
                         type_string_sentence_plural=type_string_sentence_plural)
        self.source_layer = source_layer
        self.source_field = source_field

    def flags(self):
        """
        Returns flags indicating registry behavior
        """
        return self.FLAG_ALLOWS_SPATIAL_SELECT

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
        request.setSubsetOfAttributes([field_index])
        for f in self.source_layer.getFeatures(request):
            return f[field_index]
        return None
