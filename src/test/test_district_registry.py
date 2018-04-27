# coding=utf-8
"""District Registry Test.

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
from src.core.district_registry import DistrictRegistry


class DistrictRegistryTest(unittest.TestCase):
    """Test DistrictRegistry."""

    def testConstruct(self):
        """
        Test creating registry
        """
        self.assertIsNotNone(DistrictRegistry())

    def testDistricts(self):
        """
        Test retrieving districts
        """
        registry = DistrictRegistry(['district 1', 'district 9'])
        self.assertEqual(registry.district_list(), ['district 1',
                                                    'district 9'])


if __name__ == "__main__":
    suite = unittest.makeSuite(DistrictRegistryTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
