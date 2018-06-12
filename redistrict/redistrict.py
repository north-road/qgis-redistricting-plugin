# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

# pylint: disable=too-many-lines

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '20/04/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os.path
from functools import partial
from typing import Optional
from qgis.PyQt.QtCore import (QObject,
                              Qt,
                              QDir,
                              QFile,
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
                       QgsVectorLayer,
                       QgsMapThemeCollection,
                       QgsExpressionContextUtils,
                       Qgis,
                       QgsSettings,
                       QgsTask)
from qgis.gui import (QgisInterface,
                      QgsMapTool,
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
from .gui.message_bar_progress import MessageBarProgressItem
from .gui.gui_utils import (GuiUtils,
                            BlockingDialog,
                            ConfirmationDialog)
from .gui.district_settings_dialog import DistrictSettingsDialog, SETTINGS_AUTH_CONFIG_KEY  # pylint: disable=unused-import
from .linz.interactive_redistrict_decorator import CentroidDecoratorFactory
from .linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget
from .linz.linz_redistrict_gui_handler import LinzRedistrictGuiHandler
from .linz.scenario_selection_dialog import ScenarioSelectionDialog
from .linz.db_utils import CopyFileTask
from .linz.create_electorate_dialog import CreateElectorateDialog
from .linz.deprecate_electorate_dialog import DeprecateElectorateDialog
from .linz.scenario_switch_task import ScenarioSwitchTask
from .linz.staged_electorate_update_task import UpdateStagedElectoratesTask
from .linz.linz_mb_scenario_bridge import LinzMeshblockScenarioBridge
from .linz.validation_task import ValidationTask
from .linz.export_task import ExportTask


API_BASE_URL = 'https://electoral-api-uat.stats.govt.nz/electoral-api-uat/v1/'


class LinzRedistrict(QObject):  # pylint: disable=too-many-public-methods
    """QGIS Plugin Implementation."""

    TASK_GN = 'GN'
    TASK_GS = 'GS'
    TASK_M = 'M'

    MESHBLOCK_NUMBER_FIELD = 'MB2018_V1_00'

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        super().__init__()
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
        self.open_settings_action = None
        self.interactive_redistrict_action = None
        self.redistrict_selected_action = None
        self.start_editing_action = None
        self.save_edits_action = None
        self.rollback_edits_action = None
        self.begin_action = None
        self.stats_tool_action = None
        self.validate_action = None
        self.theme_menu = None
        self.new_themed_view_menu = None
        self.tool = None
        self.dock = None
        self.scenarios_tool_button = None
        self.context = None
        self.current_dock_electorate = None

        self.is_redistricting = False
        self.electorate_layer = None
        self.meshblock_layer = None
        self.scenario_layer = None
        self.quota_layer = None
        self.meshblock_electorate_layer = None
        self.user_log_layer = None
        self.scenario_registry = None
        self.meshblock_scenario_bridge = None
        self.db_source = os.path.join(self.plugin_dir,
                                      'db', 'nz_db.gpkg')
        self.task = None
        self.copy_task = None
        self.switch_task = None
        self.staged_task = None
        self.validation_task = None
        self.export_task = None
        self.progress_item = None
        self.switch_menu = None

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

        self.switch_menu = QMenu(self.tr('Switch Task'), parent=self.redistricting_menu)
        self.switch_menu.setIcon(GuiUtils.get_icon('switch_task.svg'))

        switch_ni_general_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_GN),
                                                      parent=self.switch_menu)
        switch_ni_general_electorate_action.triggered.connect(partial(self.set_task_and_show_progress, self.TASK_GN))
        switch_ni_general_electorate_action.setEnabled(False)
        self.switch_menu.addAction(switch_ni_general_electorate_action)
        switch_si_general_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_GS),
                                                      parent=self.switch_menu)
        switch_si_general_electorate_action.triggered.connect(partial(self.set_task_and_show_progress, self.TASK_GS))
        switch_si_general_electorate_action.setEnabled(False)
        self.switch_menu.addAction(switch_si_general_electorate_action)
        switch_maori_electorate_action = QAction(LinzRedistrictingContext.get_name_for_task(self.TASK_M),
                                                 parent=self.switch_menu)
        switch_maori_electorate_action.triggered.connect(partial(self.set_task_and_show_progress, self.TASK_M))
        switch_maori_electorate_action.setEnabled(False)
        self.switch_menu.addAction(switch_maori_electorate_action)
        self.redistricting_menu.addMenu(self.switch_menu)

        self.redistricting_menu.addSeparator()
        self.open_settings_action = QAction(GuiUtils.get_icon(
            'open_settings.svg'), self.tr('Settings...'))
        self.open_settings_action.triggered.connect(
            self.open_settings)
        self.redistricting_menu.addAction(
            self.open_settings_action)

        self.iface.mainWindow().menuBar().addMenu(self.redistricting_menu)

    def create_redistricting_ui(self):  # pylint: disable=too-many-statements,too-many-locals
        """
        Creates the UI components relating to redistricting operations
        """
        self.redistricting_toolbar = QToolBar(self.tr('Redistricting'))
        self.redistricting_toolbar.setObjectName('redistricting')
        self.start_editing_action = QAction(GuiUtils.get_icon(
            'toggle_editing.svg'), self.tr('Toggle Editing'))
        self.start_editing_action.setCheckable(True)
        self.start_editing_action.toggled.connect(
            self.toggle_editing)
        self.redistricting_toolbar.addAction(
            self.start_editing_action)
        self.start_editing_action.setEnabled(False)
        self.save_edits_action = QAction(GuiUtils.get_icon(
            'save_edits.svg'), self.tr('Save Staged Edits'))
        self.save_edits_action.triggered.connect(
            self.save_edits)
        self.redistricting_toolbar.addAction(
            self.save_edits_action)
        self.save_edits_action.setEnabled(False)
        self.rollback_edits_action = QAction(GuiUtils.get_icon(
            'rollback_edits.svg'), self.tr('Rollback Edits'))
        self.rollback_edits_action.triggered.connect(
            self.rollback_edits)
        self.redistricting_toolbar.addAction(
            self.rollback_edits_action)
        self.rollback_edits_action.setEnabled(False)

        self.redistricting_toolbar.addSeparator()

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

        self.context.scenario_changed.connect(self.scenario_changed)

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
        import_scenario_action.triggered.connect(self.import_scenario)
        scenarios_menu.addAction(import_scenario_action)

        self.scenarios_tool_button.setMenu(scenarios_menu)
        self.dock.dock_toolbar().addWidget(self.scenarios_tool_button)

        self.validate_action = QAction(GuiUtils.get_icon('validate.svg'), self.tr('Validate Electorates'))
        self.validate_action.triggered.connect(self.validate_electorates)
        self.dock.dock_toolbar().addAction(self.validate_action)

        options_menu = QMenu(parent=self.dock.dock_toolbar())

        electorate_menu = QMenu(self.tr('Manage Electorates'), parent=options_menu)

        new_electorate_action = QAction(self.tr('Create New Electorate...'), parent=electorate_menu)
        new_electorate_action.triggered.connect(self.create_new_electorate)
        electorate_menu.addAction(new_electorate_action)

        deprecate_electorate_action = QAction(self.tr('Deprecate Electorate...'), parent=electorate_menu)
        deprecate_electorate_action.triggered.connect(self.deprecate_electorate)
        electorate_menu.addAction(deprecate_electorate_action)

        options_menu.addMenu(electorate_menu)

        master_db_menu = QMenu(self.tr('Database'), parent=options_menu)
        export_master_action = QAction(self.tr('Export Database...'), parent=master_db_menu)
        export_master_action.triggered.connect(self.export_database)
        master_db_menu.addAction(export_master_action)
        import_master_action = QAction(self.tr('Import Master Database...'), parent=master_db_menu)
        import_master_action.triggered.connect(self.import_master_database)
        master_db_menu.addAction(import_master_action)

        options_menu.addMenu(master_db_menu)

        export_action = QAction(self.tr('Export Electorates...'), parent=options_menu)
        export_action.triggered.connect(self.export_electorates)
        options_menu.addAction(export_action)

        options_menu.addSeparator()
        log_action = QAction(self.tr('View Log...'), parent=options_menu)
        log_action.triggered.connect(self.view_log)
        options_menu.addAction(log_action)

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

        # matching layers
        try:
            self.electorate_layer = QgsProject.instance().mapLayersByName(
                'Electorates')[0]
            self.meshblock_layer = QgsProject.instance().mapLayersByName(
                'Meshblocks')[0]
            self.quota_layer = QgsProject.instance().mapLayersByName(
                'quotas')[0]
            self.scenario_layer = QgsProject.instance().mapLayersByName(
                'scenarios')[0]
            self.meshblock_electorate_layer = QgsProject.instance().mapLayersByName(
                'meshblock_electorates')[0]
            self.user_log_layer = QgsProject.instance().mapLayersByName(
                'user_log')[0]
        except IndexError:
            self.report_failure(self.tr('Cannot find map layers - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        self.is_redistricting = True
        self.begin_action.setChecked(True)

        self.db_source = self.electorate_layer.dataProvider().dataSourceUri().split('|')[0]

        self.scenario_registry = ScenarioRegistry(source_layer=self.scenario_layer,
                                                  id_field='scenario_id',
                                                  name_field='name',
                                                  meshblock_electorate_layer=self.meshblock_electorate_layer)

        self.context = LinzRedistrictingContext(scenario_registry=self.scenario_registry)
        self.context.task = self.TASK_GN
        self.meshblock_layer.layerModified.connect(self.update_layer_modified_actions)
        self.meshblock_layer.editingStarted.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.editingStopped.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.selectionChanged.connect(self.toggle_redistrict_actions)

        self.meshblock_scenario_bridge = LinzMeshblockScenarioBridge(meshblock_layer=self.meshblock_layer,
                                                                     meshblock_scenario_layer=self.meshblock_electorate_layer,
                                                                     meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD)
        self.meshblock_scenario_bridge.scenario = self.context.scenario

        self.create_redistricting_ui()

        self.progress_item = MessageBarProgressItem(self.tr('Preparing redistricting'), iface=self.iface)
        self.switch_task.progressChanged.connect(self.progress_item.set_progress)
        self.switch_task.taskCompleted.connect(self.progress_item.close)
        self.switch_task.taskCompleted.connect(partial(self.start_editing_action.setEnabled, True))
        self.switch_task.taskTerminated.connect(self.progress_item.close)

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
        self.update_layer_modified_actions()

    def update_layer_modified_actions(self):
        """
        Triggered on meshblock layer modification
        """
        save_enabled = self.meshblock_layer.isEditable() and self.meshblock_layer.isModified()
        self.save_edits_action.setEnabled(save_enabled)
        self.rollback_edits_action.setEnabled(self.meshblock_layer.isModified())

    def toggle_editing(self, active: bool):
        """
        Triggered when editing begins/ends
        :param active: True if editing is active
        """
        tools = self.iface.vectorLayerTools()
        if active:
            tools.startEditing(self.meshblock_layer)
        else:
            tools.stopEditing(self.meshblock_layer, allowCancel=False)
        self.set_current_tool(tool=None)

    def open_settings(self):
        """
        Open the settings dialog
        """
        dlg = DistrictSettingsDialog()
        dlg.exec_()

    def save_edits(self):
        """Saves pending edits"""
        tools = self.iface.vectorLayerTools()
        tools.saveEdits(self.meshblock_layer)

    def rollback_edits(self):
        """
        Rolls back pending edits
        """
        if not self.meshblock_layer.isEditable():
            return

        self.meshblock_layer.rollBack(deleteBuffer=False)
        self.meshblock_layer.triggerRepaint()

    def enable_task_switches(self, enabled):
        """
        Enables or disables the task switching commands
        """
        for action in self.switch_menu.actions():
            action.setEnabled(enabled)

    def set_task(self, task: str):
        """
        Sets the current task
        :param task: task, eg 'GN','GS' or 'M'
        """
        self.enable_task_switches(False)
        self.meshblock_scenario_bridge.task = task
        progress_dialog = BlockingDialog(self.tr('Switch Task'), self.tr('Preparing switch...'))
        progress_dialog.force_show_and_paint()

        task_name = self.context.get_name_for_task(task)
        description = self.tr('Switching to task {}').format(task_name)

        self.switch_task = UpdateStagedElectoratesTask(description,
                                                       meshblock_layer=self.meshblock_layer,
                                                       meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                                       scenario_registry=self.scenario_registry,
                                                       scenario=self.context.scenario,
                                                       task=task)
        progress_dialog.deleteLater()

        self.switch_task.taskCompleted.connect(
            partial(self.task_set, task))
        self.switch_task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Error while switching to “{}”').format(task_name)))

        QgsApplication.taskManager().addTask(self.switch_task)

    def set_task_and_show_progress(self, task):
        """
        Sets the current task, showing a progress bar to report status
        """
        self.set_task(task)
        self.progress_item = MessageBarProgressItem(
            self.tr('Switching to {}').format(self.context.get_name_for_task(task)), iface=self.iface)
        self.switch_task.progressChanged.connect(self.progress_item.set_progress)
        self.switch_task.taskCompleted.connect(self.progress_item.close)
        self.switch_task.taskTerminated.connect(self.progress_item.close)

    def task_set(self, task):
        """
        Triggered after current task has been set
        """
        self.context.task = task
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), 'task', self.context.task)

        # self.electorate_layer.renderer().rootRule().children()[0].setLabel(self.context.get_name_for_current_task())

        self.iface.layerTreeView().refreshLayerSymbology(self.electorate_layer.id())
        self.iface.layerTreeView().refreshLayerSymbology(self.meshblock_layer.id())

        self.refresh_canvases()
        if self.tool is not None:
            self.tool.deleteLater()

        task_name = self.context.get_name_for_task(task)
        self.report_success(self.tr('Switched to “{}”').format(task_name))

        self.dock.update_dock_title(context=self.context)

        self.enable_task_switches(True)

    def refresh_canvases(self):
        """
        Refreshes all visible map canvases
        """
        for canvas in self.iface.mapCanvases():
            canvas.refreshAllLayers()

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
        handler = LinzRedistrictHandler(meshblock_layer=self.meshblock_layer,
                                        meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                        target_field='staged_electorate',
                                        electorate_layer=self.electorate_layer,
                                        electorate_layer_field='electorate_id',
                                        task=self.context.task,
                                        user_log_layer=self.user_log_layer,
                                        scenario=self.context.scenario)
        handler.redistrict_occured.connect(self.refresh_dock_stats)
        return handler

    def get_gui_handler(self) -> LinzRedistrictGuiHandler:
        """
        Returns the current redistricting GUI handler
        """
        handler = LinzRedistrictGuiHandler(redistrict_dock=self.dock,
                                           district_registry=self.get_district_registry())
        handler.current_district_changed.connect(self.current_dock_electorate_changed)
        return handler

    def current_dock_electorate_changed(self, electorate):
        """
        Triggered when electorate shown in dock changes
        :param electorate: current electorate shown
        """
        self.current_dock_electorate = electorate

    def refresh_dock_stats(self):
        """
        Refreshes the stats shown in the dock widget
        """
        handler = self.get_gui_handler()
        handler.show_stats_for_district(self.current_dock_electorate)

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
            self.report_success(
                self.tr('Redistricted selected meshblocks to {}').format(
                    district_registry.get_district_title(dlg.selected_district)))
            gui_handler.show_stats_for_district(dlg.selected_district)
            self.meshblock_layer.removeSelection()
        else:
            self.report_failure(
                self.tr('Could not redistricted selected meshblocks'))
        handler.end_edit_group()

    def set_current_tool(self, tool: Optional[QgsMapTool]):
        """
        Sets the current map tool
        :param tool: new map tool
        """
        if self.tool is not None:
            # Disconnect from old tool
            self.tool.deactivated.disconnect(self.tool_deactivated)
            self.tool.deleteLater()
        self.tool = tool
        if tool is not None:
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
                                            decorator_factory=CentroidDecoratorFactory(
                                                electorate_layer=self.electorate_layer,
                                                meshblock_layer=self.meshblock_layer,
                                                task=self.context.task))
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
        electorate_registry = self.get_district_registry()
        scenario_name = self.scenario_registry.get_scenario_name(scenario)
        task_name = self.tr('Switching to {}').format(scenario_name)

        progress_dialog = BlockingDialog(self.tr('Switch Scenario'), self.tr('Preparing switch...'))
        progress_dialog.force_show_and_paint()

        self.switch_task = ScenarioSwitchTask(task_name,
                                              electorate_layer=electorate_registry.source_layer,
                                              meshblock_layer=self.meshblock_layer,
                                              meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                              scenario_registry=self.scenario_registry,
                                              scenario=scenario)
        self.staged_task = UpdateStagedElectoratesTask(task_name,
                                                       meshblock_layer=self.meshblock_layer,
                                                       meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                                       scenario_registry=self.scenario_registry,
                                                       scenario=self.context.scenario,
                                                       task=self.context.task)
        self.staged_task.addSubTask(self.switch_task, subTaskDependency=QgsTask.ParentDependsOnSubTask)

        progress_dialog.deleteLater()

        self.staged_task.taskCompleted.connect(
            partial(self.report_success, self.tr('Successfully switched to “{}”').format(scenario_name)))
        self.staged_task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Error while switching to “{}”').format(scenario_name)))

        self.progress_item = MessageBarProgressItem(self.tr('Switching to {}').format(scenario_name), iface=self.iface)
        self.staged_task.progressChanged.connect(self.progress_item.set_progress)
        self.staged_task.taskCompleted.connect(self.progress_item.close)
        self.staged_task.taskTerminated.connect(self.progress_item.close)

        QgsApplication.taskManager().addTask(self.staged_task)

        self.context.set_scenario(scenario)

    def scenario_changed(self):
        """
        Triggered when the current scenario changes
        """
        self.meshblock_scenario_bridge.scenario = self.context.scenario
        self.update_dock_title()
        self.refresh_canvases()

    def create_new_scenario_name_dlg(self, existing_name: Optional[str],
                                     initial_scenario_name: str) -> QgsNewNameDialog:
        """
        Creates a dialog for entering a new scenario name
        """
        existing_names = list(self.scenario_registry.scenario_titles().keys())
        dlg = QgsNewNameDialog(existing_name, initial_scenario_name,
                               existing=existing_names, parent=self.iface.mainWindow())
        dlg.setOverwriteEnabled(False)
        dlg.setHintString(self.tr('Enter name for new scenario'))
        dlg.setConflictingNameWarning(self.tr('A scenario with this name already exists!'))
        return dlg

    def branch_scenario(self):
        """
        Branches the current scenario to a new scenario
        """
        current_scenario_name = self.context.get_name_for_current_scenario()
        dlg = self.create_new_scenario_name_dlg(existing_name=current_scenario_name,
                                                initial_scenario_name=self.tr('{} Copy').format(current_scenario_name))
        dlg.setWindowTitle(self.tr('Branch to New Scenario'))
        if dlg.exec_():
            progress_dialog = BlockingDialog(self.tr('Branching Scenario'), self.tr('Branching scenario...'))
            progress_dialog.force_show_and_paint()

            res, error = self.scenario_registry.branch_scenario(scenario_id=self.context.scenario,
                                                                new_scenario_name=dlg.name())
            if not res:
                self.report_failure(error)
            else:
                self.report_success(self.tr('Branched scenario to “{}”').format(dlg.name()))
                self.context.set_scenario(res)

    def import_scenario(self):
        """
        Import scenario from another database
        """
        last_path = QgsSettings().value('redistricting/last_import_path', QDir.homePath())

        source, _filter = QFileDialog.getOpenFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                      self.tr('Import Scenario from Database'), last_path,
                                                      filter='Database Files (*.gpkg)')
        if not source:
            return

        QgsSettings().setValue('redistricting/last_import_path', source)

        foreign_scenario_layer = QgsVectorLayer('{}|layername=scenarios'.format(source), 'foreign_scenarios')
        if not foreign_scenario_layer.isValid():
            self.report_failure(self.tr('Could not import scenarios from “{}”').format(source))
            return
        meshblock_electorates_uri = '{}|layername=meshblock_electorates'.format(source)
        foreign_meshblock_electorates_layer = QgsVectorLayer(meshblock_electorates_uri, 'foreign_meshblock_electorates')
        if not foreign_meshblock_electorates_layer.isValid():
            self.report_failure(self.tr('Could not import scenarios from “{}”').format(source))
            return

        source_registry = ScenarioRegistry(source_layer=foreign_scenario_layer,
                                           id_field='scenario_id',
                                           name_field='name',
                                           meshblock_electorate_layer=foreign_meshblock_electorates_layer)
        dlg = ScenarioSelectionDialog(scenario_registry=source_registry,
                                      parent=self.iface.mainWindow())
        dlg.setWindowTitle(self.tr('Import Scenario from Database'))
        if not dlg.exec_():
            return

        source_scenario_id = dlg.selected_scenario()
        source_scenario_name = source_registry.get_scenario_name(source_scenario_id)

        dlg = self.create_new_scenario_name_dlg(existing_name=None,
                                                initial_scenario_name=source_scenario_name)
        dlg.setWindowTitle(self.tr('Import Scenario from Database'))
        dlg.setHintString(self.tr('Enter name for imported scenario'))
        if not dlg.exec_():
            return

        new_scenario_name = dlg.name()

        dlg = BlockingDialog(self.tr('Import Scenario'), self.tr('Importing scenario...'))
        dlg.force_show_and_paint()
        result, error = self.scenario_registry.import_scenario_from_other_registry(source_registry=source_registry,
                                                                                   source_scenario_id=source_scenario_id,
                                                                                   new_scenario_name=new_scenario_name)
        if not result:
            self.report_failure(error)
        else:
            self.report_success(
                self.tr('Successfully imported “{}” to “{}”').format(source_scenario_name, new_scenario_name))

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

    def reset(self):
        """
        Resets the plugin, clearing the current project and stopping the redistrict operation
        """
        QgsProject.instance().clear()
        self.is_redistricting = False
        self.electorate_layer = None
        self.meshblock_layer = None
        self.quota_layer = None
        self.scenario_layer = None
        self.meshblock_electorate_layer = None
        self.user_log_layer = None
        self.begin_action.setChecked(False)
        self.db_source = None
        self.scenario_registry = None
        self.context = None
        self.meshblock_scenario_bridge = None

        self.dock.deleteLater()
        self.dock = None

        self.redistricting_toolbar.deleteLater()
        self.redistricting_toolbar = None

    def export_database(self):
        """
        Exports the current database using a background task
        """
        settings = QgsSettings()
        last_path = settings.value('redistricting/last_export_path', QDir.homePath())

        destination, _filter = QFileDialog.getSaveFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                           self.tr('Export Database'), last_path,
                                                           filter='Database Files (*.gpkg)')
        if not destination:
            return

        if not destination.endswith('.gpkg'):
            destination += '.gpkg'

        settings.setValue('redistricting/last_export_path', destination)

        prev_source = self.db_source
        self.reset()

        self.copy_task = CopyFileTask(self.tr('Exporting database'), {prev_source: destination})
        self.copy_task.taskCompleted.connect(
            partial(self.report_success, self.tr('Exported database to “{}”').format(destination)))
        self.copy_task.taskTerminated.connect(self.copy_task_failed)

        QgsApplication.taskManager().addTask(self.copy_task)

    def copy_task_failed(self):
        """
        Triggered on an error while copying files
        """
        error = self.copy_task.error
        self.report_failure(self.tr('Error while exporting database: {}').format(error))

    def import_master_database(self):
        """
        Imports a new master database, replacing the current database
        """
        settings = QgsSettings()
        last_path = settings.value('redistricting/last_import_path', QDir.homePath())

        source, _filter = QFileDialog.getOpenFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                      self.tr('Import Master Database'), last_path,
                                                      filter='Database Files (*.gpkg)')
        if not source:
            return

        settings.setValue('redistricting/last_import_path', source)

        dlg = ConfirmationDialog(self.tr('Import Master Database'),
                                 self.tr(
                                     'Importing a new master database will completely replace the existing district database.\n\nThis action cannot be reversed!\n\nEnter \'I ACCEPT\' to continue.'),
                                 self.tr('I ACCEPT'), parent=self.iface.mainWindow())
        if not dlg.exec_():
            return

        QMessageBox.warning(self.iface.mainWindow(), self.tr('Import Master Database'),
                            self.tr(
                                'Before importing a master database you must make a backup copy of the current database.\n\nClick OK, and then select a path for this backup.'))

        # force backup of existing database
        last_backup_path = settings.value('redistricting/last_backup_path', QDir.homePath())
        destination, _filter = QFileDialog.getSaveFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                           self.tr('Backup Current Database'), last_backup_path,
                                                           filter='Database Files (*.gpkg)')
        if not destination:
            return

        settings.setValue('redistricting/last_backup_path', destination)

        prev_source = self.db_source
        self.reset()

        if QFile.exists(destination):
            if not QFile.remove(destination):
                self.report_failure(self.tr('Could not backup current database to “{}”').format(destination))
                return

        if not QFile.copy(prev_source, destination):
            self.report_failure(self.tr('Could not backup current database to “{}”').format(destination))
            return

        if not QFile.remove(prev_source):
            self.report_failure(self.tr('Could not remove current master database at “{}”').format(prev_source))

        if not QFile.copy(source, prev_source):
            self.report_failure(self.tr('Critical error occurred while replacing master database'))
        else:
            self.report_success(self.tr('New master database imported successfully'))

    def create_new_electorate(self):
        """
        Triggered when creating a new electorate
        """
        registry = self.get_district_registry()
        dlg = CreateElectorateDialog(registry=registry,
                                     context=self.context, parent=self.iface.mainWindow())
        if not dlg.exec_():
            return

        new_name = dlg.name()
        new_code = dlg.code()

        res, error = registry.create_electorate(new_electorate_code=new_code, new_electorate_name=new_name)
        if not res:
            self.report_failure(error)
        else:
            self.report_success(self.tr('Created electorate “{}”').format(new_name))

    def deprecate_electorate(self):
        """
        Triggered when deprecating an electorate
        """
        registry = self.get_district_registry()
        dlg = DeprecateElectorateDialog(electorate_registry=registry,
                                        parent=self.iface.mainWindow())
        if not dlg.exec_():
            return

        electorate_id = dlg.selected_district()
        electorate_type = registry.get_district_type(electorate_id)

        mbs = [str(f['meshblock_number']) for f in
               self.scenario_registry.electorate_meshblocks(electorate_id=electorate_id,
                                                            electorate_type=electorate_type,
                                                            scenario_id=self.context.scenario)]
        if mbs:
            warning_string = ', '.join(mbs[:5])
            if len(mbs) > 5:
                warning_string += '...'
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Deprecate Electorate'),
                                self.tr(
                                    'Cannot deprecate an electorate which has meshblocks assigned!') + '\n\n' +
                                self.tr('Assigned meshblocks include:') + ' ' + warning_string)
            return
        else:
            registry.toggle_electorate_deprecation(electorate_id)

    def validate_electorates(self):
        """
        Validate electorates
        """
        electorate_registry = self.get_district_registry()
        task_name = self.tr('Validating Electorates')

        progress_dialog = BlockingDialog(self.tr('Validating Electorates'), self.tr('Preparing validation...'))
        progress_dialog.force_show_and_paint()

        self.validation_task = ValidationTask(task_name,
                                              electorate_registry=electorate_registry,
                                              meshblock_layer=self.meshblock_layer,
                                              meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                              scenario_registry=self.scenario_registry,
                                              scenario=self.context.scenario,
                                              task=self.context.task)

        progress_dialog.deleteLater()

        self.validation_task.taskCompleted.connect(self.validation_complete)
        self.validation_task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Validation failed')))

        QgsApplication.taskManager().addTask(self.validation_task)

    def validation_complete(self):
        """
        Triggered on validation task complete
        """
        self.report_success(self.tr('Validation complete'))
        results = self.validation_task.results
        self.dock.show_validation_results(results=results)

    def view_log(self):
        """
        Shows the user interaction log
        """
        self.iface.showAttributeTable(self.user_log_layer)

    def export_electorates(self):
        """
        Exports the final electorates to a database package
        """
        settings = QgsSettings()
        last_export_path = settings.value('redistricting/last_electorate_export_path', QDir.homePath())

        destination, _filter = QFileDialog.getSaveFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                           self.tr('Export Electorates'), last_export_path,
                                                           filter='Database Files (*.gpkg)')
        if not destination:
            return

        if not destination.endswith('.gpkg'):
            destination += '.gpkg'

        settings.setValue('redistricting/last_electorate_export_path', destination)

        electorate_registry = self.get_district_registry()
        task_name = self.tr('Exporting Electorates')

        progress_dialog = BlockingDialog(self.tr('Exporting Electorates'), self.tr('Preparing export...'))
        progress_dialog.force_show_and_paint()

        self.export_task = ExportTask(task_name=task_name, dest_file=destination,
                                      electorate_registry=electorate_registry,
                                      meshblock_layer=self.meshblock_layer,
                                      meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                                      scenario_registry=self.scenario_registry,
                                      scenario=self.context.scenario, user_log_layer=self.user_log_layer)

        self.export_task.taskCompleted.connect(
            partial(self.report_success, self.tr('Export complete')))
        self.export_task.taskTerminated.connect(self.__export_failed)

        QgsApplication.taskManager().addTask(self.export_task)

    def __export_failed(self):
        """
        Triggered on export failure
        """
        self.report_failure(self.tr('Export failed: {}').format(self.export_task.message))
