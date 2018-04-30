# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Redistricting handler

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '30/04/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication


class RedistrictHandler():
    """
    Base class for redistrict handling operations. Pushes
    redistricting operations into the target layer's
    edit buffer
    """

    def __init__(self, target_layer, target_field):
        self.target_layer = target_layer
        self.target_field = target_field

    def assign_district(self, target_ids, new_district):
        """
        Assigns a new district to a set of target features
        :param target_ids: feature IDs for features to redistrict
        :param new_district: new district attribute for targets
        :return True if redistrict was successful
        """
        if not self.target_layer.isEditable():
            return False

        self.target_layer.beginEditCommand(
            QCoreApplication.translate('LinzRedistrict', 'Redistrict to {}').format(str(new_district)))
        field_index = self.target_layer.fields().lookupField(self.target_field)
        success = True
        for feature_id in target_ids:
            if not self.target_layer.changeAttributeValue(feature_id, field_index, new_district):
                success = False
        self.target_layer.endEditCommand()
        return success
