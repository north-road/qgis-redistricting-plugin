# coding=utf-8
"""District Selection Dialog Test.

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
from qgis.core import QgsVectorLayer
from redistrict.core.district_registry import DistrictRegistry, VectorLayerDistrictRegistry
from redistrict.gui.district_selection_dialog import DistrictSelectionDialog
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class DistrictSelectionDialogTest(unittest.TestCase):
    """Test ElectorateSelectionDialog."""

    def testConstruct(self):
        """
        Test creating dialog
        """
        registry = DistrictRegistry()
        self.assertIsNotNone(DistrictSelectionDialog(registry))

    def testPopulation(self):
        """
        Test that dialog is correctly populated from registry
        """
        registry = DistrictRegistry(districts=['d1', 'd2', 'd5', 'd3',
                                               'd4', 'd9', 'd7'],
                                    type_string_title='Electorate',
                                    type_string_sentence='electorate',
                                    type_string_sentence_plural='electorates')
        registry.clear_recent_districts()
        registry.push_recent_district('d3')
        registry.push_recent_district('d9')
        registry.push_recent_district('d7')
        dlg = DistrictSelectionDialog(registry)
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['d1', 'd2', 'd5', 'd3',
                          'd4', 'd9', 'd7'])
        self.assertEqual([dlg.recent_list.item(r).text()
                          for r in range(dlg.recent_list.count())],
                         ['d7', 'd9', 'd3'])

        # strings
        self.assertEqual(dlg.windowTitle(), 'Select New Electorate')
        self.assertEqual(dlg.recent_label.text(), 'Recently used electorates')
        self.assertEqual(dlg.available_label.text(), 'Available electorates')
        self.assertEqual(dlg.search.placeholderText(), 'Search for electorate')

        # initial selection must be recently used district
        self.assertEqual(dlg.selected_district(), 'd7')

    def testSelection(self):
        """
        Test setting/getting selected district
        """
        registry = DistrictRegistry(districts=['d1', 'd2', 'd5', 'd3',
                                               'd4', 'd9', 'd7'],
                                    type_string_title='Electorate',
                                    type_string_sentence='electorate',
                                    type_string_sentence_plural='electorates')
        registry.clear_recent_districts()
        registry.push_recent_district('d3')
        registry.push_recent_district('d9')
        registry.push_recent_district('d7')
        dlg = DistrictSelectionDialog(registry)

        dlg.set_selected_district('d2')
        self.assertEqual(dlg.selected_district(), 'd2')
        dlg.set_selected_district('d4')
        self.assertEqual(dlg.selected_district(), 'd4')

        # no recent item selected
        self.assertEqual(dlg.recent_list.selectedItems(), [])
        # select recent item
        dlg.recent_list.item(1).setSelected(True)
        self.assertEqual(dlg.selected_district(), 'd9')
        # should be nothing selected in other list
        self.assertEqual(dlg.list.selectedItems(), [])
        dlg.set_selected_district('d2')
        self.assertEqual(dlg.list.selectedItems()[0].text(), 'd2')
        self.assertEqual(dlg.recent_list.selectedItems(), [])

        # nothing at all selected
        dlg.list.clearSelection()
        dlg.recent_list.clearSelection()
        self.assertIsNone(dlg.selected_district())

    def testAccept(self):
        """
        Test that accepting dialog results in new recent district
        """
        registry = DistrictRegistry(districts=['d1', 'd2', 'd5', 'd3',
                                               'd4', 'd9', 'd7'],
                                    type_string_title='Electorate',
                                    type_string_sentence='electorate',
                                    type_string_sentence_plural='electorates')
        registry.clear_recent_districts()
        registry.push_recent_district('d3')
        registry.push_recent_district('d9')
        registry.push_recent_district('d7')
        dlg = DistrictSelectionDialog(registry)
        dlg.set_selected_district('d4')
        dlg.accept()
        self.assertEqual(registry.recent_districts_list(),
                         ['d4', 'd7', 'd9', 'd3'])

    def testFilter(self):
        """
        Test filtering inside the dialog
        """
        registry = DistrictRegistry(districts=['d1', 'd2', 'd5', 'd3',
                                               'e4', 'e9', 'e7'],
                                    type_string_title='Electorate',
                                    type_string_sentence='electorate',
                                    type_string_sentence_plural='electorates')
        dlg = DistrictSelectionDialog(registry)
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count())],
                         ['d1', 'd2', 'd5', 'd3',
                          'e4', 'e9', 'e7'])
        dlg.search.setText('eee')  # connection not fired on first change?
        dlg.search.setText('e')
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count()) if not dlg.list.item(r).isHidden()],
                         ['e4', 'e9', 'e7'])
        dlg.search.setText('d')
        self.assertEqual([dlg.list.item(r).text()
                          for r in range(dlg.list.count()) if not dlg.list.item(r).isHidden()],
                         ['d1', 'd2', 'd5', 'd3'])

    def testPickFromMap(self):
        """
        Test selecting district from map
        """
        registry = DistrictRegistry(districts=[])
        dlg = DistrictSelectionDialog(registry)
        self.assertIsNone(dlg.select_from_map_button)

        layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=fld2:string",
            "source", "memory")
        registry = VectorLayerDistrictRegistry(
            source_layer=layer,
            source_field='fld1')
        dlg = DistrictSelectionDialog(registry)
        self.assertIsNotNone(dlg.select_from_map_button)


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictSelectionDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
