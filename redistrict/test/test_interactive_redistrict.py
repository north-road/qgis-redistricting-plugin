# coding=utf-8
"""LINZ Interactive Redistricting Tool test.

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
from qgis.PyQt.QtCore import (QEvent,
                              QPoint,
                              Qt)
from qgis.core import (QgsVectorLayer,
                       QgsCoordinateReferenceSystem,
                       QgsRectangle,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsPointLocator)
from qgis.gui import (QgsMapCanvas,
                      QgsMapMouseEvent,
                      QgsVertexMarker)
from redistrict.core.district_registry import DistrictRegistry
from redistrict.core.redistrict_handler import RedistrictHandler
from redistrict.gui.interactive_redistrict_tool import InteractiveRedistrictingTool, DecoratorFactory


class TestDecoratorFactory(DecoratorFactory):
    """
    Test decorator factory
    """

    def create_decorator(self, canvas):
        return QgsVertexMarker(canvas)


class InteractiveRedistrictTest(unittest.TestCase):
    """Test InteractiveRedistrictingTool."""

    def testDistrictBoundaryMatches(self):
        """
        Test retrieving district boundary matches
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
        f2.setAttributes(['a'])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(15, 25, 18, 45)))
        f3 = QgsFeature()
        f3.setAttributes(['b'])
        f3.setGeometry(QgsGeometry.fromWkt('Polygon((18 30.01 19 35, 20 30, 19 25, 18 29.99, 20 30, 18 30.01))'))
        success, (f, f2, f3) = layer.dataProvider().addFeatures([f, f2, f3])
        self.assertTrue(success)

        canvas.setLayers([layer])
        canvas.setExtent(QgsRectangle(10, 30, 20, 35))
        canvas.show()

        handler = RedistrictHandler(layer, 'fldtxt')
        registry = DistrictRegistry(districts=['a', 'b'])
        tool = InteractiveRedistrictingTool(canvas, handler, district_registry=registry)
        # point inside a feature
        self.assertFalse(tool.get_district_boundary_matches(QgsPointXY(10, 30)))
        self.assertFalse([f for f in tool.get_target_features_from_matches([])])
        self.assertFalse(tool.get_districts_from_matches([]))
        self.assertFalse(tool.matches_are_valid_for_boundary([]))

        # point directly on boundary
        matches = tool.get_district_boundary_matches(QgsPointXY(15, 30))
        self.assertTrue(matches)
        self.assertCountEqual([match.featureId() for match in matches], [f.id(), f2.id()])
        self.assertCountEqual([f.id() for f in tool.get_target_features_from_matches(matches)], [f.id(), f2.id()])
        self.assertCountEqual(tool.get_districts_from_matches(matches), ['a'])
        # not a valid boundary match - both features have same district!
        self.assertFalse(tool.matches_are_valid_for_boundary(matches))

        # point just offset from boundary
        matches = tool.get_district_boundary_matches(QgsPointXY(15.1, 30))
        self.assertTrue(matches)
        self.assertCountEqual([match.featureId() for match in matches], [f.id(), f2.id()])
        self.assertCountEqual([f.id() for f in tool.get_target_features_from_matches(matches)], [f.id(), f2.id()])
        self.assertCountEqual(tool.get_districts_from_matches(matches), ['a'])
        self.assertFalse(tool.matches_are_valid_for_boundary(matches))

        # unique matches only
        matches = tool.get_district_boundary_matches(QgsPointXY(18, 30))
        self.assertTrue(matches)
        self.assertCountEqual([match.featureId() for match in matches], [f2.id(), f3.id()])
        self.assertCountEqual([f.id() for f in tool.get_target_features_from_matches(matches)], [f2.id(), f3.id()])
        self.assertCountEqual(tool.get_districts_from_matches(matches), ['a', 'b'])
        # valid boundary match - both features have different districts
        self.assertTrue(tool.matches_are_valid_for_boundary(matches))

    def testDistrictAreaMatches(self):
        """
        Test retrieving district area matches
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
        success, (f, f2) = layer.dataProvider().addFeatures([f, f2])
        self.assertTrue(success)

        canvas.setLayers([layer])
        canvas.setExtent(QgsRectangle(10, 30, 20, 35))
        canvas.show()

        handler = RedistrictHandler(layer, 'fldtxt')
        registry = DistrictRegistry(districts=['a', 'b'])
        tool = InteractiveRedistrictingTool(canvas, handler, district_registry=registry)
        # point outside a feature
        match = tool.get_district_area_match(QgsPointXY(20, 30))
        self.assertFalse(match.isValid())

        # point inside features
        match = tool.get_district_area_match(QgsPointXY(10, 30))
        self.assertTrue(match.isValid())
        self.assertEqual(match.featureId(), f.id())
        self.assertEqual([f.id() for f in tool.get_target_features_from_matches([match])], [f.id()])
        self.assertCountEqual(tool.get_districts_from_matches([match]), ['a'])
        self.assertFalse(tool.matches_are_valid_for_boundary([match]))

        match = tool.get_district_area_match(QgsPointXY(16, 30))
        self.assertTrue(match.isValid())
        self.assertEqual(match.featureId(), f2.id())
        self.assertEqual([f.id() for f in tool.get_target_features_from_matches([match])], [f2.id()])
        self.assertCountEqual(tool.get_districts_from_matches([match]), ['b'])
        self.assertFalse(tool.matches_are_valid_for_boundary([match]))

    def testInteraction(self):  # pylint: disable=too-many-statements
        """
        Test tool interaction
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
        f.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 32, 15, 45)))
        f2 = QgsFeature()
        f2.setAttributes(['b'])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(15, 25, 18, 45)))
        success, (f, f2) = layer.dataProvider().addFeatures([f, f2])
        self.assertTrue(success)

        canvas.setLayers([layer])
        canvas.setExtent(QgsRectangle(10, 30, 20, 35))
        canvas.show()

        handler = RedistrictHandler(layer, 'fldtxt')
        factory = DecoratorFactory()
        registry = DistrictRegistry(districts=['a', 'b'])
        tool = InteractiveRedistrictingTool(canvas, handler, district_registry=registry, decorator_factory=factory)

        # mouse over a feature's interior
        point = canvas.mapSettings().mapToPixel().transform(20, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertFalse(tool.is_active)
        self.assertFalse(tool.snap_indicator.match().isValid())
        # mouse over a single feature's boundary (not valid district boundary)
        point = canvas.mapSettings().mapToPixel().transform(5, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertFalse(tool.is_active)
        self.assertFalse(tool.snap_indicator.match().isValid())
        # mouse over a two feature's boundary (valid district boundary)
        point = canvas.mapSettings().mapToPixel().transform(15, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertFalse(tool.is_active)
        self.assertTrue(tool.snap_indicator.match().isValid())

        # avoid segfault
        tool.snap_indicator.setMatch(QgsPointLocator.Match())

        # clicks to ignore
        point = canvas.mapSettings().mapToPixel().transform(10, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.MidButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.RightButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)

        # click over bad area
        point = canvas.mapSettings().mapToPixel().transform(10, 30)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)

        # click over feature area
        layer.startEditing()
        point = canvas.mapSettings().mapToPixel().transform(10, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.click_point.x(), 10)
        self.assertEqual(tool.click_point.y(), 33)
        self.assertEqual(tool.districts, {'a'})
        self.assertFalse(tool.modified)

        # now move over current feature - should do nothing!
        point = canvas.mapSettings().mapToPixel().transform(10, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertFalse(tool.modified)

        # move over other feature
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')
        point = canvas.mapSettings().mapToPixel().transform(16, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.modified, {f2.id()})
        self.assertEqual(tool.current_district, 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'a')

        # move over nothing
        point = canvas.mapSettings().mapToPixel().transform(26, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.modified, {f2.id()})

        # left click - commit changes
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)

        layer.rollBack()
        layer.startEditing()

        # add a decorator
        tool.decorator_factory = TestDecoratorFactory()

        # now try with clicks over boundary
        point = canvas.mapSettings().mapToPixel().transform(15, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.click_point.x(), 15)
        self.assertEqual(tool.click_point.y(), 33)
        self.assertEqual(tool.districts, {'a', 'b'})
        self.assertFalse(tool.modified)

        # move left
        self.assertEqual(layer.getFeature(f.id())[0], 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')
        point = canvas.mapSettings().mapToPixel().transform(10, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.modified, {f.id()})
        self.assertEqual(tool.current_district, 'b')
        self.assertEqual(layer.getFeature(f.id())[0], 'b')
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')

        # move over nothing
        point = canvas.mapSettings().mapToPixel().transform(26, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.modified, {f.id()})

        # right click - discard changes
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.RightButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)
        self.assertEqual(layer.getFeature(f.id())[0], 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')

        # try again, move right
        point = canvas.mapSettings().mapToPixel().transform(15, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.LeftButton)
        tool.canvasPressEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.click_point.x(), 15)
        self.assertEqual(tool.click_point.y(), 33)
        self.assertEqual(tool.districts, {'a', 'b'})
        self.assertFalse(tool.modified)
        # move right
        self.assertEqual(layer.getFeature(f.id())[0], 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')
        point = canvas.mapSettings().mapToPixel().transform(17, 33)
        event = QgsMapMouseEvent(canvas, QEvent.MouseMove, QPoint(point.x(), point.y()))
        tool.canvasMoveEvent(event)
        self.assertTrue(tool.is_active)
        self.assertEqual(tool.modified, {f2.id()})
        self.assertEqual(tool.current_district, 'a')
        self.assertEqual(layer.getFeature(f.id())[0], 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'a')
        event = QgsMapMouseEvent(canvas, QEvent.MouseButtonPress, QPoint(point.x(), point.y()), Qt.RightButton)
        tool.canvasPressEvent(event)
        self.assertFalse(tool.is_active)
        self.assertEqual(layer.getFeature(f.id())[0], 'a')
        self.assertEqual(layer.getFeature(f2.id())[0], 'b')

        layer.rollBack()


if __name__ == "__main__":
    suite = unittest.makeSuite(InteractiveRedistrictTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
