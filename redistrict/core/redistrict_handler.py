# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Redistricting handler

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '30/04/2018'
__copyright__ = 'Copyright 2018, LINZ'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import (QObject,
                              pyqtSignal)


class RedistrictHandler(QObject):
    """
    Base class for redistrict handling operations. Pushes
    redistricting operations into the target layer's
    edit buffer
    """

    redistrict_occured = pyqtSignal()
    operation_ended = pyqtSignal()

    def __init__(self, target_layer, target_field):
        super().__init__()
        self.target_layer = target_layer
        self.target_field = target_field
        self.pending_changes = []

    def begin_operation(self):
        """
        Called when a new edit type operation is about to begin, before any edits are made
        """
        pass  # pylint: disable=unnecessary-pass

    def end_operation(self):
        """
        Called after an edit type operation is about to finished
        """
        pass  # pylint: disable=unnecessary-pass

    def begin_edit_group(self, message):
        """
        Begins a batch redistricting edit operation
        :param message: user-visible string describing changes
        """
        self.target_layer.beginEditCommand(message)

    def end_edit_group(self):
        """
        Ends a batch redistricting edit operation
        """
        self.target_layer.endEditCommand()
        self.redistrict_occured.emit()
        self.operation_ended.emit()

    def discard_edit_group(self):
        """
        Ends a batch redistricting edit operation,
        discarding the changes
        """
        self.target_layer.destroyEditCommand()
        self.target_layer.triggerRepaint()
        self.redistrict_occured.emit()
        self.operation_ended.emit()

    def assign_district(self, target_ids, new_district):
        """
        Assigns a new district to a set of target features
        :param target_ids: feature IDs for features to redistrict
        :param new_district: new district attribute for targets
        :return True if redistrict was successful
        """
        if not self.target_layer.isEditable():
            return False

        field_index = self.target_layer.fields().lookupField(self.target_field)
        success = True
        for feature_id in target_ids:
            if not self.target_layer.changeAttributeValue(feature_id, field_index, new_district):
                success = False

        self.target_layer.triggerRepaint()
        self.redistrict_occured.emit()
        return success
