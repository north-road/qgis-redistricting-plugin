# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Export electorates task

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
                       QgsFeature,
                       QgsVectorFileWriter,
                       QgsFeedback,
                       NULL)
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_base_task import (ScenarioBaseTask,
                                                CanceledException)


class ExportTask(ScenarioBaseTask):
    """
    A background task for exporting electorates, meshblock assignments
    """

    GN = 'GN'
    GS = 'GS'
    M = 'M'

    def __init__(self, task_name: str, dest_file: str, electorate_registry: LinzElectoralDistrictRegistry,
                 meshblock_layer: QgsVectorLayer,
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario,
                 user_log_layer: QgsVectorLayer):
        """
        Constructor for ExportTask
        :param task_name: user-visible, translated name for task
        :param dest_file: destination filename
        :param electorate_registry: electorate registry
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        :param user_log_layer: user log layer
        """
        self.electorate_registry = electorate_registry
        super().__init__(task_name=task_name, electorate_layer=self.electorate_registry.source_layer,
                         meshblock_layer=meshblock_layer,
                         meshblock_number_field_name=meshblock_number_field_name, scenario_registry=scenario_registry,
                         scenario=scenario, task=None)
        self.dest_file = dest_file
        self.message = None
        self.user_log_layer = user_log_layer

        self.feedback = QgsFeedback()

    def cancel(self):
        """
        Cancels the export
        """
        super().cancel()
        self.feedback.cancel()

    def run(self):  # pylint: disable=missing-docstring,too-many-locals,too-many-return-statements,too-many-branches,too-many-statements
        try:
            electorate_geometries, electorate_attributes = self.calculate_new_electorates()
        except CanceledException:
            return False

        # we also need a dictionary of meshblock number to all electorate types
        meshblock_electorates = {}

        electorate_features = []

        for electorate_feature_id, attributes in electorate_attributes.items():
            if self.isCanceled():
                return False

            electorate_code = attributes[self.ELECTORATE_CODE]
            geometry = electorate_geometries[electorate_feature_id]

            meshblocks = attributes[self.MESHBLOCKS]
            electorate_type = attributes[self.ELECTORATE_TYPE]
            name = attributes[self.ELECTORATE_NAME]

            for m in meshblocks:
                meshblock_number = m[self.meshblock_number_idx]
                if meshblock_number not in meshblock_electorates:
                    meshblock_electorates[meshblock_number] = {}
                meshblock_electorates[meshblock_number][electorate_type] = electorate_code

                if self.isCanceled():
                    return False

            electorate_feature = QgsFeature()
            electorate_feature.setGeometry(geometry)
            electorate_feature.setAttributes([electorate_type, electorate_code, name])
            electorate_features.append(electorate_feature)

        electorate_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:2193&field=type:string(2)&field=code:string&field=name:string",
            "source", "memory")
        if not electorate_layer.dataProvider().addFeatures(electorate_features):
            return False

        if self.isCanceled():
            return False

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'electorates'
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        options.feedback = self.feedback
        error, self.message = QgsVectorFileWriter.writeAsVectorFormat(electorate_layer, self.dest_file, options)
        if error:
            return False
        if self.isCanceled():
            return False

        layer = QgsVectorLayer(
            "NoGeometry?field=meshblock_number:int&field=gn_code:string&field=gs_code:string&field=m_code:string",
            "source", "memory")
        meshblock_features = []
        for meshblock_number, electorates in meshblock_electorates.items():
            f = QgsFeature()
            gn = electorates[self.GN] if self.GN in electorates else NULL
            gs = electorates[self.GS] if self.GS in electorates else NULL
            m = electorates[self.M] if self.M in electorates else NULL
            f.setAttributes([meshblock_number, gn, gs, m])
            meshblock_features.append(f)
            if self.isCanceled():
                return False

        layer.dataProvider().addFeatures(meshblock_features)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'meshblocks'
        options.feedback = self.feedback
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        error, self.message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.dest_file, options)
        if error:
            return False
        if self.isCanceled():
            return False

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'user_log'
        options.feedback = self.feedback
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        error, self.message = QgsVectorFileWriter.writeAsVectorFormat(self.user_log_layer, self.dest_file, options)
        if error:
            return False

        return True
