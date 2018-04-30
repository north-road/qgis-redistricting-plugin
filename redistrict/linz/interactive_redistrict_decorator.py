# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Decorator for electorates

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

from qgis.PyQt.QtCore import (QSizeF,
                              QPointF)
from qgis.PyQt.QtGui import (QImage,
                             QPainter)
from qgis.core import (QgsFeatureRequest,
                       QgsTextFormat,
                       QgsRenderContext,
                       QgsTextRenderer)
from qgis.gui import QgsMapCanvasItem
from redistrict.gui.interactive_redistrict_tool import DecoratorFactory


class CentroidDecorator(QgsMapCanvasItem):
    """
    Decorates centroids of features with population statistics
    """

    def __init__(self, canvas, layer):
        """
        Constructor
        :param canvas: map canvas
        :param layer: district layer to obtain population from
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.text_format = QgsTextFormat()
        # self.text_format.shadow().setEnabled(True)
        self.text_format.background().setEnabled(True)
        self.text_format.background().setSize(QSizeF(1, 0))
        self.text_format.background().setOffset(QPointF(0, -0.7))
        self.text_format.background().setRadii(QSizeF(1, 1))

    def paint(self, painter, option, widget):  # pylint: disable=missing-docstring, unused-argument
        image_size = self.canvas.mapSettings().outputSize()
        image = QImage(image_size.width(), image_size.height(), QImage.Format_ARGB32)
        image.fill(0)
        image_painter = QPainter(image)
        render_context = QgsRenderContext.fromQPainter(image_painter)

        image_painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.canvas.mapSettings().visibleExtent()
        for f in self.layer.getFeatures(QgsFeatureRequest().setFilterRect(rect)):
            #    pole, dist = f.geometry().clipped(rect).poleOfInaccessibility(rect.width() / 30)
            pole = f.geometry().clipped(rect).centroid()
            pixel = self.toCanvasCoordinates(pole.asPoint())

            text_string = ['{}'.format(f['GeneralConstituencyCode']),
                           '{}'.format(int(f['Shape_Length']))]  # ,'M: {}'.format(int(f['Shape_Length']*.5))]
            QgsTextRenderer().drawText(QPointF(pixel.x(), pixel.y()), 0, QgsTextRenderer.AlignCenter,
                                       text_string, render_context, self.text_format)

        image_painter.end()

        painter.drawImage(0, 0, image)


class CentroidDecoratorFactory(DecoratorFactory):
    """
    Factory for CentroidDecorator
    """

    def __init__(self, district_layer):
        super().__init__()
        self.district_layer = district_layer

    def create_decorator(self, canvas):
        """
        Creates a new QgsMapCanvasItem decorator
        :param canvas: associated map canvas
        :return: QgsMapCanvasItem to display on map if decorations
        are desired
        """
        return CentroidDecorator(canvas, self.district_layer)
