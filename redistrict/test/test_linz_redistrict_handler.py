# coding=utf-8
"""LINZ Redistricting Handler test.

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
from redistrict.linz.linz_redistrict_handler import (
    LinzRedistrictHandler
)
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsRectangle,
                       NULL)


class LINZRedistrictHandlerTest(unittest.TestCase):
    """Test LinzRedistrictHandler."""

    def testBatched(self):  # pylint: disable=too-many-statements
        """
        Test batched operations
        """
        meshblock_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=fld2:string",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1"])
        f.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 0, 5, 5)))
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3"])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 5, 10, 10)))
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3"])
        f3.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 5, 5, 10)))
        f4 = QgsFeature()
        f4.setAttributes(["test1", NULL])
        f4.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 0, 10, 5)))
        f5 = QgsFeature()
        f5.setAttributes(["test2", "xtest2"])
        f5.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 10, 10, 15)))
        success, [f, f2, f3, f4, f5] = meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5])
        self.assertTrue(success)

        district_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string",
            "source", "memory")
        d = QgsFeature()
        d.setAttributes(["test1"])
        d.setGeometry(f4.geometry())
        d2 = QgsFeature()
        d2.setAttributes(["test2"])
        d2.setGeometry(QgsGeometry.unaryUnion([f2.geometry(), f5.geometry()]))
        d3 = QgsFeature()
        d3.setAttributes(["test3"])
        d3.setGeometry(f3.geometry())
        d4 = QgsFeature()
        d4.setAttributes(["test4"])
        d4.setGeometry(f.geometry())
        d5 = QgsFeature()
        d5.setAttributes(["aaa"])
        success, [d, d2, d3, d4, d5] = district_layer.dataProvider().addFeatures([d, d2, d3, d4, d5])
        self.assertTrue(success)

        handler = LinzRedistrictHandler(meshblock_layer=meshblock_layer, target_field='fld1',
                                        electorate_layer=district_layer, electorate_layer_field='fld1')
        self.assertTrue(meshblock_layer.startEditing())
        handler.begin_edit_group('test')
        self.assertTrue(handler.assign_district([f.id(), f3.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f5.id()], 'aaa'))

        # pending changes should be recorded
        self.assertEqual(handler.pending_affected_districts, {'aaa': {'ADD': [f.id(), f3.id(), f5.id()], 'REMOVE': []},
                                                              'test2': {'ADD': [], 'REMOVE': [f5.id()]},
                                                              'test3': {'ADD': [], 'REMOVE': [f3.id()]},
                                                              'test4': {'ADD': [], 'REMOVE': [f.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN ('test4','test3','aaa','test2')")

        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts()], ['test4', 'test3', 'aaa', 'test2'])
        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts(['fld1'])],
                              ['test4', 'test3', 'aaa', 'test2'])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks('test2')])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks('test3')])
        self.assertCountEqual([f.id() for f in handler.get_added_meshblocks('aaa')], [1, 3, 5])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test2')], [5])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test3')], [3])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks('aaa')])

        handler.end_edit_group()
        self.assertFalse(handler.pending_affected_districts)
        self.assertEqual(handler.create_affected_district_filter(), '')
        self.assertFalse([f for f in handler.get_affected_districts()])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks('test3')])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks('aaa')])
        self.assertFalse([f.id() for f in handler.get_removed_meshblocks('test2')])
        self.assertFalse([f.id() for f in handler.get_removed_meshblocks('test3')])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks('aaa')])

        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, 0 15, 10 15, 10 10, 5 10, 5 5))')

        handler.begin_edit_group('test2')
        self.assertTrue(handler.assign_district([f2.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f4.id()], 'aaa'))
        self.assertEqual(handler.pending_affected_districts, {'aaa': {'ADD': [f2.id(), f4.id()], 'REMOVE': []},
                                                              'test2': {'ADD': [], 'REMOVE': [f2.id()]},
                                                              'test1': {'ADD': [], 'REMOVE': [f4.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN ('test2','aaa','test1')")
        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts()], ['test2', 'aaa', 'test1'])
        self.assertCountEqual([f.id() for f in handler.get_added_meshblocks('aaa')], [2, 4])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test2')], [2])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test1')], [4])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks('aaa')])

        handler.discard_edit_group()
        self.assertFalse(handler.pending_affected_districts)
        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, 0 15, 10 15, 10 10, 5 10, 5 5))')


if __name__ == "__main__":
    suite = unittest.makeSuite(LINZRedistrictHandlerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
