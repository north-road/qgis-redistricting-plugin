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
                                 QMenu,
                                 QFileDialog)
from qgis.core import (QgsApplication,
                       QgsProject,
                       QgsMapThemeCollection,
                       QgsExpressionContextUtils,
                       Qgis)
from qgis.gui import (QgsMapTool,
                      QgsNewNameDialog)
from .linz.linz_district_registry import (
    LinzElectoralDistrictRegistry)
from .linz.linz_redistrict_handler import LinzRedistrictHandler
from .linz.scenario_registry import ScenarioRegistry
from .linz.linz_redistricting_context import LinzRedistrictingContext
from .gui.district_selection_dialog import (
    DistrictPicker)
from .gui.interactive_redistrict_tool import InteractiveRedistrictingTool
from .gui.district_statistics_tool import DistrictStatisticsTool
from .gui.gui_utils import (GuiUtils,
                            BlockingDialog,
                            ConfirmationDialog)
from .linz.interactive_redistrict_decorator import CentroidDecoratorFactory
from .linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget
from .linz.linz_redistrict_gui_handler import LinzRedistrictGuiHandler
from .linz.scenario_selection_dialog import ScenarioSelectionDialog
from .linz.db_utils import CopyFileTask


class LinzRedistrict:  # pylint: disable=too-many-public-methods
    """QGIS Plugin Implementation."""

    TASK_GN = 'GN'
    TASK_GS = 'GS'
    TASK_M = 'M'

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
        self.begin_action = None
        self.stats_tool_action = None
        self.theme_menu = None
        self.new_themed_view_menu = None
        self.tool = None
        self.dock = None
        self.scenarios_tool_button = None
        self.context = None

        self.is_redistricting = False
        self.electorate_layer = None
        self.meshblock_layer = None
        self.scenario_layer = None
        self.quota_layer = None
        self.meshblock_electorate_layer = None
        self.scenario_registry = None
        self.db_source = os.path.join(self.plugin_dir,
                                      'db', 'nz_db.gpkg')
        self.task = None

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
        self.redistricting_menu = QMenu(self.tr('Redistricting'))

        self.begin_action = QAction(self.tr('Begin Redistricting'))
        self.begin_action.triggered.connect(self.begin_redistricting)
        self.begin_action.setCheckable(True)
        self.redistricting_menu.addAction(self.begin_action)

        switch_menu = QMenu(self.tr('Switch Task'), parent=self.redistricting_menu)
        switch_menu.setIcon(GuiUtils.get_icon('switch_task.svg'))

        switch_ni_general_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_GN),
                                                      parent=switch_menu)
        switch_ni_general_electorate_action.triggered.connect(partial(self.set_task, self.TASK_GN))
        switch_menu.addAction(switch_ni_general_electorate_action)
        switch_si_general_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_GS),
                                                      parent=switch_menu)
        switch_si_general_electorate_action.triggered.connect(partial(self.set_task, self.TASK_GS))
        switch_menu.addAction(switch_si_general_electorate_action)
        switch_maori_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_M),
                                                 parent=switch_menu)
        switch_maori_electorate_action.triggered.connect(partial(self.set_task, self.TASK_M))
        switch_menu.addAction(switch_maori_electorate_action)
        self.redistricting_menu.addMenu(switch_menu)
        self.iface.mainWindow().menuBar().addMenu(self.redistricting_menu)

    def create_redistricting_ui(self):  # pylint: disable=too-many-statements
        """
        Creates the UI components relating to redistricting operations
        """
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

        self.dock = LinzRedistrictingDockWidget(context=self.context)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.context.scenario_changed.connect(self.update_dock_title)

        self.scenarios_tool_button = QToolButton()
        self.scenarios_tool_button.setAutoRaise(True)
        self.scenarios_tool_button.setToolTip('Scenarios')
        self.scenarios_tool_button.setIcon(GuiUtils.get_icon(icon='scenarios.svg'))
        self.scenarios_tool_button.setPopupMode(QToolButton.InstantPopup)

        scenarios_menu = QMenu(parent=self.scenarios_tool_button)
        switch_scenario_action = QAction(self.tr('Switch to Existing Scenario...'), parent=scenarios_menu)
        switch_scenario_action.triggered.connect(self.select_current_scenario)
        scenarios_menu.addAction(switch_scenario_action)

        scenarios_menu.addSeparator()
        update_scenario_action = QAction(self.tr('Update Statistics for Scenario...'), parent=scenarios_menu)
        # update_scenario_action.triggered.connect(update_scenario)
        scenarios_menu.addAction(update_scenario_action)

        scenarios_menu.addSeparator()

        branch_scenario_action = QAction(self.tr('Branch to New Scenario...'), parent=scenarios_menu)
        branch_scenario_action.triggered.connect(self.branch_scenario)
        scenarios_menu.addAction(branch_scenario_action)
        import_scenario_action = QAction(self.tr('Import Scenario from Database...'), parent=scenarios_menu)
        # import_scenario_action.triggered.connect(import_scenario)
        scenarios_menu.addAction(import_scenario_action)

        self.scenarios_tool_button.setMenu(scenarios_menu)
        self.dock.dock_toolbar().addWidget(self.scenarios_tool_button)

        options_menu = QMenu(parent=self.dock.dock_toolbar())
        # options_menu.addMenu(electorate_menu)
        # options_menu.addSeparator()

        master_db_menu = QMenu(self.tr('Database'), parent=options_menu)
        export_master_action = QAction(self.tr('Export Database...'), parent=master_db_menu)
        export_master_action.triggered.connect(self.export_database)
        master_db_menu.addAction(export_master_action)
        options_menu.addMenu(master_db_menu)

        options_button = QToolButton(parent=self.dock.dock_toolbar())
        options_button.setAutoRaise(True)
        options_button.setToolTip('Options')
        options_button.setIcon(GuiUtils.get_icon('options.svg'))
        options_button.setPopupMode(QToolButton.InstantPopup)
        options_button.setMenu(options_menu)
        self.dock.dock_toolbar().addWidget(options_button)

        self.set_task(self.TASK_GN)

    def begin_redistricting(self):
        """
        Starts the redistricting operation, opening toolbars and docks as needed
        """
        if self.is_redistricting:
            return

        self.is_redistricting = True
        self.begin_action.setChecked(True)

        # matching layers
        # TODO - use paths, not project layers
        self.electorate_layer = QgsProject.instance().mapLayersByName(
            'general')[0]
        self.meshblock_layer = QgsProject.instance().mapLayersByName(
            'meshblock')[0]
        self.quota_layer = QgsProject.instance().mapLayersByName(
            'quotas')[0]
        self.scenario_layer = QgsProject.instance().mapLayersByName(
            'scenarios')[0]
        self.meshblock_electorate_layer = QgsProject.instance().mapLayersByName(
            'meshblock_electorates')[0]
        self.db_source = self.electorate_layer.dataProvider().dataSourceUri().split('|')[0]

        self.scenario_registry = ScenarioRegistry(source_layer=self.scenario_layer,
                                                  id_field='scenario_id',
                                                  name_field='name',
                                                  meshblock_electorate_layer=self.meshblock_electorate_layer)

        self.context = LinzRedistrictingContext(scenario_registry=self.scenario_registry)
        self.context.task = self.TASK_GN

        self.meshblock_layer.editingStarted.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.editingStopped.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.selectionChanged.connect(self.toggle_redistrict_actions)

        self.create_redistricting_ui()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.redistricting_toolbar is not None:
            self.redistricting_toolbar.deleteLater()
        if self.dock is not None:
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

    def set_task(self, task: str):
        """
        Sets the current task
        :param task: task, eg 'GN','GS' or 'M'
        """
        self.context.task = task
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'task', self.context.task)

        self.electorate_layer.renderer().rootRule().children()[0].setLabel(self.context.get_name_for_current_task())

        self.iface.layerTreeView().refreshLayerSymbology(self.electorate_layer.id())
        self.iface.layerTreeView().refreshLayerSymbology(self.meshblock_layer.id())

        for canvas in self.iface.mapCanvases():
            canvas.refreshAllLayers()

        if self.tool is not None:
            self.tool.deleteLater()

        self.dock.update_dock_title(context=self.context)

    def get_district_registry(self) -> LinzElectoralDistrictRegistry:
        """
        Returns the current district registry
        """
        return LinzElectoralDistrictRegistry(
            source_layer=self.electorate_layer,
            source_field='electorate_id',
            quota_layer=self.quota_layer,
            electorate_type=self.context.task,
            title_field='name',
            name='General NI')

    def get_handler(self) -> LinzRedistrictHandler:
        """
        Returns the current redistricting handler
        """
        return LinzRedistrictHandler(meshblock_layer=self.meshblock_layer,
                                     target_field='staged_electorate',
                                     electorate_layer=self.electorate_layer,
                                     electorate_layer_field='electorate_id')

    def get_gui_handler(self) -> LinzRedistrictGuiHandler:
        """
        Returns the current redistricting GUI handler
        """
        return LinzRedistrictGuiHandler(redistrict_dock=self.dock,
                                        district_registry=self.get_district_registry())

    def redistrict_selected(self):
        """
        Redistrict the currently selected meshblocks
        """
        dlg = DistrictPicker(district_registry=self.get_district_registry(),
                             parent=self.iface.mainWindow())
        if dlg.selected_district is None:
            return

        district_registry = self.get_district_registry()

        if dlg.requires_confirmation and QMessageBox.question(self.iface.mainWindow(),
                                                              self.tr('Redistrict Selected'),
                                                              self.tr(
                                                                  'Are you sure you want to redistrict the selected meshblocks to “{}”?'
                                                              ).format(district_registry.get_district_title(
                                                                  dlg.selected_district)),
                                                              QMessageBox.Yes | QMessageBox.No,
                                                              QMessageBox.No) != QMessageBox.Yes:
            return

        handler = self.get_handler()
        gui_handler = self.get_gui_handler()
        handler.begin_edit_group(
            QCoreApplication.translate('LinzRedistrict', 'Redistrict to {}').format(
                district_registry.get_district_title(dlg.selected_district)))
        if handler.assign_district(self.meshblock_layer.selectedFeatureIds(), dlg.selected_district):
            self.iface.messageBar().pushMessage(
                self.tr('Redistricted selected meshblocks to {}').format(
                    district_registry.get_district_title(dlg.selected_district)), level=Qgis.Success)
            gui_handler.show_stats_for_district(dlg.selected_district)
            self.meshblock_layer.removeSelection()
        else:
            self.iface.messageBar().pushMessage(
                self.tr('Could not redistricted selected meshblocks'), level=Qgis.Critical)
        handler.end_edit_group()

    def set_current_tool(self, tool: QgsMapTool):
        """
        Sets the current map tool
        :param tool: new map tool
        """
        if self.tool is not None:
            # Disconnect from old tool
            self.tool.deactivated.disconnect(self.tool_deactivated)
            self.tool.deleteLater()
        self.tool = tool
        self.tool.deactivated.connect(self.tool_deactivated)
        self.iface.mapCanvas().setMapTool(self.tool)

    def tool_deactivated(self):
        """
        Triggered on tool deactivation
        """
        self.tool = None

    def interactive_redistrict(self):
        """
        Interactively redistrict the currently selected meshblocks
        """

        tool = InteractiveRedistrictingTool(self.iface.mapCanvas(), handler=self.get_handler(),
                                            district_registry=self.get_district_registry(),
                                            decorator_factory=CentroidDecoratorFactory(self.electorate_layer))
        self.set_current_tool(tool=tool)

    def trigger_stats_tool(self):
        """
        Triggers the district statistics tool
        """
        tool = DistrictStatisticsTool(canvas=self.iface.mapCanvas(), gui_handler=self.get_gui_handler())
        self.set_current_tool(tool=tool)

    def map_themes_for_task(self):
        """
        Lists available map themes for the current task
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()

    def clean_theme_name(self, theme_name: str):
        """
        Cleans up a theme name
        :param theme_name: name of theme
        """
        return theme_name.strip()

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

        for theme in self.map_themes_for_task():
            is_current_theme = current_theme == QgsProject.instance().mapThemeCollection().mapThemeState(theme)
            theme_action = QAction(self.clean_theme_name(theme), parent=menu)
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

    def select_current_scenario(self):
        """
        Allows user to switch the current scenario
        """
        dlg = ScenarioSelectionDialog(scenario_registry=self.scenario_registry, parent=self.iface.mainWindow())
        if dlg.exec_():
            self.switch_scenario(dlg.selected_scenario())
        dlg.deleteLater()

    def switch_scenario(self, scenario: int):
        """
        Switches the current scenario to a new scenario
        :param scenario: new scenario ID
        """
        self.context.set_scenario(scenario)

    def branch_scenario(self):
        """
        Branches the current scenario to a new scenario
        """
        current_scenario_name = self.context.get_name_for_current_scenario()
        existing_names = list(self.scenario_registry.scenario_titles().keys())
        dlg = QgsNewNameDialog(current_scenario_name, self.tr('{} Copy').format(current_scenario_name),
                               existing=existing_names, parent=self.iface.mainWindow())
        dlg.setWindowTitle(self.tr('Branch to New Scenario'))
        dlg.setHintString(self.tr('Enter name for new scenario'))
        dlg.setOverwriteEnabled(False)
        if dlg.exec_():
            progress_dialog = BlockingDialog(self.tr('Branching Scenario'), self.tr('Branching scenario...'))
            progress_dialog.force_show_and_paint()

            res, error = self.scenario_registry.branch_scenario(scenario_id=self.context.scenario,
                                                                new_scenario_name=dlg.name())
            if not res:
                self.iface.messageBar().pushMessage(
                    error, level=Qgis.Critical)
            else:
                self.iface.messageBar().pushMessage(
                    self.tr('Branched scenario to “{}”').format(dlg.name()), level=Qgis.Success)
                self.context.set_scenario(res)

    def update_dock_title(self):
        """
        Update dock title
        """
        self.dock.update_dock_title(self.context)

    def report_success(self, message: str):
        """
        Reports a success message
        """
        self.iface.messageBar().pushMessage(
            message, level=Qgis.Success)

    def report_failure(self, message: str):
        """
        Reports a failure message
        """
        self.iface.messageBar().pushMessage(
            message, level=Qgis.Critical)

    def export_database(self):
        """
        Exports the current database using a background task
        """
        destination, _filter = QFileDialog.getSaveFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                           self.tr('Export Database'), '',
                                                           filter='Database Files (*.gpkg)')
        if not destination:
            return

        if not destination.endswith('.gpkg'):
            destination += '.gpkg'

        self.task = CopyFileTask(self.tr('Exporting database'), {self.db_source: destination})
        self.task.taskCompleted.connect(
            partial(self.report_success, self.tr('Exported database to {}').format(destination)))
        self.task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Error while exporting database to {}').format(destination)))

        QgsApplication.taskManager().addTask(self.task)

    def import_database(self):
        """
        Imports a new master database, replacing the current database
        """
        source, _filter = QFileDialog.getOpenFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                      self.tr('Import Master Database'), '',
                                                      filter='Database Files (*.gpkg)')
        if not source:
            return

        QgsProject.instance().clear()
        dlg = ConfirmationDialog(self.tr('Import Master Database'),
                                 self.tr(
                                     'Importing a new master database will completely replace the existing district database.\n\nThis action cannot be reversed!\n\nEnter \'I ACCEPT\' to continue.'),
                                 self.tr('I ACCEPT'), parent=self.iface.mainWindow())
        if not dlg.exec_():
            return
