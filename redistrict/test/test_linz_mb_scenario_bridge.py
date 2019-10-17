# coding=utf-8
"""LINZ Scenario - Meshblock Bridge Test.

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
from redistrict.linz.linz_mb_scenario_bridge import LinzMeshblockScenarioBridge
from redistrict.test.test_linz_scenario_registry import make_meshblock_layer, make_meshblock_electorate_layer


class ScenarioMeshblockBridgeTest(unittest.TestCase):
    """Test LinzMeshblockScenarioBridge."""

    def testCreation(self):
        """
        Test creating a LinzMeshblockScenarioBridge
        """
        meshblock_layer = make_meshblock_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        bridge = LinzMeshblockScenarioBridge(
            meshblock_layer=meshblock_layer,
            meshblock_scenario_layer=mb_electorate_layer,
            meshblock_number_field_name='MeshblockNumber'
        )
        self.assertEqual(bridge.meshblock_layer, meshblock_layer)
        self.assertEqual(bridge.meshblock_scenario_layer, mb_electorate_layer)

    def testMeshblockIds(self):
        """
        Test retrieving target meshblock feature ids for different scenarios
        """
        meshblock_layer = make_meshblock_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        bridge = LinzMeshblockScenarioBridge(
            meshblock_layer=meshblock_layer,
            meshblock_scenario_layer=mb_electorate_layer,
            meshblock_number_field_name='MeshblockNumber'
        )

        bridge.scenario = 1
        mb_ids = bridge.get_target_meshblock_ids_from_numbers([0, 1])
        self.assertEqual(mb_ids, {0: 3, 1: 4})
        bridge.scenario = 2
        mb_ids = bridge.get_target_meshblock_ids_from_numbers([0, 1])
        self.assertEqual(mb_ids, {0: 1, 1: 2})

    def testGetNewElectorates(self):
        """
        Test retrieving pending electorate changes
        """
        meshblock_layer = make_meshblock_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()

        bridge = LinzMeshblockScenarioBridge(
            meshblock_layer=meshblock_layer,
            meshblock_scenario_layer=mb_electorate_layer,
            meshblock_number_field_name='MeshblockNumber'
        )

        bridge.task = 'GN'
        bridge.scenario = 1
        # not editable
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {})
        # no changes in buffer
        self.assertTrue(meshblock_layer.startEditing())
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {})

        # add change
        features = [f for f in meshblock_layer.getFeatures()]  # pylint: disable=unnecessary-comprehension
        meshblock_layer.changeAttributeValues(features[0].id(), {1: 'c'})
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {0: 'c'})
        meshblock_layer.changeAttributeValues(features[0].id(), {1: 'd'})
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {0: 'd'})
        meshblock_layer.changeAttributeValues(features[1].id(), {1: 'c'})
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {0: 'd', 1: 'c'})

        # no saved changes in scenario yet!
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'a', 'x'],
                                   [2, 2, 1, 'b', 'y'],
                                   [3, 1, 0, 'c', 'z'],
                                   [4, 1, 1, 'd', 'zz']])

        bridge.meshblock_layer_saved()
        self.assertTrue(meshblock_layer.commitChanges())
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'a', 'x'],
                                   [2, 2, 1, 'b', 'y'],
                                   [3, 1, 0, 'd', 'z'],
                                   [4, 1, 1, 'c', 'zz']])
        new_electorates = bridge.get_new_electorates()
        self.assertEqual(new_electorates, {})

        # different scenario
        bridge.scenario = 2
        self.assertTrue(meshblock_layer.startEditing())
        meshblock_layer.changeAttributeValues(features[0].id(), {1: 'd'})
        meshblock_layer.changeAttributeValues(features[1].id(), {1: 'c'})
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'a', 'x'],
                                   [2, 2, 1, 'b', 'y'],
                                   [3, 1, 0, 'd', 'z'],
                                   [4, 1, 1, 'c', 'zz']])
        bridge.meshblock_layer_saved()
        self.assertTrue(meshblock_layer.commitChanges())
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'd', 'x'],
                                   [2, 2, 1, 'c', 'y'],
                                   [3, 1, 0, 'd', 'z'],
                                   [4, 1, 1, 'c', 'zz']])

        # different task
        bridge.task = 'GS'
        self.assertTrue(meshblock_layer.startEditing())
        meshblock_layer.changeAttributeValues(features[0].id(), {1: 'a'})
        meshblock_layer.changeAttributeValues(features[1].id(), {1: 'b'})
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'd', 'x'],
                                   [2, 2, 1, 'c', 'y'],
                                   [3, 1, 0, 'd', 'z'],
                                   [4, 1, 1, 'c', 'zz']])
        bridge.meshblock_layer_saved()
        self.assertTrue(meshblock_layer.commitChanges())
        results = [f.attributes() for f in mb_electorate_layer.getFeatures()]
        self.assertEqual(results, [[1, 2, 0, 'd', 'a'],
                                   [2, 2, 1, 'c', 'b'],
                                   [3, 1, 0, 'd', 'z'],
                                   [4, 1, 1, 'c', 'zz']])


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioMeshblockBridgeTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
