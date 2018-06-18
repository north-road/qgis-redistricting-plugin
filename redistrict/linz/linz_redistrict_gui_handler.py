# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - LINZ Specific redistricting GUI handler

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = '(C) 2018 by Nyall Dawson'
__date__ = '30/04/2018'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QCoreApplication
from redistrict.gui.redistrict_gui_handler import RedistrictGuiHandler
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry


class LinzRedistrictGuiHandler(RedistrictGuiHandler):
    """
    LINZ specific redistricting GUI handler
    """

    def __init__(self, redistrict_dock, district_registry: LinzElectoralDistrictRegistry):
        super().__init__(redistrict_dock=redistrict_dock,
                         district_registry=district_registry)

    def show_stats_for_district(self, district):
        """
        Displays the full statistics for a district in the dock
        :param district: id/code for district to show
        """
        if not district:
            self.redistrict_dock().show_message('')
            return

        district_type = self._district_registry.get_district_type(district)
        contents = {
            'DISTRICT_NAME': self._district_registry.get_district_title(district),
            'TYPE': self._district_registry.district_type_title(district_type),
            'QUOTA': self._district_registry.get_quota_for_district_type(district_type),
            'POPULATION': self._district_registry.get_estimated_population(district),
            'IS_ESTIMATED_POP': True
        }
        contents['VARIATION'] = self._district_registry.get_variation_from_quota_percent(quota=contents['QUOTA'],
                                                                                         population=contents[
                                                                                             'POPULATION'])
        if contents['VARIATION'] > 0:
            contents['VARIATION'] = '+{}'.format(contents['VARIATION'])

        contents['ESTIMATED_POP_*'] = '*' if contents['IS_ESTIMATED_POP'] else ''
        tr_estimated_pop_string = QCoreApplication.translate('LinzRedistrict', 'Only estimated population available')
        contents['ESTIMATED_POP_STRING'] = """<br>
        <span style="font-style:italic">* {}</span>""".format(tr_estimated_pop_string) if contents[
            'IS_ESTIMATED_POP'] else ''
        contents['VARIATION_COLOR'] = 'red' if self._district_registry.variation_exceeds_allowance(
            quota=contents['QUOTA'],
            population=contents[
                'POPULATION']) else 'black'

        message = QCoreApplication.translate('LinzRedistrict', """<h1>Statistics for {DISTRICT_NAME}</h1>
        <h2>{TYPE}</h2>
        <p>Quota: <span style="font-weight:bold">{QUOTA}</span></p>
        <p>Population: <span style="font-weight:bold;">{POPULATION}{ESTIMATED_POP_*}</span> <span style="color: {VARIATION_COLOR}; font-weight: bold">({VARIATION}%)</span>{ESTIMATED_POP_STRING}</p>
        <p>Quota Variation 2020: <span style="font-weight:bold">unknown</span><br>
        Quota Variation 2023: <span style="font-weight:bold">unknown</span></p>
        <p><a href="request">Request population from Statistics NZ</a></p>""").format(
            **contents)
        self.redistrict_dock().show_message(message)
        self.redistrict_dock().request_population_callback = self.request_population

        self.current_district_changed.emit(district)

    def request_population(self):
        """
        Triggered on a population update request
        """
        QgsApplication.messageLog().logMessage('xxxxxxxxxxxx')
