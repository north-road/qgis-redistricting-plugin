"""
LINZ Scenario Export Task Test.
"""

import unittest
from qgis.core import (
    NULL,
    QgsVectorLayer,
    QgsGeometry,
    QgsFeature
)
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.linz_district_registry import \
    LinzElectoralDistrictRegistry
from redistrict.linz.export_task import ExportTask
from redistrict.test.test_linz_scenario_registry import make_scenario_layer
from redistrict.test.test_linz_district_registry import make_quota_layer
from redistrict.test.test_linz_redistrict_handler import make_user_log_layer


class ExportTaskTest(unittest.TestCase):
    """Test ExportTask."""

    def testExportTask(self):  # pylint: disable=too-many-locals, too-many-statements
        """
        Test export task
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
            "Point?crs=EPSG:4326&field=electorate_id:int&field=code:string&field=type:string&field=estimated_pop:int&field=scenario_id:int&field=deprecated:int&field=invalid:int&field=invalid_reason:string&field=name:string&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=electorate_id_stats:string&field=expected_regions:int",
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
            "Polygon?crs=EPSG:4326&field=MeshblockNumber:string&field=offline_pop_m:int&field=offline_pop_gn:int&field=offline_pop_gs:int&field=staged_electorate:int&field=offshore:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["11", 5, 58900, 0])
        f.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        f2 = QgsFeature()
        f2.setAttributes(["12", 6, 57000, 0])
        f2.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        f3 = QgsFeature()
        f3.setAttributes(["13", 7, 2000, 0])
        f3.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        f4 = QgsFeature()
        f4.setAttributes(["14", 8, 0, 20])
        f4.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        f5 = QgsFeature()
        f5.setAttributes(["15", 9, 0, 30])
        f5.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        f6 = QgsFeature()
        f6.setAttributes(["16", 10, 0, 40])
        f6.setGeometry(QgsGeometry.fromWkt('Polygon((1 1, 2 1, 2 2, 1 2, 1 1))'))
        self.assertTrue(meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6]))

        quota_layer = make_quota_layer()
        user_log_layer = make_user_log_layer()
        f = QgsFeature()
        f.setAttributes([1, NULL, 'user', 'v1', 1, '11', 'GN', 1, 2])
        user_log_layer.dataProvider().addFeature(f)

        electorate_registry = LinzElectoralDistrictRegistry(source_layer=electorate_layer, source_field='electorate_id',
                                                            title_field='code', electorate_type='GN',
                                                            quota_layer=quota_layer)

        out_file = '/tmp/test.gpkg'
        task = ExportTask(task_name='', dest_file=out_file, electorate_registry=electorate_registry,
                          meshblock_layer=meshblock_layer,
                          meshblock_number_field_name='MeshblockNumber', scenario_registry=reg, scenario=1,
                          user_log_layer=user_log_layer)

        self.assertTrue(task.run(), task.message)

        out_electorate_layer = QgsVectorLayer(f'{out_file}|layername=electorates', 'electorates', 'ogr')
        self.assertTrue(out_electorate_layer.isValid())
        self.assertEqual([f.attributes() for f in out_electorate_layer.getFeatures()], [[1, 'GN', 'test1', NULL],
                                                                                        [2, 'GN', 'test2', NULL],
                                                                                        [3, 'GN', 'test3', NULL],
                                                                                        [4, 'GS', 'test4', NULL],
                                                                                        [5, 'GS', 'test5', NULL],
                                                                                        [6, 'M', 'test7', NULL],
                                                                                        [7, 'M', 'test8', NULL]])
        self.assertEqual([f.geometry().asWkt() for f in out_electorate_layer.getFeatures()],
                         ['Polygon ((1 1, 2 1, 2 2, 1 2, 1 1))',
                          'Polygon ((2 1, 1 1, 1 2, 2 2, 2 1))',
                          'Polygon ((1 1, 2 1, 2 2, 1 2, 1 1))',
                          'Polygon ((1 1, 2 1, 2 2, 1 2, 1 1))',
                          'Polygon ((2 1, 1 1, 1 2, 2 2, 2 1))',
                          'Polygon ((2 1, 1 1, 1 2, 2 2, 2 1))',
                          'Polygon ((2 1, 1 1, 1 2, 2 2, 2 1))'])
        out_mb_layer = QgsVectorLayer(f'{out_file}|layername=meshblocks', 'electorates', 'ogr')
        self.assertTrue(out_mb_layer.isValid())
        self.assertEqual([f.attributes() for f in out_mb_layer.getFeatures()], [[1, 11, 'test1', NULL, 'test7'],
                                                                                [2, 12, 'test2', NULL, 'test7'],
                                                                                [3, 13, 'test2', NULL, 'test7'],
                                                                                [4, 14, 'test3', 'test4', 'test8'],
                                                                                [5, 15, NULL, 'test5', 'test8'],
                                                                                [6, 16, NULL, 'test5', 'test8']])
        out_log_layer = QgsVectorLayer(f'{out_file}|layername=user_log', 'electorates', 'ogr')
        self.assertTrue(out_log_layer.isValid())
        self.assertEqual([f.attributes() for f in out_log_layer.getFeatures()],
                         [[1, 1, NULL, 'user', 'v1', 1, '11', 'GN', 1, 2]])


if __name__ == "__main__":
    suite = unittest.makeSuite(ExportTaskTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
