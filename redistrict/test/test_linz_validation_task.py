# coding=utf-8
"""LINZ Scenario Validation Task Test.

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

import unittest
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from redistrict.linz.validation_task import ValidationTask
from redistrict.test.test_linz_scenario_registry import make_scenario_layer
from redistrict.test.test_linz_district_registry import make_quota_layer
from qgis.core import (NULL,
                       QgsVectorLayer,
                       QgsGeometry,
                       QgsPointXY,
                       QgsFeature)


class ValidationTaskTest(unittest.TestCase):
    """Test ValidationTask."""

    def testValidationTask(self):  # pylint: disable=too-many-locals, too-many-statements
        """
        Test validation task
        """
        layer = make_scenario_layer()
        mb_electorate_layer = QgsVectorLayer(
            "NoGeometry?field=id:int&field=scenario_id:int&field=meshblock_number:int&field=gn_id:int&field=gs_id:int&field=m_id:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes([1, 1, 11, 1, 0, 7])
        f2 = QgsFeature()
        f2.setAttributes([2, 1, 12, 2, 0, 7])
        f3 = QgsFeature()
        f3.setAttributes([3, 1, 13, 2, 0, 7])
        f4 = QgsFeature()
        f4.setAttributes([4, 1, 14, 3, 4, 8])
        f5 = QgsFeature()
        f5.setAttributes([5, 1, 15, 0, 5, 8])
        f6 = QgsFeature()
        f6.setAttributes([6, 1, 16, 0, 5, 8])
        mb_electorate_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6])

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        electorate_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=electorate_id:int&field=code:string&field=type:string&field=estimated_pop:int&field=scenario_id:int&field=deprecated:int&field=invalid:int&field=invalid_reason:string&field=name:string&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=electorate_id_stats:string",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes([1, "test1", 'GN', 1, 0, 0, 1, 'old invalid'])
        f2 = QgsFeature()
        f2.setAttributes([2, "test2", 'GN', 1, 0, 0, 1, 'old invalid 2'])
        f3 = QgsFeature()
        f3.setAttributes([3, "test3", 'GN', 1, 0, 0, 1, 'old invalid 3'])
        f4 = QgsFeature()
        f4.setAttributes([4, "test4", 'GS', 1, 0, 0, 1, 'old invalid 4'])
        f5 = QgsFeature()
        f5.setAttributes([5, "test5", 'GS', 1, 0, 0, 1, 'old invalid 5'])
        f6 = QgsFeature()
        f6.setAttributes([6, "test6", 'GS', 1, 0, 0, 1, 'old invalid 6'])
        f7 = QgsFeature()
        f7.setAttributes([7, "test7", 'M', 1, 0, 0, 1, 'old invalid 7'])
        f8 = QgsFeature()
        f8.setAttributes([8, "test8", 'M', 1, 0, 0, 1, 'old invalid 8'])
        electorate_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6, f7, f8])

        meshblock_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=MeshblockNumber:string&field=offline_pop_m:int&field=offline_pop_gn:int&field=offline_pop_gs:int&field=staged_electorate:int&field=offshore:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["11", 5, 58900, 0, NULL, 0])
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
        f2 = QgsFeature()
        f2.setAttributes(["12", 6, 57000, 0, NULL, 0])
        f2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(2, 3)))
        f3 = QgsFeature()
        f3.setAttributes(["13", 7, 2000, 0, NULL, 0])
        f3.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(4, 5)))
        f4 = QgsFeature()
        f4.setAttributes(["14", 8, 0, 20, NULL, 0])
        f4.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(6, 7)))
        f5 = QgsFeature()
        f5.setAttributes(["15", 9, 0, 30, NULL, 0])
        f5.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(8, 9)))
        f6 = QgsFeature()
        f6.setAttributes(["16", 10, 0, 40, NULL, 1])
        f6.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10, 11)))
        meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6])

        quota_layer = make_quota_layer()

        electorate_registry = LinzElectoralDistrictRegistry(source_layer=electorate_layer, source_field='electorate_id',
                                                            title_field='code', electorate_type='GN',
                                                            quota_layer=quota_layer)

        task = ValidationTask(task_name='', electorate_registry=electorate_registry, meshblock_layer=meshblock_layer,
                              meshblock_number_field_name='MeshblockNumber', scenario_registry=reg, scenario=1,
                              task='GN')
        self.assertEqual([f.attributes()[:9] for f in electorate_layer.getFeatures()],
                         [[1, 'test1', 'GN', 1, 0, 0, NULL, NULL, NULL],
                          [2, 'test2', 'GN', 1, 0, 0, NULL, NULL, NULL],
                          [3, 'test3', 'GN', 1, 0, 0, NULL, NULL, NULL],
                          [4, 'test4', 'GS', 1, 0, 0, 1, 'old invalid 4', NULL],
                          [5, 'test5', 'GS', 1, 0, 0, 1, 'old invalid 5', NULL],
                          [6, 'test6', 'GS', 1, 0, 0, 1, 'old invalid 6', NULL],
                          [7, 'test7', 'M', 1, 0, 0, 1, 'old invalid 7', NULL],
                          [8, 'test8', 'M', 1, 0, 0, 1, 'old invalid 8', NULL]])

        self.assertTrue(task.run())
        self.assertEqual(len(task.results), 2)
        self.assertEqual(task.results[0][ValidationTask.ELECTORATE_ID], 2)
        self.assertEqual(task.results[0][ValidationTask.ELECTORATE_NAME], 'test2')
        self.assertEqual(task.results[0][ValidationTask.ERROR], 'Electorate is non-contiguous')
        self.assertEqual(task.results[1][ValidationTask.ELECTORATE_ID], 3)
        self.assertEqual(task.results[1][ValidationTask.ELECTORATE_NAME], 'test3')
        self.assertEqual(task.results[1][ValidationTask.ERROR], 'Outside quota tolerance')
        self.assertEqual([f.attributes()[:9] for f in electorate_layer.getFeatures()],
                         [[1, 'test1', 'GN', 58900, 1, 0, 0, NULL, NULL],
                          [2, 'test2', 'GN', 1, 0, 0, 1, 'Electorate is non-contiguous', NULL],
                          [3, 'test3', 'GN', 1, 0, 0, 1, 'Outside quota tolerance', NULL],
                          [4, 'test4', 'GS', 1, 0, 0, 1, 'old invalid 4', NULL],
                          [5, 'test5', 'GS', 1, 0, 0, 1, 'old invalid 5', NULL],
                          [6, 'test6', 'GS', 1, 0, 0, 1, 'old invalid 6', NULL],
                          [7, 'test7', 'M', 1, 0, 0, 1, 'old invalid 7', NULL],
                          [8, 'test8', 'M', 1, 0, 0, 1, 'old invalid 8', NULL]])

        electorate_registry = LinzElectoralDistrictRegistry(source_layer=electorate_layer, source_field='electorate_id',
                                                            title_field='code', electorate_type='GN',
                                                            quota_layer=quota_layer)

        task = ValidationTask(task_name='', electorate_registry=electorate_registry, meshblock_layer=meshblock_layer,
                              meshblock_number_field_name='MeshblockNumber', scenario_registry=reg, scenario=1,
                              task='GS')

        self.assertTrue(task.run())
        self.assertEqual(len(task.results), 3)
        self.assertEqual(task.results[0][ValidationTask.ELECTORATE_ID], 4)
        self.assertEqual(task.results[0][ValidationTask.ELECTORATE_NAME], 'test4')
        self.assertEqual(task.results[0][ValidationTask.ERROR], 'Outside quota tolerance')
        self.assertEqual(task.results[1][ValidationTask.ELECTORATE_ID], 5)
        self.assertEqual(task.results[1][ValidationTask.ELECTORATE_NAME], 'test5')
        self.assertEqual(task.results[1][ValidationTask.ERROR], 'Outside quota tolerance')
        self.assertEqual(task.results[2][ValidationTask.ELECTORATE_ID], 6)
        self.assertEqual(task.results[2][ValidationTask.ELECTORATE_NAME], 'test6')
        self.assertEqual(task.results[2][ValidationTask.ERROR], 'Outside quota tolerance')
        self.assertEqual([f.attributes()[:9] for f in electorate_layer.getFeatures()],
                         [[1, 'test1', 'GN', 58900, 1, 0, 0, NULL, NULL],
                          [2, 'test2', 'GN', 1, 0, 0, 1, 'Electorate is non-contiguous', NULL],
                          [3, 'test3', 'GN', 1, 0, 0, 1, 'Outside quota tolerance', NULL],
                          [4, 'test4', 'GS', 1, 0, 0, 1, 'Outside quota tolerance', NULL],
                          [5, 'test5', 'GS', 1, 0, 0, 1, 'Outside quota tolerance', NULL],
                          [6, 'test6', 'GS', 1, 0, 0, 1, 'Outside quota tolerance', NULL],
                          [7, 'test7', 'M', 1, 0, 0, 1, 'old invalid 7', NULL],
                          [8, 'test8', 'M', 1, 0, 0, 1, 'old invalid 8', NULL]])


if __name__ == "__main__":
    suite = unittest.makeSuite(ValidationTaskTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
