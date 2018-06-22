# coding=utf-8
"""LINZ Interactive Validation Results Dock test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '1/05/2018'
__copyright__ = 'Copyright 2018, LINZ'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import unittest
from qgis.core import QgsGeometry
from redistrict.linz.linz_validation_results_dock_widget import LinzValidationResultsDockWidget
from redistrict.linz.validation_task import ValidationTask
from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class LinzValidationResultsDockWidgetTest(unittest.TestCase):
    """Test LinzValidationResultsDockWidget."""

    def testConstruct(self):
        """
        Test constructing dock
        """
        widget = LinzValidationResultsDockWidget(IFACE)
        self.assertIsNotNone(widget)

    def testShowResults(self):
        """
        Test showing validation results
        """
        widget = LinzValidationResultsDockWidget(IFACE)
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


if __name__ == "__main__":
    suite = unittest.makeSuite(LinzValidationResultsDockWidgetTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
