# coding=utf-8
"""District Selection Dialog Test.

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
from qgis.core import QgsSettings
from core.district_registry import DistrictRegistry
from gui.district_selection_dialog import DistrictSelectionDialog
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class DistrictSelectionDialogTest(unittest.TestCase):
    """Test ElectorateSelectionDialog."""

    def testConstruct(self):
        """
        Test creating dialog
        """
        registry = DistrictRegistry()
        self.assertIsNotNone(DistrictSelectionDialog(registry))

    def testPopulation(self):
        """
        Test that dialog is correctly populated from registry
        """
        registry = DistrictRegistry(districts=['d1', 'd2', 'd5', 'd3',
                                               'd4', 'd9', 'd7'])
        registry.clear_recent_districts()
        registry.push_recent_district('d3')
        registry.push_recent_district('d9')
        registry.push_recent_district('d7')
        dlg = DistrictSelectionDialog(registry)
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['d1', 'd2', 'd5', 'd3',
                          'd4', 'd9', 'd7'])
        self.assertEqual([dlg.recent_list.item(r).text()
                          for r in range(dlg.recent_list.count())],
                         ['d7', 'd9', 'd3'])


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
