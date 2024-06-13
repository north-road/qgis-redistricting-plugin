"""
LINZ Scenario Registry Test.
"""

import unittest
from collections import OrderedDict

from qgis.PyQt.QtCore import (
    QDateTime,
    QDate,
    QTime
)

from qgis.core import (
    NULL,
    QgsApplication,
    QgsVectorLayer,
    QgsGeometry,
    QgsPointXY,
    QgsFeature
)

from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_switch_task import ScenarioSwitchTask
from redistrict.linz.staged_electorate_update_task import \
    UpdateStagedElectoratesTask
from redistrict.test.utilities import normalized_wkt, get_qgis_app

QGIS_APP = get_qgis_app()


EMPTY_GEOMETRY_COLLECTION_WKT = QgsGeometry.fromWkt('GeometryCollection ()').asWkt()


def make_scenario_layer() -> QgsVectorLayer:
    """
    Makes a dummy scenario layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=id:int&field=name:string&field=created:datetime&field=created_by:string",
        "source", "memory")
    f = QgsFeature()
    f.setAttributes([1, "Scenario 1", QDateTime(QDate(2018, 6, 4), QTime(12, 13, 14)), 'user 1'])
    f2 = QgsFeature()
    f2.setAttributes([2, "scenario B", QDateTime(QDate(2018, 7, 5), QTime(12, 13, 14)), 'user 2'])
    f3 = QgsFeature()
    f3.setAttributes([3, "scenario 3", QDateTime(QDate(2018, 8, 9), QTime(12, 13, 14)), 'user 3'])
    layer.dataProvider().addFeatures([f, f2, f3])
    assert layer.featureCount() == 3
    return layer


def make_meshblock_electorate_layer() -> QgsVectorLayer:
    """
    Makes a dummy meshblock-electorate layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=id:int&field=scenario_id:int&field=meshblock_number:int&field=gn_id:string&field=gs_id:string",
        "source", "memory")
    f = QgsFeature()
    f.setAttributes([1, 2, 0, 'a', 'x'])
    f2 = QgsFeature()
    f2.setAttributes([2, 2, 1, 'b', 'y'])
    f3 = QgsFeature()
    f3.setAttributes([3, 1, 0, 'c', 'z'])
    f4 = QgsFeature()
    f4.setAttributes([4, 1, 1, 'd', 'zz'])
    layer.dataProvider().addFeatures([f, f2, f3, f4])
    return layer


