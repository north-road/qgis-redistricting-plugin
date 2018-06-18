# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Database Utilities

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

from qgis.PyQt.QtCore import QFile
from qgis.core import QgsTask


class DbUtils:
    """
    Utilities for Database plugin components
    """

    @staticmethod
    def export_database(database, destination):
        """
        Exports the database to a destination file
        :param database: source database
        :param destination: destination file
        :return: boolean representing success or not
        """
        pass


class CopyFileTask(QgsTask):
    """
    QgsTask subclass for copying a bunch of files, with progress reports
    and cancelation support
    """

    def __init__(self, description: str, file_map: dict):
        """
        Constructor for CopyFileTask
        :param description: task description
        :param file_map: dict of source file to destination path
        """
        super().__init__(description)
        self.file_map = file_map
        self.error = None

    def run(self):  # pylint: disable=missing-docstring
        current = 0
        for source, dest in self.file_map.items():
            self.setProgress(100 * current / len(self.file_map))

            if self.isCanceled():
                return False

            if QFile.exists(dest):
                if not QFile.remove(dest):
                    self.error = self.tr('Could not remove existing file {}'.format(dest))
                    return False

            if not QFile.copy(source, dest):
                self.error = self.tr('Could not copy file {} to {}'.format(source, dest))
                return False

            current += 1
        self.setProgress(100)

        return True
