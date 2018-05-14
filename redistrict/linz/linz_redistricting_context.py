# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ Redistricting Context

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


class LinzRedistrictingContext():
    """
    Contains settings relating to the general context of a LINZ redistricting
    operation
    """

    TASK_GN = 'GN'
    TASK_GS = 'GS'
    TASK_M = 'M'

    def __init__(self):
        self.scenario = 1
        self.task = self.TASK_GN
