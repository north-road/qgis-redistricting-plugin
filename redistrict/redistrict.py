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
from functools import partial
from qgis.PyQt.QtCore import (Qt,
                              QSettings,
                              QTranslator,
                              QCoreApplication)
from qgis.PyQt.QtWidgets import (QToolBar,
                                 QAction,
                                 QMessageBox,
                                 QToolButton,
                                 QMenu)
from qgis.core import (QgsProject,
                       QgsMapThemeCollection,
                       Qgis)
from .linz.linz_district_registry import (
    LinzElectoralDistrictRegistry)
from .linz.linz_redistrict_handler import LinzRedistrictHandler
from .gui.district_selection_dialog import (
    DistrictPicker)
from .gui.interactive_redistrict_tool import InteractiveRedistrictingTool
from .gui.district_statistics_tool import DistrictStatisticsTool
from .gui.gui_utils import GuiUtils
from .linz.interactive_redistrict_decorator import CentroidDecoratorFactory
from .linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget
from .linz.linz_redistrict_gui_handler import LinzRedistrictGuiHandler


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

        self.redistricting_menu = None
        self.redistricting_toolbar = None
        self.interactive_redistrict_action = None
        self.redistrict_selected_action = None
        self.stats_tool_action = None
        self.theme_menu = None
        self.new_themed_view_menu = None
        self.tool = None
        self.dock = None

        self.electorate_layer = QgsProject.instance().mapLayersByName(
            'general')[0]
        self.meshblock_layer = QgsProject.instance().mapLayersByName(
            'meshblock')[0]
        self.quota_layer = QgsProject.instance().mapLayersByName(
            'quotas')[0]

        self.meshblock_layer.editingStarted.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.editingStopped.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.selectionChanged.connect(self.toggle_redistrict_actions)
        self.district_registry = LinzElectoralDistrictRegistry(
            source_layer=self.electorate_layer,
            source_field='electorate_id',
            quota_layer=self.quota_layer,
            title_field='name',
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

        self.stats_tool_action = QAction(GuiUtils.get_icon('stats_tool.svg'),
                                         self.tr('Electorate Statistics'))
        self.stats_tool_action.triggered.connect(
            self.trigger_stats_tool)
        self.redistricting_toolbar.addAction(self.stats_tool_action)

        self.redistricting_menu = QMenu(self.tr('Redistricting'))
        switch_menu = QMenu(self.tr('Switch Task'), parent=self.redistricting_menu)
        switch_menu.setIcon(GuiUtils.get_icon('switch_task.svg'))

        switch_ni_general_electorate_action = QAction(self.tr('NI General Electorate'), parent=switch_menu)
        switch_menu.addAction(switch_ni_general_electorate_action)
        switch_si_general_electorate_action = QAction(self.tr('SI General Electorate'), parent=switch_menu)
        switch_menu.addAction(switch_si_general_electorate_action)
        switch_maori_electorate_action = QAction(self.tr('Māori Electorate'), parent=switch_menu)
        switch_menu.addAction(switch_maori_electorate_action)
        self.redistricting_menu.addMenu(switch_menu)
        self.iface.mainWindow().menuBar().addMenu(self.redistricting_menu)

        self.theme_menu = QMenu()
        self.theme_menu.aboutToShow.connect(partial(self.populate_theme_menu, self.theme_menu, False))

        themes_tool_button = QToolButton()
        themes_tool_button.setAutoRaise(True)
        themes_tool_button.setToolTip(self.tr('Map Themes'))
        themes_tool_button.setIcon(GuiUtils.get_icon('themes.svg'))
        themes_tool_button.setPopupMode(QToolButton.InstantPopup)
        themes_tool_button.setMenu(self.theme_menu)
        self.redistricting_toolbar.addWidget(themes_tool_button)

        self.new_themed_view_menu = QMenu()
        self.new_themed_view_menu.aboutToShow.connect(
            partial(self.populate_theme_menu, self.new_themed_view_menu, True))

        new_themed_map_tool_button = QToolButton()
        new_themed_map_tool_button.setAutoRaise(True)
        new_themed_map_tool_button.setToolTip(self.tr('New Theme Map View'))
        new_themed_map_tool_button.setIcon(GuiUtils.get_icon('new_themed_map.svg'))
        new_themed_map_tool_button.setPopupMode(QToolButton.InstantPopup)
        new_themed_map_tool_button.setMenu(self.new_themed_view_menu)
        self.redistricting_toolbar.addWidget(new_themed_map_tool_button)

        self.iface.addToolBar(self.redistricting_toolbar)
        GuiUtils.float_toolbar_over_widget(self.redistricting_toolbar,
                                           self.iface.mapCanvas())

        self.toggle_redistrict_actions()

        self.dock = LinzRedistrictingDockWidget()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.redistricting_toolbar.deleteLater()
        self.dock.deleteLater()
        self.redistricting_menu.deleteLater()
        if self.tool is not None:
            self.tool.deleteLater()

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
        return LinzRedistrictGuiHandler(redistrict_dock=self.dock,
                                        district_registry=self.district_registry)

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
                                                              ).format(self.district_registry.get_district_title(
                                                                  dlg.selected_district)),
                                                              QMessageBox.Yes | QMessageBox.No,
                                                              QMessageBox.No) != QMessageBox.Yes:
            return

        handler = self.get_handler()
        gui_handler = self.get_gui_handler()
        handler.begin_edit_group(
            QCoreApplication.translate('LinzRedistrict', 'Redistrict to {}').format(
                self.district_registry.get_district_title(dlg.selected_district)))
        if handler.assign_district(self.meshblock_layer.selectedFeatureIds(), dlg.selected_district):
            self.iface.messageBar().pushMessage(
                self.tr('Redistricted selected meshblocks to {}').format(
                    self.district_registry.get_district_title(dlg.selected_district)), level=Qgis.Success)
            gui_handler.show_stats_for_district(dlg.selected_district)
            self.meshblock_layer.removeSelection()
        else:
            self.iface.messageBar().pushMessage(
                self.tr('Could not redistricted selected meshblocks'), level=Qgis.Critical)
        handler.end_edit_group()

    def interactive_redistrict(self):
        """
        Interactively redistrict the currently selected meshblocks
        """

        self.tool = InteractiveRedistrictingTool(self.iface.mapCanvas(), handler=self.get_handler(),
                                                 district_registry=self.district_registry,
                                                 decorator_factory=CentroidDecoratorFactory(self.electorate_layer))
        self.iface.mapCanvas().setMapTool(self.tool)

    def trigger_stats_tool(self):
        """
        Triggers the district statistics tool
        """
        self.tool = DistrictStatisticsTool(canvas=self.iface.mapCanvas(), gui_handler=self.get_gui_handler())
        self.iface.mapCanvas().setMapTool(self.tool)

    def populate_theme_menu(self, menu, new_map=False):
        """
        Adds available themes to the theme menu
        :param menu: menu to populate
        :param new_map: if True, triggering the action will open a new map canvas
        """
        menu.clear()

        root = QgsProject.instance().layerTreeRoot()
        model = self.iface.layerTreeView().layerTreeModel()
        current_theme = QgsMapThemeCollection.createThemeFromCurrentState(root, model)

        for theme in QgsProject.instance().mapThemeCollection().mapThemes():
            is_current_theme = current_theme == QgsProject.instance().mapThemeCollection().mapThemeState(theme)
            theme_action = QAction(theme, parent=menu)
            theme_action.triggered.connect(
                lambda state, new_theme=theme, open_new_map=new_map: self.switch_theme(new_theme, open_new_map))
            if is_current_theme:
                theme_action.setCheckable(True)
                theme_action.setChecked(True)
            menu.addAction(theme_action)

    def get_unique_canvas_name(self, theme_name: str) -> str:
        """
        Generates a unique name for a canvas showing the specified theme1
        :param theme_name: name of theme to show in canvas
        """
        new_name = theme_name
        clash = True
        counter = 1
        while clash:
            clash = False
            for canvas in self.iface.mapCanvases():
                if canvas.objectName() == new_name:
                    clash = True
                    counter += 1
                    new_name = theme_name + ' ' + str(counter)
                    break
            if not clash:
                return new_name

    def switch_theme(self, new_theme: str, open_new_map: bool):
        """
        Switches to the selected map theme
        :param new_theme: new map theme to show
        :param open_new_map: set to True to open a new map canvas
        """
        root = QgsProject.instance().layerTreeRoot()
        model = self.iface.layerTreeView().layerTreeModel()

        if open_new_map:
            new_name = self.get_unique_canvas_name(new_theme)
            new_canvas = self.iface.createNewMapCanvas(new_name)
            new_canvas.setTheme(new_theme)
        else:
            QgsProject.instance().mapThemeCollection().applyTheme(new_theme, root, model)
