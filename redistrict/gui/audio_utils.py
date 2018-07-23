# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Audio Utilities

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

from qgis.core import QgsSettings
from redistrict.gui.playsound import playsound


class AudioUtils:
    """
    Utilities for audio plugin components
    """

    ENABLED = False
    ON_REDISTRICT = None

    @staticmethod
    def play_redistrict_sound():
        """
        Plays the 'redistrict' sound effect
        """
        if AudioUtils.ON_REDISTRICT:
            playsound(AudioUtils.ON_REDISTRICT, block=False)

    @staticmethod
    def update_settings():
        """
        Updates audio feedback based on current settings
        """
        AudioUtils.ENABLED = QgsSettings().value('redistrict/use_audio_feedback', False, bool, QgsSettings.Plugins)
        if AudioUtils.ENABLED:
            AudioUtils.ON_REDISTRICT = QgsSettings().value('redistrict/on_redistrict', '', str, QgsSettings.Plugins)
        else:
            AudioUtils.ON_REDISTRICT = None
