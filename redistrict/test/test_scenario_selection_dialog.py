# coding=utf-8
"""Scenario Selection Dialog Test.

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
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_selection_dialog import ScenarioSelectionDialog
from redistrict.test.test_linz_scenario_registry import make_scenario_layer, make_meshblock_electorate_layer

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class ScenarioSelectionDialogTest(unittest.TestCase):
    """Test ScenarioSelectionDialog."""

    def testConstruct(self):
        """
        Test creating dialog
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        self.assertIsNotNone(ScenarioSelectionDialog(scenario_registry=registry))

    def testPopulation(self):
        """
        Test that dialog is correctly populated from registry
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        dlg = ScenarioSelectionDialog(scenario_registry=registry)
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])

        # initial selection must be final scenario
        self.assertEqual(dlg.selected_scenario(), 2)

    def testSelection(self):
        """
        Test setting/getting selected scenario
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        dlg = ScenarioSelectionDialog(scenario_registry=registry)

        dlg.set_selected_scenario(1)
        self.assertEqual(dlg.selected_scenario(), 1)
        dlg.set_selected_scenario(2)
        self.assertEqual(dlg.selected_scenario(), 2)
        dlg.set_selected_scenario(3)
        self.assertEqual(dlg.selected_scenario(), 3)

        # nothing at all selected
        dlg.list.clearSelection()
        self.assertIsNone(dlg.selected_scenario())

    def testAccept(self):
        """
        Test that accepting dialog
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        dlg = ScenarioSelectionDialog(scenario_registry=registry)
        dlg.set_selected_scenario('d4')
        dlg.accept()

    def testFilter(self):
        """
        Test filtering inside the dialog
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        dlg = ScenarioSelectionDialog(scenario_registry=registry)
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])
        dlg.search.setText('eee')  # connection not fired on first change?
        dlg.search.setText('3')
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count()) if not dlg.list.item(r).isHidden()],
                         ['scenario 3'])
        dlg.search.setText('B')
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count()) if not dlg.list.item(r).isHidden()],
                         ['scenario B'])
        # case insensitive!
        dlg.search.setText('b')
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count()) if not dlg.list.item(r).isHidden()],
                         ['scenario B'])


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
