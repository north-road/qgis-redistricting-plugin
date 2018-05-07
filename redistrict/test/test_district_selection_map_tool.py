# coding=utf-8
"""LINZ District Selection Map Tool test

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
from qgis.PyQt.QtCore import (QEvent,
                              QPoint,
                              Qt)
from qgis.core import (QgsVectorLayer,
                       QgsCoordinateReferenceSystem,
                       QgsRectangle,
                       QgsFeature,
                       QgsGeometry)
from qgis.gui import (QgsMapCanvas,
                      QgsMapMouseEvent)
from redistrict.core.district_registry import VectorLayerDistrictRegistry
from redistrict.gui.district_selection_map_tool import DistrictSelectionMapTool


class DistrictSelectionMapToolTest(unittest.TestCase):
    """Test DistrictSelectionMapTool."""

    def testDistrict(self):
        """
        Test retrieving district matches
        """
        canvas = QgsMapCanvas()
        canvas.setDestinationCrs(QgsCoordinateReferenceSystem(4326))
        canvas.setFrameStyle(0)
        canvas.resize(600, 400)

        self.assertEqual(canvas.width(), 600)
        self.assertEqual(canvas.height(), 400)

        layer = QgsVectorLayer("Polygon?crs=epsg:4326&field=fldtxt:string",
                               "layer", "memory")
        f = QgsFeature()
        f.setAttributes(['a'])
        f.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 25, 15, 45)))
        f2 = QgsFeature()
        f2.setAttributes(['b'])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(15, 25, 18, 45)))
        f3 = QgsFeature()
        f3.setAttributes(['c'])
        f3.setGeometry(QgsGeometry.fromWkt('Polygon((18 30.01 19 35, 20 30, 19 25, 18 29.99, 20 30, 18 30.01))'))
        success, (f, f2, f3) = layer.dataProvider().addFeatures([f, f2, f3])
        self.assertTrue(success)

        canvas.setLayers([layer])
        canvas.setExtent(QgsRectangle(10, 30, 20, 35))
        canvas.show()

        registry = VectorLayerDistrictRegistry(layer, source_field='fldtxt')
        tool = DistrictSelectionMapTool(canvas=canvas, district_registry=registry)

        # point inside a feature
        point = canvas.mapSettings().mapToPixel().transform(14, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertEqual(tool.get_clicked_district(), 'a')
        self.assertAlmostEqual(tool.search_rectangle().xMinimum(), 13.87, 2)
        self.assertAlmostEqual(tool.search_rectangle().xMaximum(), 14.13, 2)
        self.assertAlmostEqual(tool.search_rectangle().yMinimum(), 32.87, 2)
        self.assertAlmostEqual(tool.search_rectangle().yMaximum(), 33.13, 2)
        point = canvas.mapSettings().mapToPixel().transform(16, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertEqual(tool.get_clicked_district(), 'b')

        # outside features
        point = canvas.mapSettings().mapToPixel().transform(1, 1)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertIsNone(tool.get_clicked_district())


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictSelectionMapToolTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
