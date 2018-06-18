# coding=utf-8
"""Redistricting Handler test.

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
from redistrict.core.redistrict_handler import (
    RedistrictHandler
)
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       NULL)


class RedistrictHandlerTest(unittest.TestCase):
    """Test RedistrictHandler."""

    def testRedistrictHandler(self):
        """
        Test a base redistrict handler
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1"])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3"])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3"])
        f4 = QgsFeature()
        f4.setAttributes(["test1", NULL])
        f5 = QgsFeature()
        f5.setAttributes(["test2", "xtest2"])
        success, [f, f2, f3, f4, f5] = layer.dataProvider().addFeatures([f, f2, f3, f4, f5])
        self.assertTrue(success)

        handler = RedistrictHandler(target_layer=layer, target_field='fld1')

        self.assertFalse(handler.assign_district([], 'aaa'))
        self.assertTrue(layer.startEditing())
        self.assertTrue(handler.assign_district([], 'aaa'))
        self.assertEqual([f['fld1'] for f in layer.getFeatures()], ['test4', 'test2', 'test3', 'test1', 'test2'])
        self.assertTrue(handler.assign_district([f.id(), f5.id(), f3.id()], 'aaa'))
        self.assertEqual([f['fld1'] for f in layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        self.assertTrue(handler.assign_district([f2.id()], 'bb'))
        self.assertEqual([f['fld1'] for f in layer.getFeatures()], ['aaa', 'bb', 'aaa', 'test1', 'aaa'])

        handler = RedistrictHandler(target_layer=layer, target_field='fld2')
        self.assertTrue(handler.assign_district([], 'aaa'))
        self.assertEqual([f['fld2'] for f in layer.getFeatures()], ['xtest1', 'xtest3', 'xtest3', NULL, 'xtest2'])
        self.assertTrue(handler.assign_district([f.id(), f5.id(), f3.id()], 'xxxx'))
        self.assertEqual([f['fld2'] for f in layer.getFeatures()], ['xxxx', 'xtest3', 'xxxx', NULL, 'xxxx'])
        self.assertTrue(handler.assign_district([f4.id(), f2.id()], 'yyyy'))
        self.assertEqual([f['fld2'] for f in layer.getFeatures()], ['xxxx', 'yyyy', 'xxxx', 'yyyy', 'xxxx'])

    def testBatched(self):
        """
        Test batched operations
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1"])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3"])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3"])
        f4 = QgsFeature()
        f4.setAttributes(["test1", NULL])
        f5 = QgsFeature()
        f5.setAttributes(["test2", "xtest2"])
        success, [f, f2, f3, f4, f5] = layer.dataProvider().addFeatures([f, f2, f3, f4, f5])
        self.assertTrue(success)

        handler = RedistrictHandler(target_layer=layer, target_field='fld1')
        self.assertTrue(layer.startEditing())
        handler.begin_edit_group('test')
        self.assertTrue(handler.assign_district([f.id(), f3.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f5.id()], 'aaa'))
        handler.end_edit_group()
        self.assertEqual(layer.undoStack().count(), 1)
        self.assertEqual([f['fld1'] for f in layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])
        handler.begin_edit_group('test2')
        self.assertTrue(handler.assign_district([f2.id()], 'aaa'))
        self.assertTrue(handler.assign_district([f4.id()], 'aaa'))
        handler.discard_edit_group()
        # self.assertEqual(layer.undoStack().count(), 1) # awaiting core change
        self.assertEqual([f['fld1'] for f in layer.getFeatures()], ['aaa', 'test2', 'aaa', 'test1', 'aaa'])


if __name__ == "__main__":
    suite = unittest.makeSuite(RedistrictHandlerTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
