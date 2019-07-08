# coding=utf-8
"""Create Electorate Dialog Test.

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
from qgis.PyQt.QtWidgets import QDialogButtonBox
from qgis.core import (QgsVectorLayer,
                       QgsFeature)
from redistrict.linz.create_electorate_dialog import CreateElectorateDialog
from redistrict.test.test_linz_redistrict_context import make_scenario_layer
from redistrict.test.test_linz_district_registry import make_quota_layer
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class CreateElectorateDialogTest(unittest.TestCase):
    """Test CreateElectorateDialog."""

    def testDialog(self):
        """
        Test dialog functionality
        """
        scenario_layer = make_scenario_layer()
        scenario_registry = ScenarioRegistry(source_layer=scenario_layer, id_field='id', name_field='name',
                                             meshblock_electorate_layer=None)

        layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=fld1:string&field=code:string&field=type:string&field=estimated_pop:int&field=deprecated:int&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=scenario_id:int&field=electorate_id_stats:string",
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

        context = LinzRedistrictingContext(scenario_registry=scenario_registry)
        dlg = CreateElectorateDialog(registry=reg, context=context)
        self.assertIsNotNone(dlg)

        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())

        dlg.name_line_edit.setText('new district')
        dlg.code_line_edit.setText('new code')
        self.assertEqual(dlg.name(), 'new district')
        self.assertEqual(dlg.code(), 'new code')

        # dupe name
        dlg.name_line_edit.setText('test4')
        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertIn('already exists', dlg.feedback_label.text())
        dlg.name_line_edit.setText('test99')
        self.assertTrue(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertFalse(dlg.feedback_label.text())
        dlg.name_line_edit.setText('')
        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertIn('must be entered', dlg.feedback_label.text())
        dlg.name_line_edit.setText('test99')
        self.assertTrue(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertFalse(dlg.feedback_label.text())

        # dupe code
        dlg.code_line_edit.setText('xtest1')
        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertIn('already exists', dlg.feedback_label.text())
        dlg.code_line_edit.setText('test99')
        self.assertTrue(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        self.assertFalse(dlg.feedback_label.text())
        dlg.code_line_edit.setText('')
        self.assertIn('must be entered', dlg.feedback_label.text())
        self.assertFalse(dlg.button_box.button(QDialogButtonBox.Ok).isEnabled())
        dlg.code_line_edit.setText('test99')
        self.assertFalse(dlg.feedback_label.text())


if __name__ == "__main__":
    suite = unittest.makeSuite(CreateElectorateDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
