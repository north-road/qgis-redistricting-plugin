# coding=utf-8
"""LINZ Interactive Redistricting Dock test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '1/05/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import unittest
from qgis.core import QgsGeometry
from redistrict.linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.validation_task import ValidationTask
from redistrict.test.test_linz_scenario_registry import make_scenario_layer
from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LinzRedistrictingDockWidgetTest(unittest.TestCase):
    """Test LinzRedistrictingDockWidget."""

    def testConstruct(self):
        """
        Test constructing dock
        """
        scenario_layer = make_scenario_layer()
        scenario_registry = ScenarioRegistry(source_layer=scenario_layer, id_field='id', name_field='name',
                                             meshblock_electorate_layer=None)
        context = LinzRedistrictingContext(scenario_registry=scenario_registry)
        widget = LinzRedistrictingDockWidget(context=context, iface=IFACE)
        self.assertIsNotNone(widget)

    def testTitle(self):
        """
        Test title updates
        """
        scenario_layer = make_scenario_layer()
        scenario_registry = ScenarioRegistry(source_layer=scenario_layer, id_field='id', name_field='name',
                                             meshblock_electorate_layer=None)
        context = LinzRedistrictingContext(scenario_registry=scenario_registry)
        context.task = LinzRedistrictingContext.TASK_GS
        context.scenario = 1
        widget = LinzRedistrictingDockWidget(context=context, iface=IFACE)
        self.assertEqual(widget.windowTitle(), 'Redistricting - General (South Island) - Scenario 1')
        context.task = LinzRedistrictingContext.TASK_GN
        context.scenario = 3
        widget.update_dock_title(context=context)
        self.assertEqual(widget.windowTitle(), 'Redistricting - General (North Island) - scenario 3')

    def testShowResults(self):
        """
        Test showing validation results
        """
        scenario_layer = make_scenario_layer()
        scenario_registry = ScenarioRegistry(source_layer=scenario_layer, id_field='id', name_field='name',
                                             meshblock_electorate_layer=None)
        context = LinzRedistrictingContext(scenario_registry=scenario_registry)
        widget = LinzRedistrictingDockWidget(context=context, iface=IFACE)
        widget.show_validation_results([{ValidationTask.ELECTORATE_ID: 1, ValidationTask.ELECTORATE_NAME: 'name 1',
                                         ValidationTask.ERROR: 'error 1',
                                         ValidationTask.ELECTORATE_GEOMETRY: QgsGeometry()},
                                        {ValidationTask.ELECTORATE_ID: 2, ValidationTask.ELECTORATE_NAME: 'name 2',
                                         ValidationTask.ERROR: 'error 2',
                                         ValidationTask.ELECTORATE_GEOMETRY: QgsGeometry()}])
        self.assertEqual(widget.table.rowCount(), 2)
        self.assertEqual(widget.table.item(0, 1).text(), 'name 1')
        self.assertEqual(widget.table.item(0, 2).text(), 'error 1')
        self.assertEqual(widget.table.item(1, 1).text(), 'name 2')
        self.assertEqual(widget.table.item(1, 2).text(), 'error 2')
        widget.show_validation_results([{ValidationTask.ELECTORATE_ID: 1, ValidationTask.ELECTORATE_NAME: 'name 1',
                                         ValidationTask.ERROR: 'error 1',
                                         ValidationTask.ELECTORATE_GEOMETRY: QgsGeometry()}])
        self.assertEqual(widget.table.rowCount(), 1)
        self.assertEqual(widget.table.item(0, 1).text(), 'name 1')
        self.assertEqual(widget.table.item(0, 2).text(), 'error 1')

        # pretend click
        widget.table.cellWidget(0, 0).click()

        # hide table
        widget.show_message('Test<br />Message')
        self.assertIn('Test<br />Message', widget.frame.toHtml())
        self.assertIsNone(widget.table)


if __name__ == "__main__":
    suite = unittest.makeSuite(LinzRedistrictingDockWidgetTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