def make_meshblock_layer() -> QgsVectorLayer:
    """
    Makes a dummy meshblock layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=MeshblockNumber:string&field=staged_electorate:string",
        "source", "memory")
    f = QgsFeature()
    f.setAttributes(['0', 'a'])
    f2 = QgsFeature()
    f2.setAttributes(['1', 'b'])
    assert layer.dataProvider().addFeatures([f, f2])
    return layer


class ScenarioRegistryTest(unittest.TestCase):
    """Test ScenarioRegistry."""

    def testScenarioRegistry(self):
        """
        Test a LinzDistrictRegistry
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertEqual(reg.source_layer, layer)
        self.assertEqual(reg.id_field, 'id')
        self.assertEqual(reg.id_field_index, 0)
        self.assertEqual(reg.name_field, 'name')
        self.assertEqual(reg.name_field_index, 1)

    def testGetScenarioName(self):
        """
        Test retrieving scenario name
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertEqual(reg.get_scenario_name(1), "Scenario 1")
        self.assertEqual(reg.get_scenario_name(2), "scenario B")
        self.assertEqual(reg.get_scenario_name(3), "scenario 3")

    def testGetScenario(self):
        """
        Test retrieving scenario feature
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        f = reg.get_scenario(1)
        self.assertEqual(f.attributes(), [1, 'Scenario 1', QDateTime(2018, 6, 4, 12, 13, 14), 'user 1'])
        f = reg.get_scenario(2)
        self.assertEqual(f.attributes(), [2, 'scenario B', QDateTime(2018, 7, 5, 12, 13, 14), 'user 2'])

    def testGetScenarioList(self):
        """
        Test retrieving scenario list
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertEqual(reg.scenario_list(), [1, 2, 3])

    def testGetScenarioTitles(self):
        """
        Test retrieving scenario titles
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertEqual(reg.scenario_titles(), OrderedDict([('Scenario 1', 1), ('scenario 3', 3), ('scenario B', 2)]))

    def testScenarioNameExists(self):
        """
        Test scenario name exists
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertFalse(reg.scenario_name_exists('bbbb'))
        self.assertTrue(reg.scenario_name_exists('Scenario 1'))
        self.assertTrue(reg.scenario_name_exists('scenario 3'))

    def testScenarioExists(self):
        """
        Test scenario exists
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        self.assertFalse(reg.scenario_exists(-1))
        self.assertTrue(reg.scenario_exists(1))
        self.assertTrue(reg.scenario_exists(3))
        self.assertFalse(reg.scenario_exists(5))

    def testBranch(self):
        """
        Test branching scenario
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )

        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz']])

        # dupe name
        res, error = reg.branch_scenario(1, 'Scenario 1')
        self.assertFalse(res)
        self.assertIn('already exists', error)
        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz']])

        # missing source scenario
        res, error = reg.branch_scenario(5, 'Scenario 5')
        self.assertFalse(res)
        self.assertIn('does not exist', error)
        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz']])

        # good
        res, error = reg.branch_scenario(1, 'Scenario 5')
        self.assertFalse(error)
        self.assertEqual(res, 4)

        f = [f for f in layer.getFeatures()][-1]  # pylint: disable=unnecessary-comprehension
        self.assertEqual(f[0], res)
        self.assertEqual(f[1], 'Scenario 5')
        self.assertEqual(f[2].date(), QDateTime.currentDateTime().date())
        self.assertEqual(f[3], QgsApplication.userFullName())

        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz'],
                             [3, 4, 0, 'c', 'z'],
                             [4, 4, 1, 'd', 'zz']])

        res, error = reg.branch_scenario(2, 'Scenario 6')
        self.assertFalse(error)
        self.assertEqual(res, 5)

        f = [f for f in layer.getFeatures()][-1]  # pylint: disable=unnecessary-comprehension
        self.assertEqual(f[0], res)
        self.assertEqual(f[1], 'Scenario 6')
        self.assertEqual(f[2].date(), QDateTime.currentDateTime().date())
        self.assertEqual(f[3], QgsApplication.userFullName())

        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz'],
                             [3, 4, 0, 'c', 'z'],
                             [4, 4, 1, 'd', 'zz'],
                             [1, 5, 0, 'a', 'x'],
                             [2, 5, 1, 'b', 'y']])

    def testCopyScenarios(self):
        """
        Test copying scenarios between registries
        """
        layer1 = make_scenario_layer()
        mb_electorate_layer1 = make_meshblock_electorate_layer()

        reg1 = ScenarioRegistry(
            source_layer=layer1,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer1
        )

        layer2 = make_scenario_layer()
        layer2.dataProvider().truncate()
        mb_electorate_layer2 = make_meshblock_electorate_layer()
        mb_electorate_layer2.dataProvider().truncate()

        reg2 = ScenarioRegistry(
            source_layer=layer2,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer2
        )
        self.assertEqual(layer2.featureCount(), 0)
        self.assertEqual(mb_electorate_layer2.featureCount(), 0)

        res, error = reg2.import_scenario_from_other_registry(source_registry=reg1,
                                                              source_scenario_id=-1,
                                                              new_scenario_name='copied scenario')
        self.assertFalse(res)
        self.assertIn('does not exist ', error)

        # good params
        res, error = reg2.import_scenario_from_other_registry(source_registry=reg1,
                                                              source_scenario_id=1,
                                                              new_scenario_name='copied scenario')
        self.assertTrue(res)
        self.assertFalse(error)
        self.assertEqual(layer2.featureCount(), 1)
        self.assertEqual(mb_electorate_layer2.featureCount(), 2)
        f = [f for f in layer2.getFeatures()][-1]  # pylint: disable=unnecessary-comprehension
        self.assertEqual(f[0], res)
        self.assertEqual(f[1], 'copied scenario')
        self.assertEqual(f[2].date(), QDate(2018, 6, 4))
        self.assertEqual(f[3], 'user 1')

        f = [f.attributes() for f in mb_electorate_layer2.getFeatures()]
        self.assertEqual(f, [[3, res, 0, 'c', 'z'],
                             [4, res, 1, 'd', 'zz']])

        res2, error = reg2.import_scenario_from_other_registry(source_registry=reg1,
                                                               source_scenario_id=2,
                                                               new_scenario_name='copied scenario 2')
        self.assertTrue(res2)
        self.assertFalse(error)
        self.assertEqual(layer2.featureCount(), 2)
        self.assertEqual(mb_electorate_layer2.featureCount(), 4)
        f = [f for f in layer2.getFeatures()][-1]  # pylint: disable=unnecessary-comprehension
        self.assertEqual(f[0], res2)
        self.assertEqual(f[1], 'copied scenario 2')
        self.assertEqual(f[2].date(), QDate(2018, 7, 5))
        self.assertEqual(f[3], 'user 2')

        f = [f.attributes() for f in mb_electorate_layer2.getFeatures()]
        self.assertEqual(f, [[3, res, 0, 'c', 'z'],
                             [4, res, 1, 'd', 'zz'],
                             [1, res2, 0, 'a', 'x'],
                             [2, res2, 1, 'b', 'y']])

        # dupe name
        res, error = reg2.import_scenario_from_other_registry(source_registry=reg1,
                                                              source_scenario_id=-1,
                                                              new_scenario_name='copied scenario')
        self.assertFalse(res)
        self.assertIn('already exists', error)

    def testElectorateMeshblocks(self):
        """
        Test retrieving meshblocks belong to an electorate for a scenario
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )

        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='c', electorate_type='GN', scenario_id=1)]
        self.assertEqual(res, [0])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='d', electorate_type='GN', scenario_id=1)]
        self.assertEqual(res, [1])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='a', electorate_type='GN', scenario_id=1)]
        self.assertEqual(res, [])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='z', electorate_type='GS', scenario_id=1)]
        self.assertEqual(res, [0])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='zz', electorate_type='GS', scenario_id=1)]
        self.assertEqual(res, [1])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='x', electorate_type='GS', scenario_id=1)]
        self.assertEqual(res, [])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='a', electorate_type='GN', scenario_id=2)]
        self.assertEqual(res, [0])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='b', electorate_type='GN', scenario_id=2)]
        self.assertEqual(res, [1])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='c', electorate_type='GN', scenario_id=2)]
        self.assertEqual(res, [])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='x', electorate_type='GS', scenario_id=2)]
        self.assertEqual(res, [0])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='y', electorate_type='GS', scenario_id=2)]
        self.assertEqual(res, [1])
        res = [f['meshblock_number'] for f in
               reg.electorate_meshblocks(electorate_id='z', electorate_type='GS', scenario_id=2)]
        self.assertEqual(res, [])

    def testElectorateHasMeshblocks(self):
        """
        Test checking whether an electorate has meshblocks assigned
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )

        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='c', electorate_type='GN', scenario_id=1))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='d', electorate_type='GN', scenario_id=1))
        self.assertFalse(reg.electorate_has_meshblocks(electorate_id='a', electorate_type='GN', scenario_id=1))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='z', electorate_type='GS', scenario_id=1))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='zz', electorate_type='GS', scenario_id=1))
        self.assertFalse(reg.electorate_has_meshblocks(electorate_id='x', electorate_type='GS', scenario_id=1))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='a', electorate_type='GN', scenario_id=2))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='b', electorate_type='GN', scenario_id=2))
        self.assertFalse(reg.electorate_has_meshblocks(electorate_id='c', electorate_type='GN', scenario_id=2))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='x', electorate_type='GS', scenario_id=2))
        self.assertTrue(reg.electorate_has_meshblocks(electorate_id='y', electorate_type='GS', scenario_id=2))
        self.assertFalse(reg.electorate_has_meshblocks(electorate_id='z', electorate_type='GS', scenario_id=2))

    def testSwitchTask(self):  # pylint: disable=too-many-locals, too-many-statements
        """
        Test scenario switch task
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
        f4.setAttributes([4, 1, 14, 0, 4, 8])
        f5 = QgsFeature()
        f5.setAttributes([5, 1, 15, 0, 5, 8])
        f6 = QgsFeature()
        f6.setAttributes([6, 1, 16, 0, 5, 8])
        f7 = QgsFeature()
        f7.setAttributes([7, 2, 11, 2, 0, 7])
        f8 = QgsFeature()
        f8.setAttributes([8, 2, 12, 2, 0, 8])
        f9 = QgsFeature()
        f9.setAttributes([9, 2, 13, 3, 0, 7])
        f10 = QgsFeature()
        f10.setAttributes([10, 2, 14, 0, 5, 8])
        f11 = QgsFeature()
        f11.setAttributes([11, 2, 15, 0, 4, 7])
        f12 = QgsFeature()
        f12.setAttributes([12, 2, 16, 0, 4, 8])
        mb_electorate_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12])

        reg = ScenarioRegistry(
            source_layer=layer,
            id_field='id',
            name_field='name',
            meshblock_electorate_layer=mb_electorate_layer
        )
        electorate_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=electorate_id:int&field=code:string&field=type:string&field=estimated_pop:int&field=scenario_id:int&field=invalid:int&field=invalid_reason:string&field=name:string&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=expected_regions:int&field=deprecated:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes([1, "test1", 'GN', -1, 0, 1, 'old invalid', NULL, 1111, 11, -11])
        f2 = QgsFeature()
        f2.setAttributes([2, "test2", 'GN', -1, 0, 1, 'old invalid 2', NULL, 1112, 12, -12])
        f3 = QgsFeature()
        f3.setAttributes([3, "test3", 'GN', -1, 0, 1, 'old invalid 3', NULL, 1113, 13, -13])
        f4 = QgsFeature()
        f4.setAttributes([4, "test4", 'GS', -1, 0, 1, 'old invalid 4', NULL, 1114, 14, -14])
        f5 = QgsFeature()
        f5.setAttributes([5, "test5", 'GS', -1, 0, 1, 'old invalid 5', NULL, 1115, 15, -15])
        f6 = QgsFeature()
        f6.setAttributes([6, "test6", 'GS', -1, 0, 1, 'old invalid 6', NULL, 1116, 16, -16])
        f7 = QgsFeature()
        f7.setAttributes([7, "test7", 'M', -1, 0, 1, 'old invalid 7', NULL, 1117, 17, -17])
        f8 = QgsFeature()
        f8.setAttributes([8, "test8", 'M', -1, 0, 1, 'old invalid 8', NULL, 1118, 18, -18])
        electorate_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6, f7, f8])

        meshblock_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=MeshblockNumber:string&field=offline_pop_m:int&field=offline_pop_gn:int&field=offline_pop_gs:int&field=staged_electorate:int&field=offshore:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["11", 5, 11, 0])
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(1, 2)))
        f2 = QgsFeature()
        f2.setAttributes(["12", 6, 12, 0])
        f2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(2, 3)))
        f3 = QgsFeature()
        f3.setAttributes(["13", 7, 13, 0])
        f3.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(4, 5)))
        f4 = QgsFeature()
        f4.setAttributes(["14", 8, 0, 20])
        f4.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(6, 7)))
        f5 = QgsFeature()
        f5.setAttributes(["15", 9, 0, 30])
        f5.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(8, 9)))
        f6 = QgsFeature()
        f6.setAttributes(["16", 10, 0, 40])
        f6.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(10, 11)))
        meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6])

        task = ScenarioSwitchTask(task_name='', electorate_layer=electorate_layer, meshblock_layer=meshblock_layer,
                                  meshblock_number_field_name='MeshblockNumber', scenario_registry=reg, scenario=1)
        self.assertTrue(task.run())
        self.assertEqual([f.attributes() for f in electorate_layer.getFeatures()],
                         [[1, 'test1', 'GN', 11, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [2, 'test2', 'GN', 25, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [3, 'test3', 'GN', 0, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [4, 'test4', 'GS', 20, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [5, 'test5', 'GS', 70, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [6, 'test6', 'GS', 0, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [7, 'test7', 'M', 18, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [8, 'test8', 'M', 27, 1, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL]])
        self.assertEqual([normalized_wkt(f.geometry()) for f in electorate_layer.getFeatures()], ['Point (1 2)',
                                                                                          'MultiPoint ((4 5),(2 3))',
                                                                                          '',
                                                                                          'Point (6 7)',
                                                                                          'MultiPoint ((10 11),(8 9))',
                                                                                          '',
                                                                                          'MultiPoint ((4 5),(2 3),(1 2))',
                                                                                          'MultiPoint ((10 11),(8 9),(6 7))'])
        task = UpdateStagedElectoratesTask(task_name='', meshblock_layer=meshblock_layer,
                                           meshblock_number_field_name='MeshblockNumber',
                                           scenario_registry=reg, scenario=1, task='GN')
        self.assertTrue(task.run())
        self.assertEqual([f['staged_electorate'] for f in meshblock_layer.getFeatures()], [1, 2, 2, 0, 0, 0])
        task = UpdateStagedElectoratesTask(task_name='', meshblock_layer=meshblock_layer,
                                           meshblock_number_field_name='MeshblockNumber',
                                           scenario_registry=reg, scenario=1, task='M')
        self.assertTrue(task.run())
        self.assertEqual([f['staged_electorate'] for f in meshblock_layer.getFeatures()], [7, 7, 7, 8, 8, 8])

        task = ScenarioSwitchTask(task_name='', electorate_layer=electorate_layer, meshblock_layer=meshblock_layer,
                                  meshblock_number_field_name='MeshblockNumber', scenario_registry=reg, scenario=2)
        self.assertTrue(task.run())
        self.assertEqual([f.attributes() for f in electorate_layer.getFeatures()],
                         [[1, 'test1', 'GN', 0, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [2, 'test2', 'GN', 23, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [3, 'test3', 'GN', 13, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [4, 'test4', 'GS', 70, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [5, 'test5', 'GS', 20, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [6, 'test6', 'GS', 0, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [7, 'test7', 'M', 21, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL],
                          [8, 'test8', 'M', 24, 2, NULL, None, NULL, NULL, NULL, NULL, NULL, NULL]])
        self.assertEqual([normalized_wkt(f.geometry()) for f in electorate_layer.getFeatures()], ['',
                                                                                          'MultiPoint ((2 3),(1 2))',
                                                                                          'Point (4 5)',
                                                                                          'MultiPoint ((10 11),(8 9))',
                                                                                          'Point (6 7)',
                                                                                          '',
                                                                                          'MultiPoint ((8 9),(4 5),(1 2))',
                                                                                          'MultiPoint ((10 11),(6 7),(2 3))'])
        task = UpdateStagedElectoratesTask(task_name='', meshblock_layer=meshblock_layer,
                                           meshblock_number_field_name='MeshblockNumber',
                                           scenario_registry=reg, scenario=2, task='GN')
        self.assertTrue(task.run())
        self.assertEqual([f['staged_electorate'] for f in meshblock_layer.getFeatures()], [2, 2, 3, 0, 0, 0])
        task = UpdateStagedElectoratesTask(task_name='', meshblock_layer=meshblock_layer,
                                           meshblock_number_field_name='MeshblockNumber',
                                           scenario_registry=reg, scenario=2, task='M')
        self.assertTrue(task.run())
        self.assertEqual([f['staged_electorate'] for f in meshblock_layer.getFeatures()], [7, 8, 7, 8, 7, 8])


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
