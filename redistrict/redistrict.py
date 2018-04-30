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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtWidgets import QToolBar, QAction
from .core.district_registry import DistrictRegistry
from .gui.district_selection_dialog import DistrictSelectionDialog
from .gui.gui_utils import GuiUtils


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

        self.district_registry = DistrictRegistry(
            name='General NI',
            districts=['District 1', 'District 9'],
            type_string_title='Electorate',
            type_string_sentence='electorate',
            type_string_sentence_plural='electorates')

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

        self.interactive_redistrict_action = QAction(
            GuiUtils.get_icon('interactive_redistrict.svg'),
            self.tr('Interactive Redistrict'), None)
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

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.redistricting_toolbar.deleteLater()

    def redistrict_selected(self):
        """
        Redistrict the currently selected meshblocks
        """
        dlg = DistrictSelectionDialog(district_registry=self.district_registry,
                                      parent=self.iface.mainWindow())
        dlg.exec_()
