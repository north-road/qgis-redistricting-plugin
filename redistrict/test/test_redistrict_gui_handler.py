# coding=utf-8
"""LINZ Redistrict GUI Handler Test.

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
from redistrict.gui.redistrict_gui_handler import RedistrictGuiHandler
from redistrict.gui.redistricting_dock_widget import RedistrictingDockWidget
from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class RedistrictingGuiHandlerTest(unittest.TestCase):
    """Test RedistrictGuiHandler."""

    def testConstruct(self):
        """
        Test constructing handler
        """
        dock = RedistrictingDockWidget(IFACE)
        handler = RedistrictGuiHandler(redistrict_dock=dock)
        self.assertEqual(handler.redistrict_dock(), dock)


if __name__ == "__main__":
    suite = unittest.makeSuite(RedistrictingGuiHandlerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
