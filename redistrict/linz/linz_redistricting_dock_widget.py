# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ specific redistricting dock widget

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

from qgis.PyQt.QtWidgets import (QToolButton,
                                 QAction,
                                 QMenu)
from redistrict.gui.gui_utils import GuiUtils
from redistrict.gui.redistricting_dock_widget import RedistrictingDockWidget
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext


class LinzRedistrictingDockWidget(RedistrictingDockWidget):
    """
    LINZ Specific redistricting dock widget
    """

    def __init__(self, context: LinzRedistrictingContext, iface=None):
        """
        Constructor for LINZ redistricting dock
        :param context: initial dock context
        :param iface: QGIS interface
        """
        super().__init__(iface)
        self.update_dock_title(context=context)

        self.scenarios_tool_button = QToolButton()
        self.scenarios_tool_button.setAutoRaise(True)
        self.scenarios_tool_button.setToolTip('Scenarios')
        self.scenarios_tool_button.setIcon(GuiUtils.get_icon(icon='scenarios.svg'))
        self.scenarios_tool_button.setPopupMode(QToolButton.InstantPopup)

        scenarios_menu = QMenu(parent=self.scenarios_tool_button)
        switch_scenario_action = QAction(self.tr('Switch to Existing Scenario...'), parent=scenarios_menu)
        # switch_scenario_action.triggered.connect(select_current_scenario)
        scenarios_menu.addAction(switch_scenario_action)

        scenarios_menu.addSeparator()
        update_scenario_action = QAction(self.tr('Update Statistics for Scenario...'), parent=scenarios_menu)
        # update_scenario_action.triggered.connect(update_scenario)
        scenarios_menu.addAction(update_scenario_action)

        scenarios_menu.addSeparator()

        store_scenario_action = QAction(self.tr('Branch to New Scenario...'), parent=scenarios_menu)
        # store_scenario_action.triggered.connect(branch_scenario)
        scenarios_menu.addAction(store_scenario_action)
        import_scenario_action = QAction(self.tr('Import Scenario from Database...'), parent=scenarios_menu)
        # import_scenario_action.triggered.connect(import_scenario)
        scenarios_menu.addAction(import_scenario_action)

        self.scenarios_tool_button.setMenu(scenarios_menu)
        self.dock_toolbar().addWidget(self.scenarios_tool_button)

    def update_dock_title(self, context: LinzRedistrictingContext):
        """
        Refreshes the dock title text, using the settings from a supplied
        context.
        :param context: redistricting context
        """
        self.setWindowTitle(self.tr('Redistricting - {} - Scenario {}').format(context.get_name_for_current_task(),
                                                                               context.scenario))
