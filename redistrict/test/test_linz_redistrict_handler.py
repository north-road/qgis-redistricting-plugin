# coding=utf-8
"""LINZ Redistricting Handler test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, LINZ'
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


def make_user_log_layer() -> QgsVectorLayer:
    """
    Makes a dummy user log layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=log_id:int&field=timestamp:datetime&field=username:string&field=meshblock_version:string&field=scenario_id:int&field=meshblock_number:string&field=type:string&field=from_electorate_id:int&field=to_electorate_id:int",
        "source", "memory")
    assert layer.isValid()

    return layer


class LINZRedistrictHandlerTest(unittest.TestCase):
    """Test LinzRedistrictHandler."""

    def testBatched(self):  # pylint: disable=too-many-statements,too-many-locals
        """
        Test batched operations
        """
        meshblock_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=fld2:string&field=offline_pop_gn:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1", 10])
        f.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 0, 5, 5)))
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3", 15])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 5, 10, 10)))
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3", 22])
        f3.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 5, 5, 10)))
        f4 = QgsFeature()
        f4.setAttributes(["test1", NULL, 31])
        f4.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 0, 10, 5)))
        f5 = QgsFeature()
        f5.setAttributes(["test2", "xtest2", 51])
        f5.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 10, 10, 15)))
        success, [f, f2, f3, f4, f5] = meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5])
        self.assertTrue(success)

        district_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=estimated_pop:int&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=invalid:int&field=invalid_reason:string",
            "source", "memory")
        d = QgsFeature()
        d.setAttributes(["test1", NULL, 11111, 12, 13, 1, 'x'])
        d.setGeometry(f4.geometry())
        d2 = QgsFeature()
        d2.setAttributes(["test2", NULL, 11112, 22, 23, 0, 'y'])
        d2.setGeometry(QgsGeometry.unaryUnion([f2.geometry(), f5.geometry()]))
        d3 = QgsFeature()
        d3.setAttributes(["test3", NULL, 11113, 32, 33, 1, 'z'])
        d3.setGeometry(f3.geometry())
        d4 = QgsFeature()
        d4.setAttributes(["test4", NULL, 11114, 42, 43, 0, 'xx'])
        d4.setGeometry(f.geometry())
        d5 = QgsFeature()
        d5.setAttributes(["aaa", NULL, 11115, 52, 53, 1, 'yy'])
        success, [d, d2, d3, d4, d5] = district_layer.dataProvider().addFeatures([d, d2, d3, d4, d5])
        self.assertTrue(success)

        user_log_layer = make_user_log_layer()

        handler = LinzRedistrictHandler(meshblock_layer=meshblock_layer, meshblock_number_field_name='fld1',
                                        target_field='fld1',
                                        electorate_layer=district_layer, electorate_layer_field='fld1', task='GN',
                                        user_log_layer=user_log_layer, scenario=1)
        self.assertTrue(meshblock_layer.startEditing())
        handler.begin_edit_group('test')
        self.assertTrue(handler.assign_district([f.id(), f3.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f5.id()], 'aaa'))

        # pending changes should be recorded
        self.assertEqual(handler.pending_affected_districts, {'aaa': {'ADD': [f.id(), f3.id(), f5.id()], 'REMOVE': []},
                                                              'test2': {'ADD': [], 'REMOVE': [f5.id()]},
                                                              'test3': {'ADD': [], 'REMOVE': [f3.id()]},
                                                              'test4': {'ADD': [], 'REMOVE': [f.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN ('aaa','test2','test3','test4')")

        self.assertEqual([f.attributes() for f in user_log_layer.getFeatures()], [])

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

        self.assertEqual([f.attributes()[4:] for f in user_log_layer.getFeatures()],
                         [[1, 'test4', 'GN', 'test4', 'aaa'],
                          [1, 'test3', 'GN', 'test3', 'aaa'],
                          [1, 'test2', 'GN', 'test2', 'aaa']])

        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        self.assertEqual([f['estimated_pop'] for f in district_layer.getFeatures()], [NULL, 15.0, 0.0, 0.0, 83.0])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, 0 15, 10 15, 10 10, 5 10, 5 5))')
        self.assertEqual([f.attributes()[-5:] for f in district_layer.getFeatures()], [[11111, 12, 13, 1, 'x'],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL]])

        handler.begin_edit_group('test2')
        self.assertTrue(handler.assign_district([f2.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f4.id()], 'aaa'))
        self.assertEqual(handler.pending_affected_districts, {'aaa': {'ADD': [f2.id(), f4.id()], 'REMOVE': []},
                                                              'test2': {'ADD': [], 'REMOVE': [f2.id()]},
                                                              'test1': {'ADD': [], 'REMOVE': [f4.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN ('aaa','test1','test2')")
        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts()], ['test2', 'aaa', 'test1'])
        self.assertCountEqual([f.id() for f in handler.get_added_meshblocks('aaa')], [2, 4])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test2')], [2])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks('test1')], [4])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks('aaa')])

        handler.discard_edit_group()
        self.assertFalse(handler.pending_affected_districts)
        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        self.assertEqual([f['estimated_pop'] for f in district_layer.getFeatures()], [NULL, 15.0, 0.0, 0.0, 83.0])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, 0 15, 10 15, 10 10, 5 10, 5 5))')
        self.assertEqual([f.attributes()[-5:] for f in district_layer.getFeatures()], [[11111, 12, 13, 1, 'x'],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL],
                                                                                       [NULL, NULL, NULL, NULL, NULL]])

        self.assertEqual([f.attributes()[4:] for f in user_log_layer.getFeatures()],
                         [[1, 'test4', 'GN', 'test4', 'aaa'],
                          [1, 'test3', 'GN', 'test3', 'aaa'],
                          [1, 'test2', 'GN', 'test2', 'aaa']])

    def testBatchedIntField(self):  # pylint: disable=too-many-statements,too-many-locals
        """
        Test batched operations when district is using an integer field key
        """
        meshblock_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:int&field=offline_pop_gn:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes([4, 1])
        f.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 0, 5, 5)))
        f2 = QgsFeature()
        f2.setAttributes([2, 11])
        f2.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 5, 10, 10)))
        f3 = QgsFeature()
        f3.setAttributes([3, 21])
        f3.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 5, 5, 10)))
        f4 = QgsFeature()
        f4.setAttributes([1, 31])
        f4.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 0, 10, 5)))
        f5 = QgsFeature()
        f5.setAttributes([2, 41])
        f5.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 10, 10, 15)))
        f6 = QgsFeature()
        f6.setAttributes([NULL, 51])
        f6.setGeometry(QgsGeometry.fromRect(QgsRectangle(-5, 10, 0, 15)))
        success, [f, f2, f3, f4, f5, f6] = meshblock_layer.dataProvider().addFeatures([f, f2, f3, f4, f5, f6])
        self.assertTrue(success)

        district_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:int&field=estimated_pop:int&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=invalid:int&field=invalid_reason:string",
            "source", "memory")
        d = QgsFeature()
        d.setAttributes([1])
        d.setGeometry(f4.geometry())
        d2 = QgsFeature()
        d2.setAttributes([2])
        d2.setGeometry(QgsGeometry.unaryUnion([f2.geometry(), f5.geometry()]))
        d3 = QgsFeature()
        d3.setAttributes([3])
        d3.setGeometry(f3.geometry())
        d4 = QgsFeature()
        d4.setAttributes([4])
        d4.setGeometry(f.geometry())
        d5 = QgsFeature()
        d5.setAttributes([5])
        success, [d, d2, d3, d4, d5] = district_layer.dataProvider().addFeatures([d, d2, d3, d4, d5])
        self.assertTrue(success)

        user_log_layer = make_user_log_layer()

        handler = LinzRedistrictHandler(meshblock_layer=meshblock_layer, meshblock_number_field_name='fld1',
                                        target_field='fld1',
                                        electorate_layer=district_layer, electorate_layer_field='fld1', task='GN',
                                        user_log_layer=user_log_layer, scenario=1)
        self.assertTrue(meshblock_layer.startEditing())
        handler.begin_edit_group('test')
        self.assertTrue(handler.assign_district([f.id(), f3.id(), f6.id()], 5))
        self.assertTrue(handler.assign_district([f5.id()], 5))

        # pending changes should be recorded
        self.assertEqual(handler.pending_affected_districts,
                         {5: {'ADD': [f.id(), f3.id(), f6.id(), f5.id()], 'REMOVE': []},
                          2: {'ADD': [], 'REMOVE': [f5.id()]},
                          3: {'ADD': [], 'REMOVE': [f3.id()]},
                          4: {'ADD': [], 'REMOVE': [f.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN (2,3,4,5)")

        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts()], [4, 3, 5, 2])
        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts(['fld1'])],
                              [4, 3, 5, 2])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks(2)])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks(3)])
        self.assertCountEqual([f.id() for f in handler.get_added_meshblocks(5)], [1, 3, 6, 5])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks(2)], [5])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks(3)], [3])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks(5)])

        handler.end_edit_group()
        self.assertFalse(handler.pending_affected_districts)
        self.assertEqual(handler.create_affected_district_filter(), '')
        self.assertFalse([f for f in handler.get_affected_districts()])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks(3)])
        self.assertFalse([f["fld1"] for f in handler.get_added_meshblocks(5)])
        self.assertFalse([f.id() for f in handler.get_removed_meshblocks(2)])
        self.assertFalse([f.id() for f in handler.get_removed_meshblocks(3)])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks(5)])

        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], [5, 2, 5, 1, 5, 5])
        self.assertEqual([f['estimated_pop'] for f in district_layer.getFeatures()], [NULL, 11.0, 0.0, 0.0, 114.0])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, -5 10, -5 15, 0 15, 10 15, 10 10, 5 10, 5 5))')

        self.assertEqual([f.attributes()[4:] for f in user_log_layer.getFeatures()],
                         [[1, 4, 'GN', 4, 5],
                          [1, 3, 'GN', 3, 5],
                          [1, 2, 'GN', 2, 5]])

        handler.begin_edit_group('test2')
        self.assertTrue(handler.assign_district([f2.id()], 5))
        self.assertTrue(handler.assign_district([f4.id()], 5))
        self.assertEqual(handler.pending_affected_districts, {5: {'ADD': [f2.id(), f4.id()], 'REMOVE': []},
                                                              2: {'ADD': [], 'REMOVE': [f2.id()]},
                                                              1: {'ADD': [], 'REMOVE': [f4.id()]}})
        self.assertEqual(handler.create_affected_district_filter(), "fld1 IN (1,2,5)")
        self.assertCountEqual([f["fld1"] for f in handler.get_affected_districts()], [2, 5, 1])
        self.assertCountEqual([f.id() for f in handler.get_added_meshblocks(5)], [2, 4])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks(2)], [2])
        self.assertCountEqual([f.id() for f in handler.get_removed_meshblocks(1)], [4])
        self.assertFalse([f["fld1"] for f in handler.get_removed_meshblocks(5)])

        handler.discard_edit_group()
        self.assertFalse(handler.pending_affected_districts)
        self.assertEqual([f['fld1'] for f in meshblock_layer.getFeatures()], [5, 2, 5, 1, 5, 5])
        self.assertEqual([f['estimated_pop'] for f in district_layer.getFeatures()], [NULL, 11.0, 0.0, 0.0, 114.0])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(), 'Polygon ((5 0, 10 0, 10 5, 5 5, 5 0))')
        self.assertEqual(district_layer.getFeature(d2.id()).geometry().asWkt(),
                         'Polygon ((10 10, 10 5, 5 5, 5 10, 10 10))')
        self.assertEqual(district_layer.getFeature(d3.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d4.id()).geometry().asWkt(), 'GeometryCollection ()')
        self.assertEqual(district_layer.getFeature(d5.id()).geometry().asWkt(),
                         'Polygon ((5 5, 5 0, 0 0, 0 5, 0 10, -5 10, -5 15, 0 15, 10 15, 10 10, 5 10, 5 5))')

        self.assertEqual([f.attributes()[4:] for f in user_log_layer.getFeatures()],
                         [[1, 4, 'GN', 4, 5],
                          [1, 3, 'GN', 3, 5],
                          [1, 2, 'GN', 2, 5]])


if __name__ == "__main__":
    suite = unittest.makeSuite(LINZRedistrictHandlerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
