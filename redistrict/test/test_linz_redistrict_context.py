# coding=utf-8
"""LINZ Redistricting Context test.

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

import unittest
from redistrict.linz.linz_redistricting_context import (
    LinzRedistrictingContext
)


class LINZRedistrictContextTest(unittest.TestCase):
    """Test LinzRedistrictingContext."""

    def testBasic(self):
        """
        Test getters/settings
        """
        context = LinzRedistrictingContext()
        self.assertIn(context.task, (LinzRedistrictingContext.TASK_GN,
                                     LinzRedistrictingContext.TASK_GS,
                                     LinzRedistrictingContext.TASK_M))
        context.task = LinzRedistrictingContext.TASK_GS
        self.assertEqual(context.task, LinzRedistrictingContext.TASK_GS)
        self.assertIsNotNone(context.scenario)
        context.scenario = 10
        self.assertEqual(context.scenario, 10)

    def testNameForTask(self):
        """
        Test retrieving friendly name for task
        """
        self.assertEqual(LinzRedistrictingContext.get_name_for_task(LinzRedistrictingContext.TASK_GN),
                         'General (North Island)')
        self.assertEqual(LinzRedistrictingContext.get_name_for_task(LinzRedistrictingContext.TASK_GS),
                         'General (South Island)')
        self.assertEqual(LinzRedistrictingContext.get_name_for_task(LinzRedistrictingContext.TASK_M), 'Māori')

    def testNameForCurrentTask(self):
        """
        Test retrieving friendly name for currenttask
        """
        context = LinzRedistrictingContext()
        context.task = LinzRedistrictingContext.TASK_GN
        self.assertEqual(context.get_name_for_current_task(),
                         'General (North Island)')
        context.task = LinzRedistrictingContext.TASK_GS
        self.assertEqual(context.get_name_for_current_task(),
                         'General (South Island)')
        context.task = LinzRedistrictingContext.TASK_M
        self.assertEqual(context.get_name_for_current_task(), 'Māori')


if __name__ == "__main__":
    suite = unittest.makeSuite(LINZRedistrictContextTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
