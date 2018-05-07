# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin

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

import os.path
from qgis.PyQt.QtCore import (Qt,
                              QSettings,
                              QTranslator,
                              QCoreApplication)
from qgis.PyQt.QtWidgets import (QToolBar,
                                 QAction,
                                 QMessageBox)
from qgis.core import (QgsProject,
                       Qgis)
from .linz.linz_district_registry import (
    LinzElectoralDistrictRegistry)
from .linz.linz_redistrict_handler import LinzRedistrictHandler
from .gui.district_selection_dialog import (
    DistrictPicker)
from .gui.redistrict_gui_handler import RedistrictGuiHandler
from .gui.interactive_redistrict_tool import InteractiveRedistrictingTool
from .gui.gui_utils import GuiUtils
from .linz.interactive_redistrict_decorator import CentroidDecoratorFactory
from .linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget


class LinzRedistrict:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.redistricting_toolbar = None
        self.interactive_redistrict_action = None
        self.redistrict_selected_action = None
        self.tool = None
        self.dock = None

        self.electorate_layer = QgsProject.instance().mapLayersByName(
            'general')[0]
        self.meshblock_layer = QgsProject.instance().mapLayersByName(
            'meshblock')[0]
        self.meshblock_layer.editingStarted.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.editingStopped.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.selectionChanged.connect(self.toggle_redistrict_actions)
        self.district_registry = LinzElectoralDistrictRegistry(
            source_layer=self.electorate_layer,
            source_field='GeneralElectoralDistrictName_2007',
            name='General NI')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):  # pylint: disable=no-self-use
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LinzRedistrict', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.redistricting_toolbar = QToolBar(self.tr('Redistricting'))
        self.redistricting_toolbar.setObjectName('redistricting')

        self.interactive_redistrict_action = QAction(GuiUtils.get_icon(
            'interactive_redistrict.svg'), self.tr('Interactive Redistrict'))
        self.interactive_redistrict_action.triggered.connect(
            self.interactive_redistrict)
        self.redistricting_toolbar.addAction(
            self.interactive_redistrict_action)

        self.redistrict_selected_action = QAction(
            GuiUtils.get_icon('redistrict_selected.svg'),
            self.tr('Redistrict Selected Mesh Blocks'), None)
        self.redistrict_selected_action.triggered.connect(
            self.redistrict_selected)
        self.redistricting_toolbar.addAction(self.redistrict_selected_action)

        self.iface.addToolBar(self.redistricting_toolbar)
        GuiUtils.float_toolbar_over_widget(self.redistricting_toolbar,
                                           self.iface.mapCanvas())

        self.toggle_redistrict_actions()

        self.dock = LinzRedistrictingDockWidget()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.redistricting_toolbar.deleteLater()

    def toggle_redistrict_actions(self):
        """
        Updates the enabled status of redistricting actions based
        on whether the meshblock layer is editable
        """
        enabled = self.meshblock_layer.isEditable()
        has_selection = bool(self.meshblock_layer.selectedFeatureIds())
        self.redistrict_selected_action.setEnabled(enabled and has_selection)
        self.interactive_redistrict_action.setEnabled(enabled)

    def get_handler(self):
        """
        Returns the current redistricting handler
        """
        return LinzRedistrictHandler(meshblock_layer=self.meshblock_layer,
                                     target_field='staged_electorate',
                                     electorate_layer=self.electorate_layer,
                                     electorate_layer_field='electorate_id')

    def get_gui_handler(self):
        """
        Returns the current redistricting GUI handler
        """
        return RedistrictGuiHandler(redistrict_dock=self.dock)

    def redistrict_selected(self):
        """
        Redistrict the currently selected meshblocks
        """
        dlg = DistrictPicker(district_registry=self.district_registry,
                             parent=self.iface.mainWindow())
        if dlg.selected_district is None:
            return

        if dlg.requires_confirmation and QMessageBox.question(self.iface.mainWindow(),
                                                              self.tr('Redistrict Selected'),
                                                              self.tr(
                                                                  'Are you sure you want to redistrict the selected meshblocks to “{}”?'
                                                              ).format(dlg.selected_district),
                                                              QMessageBox.Yes | QMessageBox.No,
                                                              QMessageBox.No) != QMessageBox.Yes:
            return

        handler = self.get_handler()
        handler.begin_edit_group(
            QCoreApplication.translate('LinzRedistrict', 'Redistrict to {}').format(str(dlg.selected_district)))
        if handler.assign_district(self.meshblock_layer.selectedFeatureIds(), dlg.selected_district):
            self.iface.messageBar().pushMessage(
                self.tr('Redistricted selected meshblocks to {}').format(dlg.selected_district), level=Qgis.Success)
        else:
            self.iface.messageBar().pushMessage(
                self.tr('Could not redistricted selected meshblocks'), level=Qgis.Critical)
        handler.end_edit_group()

    def interactive_redistrict(self):
        """
        Interactively redistrict the currently selected meshblocks
        """

        self.tool = InteractiveRedistrictingTool(self.iface.mapCanvas(), handler=self.get_handler(),
                                                 decorator_factory=CentroidDecoratorFactory(self.electorate_layer))
        self.iface.mapCanvas().setMapTool(self.tool)
