# coding=utf-8
"""LINZ Redistrict GUI Handler Test.

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
from qgis.core import (QgsVectorLayer,
                       QgsFeature)
from redistrict.core.district_registry import (DistrictRegistry,
                                               VectorLayerDistrictRegistry)
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
        registry = DistrictRegistry(districts=['a', 'b'])
        handler = RedistrictGuiHandler(redistrict_dock=dock, district_registry=registry)
        self.assertEqual(handler.redistrict_dock(), dock)
        self.assertEqual(handler.district_registry(), registry)

    def testShowStats(self):
        """Test show stats for district"""
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1"])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest2"])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3"])
        layer.dataProvider().addFeatures([f, f2, f3])
        registry = VectorLayerDistrictRegistry(
            source_layer=layer,
            source_field='fld1',
            title_field='fld2')

        dock = RedistrictingDockWidget(IFACE)
        handler = RedistrictGuiHandler(redistrict_dock=dock, district_registry=registry)

        handler.show_stats_for_district('test4')
        self.assertEqual(dock.frame.toPlainText(), 'Statistics for xtest1')
        handler.show_stats_for_district('test3')
        self.assertEqual(dock.frame.toPlainText(), 'Statistics for xtest3')


if __name__ == "__main__":
    suite = unittest.makeSuite(RedistrictingGuiHandlerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
