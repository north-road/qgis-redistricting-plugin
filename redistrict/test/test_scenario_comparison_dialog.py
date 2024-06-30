"""
Scenario comparison dialog Test.
"""

import unittest

from PyQt5.QtWidgets import QDialogButtonBox

from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_comparison_dialog import ScenarioComparisonDialog
from redistrict.test.test_linz_scenario_registry import make_scenario_layer, make_meshblock_electorate_layer

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class ScenarioComparisonDialogTest(unittest.TestCase):
    """Test ScenarioComparisonDialog."""

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
        self.assertIsNotNone(ScenarioComparisonDialog(scenario_registry=registry))

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
        dlg = ScenarioComparisonDialog(scenario_registry=registry)
        self.assertEqual([dlg.base_selection_widget.list.item(r).text()
                          for r in range(dlg.base_selection_widget.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])
        self.assertEqual([dlg.secondary_selection_widget.list.item(r).text()
                          for r in range(dlg.secondary_selection_widget.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])

        # initial selection must be final scenario
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertEqual(dlg.selected_secondary_scenario(), 2)

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
        dlg = ScenarioComparisonDialog(scenario_registry=registry)

        dlg.set_base_scenario(1)
        self.assertEqual(dlg.selected_base_scenario(), 1)
        self.assertEqual(dlg.selected_secondary_scenario(), 2)
        dlg.set_base_scenario(2)
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertEqual(dlg.selected_secondary_scenario(), 2)
        dlg.set_base_scenario(3)
        self.assertEqual(dlg.selected_base_scenario(), 3)
        self.assertEqual(dlg.selected_secondary_scenario(), 2)

        # nothing at all selected
        dlg.base_selection_widget.list.clearSelection()
        self.assertIsNone(dlg.selected_base_scenario())
        self.assertEqual(dlg.selected_secondary_scenario(), 2)

        dlg.set_base_scenario(2)
        dlg.set_secondary_scenario(1)
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertEqual(dlg.selected_secondary_scenario(), 1)
        dlg.set_secondary_scenario(2)
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertEqual(dlg.selected_secondary_scenario(), 2)
        dlg.set_secondary_scenario(3)
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertEqual(dlg.selected_secondary_scenario(), 3)

        # nothing at all selected
        dlg.secondary_selection_widget.list.clearSelection()
        self.assertEqual(dlg.selected_base_scenario(), 2)
        self.assertIsNone(dlg.selected_secondary_scenario())

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
        dlg = ScenarioComparisonDialog(scenario_registry=registry)
        dlg.set_base_scenario(1)
        dlg.set_secondary_scenario(2)
        self.assertTrue(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())

        # same scenario selection not permitted
        dlg.set_secondary_scenario(1)
        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())

        dlg.set_secondary_scenario(2)
        dlg.accept()


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioComparisonDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
