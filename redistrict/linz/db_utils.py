"""
LINZ Redistricting Plugin - Database Utilities
"""

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
        pass  # pylint: disable=unnecessary-pass


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
                    # pylint: disable=consider-using-f-string
                    self.error = self.tr('Could not remove existing file {}'.format(dest))
                    # pylint: enable=consider-using-f-string
                    return False

            if not QFile.copy(source, dest):
                # pylint: disable=consider-using-f-string
                self.error = self.tr('Could not copy file {} to {}'.format(source, dest))
                # pylint: enable=consider-using-f-string
                return False

            current += 1
        self.setProgress(100)

        return True
