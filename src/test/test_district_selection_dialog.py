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


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
