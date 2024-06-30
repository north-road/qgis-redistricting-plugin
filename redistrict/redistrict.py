"""
LINZ Redistricting Plugin
"""

# pylint: disable=too-many-lines,too-many-statements

import os.path
from functools import partial
from typing import (
    Optional,
    List
)
from qgis.PyQt import sip
from qgis.PyQt.QtCore import (
    QObject,
    Qt,
    QUrl,
    QDir,
    QFile,
    QSettings,
    QTranslator,
    QCoreApplication,
    QThread
)
from qgis.PyQt.QtGui import (
    QDesktopServices,
    QKeySequence
)
from qgis.PyQt.QtWidgets import (
    QToolBar,
    QAction,
    QMessageBox,
    QToolButton,
    QMenu,
    QFileDialog,
    QShortcut,
    QDockWidget,
    QWidget,
    QLineEdit
)
from qgis.core import (NULL,
                       QgsMessageLog,
                       QgsApplication,
                       QgsProject,
                       QgsVectorLayer,
                       QgsMapThemeCollection,
                       QgsExpressionContextUtils,
                       Qgis,
                       QgsSettings,
                       QgsTask,
                       QgsProviderRegistry)
from qgis.gui import (
    QgisInterface,
    QgsMapTool,
    QgsNewNameDialog,
    QgsMapCanvas
)
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
from .gui.audio_utils import AudioUtils
from .gui.district_settings_dialog import (DistrictSettingsDialog,  # pylint: disable=unused-import
                                           SETTINGS_AUTH_CONFIG_KEY)
from .linz.interactive_redistrict_decorator import CentroidDecoratorFactory
from .linz.linz_redistricting_dock_widget import LinzRedistrictingDockWidget
from .linz.linz_validation_results_dock_widget import LinzValidationResultsDockWidget
from .linz.linz_redistrict_gui_handler import LinzRedistrictGuiHandler
from .linz.scenario_selection_dialog import ScenarioSelectionDialog
from .linz.scenario_comparison_dialog import ScenarioComparisonDialog
from .linz.db_utils import CopyFileTask
from .linz.create_electorate_dialog import CreateElectorateDialog
from .linz.deprecate_electorate_dialog import DeprecateElectorateDialog
from .linz.scenario_switch_task import ScenarioSwitchTask
from .linz.staged_electorate_update_task import UpdateStagedElectoratesTask
from .linz.linz_mb_scenario_bridge import LinzMeshblockScenarioBridge
from .linz.validation_task import ValidationTask
from .linz.export_task import ExportTask
from .linz.nz_electoral_api import ConcordanceItem, BoundaryRequest, get_api_connector
from .linz.api_request_queue import ApiRequestQueue
from .linz.electorate_changes_queue import ElectorateEditQueue
from .linz.population_dock_widget import SelectedPopulationDockWidget
from .linz.compare_scenarios_task import CompareScenariosTask


VERSION = '0.1'


