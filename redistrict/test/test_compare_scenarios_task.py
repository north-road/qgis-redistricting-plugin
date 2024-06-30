"""
Compare scenarios task test.
"""

import unittest

from qgis._core import QgsGeometry
from qgis.core import (
    QgsVectorLayer,
    QgsFeature
)
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.compare_scenarios_task import CompareScenariosTask
from redistrict.test.test_linz_scenario_registry import (
    make_scenario_layer
)


class CompareScenariosTaskTest(unittest.TestCase):
    """Test CompareScenariosTask."""

    def testCompareTask(self):  # pylint: disable=too-many-locals, too-many-statements
        """
        Test compare task
        """
        layer = make_scenario_layer()
        meshblock_layer = QgsVectorLayer(
            "Polygon?field=meshblock_number:str",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(['0000011'])
        f.setGeometry(QgsGeometry.fromWkt('Polygon((0 0, 1 0, 1 1, 0 1, 0 0))'))
        f2 = QgsFeature()
        f2.setAttributes(['0000012'])
        f2.setGeometry(QgsGeometry.fromWkt('Polygon((1 0, 2 0, 2 1, 1 1, 1 0))'))
        self.assertTrue(
            meshblock_layer.dataProvider().addFeatures([f, f2])
        )
        self.assertEqual(meshblock_layer.featureCount(), 2)

        mb_electorate_layer = QgsVectorLayer(
            "NoGeometry?field=id:int&field=scenario_id:int&field=meshblock_number:int&field=gn_id:int&field=gs_id:int&field=m_id:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes([1, 1, 11, 1, 0, 4])
        f2 = QgsFeature()
        f2.setAttributes([2, 2, 11, 1, 3, 7])
        f3 = QgsFeature()
        f3.setAttributes([3, 3, 11, 2, 3, 4])
        f4 = QgsFeature()
        f4.setAttributes([4, 1, 12, 3, 4, 8])
        f5 = QgsFeature()
        f5.setAttributes([5, 2, 12, 3, 4, 8])
        f6 = QgsFeature()
        f6.setAttributes([6, 3, 12, 9, 10, 11])
        self.assertTrue(
            mb_electorate_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6])
        )
        self.assertEqual(mb_electorate_layer.featureCount(), 6)

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GN', 1, 2)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 1, 12: 3})
        self.assertEqual(task.secondary_electorates, {11: 1, 12: 3})
        self.assertFalse(task.changed_meshblocks)
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GN', 1, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 1, 12: 3})
        self.assertEqual(task.secondary_electorates, {11: 2, 12: 9})
        self.assertEqual(task.changed_meshblocks, {11, 12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 1, 2], ['0000012', 3, 9]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))', 'Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GN', 2, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 1, 12: 3})
        self.assertEqual(task.secondary_electorates, {11: 2, 12: 9})
        self.assertEqual(task.changed_meshblocks, {11, 12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 1, 2], ['0000012', 3, 9]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))', 'Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GS', 1, 2)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 0, 12: 4})
        self.assertEqual(task.secondary_electorates, {11: 3, 12: 4})
        self.assertEqual(task.changed_meshblocks, {11})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 0, 3]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GS', 1, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 0, 12: 4})
        self.assertEqual(task.secondary_electorates, {11: 3, 12: 10})
        self.assertEqual(task.changed_meshblocks, {11, 12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 0, 3], ['0000012', 4, 10]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))', 'Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'GS', 2, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 3, 12: 4})
        self.assertEqual(task.secondary_electorates, {11: 3, 12: 10})
        self.assertEqual(task.changed_meshblocks, {12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000012', 4, 10]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'M', 1, 2)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 4, 12: 8})
        self.assertEqual(task.secondary_electorates, {11: 7, 12: 8})
        self.assertEqual(task.changed_meshblocks, {11})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 4, 7]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'M', 1, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 4, 12: 8})
        self.assertEqual(task.secondary_electorates, {11: 4, 12: 11})
        self.assertEqual(task.changed_meshblocks, {12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000012', 8, 11]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

        task = CompareScenariosTask('', reg, meshblock_layer, 'meshblock_number', 'M', 2, 3)
        self.assertTrue(task.run())
        self.assertEqual(task.base_electorates, {11: 7, 12: 8})
        self.assertEqual(task.secondary_electorates, {11: 4, 12: 11})
        self.assertEqual(task.changed_meshblocks, {11, 12})
        self.assertCountEqual([f.attributes() for f in task.changed_meshblocks_layer.getFeatures()],
                              [['0000011', 7, 4], ['0000012', 8, 11]])
        self.assertCountEqual([f.geometry().asWkt() for f in task.changed_meshblocks_layer.getFeatures()],
                              ['Polygon ((0 0, 1 0, 1 1, 0 1, 0 0))', 'Polygon ((1 0, 2 0, 2 1, 1 1, 1 0))'])

if __name__ == "__main__":
    suite = unittest.makeSuite(CompareScenariosTaskTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
