# coding=utf-8
"""Deprecate Electorate Dialog Test.

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
from qgis.core import (QgsVectorLayer,
                       QgsFeature)
from redistrict.linz.deprecate_electorate_dialog import DeprecateElectorateDialog
from redistrict.test.test_linz_district_registry import make_quota_layer
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class DeprecateElectorateDialogTest(unittest.TestCase):
    """Test DeprecateElectorateDialog."""

    def testDialog(self):
        """
        Test dialog functionality
        """
        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=code:string&field=type:string&field=estimated_pop:int&field=deprecated:int",
            "source", "memory")
        f = QgsFeature()
        f.setAttributes(["test4", "xtest1", 'GN', 1, False])
        f2 = QgsFeature()
        f2.setAttributes(["test2", "xtest3", 'GN', 2, True])
        f3 = QgsFeature()
        f3.setAttributes(["test3", "xtest3", 'GN', 1, False])
        layer.dataProvider().addFeatures([f, f2, f3])
        quota_layer = make_quota_layer()

        reg = LinzElectoralDistrictRegistry(
            source_layer=layer,
            quota_layer=quota_layer,
            electorate_type='',
            source_field='fld1',
            title_field='fld1')

        dlg = DeprecateElectorateDialog(electorate_registry=reg)
        self.assertIsNotNone(dlg)

        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['test4', '*test2', 'test3'])


if __name__ == "__main__":
    suite = unittest.makeSuite(DeprecateElectorateDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
