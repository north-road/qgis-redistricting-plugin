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

from qgis.core import QgsVectorLayer


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

        # TODO - queue should record previous values, not new ones
        self.queue.append(ElectorateEditQueue.QueueItem(attribute_edits, geometry_edits))

        self.electorate_layer.dataProvider().changeGeometryValues(geometry_edits)
        self.electorate_layer.dataProvider().changeAttributeValues(attribute_edits)
        self.electorate_layer.triggerRepaint()

    def pop(self) -> (dict, dict):
        """
        Removes the last item from the queue.
        :return: dictionary of attribute edits, dictionary of geometry edits
        """
        assert self.queue
        item = self.queue[-1]
        del self.queue[-1]
        return item.attribute_edits, item.geometry_edits
