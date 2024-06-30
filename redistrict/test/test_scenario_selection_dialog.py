"""
Scenario Selection widget and dialog Test.
"""


import unittest
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.scenario_selection_dialog import ScenarioSelectionDialog
from redistrict.linz.scenario_selection_widget import ScenarioSelectionWidget
from redistrict.test.test_linz_scenario_registry import make_scenario_layer, make_meshblock_electorate_layer

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class ScenarioSelectionWidgetTest(unittest.TestCase):
    """Test ScenarioSelectionWidget."""

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
        self.assertIsNotNone(ScenarioSelectionWidget(scenario_registry=registry))

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
        widget = ScenarioSelectionWidget(scenario_registry=registry)
        self.assertEqual([widget.list.item(r).text()
                          for r in range(widget.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])

        # initial selection must be final scenario
        self.assertEqual(widget.selected_scenario(), 2)

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
        widget = ScenarioSelectionWidget(scenario_registry=registry)

        widget.set_selected_scenario(1)
        self.assertEqual(widget.selected_scenario(), 1)
        widget.set_selected_scenario(2)
        self.assertEqual(widget.selected_scenario(), 2)
        widget.set_selected_scenario(3)
        self.assertEqual(widget.selected_scenario(), 3)

        # nothing at all selected
        widget.list.clearSelection()
        self.assertIsNone(widget.selected_scenario())

    def testFilter(self):
        """
        Test filtering inside the widget
        """
        layer = make_scenario_layer()
        mb_electorate_layer = make_meshblock_electorate_layer()
        registry = ScenarioRegistry(source_layer=layer,
                                    id_field='id',
                                    name_field='name',
                                    meshblock_electorate_layer=mb_electorate_layer)
        widget = ScenarioSelectionWidget(scenario_registry=registry)
        self.assertEqual([widget.list.item(r).text()
                          for r in range(widget.list.count())],
                         ['Scenario 1', 'scenario 3', 'scenario B'])
        widget.search.setText('eee')  # connection not fired on first change?
        widget.search.setText('3')
        self.assertEqual([widget.list.item(r).text()
                          for r in range(widget.list.count()) if not widget.list.item(r).isHidden()],
                         ['scenario 3'])
        widget.search.setText('B')
        self.assertEqual([widget.list.item(r).text()
                          for r in range(widget.list.count()) if not widget.list.item(r).isHidden()],
                         ['scenario B'])
        # case insensitive!
        widget.search.setText('b')
        self.assertEqual([widget.list.item(r).text()
                          for r in range(widget.list.count()) if not widget.list.item(r).isHidden()],
                         ['scenario B'])


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
        self.assertEqual([dlg.selection_widget.list.item(r).text()
                          for r in range(dlg.selection_widget.list.count())],
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
        dlg.selection_widget.list.clearSelection()
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
        dlg.set_selected_scenario(4)
        dlg.accept()


if __name__ == "__main__":
    suite = unittest.makeSuite(ScenarioSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
