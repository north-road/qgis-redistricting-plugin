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
                       NULL)


class LinzDistrictRegistryTest(unittest.TestCase):
    """Test LinzElectoralDistrictRegistry."""

    def testLinzDistrictRegistry(self):
        """
        Test a LinzDistrictRegistry
        """
        layer = QgsVectorLayer(
            "Point?field=fld1:string&field=fld2:string",
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

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            source_field='fld1')
        self.assertEqual(reg.district_list(),
                         ['test1', 'test2', 'test3', 'test4'])
        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            source_field='fld2')
        self.assertEqual(reg.district_list(),
                         ['xtest1', 'xtest2', 'xtest3'])


if __name__ == "__main__":
    suite = unittest.makeSuite(LinzElectoralDistrictRegistry)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
