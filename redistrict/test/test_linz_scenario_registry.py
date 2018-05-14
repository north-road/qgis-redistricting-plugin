# coding=utf-8
"""LINZ Scenario Registry Test.

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

import unittest
from collections import OrderedDict
from redistrict.linz.scenario_registry import ScenarioRegistry
from qgis.PyQt.QtCore import QDateTime
from qgis.core import (QgsApplication,
                       QgsVectorLayer,
                       QgsFeature)


def make_scenario_layer() -> QgsVectorLayer:
    """
    Makes a dummy scenario layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=id:int&field=name:string&field=created:datetime&field=created_by:string",
        "source", "memory")
    f = QgsFeature()
    f.setAttributes([1, "Scenario 1"])
    f2 = QgsFeature()
    f2.setAttributes([2, "scenario B"])
    f3 = QgsFeature()
    f3.setAttributes([3, "scenario 3"])
    layer.dataProvider().addFeatures([f, f2, f3])
    return layer


def make_meshblock_electorate_layer() -> QgsVectorLayer:
    """
    Makes a dummy meshblock-electorate layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=id:int&field=scenario_id:int&field=meshblock_number:int&field=code:string&field=code2:string",
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

        # dupe name
        res, error = reg.branch_scenario(1, 'Scenario 1')
        self.assertFalse(res)
        self.assertIn('already exists', error)

        # missing source scenario
        res, error = reg.branch_scenario(5, 'Scenario 5')
        self.assertFalse(res)
        self.assertIn('does not exist', error)

        # good
        res, error = reg.branch_scenario(1, 'Scenario 5')
        self.assertEqual(res, 4)
        self.assertFalse(error)

        f = [f for f in layer.getFeatures()][-1]
        self.assertEqual(f[0], res)
        self.assertEqual(f[1], 'Scenario 5')
        self.assertEqual(f[2].date(), QDateTime.currentDateTime().date())
        self.assertEqual(f[3], QgsApplication.userFullName())

        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[3, 4, 0, 'c', 'z'],
                             [4, 4, 1, 'd', 'zz'],
                             [1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz']])

        res, error = reg.branch_scenario(2, 'Scenario 6')
        self.assertEqual(res, 5)
        self.assertFalse(error)

        f = [f for f in layer.getFeatures()][-1]
        self.assertEqual(f[0], res)
        self.assertEqual(f[1], 'Scenario 6')
        self.assertEqual(f[2].date(), QDateTime.currentDateTime().date())
        self.assertEqual(f[3], QgsApplication.userFullName())

        f = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(f, [[3, 4, 0, 'c', 'z'],
                             [4, 4, 1, 'd', 'zz'],
                             [1, 5, 0, 'a', 'x'],
                             [2, 5, 1, 'b', 'y'],
                             [1, 2, 0, 'a', 'x'],
                             [2, 2, 1, 'b', 'y'],
                             [3, 1, 0, 'c', 'z'],
                             [4, 1, 1, 'd', 'zz']])


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
