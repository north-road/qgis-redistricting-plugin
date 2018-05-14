# -*- coding: utf-8 -*-
"""LINZ Dialog for creating a new electorate

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

from qgis.PyQt.QtWidgets import (QDialog,
                                 QVBoxLayout,
                                 QLineEdit,
                                 QLabel,
                                 QDialogButtonBox)
from redistrict.linz.linz_district_registry import (
    LinzElectoralDistrictRegistry)
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext


class CreateElectorateDialog(QDialog):
    """
    Custom dialog for entering properties for a new electorate
    """

    def __init__(self, registry: LinzElectoralDistrictRegistry,
                 context: LinzRedistrictingContext, parent=None):
        super().__init__(parent)
        self.existing_names = list(registry.district_titles().keys())
        self.existing_codes = [f['code'] for f in registry.source_layer.getFeatures()]

        self.setWindowTitle(self.tr('Create New {} Electorate').format(context.get_name_for_current_task()))

        dialog_layout = QVBoxLayout()
        label = QLabel(self.tr('Enter name for new {} electorate:').format(context.get_name_for_current_task()))
        dialog_layout.addWidget(label)

        self.name_line_edit = QLineEdit()
        self.name_line_edit.setPlaceholderText('Electorate name')
        dialog_layout.addWidget(self.name_line_edit)

        label = QLabel(self.tr('Enter code for new electorate:'))
        dialog_layout.addWidget(label)

        self.code_line_edit = QLineEdit()
        self.code_line_edit.setPlaceholderText('Electorate code')
        dialog_layout.addWidget(self.code_line_edit)

        self.feedback_label = QLabel()
        dialog_layout.addWidget(self.feedback_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_layout.addWidget(self.button_box)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)

        self.name_line_edit.textChanged.connect(self.name_changed)
        self.code_line_edit.textChanged.connect(self.code_changed)

        self.setLayout(dialog_layout)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def name_changed(self):
        """
        Triggered on name change
        """
        self.__update_feedback_label()

    def code_changed(self):
        """
        Triggered on code change
        """
        self.__update_feedback_label()

    def __update_feedback_label(self):
        """
        Updates the dialog feedback label
        """
        name = self.name_line_edit.text().strip()
        code = self.code_line_edit.text().strip()
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        if name in self.existing_names:
            self.feedback_label.setText(self.tr('An electorate with this name already exists!'))
        elif not name:
            self.feedback_label.setText(self.tr('An electorate name must be entered!'))
        elif code in self.existing_codes:
            self.feedback_label.setText(self.tr('An electorate with this code already exists!'))
        elif not code:
            self.feedback_label.setText(self.tr('An electorate code must be entered!'))
        else:
            self.feedback_label.setText('')
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def name(self) -> str:
        """
        Returns the current name entered in the dialog
        """
        return self.name_line_edit.text()

    def code(self) -> str:
        """
        Returns the current code entered in the dialog
        """
        return self.code_line_edit.text()
