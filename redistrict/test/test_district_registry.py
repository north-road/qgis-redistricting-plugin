# coding=utf-8
"""District Registry Test.

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
from redistrict.core.district_registry import (
    DistrictRegistry,
    VectorLayerDistrictRegistry
)
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       NULL)


class DistrictRegistryTest(unittest.TestCase):
    """Test DistrictRegistry."""

    def testConstruct(self):
        """
        Test creating registry
        """
        self.assertIsNotNone(DistrictRegistry())

    def testTypeStrings(self):
        """
        Test identifying type strings
        """
        registry = DistrictRegistry(type_string_title='Electorate',
                                    type_string_sentence='electorate',
                                    type_string_sentence_plural='electorates')
        self.assertEqual(registry.type_string_title(), 'Electorate')
        self.assertEqual(registry.type_string_sentence(), 'electorate')
        self.assertEqual(registry.type_string_sentence_plural(), 'electorates')

    def testDistricts(self):
        """
        Test retrieving districts
        """
        registry = DistrictRegistry(name='registry',
                                    districts=['district 1', 'district 9'])
        self.assertEqual(registry.district_list(), ['district 1',
                                                    'district 9'])

    def testRecentDistricts(self):
        """
        Test recent districts setting and retrieval
        """
        reg = DistrictRegistry(
            districts=['district 1', 'district 2', 'district 3',
                       'district 4', 'district 5', 'district 9'])
        reg.clear_recent_districts()
        self.assertEqual(reg.recent_districts_list(), [])
        reg.push_recent_district('district 3')
        self.assertEqual(reg.recent_districts_list(), ['district 3'])
        reg.push_recent_district('district 2')
        self.assertEqual(reg.recent_districts_list(), ['district 2',
                                                       'district 3'])
        reg.push_recent_district('district 5')
        self.assertEqual(reg.recent_districts_list(), ['district 5',
                                                       'district 2',
                                                       'district 3'])
        reg.push_recent_district('district 3')
        self.assertEqual(reg.recent_districts_list(), ['district 3',
                                                       'district 5',
                                                       'district 2'])
        reg.push_recent_district('district 4')
        self.assertEqual(reg.recent_districts_list(), ['district 4',
                                                       'district 3',
                                                       'district 5',
                                                       'district 2'])
        reg.push_recent_district('district 1')
        self.assertEqual(reg.recent_districts_list(),
                         ['district 1', 'district 4', 'district 3',
                          'district 5', 'district 2'])
        reg.push_recent_district('district 9')
        self.assertEqual(reg.recent_districts_list(),
                         ['district 9', 'district 1', 'district 4',
                          'district 3', 'district 5'])
        reg.clear_recent_districts()
        self.assertEqual(reg.recent_districts_list(), [])

    def testVectorLayerDistrictRegistry(self):
        """
        Test a VectorLayerDistrictRegistry
        """
        layer = QgsVectorLayer(
            "Point?field=fld1:string&crs=epsg:4326&field=fld2:string",
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
        layer.dataProvider().addFeatures([f, f2, f3, f4, f5])

        reg = VectorLayerDistrictRegistry(
            source_layer=layer,
            source_field='fld1')
        self.assertEqual(reg.district_list(),
                         ['test4', 'test2', 'test3', 'test1'])
        reg = VectorLayerDistrictRegistry(
            source_layer=layer,
            source_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['xtest1', 'xtest3', 'xtest2'])


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictRegistryTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
