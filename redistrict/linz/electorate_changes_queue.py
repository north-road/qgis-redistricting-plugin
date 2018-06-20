# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Staged queue of electorate changes

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

from qgis.core import (QgsVectorLayer,
                       QgsFeatureRequest)


class ElectorateEditQueue:
    """
    Queue for staged electorate edits, used when
    redistricting changes are created or rolled back
    to restore electorate layer to a matching state
    """

    class QueueItem:
        """
        Item within an ElectorateEditQueue
        """

        def __init__(self, attribute_edits: dict, geometry_edits: dict):
            """
            Constructor
            :param attribute_edits: dictionary of attribute edits
            :param geometry_edits: dictionary of geometry edits
            """
            self.attribute_edits = attribute_edits
            self.geometry_edits = geometry_edits

    def __init__(self, electorate_layer: QgsVectorLayer):
        """
        Constructor
        :param electorate_layer: target electorate layer
        """
        self.electorate_layer = electorate_layer
        self.queue = []

    def push(self, attribute_edits: dict, geometry_edits: dict):
        """
        Pushes a new set of electorate layer changes to the end of the queue
        :param attribute_edits: dictionary of attribute edits
        :param geometry_edits: dictionary of geometry edits
        """

        # queue should record previous values, not new ones
        attribute_feature_ids = list(attribute_edits.keys())
        request = QgsFeatureRequest().setFilterFids(attribute_feature_ids).setFlags(QgsFeatureRequest.NoGeometry)
        attributes = {f.id(): f.attributes() for f in self.electorate_layer.getFeatures(request)}
        prev_attributes = {
            feature_id: {attribute_index: attributes[feature_id][attribute_index] for attribute_index in v.keys()} for
            feature_id, v in attribute_edits.items()}

        geometry_feature_ids = list(geometry_edits.keys())
        request = QgsFeatureRequest().setFilterFids(geometry_feature_ids).setSubsetOfAttributes([])
        geometries = {f.id(): f.geometry() for f in self.electorate_layer.getFeatures(request)}
        prev_geometries = {feature_id: geometries[feature_id] for feature_id, v in geometry_edits.items()}

        self.queue.append(ElectorateEditQueue.QueueItem(prev_attributes, prev_geometries))

        self.electorate_layer.dataProvider().changeGeometryValues(geometry_edits)
        self.electorate_layer.dataProvider().changeAttributeValues(attribute_edits)
        self.electorate_layer.triggerRepaint()

    def pop(self) -> bool:
        """
        Removes the last item from the queue.
        :return: True if a change was popped
        """
        if not self.queue:
            return False

        item = self.queue[-1]
        del self.queue[-1]

        # undo changes in layer
        self.electorate_layer.dataProvider().changeGeometryValues(item.geometry_edits)
        self.electorate_layer.dataProvider().changeAttributeValues(item.attribute_edits)
        self.electorate_layer.triggerRepaint()

        return True