class LinzRedistrict(QObject):  # pylint: disable=too-many-public-methods
    """QGIS Plugin Implementation."""

    TASK_GN = 'GN'
    TASK_GS = 'GS'
    TASK_M = 'M'

    MESHBLOCK_NUMBER_FIELD = 'meshblock_no'

    USE_2018_MESHBLOCKS = False

    SIMPLIFIED_MODE_TOOLBAR_SCALE = 1.4

    def __init__(self, iface: QgisInterface):  # pylint: disable=too-many-statements
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
            f'{locale}.qm')

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.redistricting_menu = None
        self.redistricting_toolbar = None
        self._enter_simplified_action: Optional[QAction] = None
        self.open_settings_action = None
        self.interactive_redistrict_action = None
        self.redistrict_selected_action = None
        self.start_editing_action = None
        self.save_edits_action = None
        self.rollback_edits_action = None
        self.undo_action = None
        self.redo_action = None
        self.begin_action = None
        self.stats_tool_action = None
        self.validate_action = None
        self.show_population_dock_action = None
        self.theme_menu = None
        self.new_themed_view_menu = None
        self.tool = None
        self.dock = None
        self.validation_results_dock = None
        self.scenarios_tool_button = None
        self.context: Optional[LinzRedistrictingContext] = None
        self.current_dock_electorate = None
        self.help_action = None
        self.scenarios_menu = None
        self.electorate_menu = None
        self.database_menu = None
        self.rebuild_action = None
        self.export_action = None
        self.toggle_simplified_mode_action: Optional[QShortcut] = None
        self.simplified_toolbar: Optional[QToolBar] = None
        self._exit_simplified_action: Optional[QAction] = None
        self._is_simplified = False
        self._previously_visible_toolbars: List[QToolBar] = []
        self._previously_visible_docks: List[QDockWidget] = []
        self._previously_visible_statusbar_widgets: List[QWidget] = []

        self.is_redistricting = False
        self.electorate_layer = None
        self.electorate_layer_labels = None
        self.meshblock_layer = None
        self.scenario_layer = None
        self.quota_layer = None
        self.meshblock_electorate_layer = None
        self.user_log_layer = None
        self.scenario_registry = None
        self.meshblock_scenario_bridge = None
        self.db_source = os.path.join(self.plugin_dir,
                                      'db', 'nz_db.gpkg')
        self.electorate_edit_queue = None
        self.task = None
        self.copy_task = None
        self.switch_task = None
        self.staged_task = None
        self.validation_task = None
        self.export_task = None
        self.compare_task = None
        self.progress_item = None
        self.switch_menu = None
        self.selected_population_dock = None
        self.api_request_queue = ApiRequestQueue()
        self.api_request_queue.result_fetched.connect(self.api_request_finished)
        self.api_request_queue.error.connect(self.stats_api_error)

        # reset the plugin when the project is unloaded
        if hasattr(QgsProject.instance(), 'cleared'):
            QgsProject.instance().cleared.connect(self.reset)
        QgsProject.instance().layerWillBeRemoved.connect(self.layer_will_be_removed)

        self.iface.mapCanvas().setPreviewJobsEnabled(False)

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

        self.begin_action = QAction(self.tr('Toggle Redistricting'))
        self.begin_action.toggled.connect(self.begin_redistricting)
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
        self._enter_simplified_action = QAction(
            self.tr('Simplified Mode')
        )
        self._enter_simplified_action.triggered.connect(
            self._toggle_simplified)
        self.redistricting_menu.addAction(
            self._enter_simplified_action)

        self.open_settings_action = QAction(GuiUtils.get_icon(
            'open_settings.svg'), self.tr('Settings...'))
        self.open_settings_action.triggered.connect(
            self.open_settings)
        self.redistricting_menu.addAction(
            self.open_settings_action)

        self.redistricting_menu.addSeparator()

        self.help_action = QAction(GuiUtils.get_icon('help.svg'), self.tr('Help'))
        self.help_action.triggered.connect(self.show_help)

        self.redistricting_menu.addAction(self.help_action)

        about_action = QAction(self.tr('About...'), parent=self.redistricting_menu)
        about_action.triggered.connect(self.about)
        self.redistricting_menu.addAction(about_action)

        self.iface.mainWindow().menuBar().addMenu(self.redistricting_menu)

        self.toggle_simplified_mode_action = QShortcut(
            QKeySequence('Alt+F10'), self.iface.mainWindow(),
            context=Qt.WindowShortcut)
        self.toggle_simplified_mode_action.setObjectName('Show simplified')
        self.toggle_simplified_mode_action.activated.connect(self._toggle_simplified)

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

        self.undo_action = QAction(GuiUtils.get_icon('undo.svg'), self.tr('Undo'))
        self.undo_action.triggered.connect(self.meshblock_layer.undoStack().undo)
        self.redistricting_toolbar.addAction(self.undo_action)
        self.undo_action.setEnabled(False)

        self.redo_action = QAction(GuiUtils.get_icon('redo.svg'), self.tr('Redo'))
        self.redo_action.triggered.connect(self.meshblock_layer.undoStack().redo)
        self.redistricting_toolbar.addAction(self.redo_action)
        self.redo_action.setEnabled(False)

        self.redistricting_toolbar.addSeparator()

        self.interactive_redistrict_action = QAction(GuiUtils.get_icon(
            'interactive_redistrict.svg'), self.tr('Interactive Redistrict'))
        self.interactive_redistrict_action.setCheckable(True)
        self.interactive_redistrict_action.toggled.connect(
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

        self.selected_population_dock = SelectedPopulationDockWidget(self.iface, self.meshblock_layer)
        self.selected_population_dock.set_task(self.context.task)
        self.selected_population_dock.set_district_registry(self.get_district_registry())
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.selected_population_dock)
        self.selected_population_dock.setFloating(True)
        self.selected_population_dock.setUserVisible(False)

        self.show_population_dock_action = QAction(GuiUtils.get_icon(
            'population.svg'), self.tr('Show Selected Population Window'))
        self.show_population_dock_action.setCheckable(True)
        self.selected_population_dock.setToggleVisibilityAction(self.show_population_dock_action)
        self.redistricting_toolbar.addAction(
            self.show_population_dock_action)

        self.iface.addToolBar(self.redistricting_toolbar)
        GuiUtils.float_toolbar_over_widget(self.redistricting_toolbar,
                                           self.iface.mapCanvas())

        self.toggle_redistrict_actions()

        self.dock = LinzRedistrictingDockWidget(context=self.context)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.validation_results_dock = LinzValidationResultsDockWidget(self.iface)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.validation_results_dock)
        self.iface.mainWindow().tabifyDockWidget(self.dock, self.validation_results_dock)
        self.dock.setUserVisible(True)

        self.context.scenario_changed.connect(self.scenario_changed)

        self.scenarios_tool_button = QToolButton()
        self.scenarios_tool_button.setAutoRaise(True)
        self.scenarios_tool_button.setToolTip('Scenarios')
        self.scenarios_tool_button.setIcon(GuiUtils.get_icon(icon='scenarios.svg'))
        self.scenarios_tool_button.setPopupMode(QToolButton.InstantPopup)

        self.scenarios_menu = QMenu(parent=self.scenarios_tool_button)
        switch_scenario_action = QAction(self.tr('Switch to Existing Scenario...'), parent=self.scenarios_menu)
        switch_scenario_action.triggered.connect(self.select_current_scenario)
        self.scenarios_menu.addAction(switch_scenario_action)

        self.scenarios_menu.addSeparator()
        update_scenario_action = QAction(self.tr('Update Statistics for Scenario...'), parent=self.scenarios_menu)
        update_scenario_action.triggered.connect(self.update_stats_for_scenario)
        self.scenarios_menu.addAction(update_scenario_action)

        self.scenarios_menu.addSeparator()

        branch_scenario_action = QAction(self.tr('Branch to New Scenario...'), parent=self.scenarios_menu)
        branch_scenario_action.triggered.connect(self.branch_scenario)
        self.scenarios_menu.addAction(branch_scenario_action)
        import_scenario_action = QAction(self.tr('Import Scenario from Database...'), parent=self.scenarios_menu)
        import_scenario_action.triggered.connect(self.import_scenario)
        self.scenarios_menu.addAction(import_scenario_action)

        compare_scenarios_action = QAction(self.tr('Compare Scenarios...'), parent=self.scenarios_menu)
        compare_scenarios_action.triggered.connect(self.compare_scenarios)
        self.scenarios_menu.addAction(compare_scenarios_action)

        self.scenarios_tool_button.setMenu(self.scenarios_menu)
        self.dock.dock_toolbar().addWidget(self.scenarios_tool_button)

        self.validate_action = QAction(GuiUtils.get_icon('validate.svg'), self.tr('Validate Electorates'))
        self.validate_action.triggered.connect(self.validate_electorates)
        self.dock.dock_toolbar().addAction(self.validate_action)

        options_menu = QMenu(parent=self.dock.dock_toolbar())

        self.electorate_menu = QMenu(self.tr('Manage Electorates'), parent=options_menu)

        new_electorate_action = QAction(self.tr('Create New Electorate...'), parent=self.electorate_menu)
        new_electorate_action.triggered.connect(self.create_new_electorate)
        self.electorate_menu.addAction(new_electorate_action)

        deprecate_electorate_action = QAction(self.tr('Deprecate Electorate...'), parent=self.electorate_menu)
        deprecate_electorate_action.triggered.connect(self.deprecate_electorate)
        self.electorate_menu.addAction(deprecate_electorate_action)

        options_menu.addMenu(self.electorate_menu)

        self.database_menu = QMenu(self.tr('Database'), parent=options_menu)
        export_master_action = QAction(self.tr('Export Database...'), parent=self.database_menu)
        export_master_action.triggered.connect(self.export_database)
        self.database_menu.addAction(export_master_action)
        import_master_action = QAction(self.tr('Import Master Database...'), parent=self.database_menu)
        import_master_action.triggered.connect(self.import_master_database)
        self.database_menu.addAction(import_master_action)
        load_meshblocks_action = QAction(self.tr('Load New Meshblocks...'), parent=self.database_menu)
        load_meshblocks_action.triggered.connect(self.load_meshblocks)
        self.database_menu.addAction(load_meshblocks_action)

        options_menu.addMenu(self.database_menu)

        self.rebuild_action = QAction(self.tr('Rebuild Electorates'), parent=options_menu)
        self.rebuild_action.triggered.connect(self.rebuild_electorates)
        options_menu.addAction(self.rebuild_action)

        self.export_action = QAction(self.tr('Export Electorates...'), parent=options_menu)
        self.export_action.triggered.connect(self.export_electorates)
        options_menu.addAction(self.export_action)

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

        self.dock.dock_toolbar().addAction(self.help_action)

        self.set_task(QgsSettings().value('redistricting/last_task', self.TASK_GN))

    # pylint: disable=too-many-branches,too-many-return-statements
    def begin_redistricting(self, checked):
        """
        Starts the redistricting operation, opening toolbars and docks as needed
        """
        if not checked:
            if not self.is_redistricting:
                return

            if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
                self.report_failure(self.tr('Cannot stop redistricting while unsaved changes are present'))
                self.begin_action.setChecked(True)
                return

            self.reset(False)
            return

        if self.is_redistricting:
            return

        # matching layers
        try:
            self.electorate_layer = QgsProject.instance().mapLayersByName(
                'Electorates')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "Electorates" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        try:
            self.electorate_layer_labels = QgsProject.instance().mapLayersByName(
                'Electorate Names and Stats')[0]
        except IndexError:
            pass

        try:
            self.meshblock_layer = QgsProject.instance().mapLayersByName(
                'Meshblocks')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "Meshblocks" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        try:
            self.quota_layer = QgsProject.instance().mapLayersByName(
                'quotas')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "quotas" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        try:
            self.scenario_layer = QgsProject.instance().mapLayersByName(
                'scenarios')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "scenarios" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        try:
            self.meshblock_electorate_layer = QgsProject.instance().mapLayersByName(
                'meshblock_electorates')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "meshblock_electorates" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        try:
            self.user_log_layer = QgsProject.instance().mapLayersByName(
                'user_log')[0]
        except IndexError:
            self.report_failure(self.tr(
                'Cannot find "user_log" layer - please open the redistricting project first'))
            self.begin_action.setChecked(False)
            return

        if self.is_editing():
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Begin Redistricting'),
                                self.tr(
                                    'Meshblock layer has a previous edit session open. Please save or discard changes to the meshblock layer and cancel editing on this layer.'))
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
        self.context.task = QgsSettings().value('redistricting/last_task', self.TASK_GN)

        last_scenario = QgsSettings().value('redistricting/last_scenario', 1,
                                            int)
        if not self.scenario_registry.scenario_exists(last_scenario):
            # uh oh - scenario doesn't exist anymore!
            QMessageBox.critical(self.iface.mainWindow(), 'Missing Scenario',
                                 f'The previously used scenario ({last_scenario}) no longer exists! Please rebuild the database from another scenario.')
            self.context.scenario = 1
        else:
            self.context.scenario = QgsSettings().value('redistricting/last_scenario', 1, int)

        self.meshblock_layer.layerModified.connect(self.update_layer_modified_actions)
        self.meshblock_layer.editingStarted.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.editingStopped.connect(self.toggle_redistrict_actions)
        self.meshblock_layer.selectionChanged.connect(self.toggle_redistrict_actions)

        self.meshblock_scenario_bridge = LinzMeshblockScenarioBridge(meshblock_layer=self.meshblock_layer,
                                                                     meshblock_scenario_layer=self.meshblock_electorate_layer,
                                                                     meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD)
        self.meshblock_scenario_bridge.scenario = self.context.scenario

        self.create_redistricting_ui()

        self.iface.setActiveLayer(self.meshblock_layer)

        self.progress_item = MessageBarProgressItem(self.tr('Preparing redistricting'), iface=self.iface)
        self.switch_task.progressChanged.connect(self.progress_item.set_progress)
        self.switch_task.taskCompleted.connect(self.progress_item.close)
        self.switch_task.taskCompleted.connect(partial(self.start_editing_action.setEnabled, True))
        self.switch_task.taskTerminated.connect(self.progress_item.close)
        self.electorate_edit_queue = ElectorateEditQueue(electorate_layer=self.electorate_layer,
                                                         user_log_layer=self.user_log_layer)

        self.meshblock_layer.undoStack().indexChanged.connect(
            self.electorate_edit_queue.sync_to_meshblock_undostack_index)
        self.meshblock_layer.undoStack().indexChanged.connect(
            self.update_undo_actions)
        self.meshblock_layer.beforeCommitChanges.connect(
            self.electorate_edit_queue.clear)
        self.meshblock_layer.beforeRollBack.connect(
            self.electorate_edit_queue.rollback)

    # pylint: enable=too-many-branches,too-many-return-statements

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        self.begin_redistricting(False)

        if self.redistricting_toolbar is not None:
            self.redistricting_toolbar.deleteLater()
        if self.dock is not None:
            self.dock.deleteLater()
        if self.validation_results_dock is not None:
            self.validation_results_dock.deleteLater()
        self.redistricting_menu.deleteLater()
        if self.tool is not None:
            self.tool.deleteLater()
        if self.toggle_simplified_mode_action and not sip.isdeleted(self.toggle_simplified_mode_action):
            self.toggle_simplified_mode_action.deleteLater()
            self.toggle_simplified_mode_action = None
        if self._enter_simplified_action and not sip.isdeleted(self._enter_simplified_action):
            self._enter_simplified_action.deleteLater()
            self._enter_simplified_action = None
        if self.simplified_toolbar and not sip.isdeleted(self.simplified_toolbar):
            self.simplified_toolbar.deleteLater()
            self.simplified_toolbar = None

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
        self.update_undo_actions()

    def update_undo_actions(self):
        """
        Enables or disables undo actions based on their applicability
        """
        self.undo_action.setEnabled(self.meshblock_layer.undoStack().canUndo())
        self.redo_action.setEnabled(self.meshblock_layer.undoStack().canRedo())

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
            self.iface.setActiveLayer(self.meshblock_layer)
        else:
            tools.stopEditing(self.meshblock_layer, allowCancel=False)
        self.set_current_tool(tool=None)

    def open_settings(self):
        """
        Open the settings dialog
        """
        dlg = DistrictSettingsDialog()
        dlg.exec_()

        self.api_request_queue.set_frequency(
            QgsSettings().value('redistrict/check_every', '30', int, QgsSettings.Plugins))
        AudioUtils.update_settings()

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

    def is_editing(self):
        """
        Returns true if user is currently editing meshblocks
        """
        return self.meshblock_layer.isEditable()

    def enable_task_switches(self, enabled):
        """
        Enables or disables the task switching commands
        """
        try:
            self.begin_action.setEnabled(enabled)
            for action in self.switch_menu.actions():
                action.setEnabled(enabled)
            for action in self.scenarios_menu.actions():
                action.setEnabled(enabled)
            for action in self.electorate_menu.actions():
                action.setEnabled(enabled)
            for action in self.database_menu.actions():
                action.setEnabled(enabled)
            self.redistrict_selected_action.setEnabled(enabled)
            self.interactive_redistrict_action.setEnabled(enabled)
            self.start_editing_action.setEnabled(enabled)
            self.save_edits_action.setEnabled(enabled)
            self.rollback_edits_action.setEnabled(enabled)
            self.undo_action.setEnabled(enabled)
            self.redo_action.setEnabled(enabled)
            self.validate_action.setEnabled(enabled)
            self.export_action.setEnabled(enabled)
            self.rebuild_action.setEnabled(enabled)
            if enabled:
                self.toggle_redistrict_actions()
        except (AttributeError, RuntimeError):
            pass

    def set_task(self, task: str) -> bool:
        """
        Sets the current task
        :param task: task, eg 'GN','GS' or 'M'
        :returns True if task switch was begun
        """
        if self.is_editing():
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Switch Task'),
                                self.tr(
                                    'Cannot switch task while editing meshblocks. Save or cancel the current edits and try again.'))
            return False

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
        self.switch_task.taskCompleted.connect(self.refresh_canvases)
        self.switch_task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Error while switching to “{}”').format(task_name)))

        QgsApplication.taskManager().addTask(self.switch_task)
        return True

    def set_task_and_show_progress(self, task):
        """
        Sets the current task, showing a progress bar to report status
        """
        if not self.set_task(task):
            return
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
        QgsSettings().setValue('redistricting/last_task', self.context.task)

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
        if self.selected_population_dock:
            self.selected_population_dock.set_task(self.context.task)
            self.selected_population_dock.set_district_registry(self.get_district_registry())

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
                                        electorate_changes_queue=self.electorate_edit_queue,
                                        electorate_layer=self.electorate_layer,
                                        electorate_layer_field='electorate_id',
                                        task=self.context.task,
                                        user_log_layer=self.user_log_layer,
                                        scenario=self.context.scenario)
        handler.redistrict_occured.connect(self.refresh_dock_stats)
        handler.operation_ended.connect(self.redistrict_occurred)
        return handler

    def get_gui_handler(self) -> LinzRedistrictGuiHandler:
        """
        Returns the current redistricting GUI handler
        """
        handler = LinzRedistrictGuiHandler(redistrict_dock=self.dock,
                                           district_registry=self.get_district_registry(),
                                           request_population_callback=self.update_stats_for_scenario)
        handler.current_district_changed.connect(self.current_dock_electorate_changed)
        return handler

    def current_dock_electorate_changed(self, electorate):
        """
        Triggered when electorate shown in dock changes
        :param electorate: current electorate shown
        """
        self.current_dock_electorate = electorate

    def redistrict_occurred(self):
        """
        Triggered whenever a redistrict occurs
        """
        if self.electorate_layer_labels:
            self.electorate_layer_labels.triggerRepaint()
        self.refresh_dock_stats()

    def refresh_dock_stats(self):
        """
        Refreshes the stats shown in the dock widget
        """
        handler = self.get_gui_handler()
        handler.show_stats_for_district(self.current_dock_electorate)
        if self.selected_population_dock:
            self.selected_population_dock.update()

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

    def interactive_redistrict(self, active: bool):
        """
        Interactively redistrict the currently selected meshblocks
        :param active: True if tool was activated
        """
        if active:
            district_registry = self.get_district_registry()
            quota = district_registry.get_quota_for_district_type(self.context.task)
            tool = InteractiveRedistrictingTool(self.iface.mapCanvas(), handler=self.get_handler(),
                                                district_registry=district_registry,
                                                decorator_factory=CentroidDecoratorFactory(
                                                    electorate_layer=self.electorate_layer,
                                                    meshblock_layer=self.meshblock_layer,
                                                    task=self.context.task,
                                                    quota=quota))
            self.set_current_tool(tool=tool)
            tool.setAction(self.interactive_redistrict_action)
        else:
            if self.tool is not None:
                # Disconnect from old tool
                if not sip.isdeleted(self.tool):
                    self.tool.deactivated.disconnect(self.tool_deactivated)
                    self.tool.deleteLater()
                self.tool = None
            # switch to 'pan' tool
            self.iface.actionPan().trigger()

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
        dlg.set_selected_scenario(self.context.scenario)
        if dlg.exec_():
            self.switch_scenario(dlg.selected_scenario())
        dlg.deleteLater()

    def switch_scenario(self, scenario: int, title=None, description=None):
        """
        Switches the current scenario to a new scenario
        :param scenario: new scenario ID
        """
        if self.is_editing():
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Switch Scenario'),
                                self.tr(
                                    'Cannot switch scenario while editing meshblocks. Save or cancel the current edits and try again.'))
            return

        self.enable_task_switches(False)
        self.clear_current_views()

        electorate_registry = self.get_district_registry()
        scenario_name = self.scenario_registry.get_scenario_name(scenario)
        task_name = title if title is not None else self.tr('Switching to {}').format(scenario_name)

        if title is None:
            title = self.tr('Switch Scenario')
        if description is None:
            description = self.tr('Preparing switch...')

        for canvas in self.iface.mapCanvases():
            canvas.freeze(True)

        progress_dialog = BlockingDialog(title, description)
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
                                                       scenario=scenario,
                                                       task=self.context.task)
        self.staged_task.addSubTask(self.switch_task, subTaskDependency=QgsTask.ParentDependsOnSubTask)

        progress_dialog.deleteLater()

        def reenable_actions():
            """
            Reenables the disabled menu actions
            """
            self.enable_task_switches(True)
            for canvas in self.iface.mapCanvases():
                canvas.freeze(False)

        self.staged_task.taskCompleted.connect(
            partial(self.report_success, self.tr('Successfully switched to “{}”').format(scenario_name)))
        self.staged_task.taskCompleted.connect(reenable_actions)
        self.staged_task.taskTerminated.connect(
            partial(self.report_failure, self.tr('Error while switching to “{}”').format(scenario_name)))
        self.staged_task.taskTerminated.connect(reenable_actions)

        self.progress_item = MessageBarProgressItem(self.tr('Switching to {}').format(scenario_name), iface=self.iface)
        self.staged_task.progressChanged.connect(self.progress_item.set_progress)
        self.staged_task.taskCompleted.connect(self.progress_item.close)
        self.staged_task.taskCompleted.connect(self.refresh_canvases)
        self.staged_task.taskTerminated.connect(self.progress_item.close)

        QgsApplication.taskManager().addTask(self.staged_task)

        self.context.set_scenario(scenario)
        QgsSettings().setValue('redistricting/last_scenario', scenario)

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

    def clear_current_views(self):
        """
        Resets current statistical views, like the selected population dock
        """
        self.selected_population_dock.reset()

    def branch_scenario(self):
        """
        Branches the current scenario to a new scenario
        """
        if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
            self.report_failure(self.tr(
                'Cannot branch scenario while unsaved changes are present. Save or cancel the current edits and try again.'))
            return

        current_scenario_name = self.context.get_name_for_current_scenario()
        dlg = self.create_new_scenario_name_dlg(existing_name=current_scenario_name,
                                                initial_scenario_name=self.tr('{} Copy').format(current_scenario_name))
        dlg.setWindowTitle(self.tr('Branch to New Scenario'))
        if dlg.exec_():
            self.clear_current_views()

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

        foreign_scenario_layer = QgsVectorLayer(f'{source}|layername=scenarios', 'foreign_scenarios')
        if not foreign_scenario_layer.isValid():
            # pylint: disable=consider-using-f-string
            self.report_failure(self.tr('Could not import scenarios from “{}”').format(source))
            # pylint: enable=consider-using-f-string
            return
        meshblock_electorates_uri = f'{source}|layername=meshblock_electorates'
        foreign_meshblock_electorates_layer = QgsVectorLayer(meshblock_electorates_uri, 'foreign_meshblock_electorates')
        if not foreign_meshblock_electorates_layer.isValid():
            # pylint: disable=consider-using-f-string
            self.report_failure(self.tr('Could not import scenarios from “{}”').format(source))
            # pylint: enable=consider-using-f-string
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

        self.clear_current_views()

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

    def compare_scenarios(self):
        """
        Allows user to compare two scenarios
        """
        dlg = ScenarioComparisonDialog(scenario_registry=self.scenario_registry,
                                       parent=self.iface.mainWindow())
        if dlg.exec_():
            base_scenario = dlg.selected_base_scenario()
            secondary_scenario = dlg.selected_secondary_scenario()

            QgsSettings().setValue('redistricting/last_base_scenario', base_scenario)
            QgsSettings().setValue('redistricting/last_secondary_scenario', secondary_scenario)

            self.compare_task = CompareScenariosTask(
                task_name='Compare scenarios',
                scenario_registry=self.scenario_registry,
                meshblock_layer=self.meshblock_layer,
                meshblock_number_field_name=self.MESHBLOCK_NUMBER_FIELD,
                task=self.context.task,
                base_scenario_id=base_scenario,
                secondary_scenario_id=secondary_scenario
            )
            self.compare_task.taskCompleted.connect(
                partial(self._comparison_finished, self.compare_task))
            self.compare_task.taskTerminated.connect(
                partial(self.report_failure, self.tr('Error while comparing scenaris')))

            QgsApplication.taskManager().addTask(self.compare_task)
        dlg.deleteLater()

    def _comparison_finished(self, task: CompareScenariosTask):
        """
        Called when the scenario comparison task finishes
        """
        if task != self.compare_task:
            return

        changed_mb_layer = task.changed_meshblocks_layer
        changed_mb_layer.moveToThread(QThread.currentThread())
        QgsProject.instance().addMapLayer(changed_mb_layer)

        changed_areas_layer = task.changed_areas_layer
        changed_areas_layer.moveToThread(QThread.currentThread())
        QgsProject.instance().addMapLayer(changed_areas_layer)

        original_layer_order = QgsProject.instance().layerTreeRoot().customLayerOrder()
        new_layer_order = [changed_mb_layer, changed_areas_layer] + [layer for layer in original_layer_order if
                                                                     layer not in (
                                                                     changed_mb_layer, changed_areas_layer)]
        QgsProject.instance().layerTreeRoot().setCustomLayerOrder(new_layer_order)

        concordance = task.concordance
        request = BoundaryRequest(concordance, area=task.associated_task)
        connector = get_api_connector()
        self.api_request_queue.append_request(connector, request)

        self.compare_task = None

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

    def layer_will_be_removed(self, layer_id):
        """
        Triggered when layers are about to be removed from the project
        """
        if not self.is_redistricting:
            return

        if layer_id in (self.meshblock_layer.id(),
                        self.electorate_layer.id(),
                        self.quota_layer.id(),
                        self.scenario_layer.id(),
                        self.meshblock_electorate_layer.id(),
                        self.user_log_layer.id()):
            # oh dear - maybe user has triggered an exit of qgis without gracefully ending redistricting?
            # better do that now, and hope for the best...
            self.reset()

    def reset(self, clear_project=False):  # pylint:disable=too-many-statements, too-many-branches
        """
        Resets the plugin, clearing the current project and stopping the redistrict operation
        """
        if not self.is_redistricting:
            return

        if self.meshblock_layer:
            # PyQt will raise TypeErrors if these signals are not connected...
            try:
                self.meshblock_layer.layerModified.disconnect(self.update_layer_modified_actions)
            except TypeError:
                pass
            try:
                self.meshblock_layer.editingStarted.disconnect(self.toggle_redistrict_actions)
            except TypeError:
                pass
            try:
                self.meshblock_layer.editingStopped.disconnect(self.toggle_redistrict_actions)
            except TypeError:
                pass
            try:
                self.meshblock_layer.selectionChanged.disconnect(self.toggle_redistrict_actions)
            except TypeError:
                pass
            try:
                self.meshblock_layer.undoStack().indexChanged.disconnect(
                    self.electorate_edit_queue.sync_to_meshblock_undostack_index)
            except TypeError:
                pass
            try:
                self.meshblock_layer.undoStack().indexChanged.disconnect(
                    self.update_undo_actions)
            except TypeError:
                pass
            try:
                self.meshblock_layer.beforeCommitChanges.disconnect(
                    self.electorate_edit_queue.clear)
            except TypeError:
                pass
            try:
                self.meshblock_layer.beforeRollBack.disconnect(
                    self.electorate_edit_queue.rollback)
            except TypeError:
                pass

        self.api_request_queue.clear()
        if clear_project:
            if hasattr(QgsProject.instance(), 'cleared'):
                QgsProject.instance().cleared.disconnect(self.reset)
            QgsProject.instance().clear()
            if hasattr(QgsProject.instance(), 'cleared'):
                QgsProject.instance().cleared.connect(self.reset)
        self.is_redistricting = False
        self.electorate_layer = None
        self.electorate_layer_labels = None
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
        self.scenarios_menu = None
        self.electorate_menu = None
        self.database_menu = None
        self.export_action = None
        self.rebuild_action = None

        # TODO - block reset when changes in queue, edits enabled!!
        self.electorate_edit_queue = None

        try:
            if self.dock:
                self.dock.deleteLater()
        except RuntimeError:
            pass
        self.dock = None

        try:
            if self.validation_results_dock:
                self.validation_results_dock.deleteLater()
        except RuntimeError:
            pass
        self.validation_results_dock = None

        try:
            if self.redistricting_toolbar:
                self.redistricting_toolbar.deleteLater()
        except RuntimeError:
            pass
        self.redistricting_toolbar = None

        try:
            if self.selected_population_dock:
                self.selected_population_dock.deleteLater()
        except RuntimeError:
            pass
        self.selected_population_dock = None

        self.enable_task_switches(False)
        self.begin_action.setEnabled(True)

    def export_database(self):
        """
        Exports the current database using a background task
        """
        if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
            self.report_failure(self.tr(
                'Cannot export database while unsaved changes are present. Save or cancel the current edits and try again.'))
            return

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
        self.reset(clear_project=True)

        def give_hint():
            """
            Shows a hint to users on what action to take after exporting the database
            """
            QMessageBox.information(self.iface.mainWindow(), self.tr('Export Database'), self.tr(
                'Please reopen the redistricting project file to continue redistricting.'))

        self.copy_task = CopyFileTask(self.tr('Exporting database'), {prev_source: destination})
        self.copy_task.taskCompleted.connect(
            partial(self.report_success, self.tr('Exported database to “{}”').format(destination)))
        self.copy_task.taskCompleted.connect(give_hint)
        self.copy_task.taskTerminated.connect(self.copy_task_failed)

        QgsApplication.taskManager().addTask(self.copy_task)

    def copy_task_failed(self):
        """
        Triggered on an error while copying files
        """
        error = self.copy_task.error
        self.report_failure(self.tr('Error while exporting database: {}').format(error))

    def current_db_path(self) -> str:
        """
        Returns the currently open database path
        """
        return self.meshblock_layer.source().split('|')[0]

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

        if source == self.current_db_path():
            self.report_failure(self.tr('Cannot re-import the active database!'))
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
        self.reset(clear_project=True)

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
            QMessageBox.information(self.iface.mainWindow(), self.tr('Import Database'), self.tr(
                'Please reopen the redistricting project file to use the newly imported database.'))

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

        res, error = registry.create_electorate(new_electorate_code=new_code,
                                                new_electorate_name=new_name,
                                                initial_scenario=self.context.scenario)
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
        if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
            self.report_failure(self.tr(
                'Cannot validate while unsaved changes are present. Save or cancel the current edits and try again.'))
            return

        electorate_registry = self.get_district_registry()
        task_name = self.tr('Validating Electorates')

        self.validation_results_dock.clear()

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
        # refresh views, in case any are showing invalid electorates view
        self.refresh_canvases()

        self.validation_task.taskCompleted.connect(self.validation_complete)
        self.validation_task.taskCompleted.connect(self.refresh_canvases)
        self.validation_task.taskTerminated.connect(self.validation_failed)

        QgsApplication.taskManager().addTask(self.validation_task)
        self.validation_results_dock.setUserVisible(True)
        self.enable_task_switches(False)

    def validation_complete(self):
        """
        Triggered on validation task complete
        """
        self.report_success(self.tr('Validation complete'))
        results = self.validation_task.results
        self.validation_results_dock.show_validation_results(results=results)

        self.validation_results_dock.setUserVisible(True)
        self.validation_task = None
        self.enable_task_switches(True)

    def validation_failed(self):
        """
        Triggered on validation task failure
        """
        self.report_failure(self.tr('Validation failed'))
        self.enable_task_switches(True)

    def view_log(self):
        """
        Shows the user interaction log
        """
        self.iface.showAttributeTable(self.user_log_layer)

    def rebuild_electorates(self):
        """
        Rebuilds the current scenario from scratch
        """

        if self.is_editing():
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Rebuild Electorates'),
                                self.tr(
                                    'Cannot rebuild electorates while editing meshblocks. Save or cancel the current edits and try again.'))
            return

        self.clear_current_views()
        self.switch_scenario(self.context.scenario, title=self.tr('Rebuild Electorates'),
                             description=self.tr('Preparing rebuild...'))

    def export_electorates(self):
        """
        Exports the final electorates to a database package
        """
        if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
            self.report_failure(self.tr(
                'Cannot export electorates while unsaved changes are present. Save or cancel the current edits and try again.'))
            return

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

        self.export_task.taskCompleted.connect(self.__export_complete)
        self.export_task.taskTerminated.connect(self.__export_failed)

        QgsApplication.taskManager().addTask(self.export_task)
        self.enable_task_switches(False)

    def __export_complete(self):
        """
        Triggered on export success
        """
        self.report_success(self.tr('Export complete'))
        self.enable_task_switches(True)

    def __export_failed(self):
        """
        Triggered on export failure
        """
        self.report_failure(self.tr('Export failed: {}').format(self.export_task.message))
        self.enable_task_switches(True)

    def load_meshblocks(self):  # pylint: disable=too-many-locals,too-many-return-statements,too-many-statements
        """
        Loads a new meshblock layer
        """
        if self.is_editing():
            QMessageBox.warning(self.iface.mainWindow(), self.tr('Load New Meshblocks'),
                                self.tr(
                                    'Cannot load meshblocks while editing meshblocks. Save or cancel the current edits and try again.'))
            return

        dlg = ConfirmationDialog(self.tr('Load New Meshblocks'),
                                 self.tr(
                                     'This method has not yet been tested, and results MUST be manually validated. Please ensure you have backups of the master DB prior to running this.\n\nEnter \'I ACCEPT\' to continue.'),
                                 self.tr('I ACCEPT'), parent=self.iface.mainWindow())
        if not dlg.exec_():
            return

        settings = QgsSettings()
        last_path = settings.value('redistricting/last_mb_import_path', QDir.homePath())

        source = QFileDialog.getExistingDirectory(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                  self.tr('Load New Meshblocks'), last_path)
        if not source:
            return

        settings.setValue('redistricting/last_mb_import_path', source)

        dlg = ConfirmationDialog(self.tr('Load New Meshblocks'),
                                 self.tr(
                                     'Loading new meshblocks will completely replace the existing meshblocks in the database.\n\nThis action cannot be reversed!\n\nEnter \'I ACCEPT\' to continue.'),
                                 self.tr('I ACCEPT'), parent=self.iface.mainWindow())
        if not dlg.exec_():
            return

        QMessageBox.warning(self.iface.mainWindow(), self.tr('Load New Meshblocks'),
                            self.tr(
                                'Before loading new meshblocks you must make a backup copy of the current database.\n\nClick OK, and then select a path for this backup.'))

        # force backup of existing database
        last_backup_path = settings.value('redistricting/last_backup_path', QDir.homePath())
        destination, _filter = QFileDialog.getSaveFileName(self.iface.mainWindow(),  # pylint: disable=unused-variable
                                                           self.tr('Backup Current Database'), last_backup_path,
                                                           filter='Database Files (*.gpkg)')
        if not destination:
            return

        settings.setValue('redistricting/last_backup_path', destination)

        prev_source = self.db_source
        prev_meshblock_layer_source = self.meshblock_layer.source()
        prev_meshblock_layer_path = QgsProviderRegistry.instance().decodeUri('ogr', prev_source)['path']
        self.reset(clear_project=True)

        if QFile.exists(destination):
            if not QFile.remove(destination):
                self.report_failure(self.tr('Could not backup current database to “{}”').format(destination))
                return

        if not QFile.copy(prev_source, destination):
            self.report_failure(self.tr('Could not backup current database to “{}”').format(destination))
            return

        if self.USE_2018_MESHBLOCKS:
            assert False, 'not supported yet'
            # meshblock_number_field = 'MB2018_V1_00'
        else:
            meshblock_layer = 'MB2013_HD_Full'
            meshblock_number_field = 'MB2013'

        source_layer = QgsVectorLayer(f'{source}|layername={meshblock_layer}', 'meshblock_source')
        assert source_layer.isValid()
        non_digitized_layer = QgsVectorLayer(
            f'{prev_meshblock_layer_path}|layername=non_digitized_meshblocks', 'non_digitized')
        non_digitized = [f['meshblock_no'] for f in non_digitized_layer.getFeatures()]
        assert non_digitized

        offshore_layer = QgsVectorLayer(f'{prev_meshblock_layer_path}|layername=offshore_meshblocks',
                                        'offshore_meshblocks')
        offshore = [f['meshblock_no'] for f in offshore_layer.getFeatures()]
        assert offshore

        island_layer = QgsVectorLayer(f'{prev_meshblock_layer_path}|layername=meshblock_island',
                                      'meshblock_island')
        island = {f['meshblock_no']: f['ns_island'] for f in island_layer.getFeatures()}
        assert island

        dest_layer = QgsVectorLayer(prev_meshblock_layer_source, 'meshblock_dest')
        assert dest_layer.isValid()

        dest_layer.dataProvider().truncate()
        meshblocks = []
        for f in source_layer.getFeatures():
            mb_id = str(int(f[meshblock_number_field]))

            if mb_id in non_digitized:
                print(f'skipping non-digitized meshblock: {mb_id}')
                continue

            is_offshore = mb_id in offshore
            nth_sth = island[mb_id]

            attrs = f.attributes()
            # offline populations not known at this stage!
            attrs.extend([0, 0, 0, is_offshore, nth_sth, NULL])
            f.setAttributes(attrs)
            meshblocks.append(f)

        assert dest_layer.dataProvider().addFeatures(meshblocks)
        QMessageBox.warning(self.iface.mainWindow(), self.tr('Load New Meshblocks'),
                            self.tr(
                                'Please run a full scenario rebuild after re-loading the plugin'))

    def request_population_update(self, electorate_id):
        """

        :param electorate_id:
        :return:
        """
        # step 1: find meshblocks for electorate
        district_registry = self.get_district_registry()

        district_registry.flag_stats_nz_updating(electorate_id)
        self.refresh_dock_stats()

        electorate_type = district_registry.get_district_type(electorate_id)
        electorate_meshblocks = self.scenario_registry.electorate_meshblocks(electorate_id=electorate_id,
                                                                             electorate_type=electorate_type,
                                                                             scenario_id=self.context.scenario)

        # TODO: track scenarios, reject responses on different scenarios

        concordance = [ConcordanceItem(str(m['meshblock_number']), str(electorate_id), self.context.task) for m in
                       electorate_meshblocks]
        request = BoundaryRequest(concordance, area=self.context.task)
        connector = get_api_connector()
        self.api_request_queue.append_request(connector, request)

    def api_request_finished(self, result: dict):
        """
        Triggered when an API request is finalized
        """
        QgsMessageLog.logMessage('Response ' + str(result), "REDISTRICT")

        district_registry = self.get_district_registry()
        for electorate_table in result['populationTable']:
            # remove the N/S/M temporary code used only for stats nz api
            electorate_id = int(electorate_table['electorate'][1:])
            district_registry.update_stats_nz_values(electorate_id, electorate_table)

        self.refresh_dock_stats()
        self.refresh_canvases()

    def update_stats_for_scenario(self, _):
        """
        Triggers a complete stats NZ refresh
        """
        if self.meshblock_layer.editBuffer() is not None and self.meshblock_layer.editBuffer().isModified():
            self.report_failure(self.tr(
                'Cannot update statistics while unsaved changes are present. Save or cancel the current edits and try again.'))
            return

        district_registry = self.get_district_registry()

        electorate_ids = [f['electorate_id'] for f in self.electorate_layer.getFeatures() if
                          f['type'] == self.context.task]
        concordance = []
        for electorate_id in electorate_ids:
            district_registry.flag_stats_nz_updating(electorate_id)
            electorate_meshblocks = self.scenario_registry.electorate_meshblocks(electorate_id=electorate_id,
                                                                                 electorate_type=self.context.task,
                                                                                 scenario_id=self.context.scenario)
            concordance.extend(
                [ConcordanceItem(str(m['meshblock_number']), str(electorate_id), self.context.task) for m in
                 electorate_meshblocks])

        self.refresh_dock_stats()

        # TODO: track scenarios, reject responses on different scenarios
        request = BoundaryRequest(concordance, area=self.context.task)

        connector = get_api_connector()
        self.api_request_queue.append_request(connector, request)

    def stats_api_error(self, boundary_request: BoundaryRequest, error: str):
        """
        Triggered on a boundary request failure
        :param boundary_request: original boundary request
        :param error: reported error message
        """
        self.report_failure(error)

        district_registry = self.get_district_registry()

        electorates = set()
        for concordance_item in boundary_request.concordance:
            electorate_id = int(ConcordanceItem.deformat_electorate_id(concordance_item.electorate))
            electorates.add(electorate_id)

        for electorate_id in electorates:
            district_registry.update_stats_nz_values(electorate_id,
                                                     {
                                                         'currentPopulation': NULL,
                                                         'varianceYear1': NULL,
                                                         'varianceYear2': NULL
                                                     })
        self.refresh_dock_stats()
        self.refresh_canvases()

    def _toggle_layer_tree_toolbar(self, visible: bool):
        """
        Toggles whether the layer tree toolbar should be visible
        """
        layer_tree_dock = self.iface.mainWindow().findChildren(
            QDockWidget,
            'Layers')
        if layer_tree_dock:
            layer_tree_dock_toolbar = \
                layer_tree_dock[0].findChildren(QToolBar)[0]
            layer_tree_dock_toolbar.setVisible(visible)

    def _toggle_simplified(self):  # pylint: disable=too-many-branches
        """
        Toggles the simplified redistricting interface
        """
        if self._is_simplified:
            self.iface.mainWindow().menuBar().show()
            if self.simplified_toolbar and not sip.isdeleted(
                    self.simplified_toolbar):
                self.simplified_toolbar.deleteLater()
                self.simplified_toolbar = None
            for toolbar in self._previously_visible_toolbars:
                toolbar.show()
            for dock in self._previously_visible_docks:
                dock.show()
            for widget in self._previously_visible_statusbar_widgets:
                widget.show()

            if self._exit_simplified_action and not sip.isdeleted(
                    self._exit_simplified_action):
                self._exit_simplified_action.deleteLater()
                self._exit_simplified_action = None

            self._toggle_layer_tree_toolbar(True)

            if self.redistricting_toolbar:
                self.redistricting_toolbar.setIconSize(
                    self.iface.iconSize()
                )
                self.redistricting_toolbar.adjustSize()
            self._is_simplified = False
        else:
            self._previously_visible_toolbars = []
            for toolbar in self.iface.mainWindow().findChildren(QToolBar,
                                                                options=Qt.FindDirectChildrenOnly):
                if toolbar in (self.redistricting_toolbar,):
                    continue

                if toolbar.isVisible():
                    self._previously_visible_toolbars.append(toolbar)
                    toolbar.hide()

            self._toggle_layer_tree_toolbar(False)

            self._previously_visible_docks = []
            for dock in self.iface.mainWindow().findChildren(QDockWidget):
                if dock.objectName() in ('Layers',
                                         'IdentifyResultsDock',
                                         'SelectedPopulationDockWidget',
                                         'LinzRedistrictingDock',
                                         'LinzValidationResultsDock'):
                    continue

                # maybe a secondary canvas
                if dock.findChildren(QgsMapCanvas):
                    continue

                if dock.isVisible():
                    self._previously_visible_docks.append(dock)
                    dock.hide()

            self._previously_visible_statusbar_widgets = []
            for widget in self.iface.statusBarIface().children():
                if not isinstance(widget, QWidget):
                    continue

                if widget.objectName() in ('mProgressBar',
                                          'mMessageLogViewerButton'):
                    continue

                # ensure task manager stays visible
                if (isinstance(widget, (QLineEdit, QToolButton)) and
                        widget.objectName() not in ('mOntheFlyProjectionStatusButton', )):
                    continue

                if widget.isVisible():
                    self._previously_visible_statusbar_widgets.append(widget)
                    widget.hide()

            self.iface.mainWindow().menuBar().hide()

            self._exit_simplified_action = QAction(GuiUtils.get_icon(
                'full_interface.svg'), self.tr('Exit Simplified Mode'),
                self.simplified_toolbar)
            self._exit_simplified_action.triggered.connect(
                self._toggle_simplified)

            self.simplified_toolbar = QToolBar()
            self.simplified_toolbar.setIconSize(
                self.iface.iconSize() * self.SIMPLIFIED_MODE_TOOLBAR_SCALE
            )
            if self.redistricting_toolbar:
                self.redistricting_toolbar.setIconSize(
                    self.iface.iconSize() * self.SIMPLIFIED_MODE_TOOLBAR_SCALE
                )
                self.redistricting_toolbar.adjustSize()

            self.simplified_toolbar.setObjectName('Simplified Redistricting')

            self.simplified_toolbar.addAction(
                self.iface.actionSaveProject()
            )
            self.simplified_toolbar.addSeparator()
            self.simplified_toolbar.addAction(
                self.iface.actionPan()
            )
            self.simplified_toolbar.addAction(
                self.iface.actionZoomToSelected()
            )
            self.simplified_toolbar.addAction(
                self.iface.actionZoomFullExtent()
            )
            self.simplified_toolbar.addSeparator()
            self.simplified_toolbar.addAction(
                self.iface.actionIdentify()
            )

            select_button = QToolButton(self.simplified_toolbar)
            select_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            select_button.addAction(self.iface.actionSelect())
            select_button.addAction(self.iface.actionSelectPolygon())
            select_button.addAction(self.iface.actionSelectFreehand())
            select_button.addAction(self.iface.actionSelectRadius())
            for a in ('mActionSelectByForm',
                      'mActionSelectByExpression',
                      'mActionDeselectAll',
                      'mProcessingAlg_native:selectbylocation'):
                matches = self.iface.mainWindow().findChildren(QAction,
                                                         a)
                if not matches:
                    continue
                select_button.addAction(matches[0])

            select_button.setDefaultAction(self.iface.actionSelect())

            def _select_button_triggered(action):
                select_button.setDefaultAction(action)

            select_button.triggered.connect(_select_button_triggered)
            self.simplified_toolbar.addWidget(select_button)

            self.simplified_toolbar.addAction(
                self.iface.actionMeasure()
            )

            self.simplified_toolbar.addSeparator()

            settings_action = QToolButton(self.simplified_toolbar)
            settings_action.setPopupMode(
                QToolButton.ToolButtonPopupMode.InstantPopup)
            settings_action.setIcon(GuiUtils.get_icon(
            'open_settings.svg'))
            self.simplified_toolbar.addWidget(settings_action)
            settings_menu = QMenu(settings_action)
            settings_menu.addAction(self.begin_action)
            settings_menu.addMenu(self.switch_menu)
            settings_menu.addSeparator()
            settings_menu.addAction(self._exit_simplified_action)

            settings_action.setMenu(settings_menu)

            self.iface.addToolBar(self.simplified_toolbar)
            GuiUtils.float_toolbar_over_widget(self.simplified_toolbar,
                                               self.iface.mapCanvas(),
                                               offset_y=-30)
            self._is_simplified = True

    def show_help(self):
        """
        Shows the plugin help
        """
        QDesktopServices.openUrl(QUrl(
            'https://github.com/north-road/qgis-redistricting-plugin/blob/master/documentation/ui_design/ui_design.md'))

    def about(self):
        """
        Shows the about dialog
        """
        QMessageBox.about(self.iface.mainWindow(), self.tr('LINZ Redistricting Plugin'),
                          self.tr('Developed by North Road (http://north-road.com) for LINZ.') + '\n\n' + self.tr(
                              'Version: {}').format(VERSION))
