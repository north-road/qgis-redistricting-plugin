# coding=utf-8
"""LINZ District Registry Test.

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
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsRectangle,
                       QgsCoordinateReferenceSystem,
                       NULL)


def make_quota_layer() -> QgsVectorLayer:
    """
    Makes a dummy quota layer for testing
    """
    layer = QgsVectorLayer(
        "NoGeometry?field=type:string&field=quota:int",
        "source", "memory")
    f = QgsFeature()
    f.setAttributes(["GN", 59000])
    f2 = QgsFeature()
    f2.setAttributes(["GS", 60000])
    f3 = QgsFeature()
    f3.setAttributes(["M", 61000])
    layer.dataProvider().addFeatures([f, f2, f3])
    return layer


class LinzDistrictRegistryTest(unittest.TestCase):
    """Test LinzElectoralDistrictRegistry."""

    def testLinzDistrictRegistry(self):
        """
        Test a LinzDistrictRegistry
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string&field=type:string&field=estimated_pop:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1", 'GN', 1000])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3", 'GS', 2000])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3", 'M', 3000])
        f4 = QgsFeature()
        f4.setAttributes(["test1", NULL, 'GN', 4000])
        f5 = QgsFeature()
        f5.setAttributes(["test2", "xtest2", 'GS', 5000])
        layer.dataProvider().addFeatures([f, f2, f3, f4, f5])
        quota_layer = make_quota_layer()

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='',
            source_field='fld1',
            title_field='fld1')
        self.assertEqual(reg.district_list(),
                         ['test1', 'test2', 'test3', 'test4'])

        self.assertEqual(reg.get_district_type('test1'), 'GN')
        self.assertEqual(reg.get_district_type('test2'), 'GS')
        self.assertEqual(reg.get_district_type('test3'), 'M')
        self.assertEqual(reg.get_district_type('test4'), 'GN')

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='',
            source_field='fld2',
            title_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['xtest1', 'xtest2', 'xtest3'])

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='GN',
            source_field='fld1',
            title_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['test1', 'test4'])
        self.assertEqual(reg.district_titles(),
                         {NULL: 'test1', 'xtest1': 'test4'})
        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='GS',
            source_field='fld1',
            title_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['test2'])
        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='M',
            source_field='fld1',
            title_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['test3'])

    def testDistrictTypeString(self):
        """
        Test district_type_title
        """
        self.assertEqual(LinzElectoralDistrictRegistry.district_type_title('GN'), 'General North Island')
        self.assertEqual(LinzElectoralDistrictRegistry.district_type_title('GS'), 'General South Island')
        self.assertEqual(LinzElectoralDistrictRegistry.district_type_title('M'), 'Māori')
        try:
            LinzElectoralDistrictRegistry.district_type_title('X')
            assert 'Unexpected success - expecting assert'
        except:  # noqa, pylint: disable=bare-except
            pass

    def testQuotas(self):
        """
        Test retrieving quotas for districts
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string&field=type:string&field=estimated_pop:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1", 'GN'])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3", 'GS'])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3", 'M'])
        layer.dataProvider().addFeatures([f, f2, f3])
        quota_layer = make_quota_layer()

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='',
            source_field='fld1',
            title_field='fld1')

        self.assertEqual(reg.get_quota_for_district_type('GN'), 59000)
        self.assertEqual(reg.get_quota_for_district_type('GS'), 60000)
        self.assertEqual(reg.get_quota_for_district_type('M'), 61000)
        try:
            reg.get_quota_for_district_type('X')
            assert 'Unexpected success - expecting assert'
        except:  # noqa, pylint: disable=bare-except
            pass

        self.assertEqual(reg.get_quota_for_district('test4'), 59000)
        self.assertEqual(reg.get_quota_for_district('test2'), 60000)
        self.assertEqual(reg.get_quota_for_district('test3'), 61000)
        try:
            reg.get_quota_for_district('X')
            assert 'Unexpected success - expecting assert'
        except:  # noqa, pylint: disable=bare-except
            pass

    def testPopulations(self):
        """
        Test retrieving populations for districts
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=fld2:string&field=type:string&field=estimated_pop:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1", 'GN', 1000])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3", 'GS', 2000])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3", 'M', 3000])
        layer.dataProvider().addFeatures([f, f2, f3])
        quota_layer = make_quota_layer()

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='',
            source_field='fld1',
            title_field='fld1')

        self.assertEqual(reg.get_estimated_population('test4'), 1000)
        self.assertEqual(reg.get_estimated_population('test2'), 2000)
        self.assertEqual(reg.get_estimated_population('test3'), 3000)
        try:
            reg.get_estimated_population('X')
            assert 'Unexpected success - expecting assert'
        except:  # noqa, pylint: disable=bare-except
            pass

    def testVariationFromQuota(self):
        """
        Test calculating variation from quota
        """
        self.assertEqual(LinzElectoralDistrictRegistry.get_variation_from_quota_percent(quota=50000, population=51000),
                         2)
        self.assertEqual(LinzElectoralDistrictRegistry.get_variation_from_quota_percent(quota=50000, population=55000),
                         10)
        self.assertEqual(LinzElectoralDistrictRegistry.get_variation_from_quota_percent(quota=50000, population=49000),
                         -2)
        self.assertEqual(LinzElectoralDistrictRegistry.get_variation_from_quota_percent(quota=50000, population=45000),
                         -10)

    def testVariationExceedsTolerance(self):
        """
        Test determining if an electorate's variation exceeds the tolerance
        """
        self.assertFalse(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=50000, population=51000))
        self.assertFalse(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=50000, population=49000))
        self.assertTrue(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=100000, population=105000))
        self.assertTrue(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=100000, population=95000))
        self.assertTrue(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=50000, population=56000))
        self.assertTrue(LinzElectoralDistrictRegistry.variation_exceeds_allowance(quota=50000, population=44000))

    def testVectorDistrictAtPoint(self):
        """
        Test getting vector layer district at point
        """
        layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=type:string&field=estimated_pop:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["GN district", "GN"])
        f.setGeometry(QgsGeometry.fromWkt('Polygon((1 10, 10 10, 10 20, 1 20, 1 10))'))
        f2 = QgsFeature()
        f2.setAttributes(["M district", "M"])
        f2.setGeometry(QgsGeometry.fromWkt('Polygon((1 10, 10 10, 10 20, 1 20, 1 10))'))
        layer.dataProvider().addFeatures([f, f2])

        quota_layer = make_quota_layer()
        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='GN',
            source_field='fld1',
            title_field='fld1')

        self.assertEqual(
            reg.get_district_at_point(QgsRectangle(5, 15, 5.2, 16.2), QgsCoordinateReferenceSystem('EPSG:4326')),
            'GN district')
        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='M',
            source_field='fld1',
            title_field='fld1')
        self.assertEqual(
            reg.get_district_at_point(QgsRectangle(5, 15, 5.2, 16.2), QgsCoordinateReferenceSystem('EPSG:4326')),
            'M district')


if __name__ == "__main__":
    suite = unittest.makeSuite(LinzElectoralDistrictRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
