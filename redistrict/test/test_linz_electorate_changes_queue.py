# coding=utf-8
"""LINZ Electorate Changes Queue test.

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
from redistrict.linz.electorate_changes_queue import (
    ElectorateEditQueue
)
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsRectangle,
                       NULL)


class LINZElectorateQueueTest(unittest.TestCase):
    """Test ElectorateEditQueue."""

    def testQueue(self):
        """
        Test queue operations
        """
        district_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=estimated_pop:int&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=invalid:int&field=invalid_reason:string",
            "source", "memory")
        d = QgsFeature()
        d.setAttributes(["test1", NULL, 11111, 12, 13, 1, 'x'])
        d.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 0, 10, 5)))
        d2 = QgsFeature()
        d2.setAttributes(["test2", NULL, 11112, 22, 23, 0, 'y'])
        d2.setGeometry(QgsGeometry.unaryUnion(
            [QgsGeometry.fromRect(QgsRectangle(5, 5, 10, 10)), QgsGeometry.fromRect(QgsRectangle(0, 10, 10, 15))]))
        d3 = QgsFeature()
        d3.setAttributes(["test3", NULL, 11113, 32, 33, 1, 'z'])
        d3.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 5, 5, 10)))
        d4 = QgsFeature()
        d4.setAttributes(["test4", NULL, 11114, 42, 43, 0, 'xx'])
        d4.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 0, 5, 5)))
        d5 = QgsFeature()
        d5.setAttributes(["aaa", NULL, 11115, 52, 53, 1, 'yy'])
        success, [d, d2, d3, d4, d5] = district_layer.dataProvider().addFeatures([d, d2, d3, d4, d5])
        self.assertTrue(success)

        queue = ElectorateEditQueue(electorate_layer=district_layer)

        queue.push({d.id(): {0: 'xtest1', 2: 21111}}, {d.id(): QgsGeometry.fromRect(QgsRectangle(115, 0, 110, 5))})
        self.assertEqual(district_layer.getFeature(d.id()).attributes(), ['xtest1', NULL, 21111, 12, 13, 1, 'x'])
        self.assertEqual(district_layer.getFeature(d.id()).geometry().asWkt(),
                         'Polygon ((110 0, 115 0, 115 5, 110 5, 110 0))')


if __name__ == "__main__":
    suite = unittest.makeSuite(LINZElectorateQueueTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
