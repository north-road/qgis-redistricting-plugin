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

from redistrict.core.district_registry import VectorLayerDistrictRegistry


class LinzElectoralDistrictRegistry(VectorLayerDistrictRegistry):
    """
    A LINZ specific registry for NZ electora; districts based off field
    values from a vector layer
    """

    def __init__(self, source_layer,
                 source_field,
                 title_field,
                 name='districts',
                 type_string_title='Electorate'):
        """
        Constructor for District Registry
        :param source_layer: vector layer to retrieve districts from
        :param source_field: source field (name) to retrieve districts
        from
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
