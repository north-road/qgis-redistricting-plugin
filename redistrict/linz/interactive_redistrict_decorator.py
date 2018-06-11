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
                       QgsExpression,
                       QgsTextFormat,
                       QgsRenderContext,
                       QgsTextRenderer,
                       QgsVectorLayer,
                       QgsAggregateCalculator)
from qgis.gui import (QgsMapCanvas,
                      QgsMapCanvasItem)
from redistrict.gui.interactive_redistrict_tool import DecoratorFactory


class CentroidDecorator(QgsMapCanvasItem):
    """
    Decorates centroids of features with population statistics
    """

    def __init__(self, canvas: QgsMapCanvas, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer, task: str):
        """
        Constructor
        :param canvas: map canvas
        :param electorate_layer: electorates layer
        :param meshblock_layer: meshblocks layer
        :param task: current task
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.electorate_layer = electorate_layer
        self.meshblock_layer = meshblock_layer
        self.task = task
        self.text_format = QgsTextFormat()
        # self.text_format.shadow().setEnabled(True)
        self.text_format.background().setEnabled(True)
        self.text_format.background().setSize(QSizeF(1, 0))
        self.text_format.background().setOffset(QPointF(0, -0.7))
        self.text_format.background().setRadii(QSizeF(1, 1))
        self.image = None

    def redraw(self):
        """
        Forces a redraw of the cached image
        """
        self.image = None

    def paint(self, painter, option, widget):  # pylint: disable=missing-docstring, unused-argument, too-many-locals
        if self.image is not None:
            painter.drawImage(0, 0, self.image)
            return

        image_size = self.canvas.mapSettings().outputSize()
        self.image = QImage(image_size.width(), image_size.height(), QImage.Format_ARGB32)
        self.image.fill(0)
        image_painter = QPainter(self.image)
        render_context = QgsRenderContext.fromQPainter(image_painter)

        image_painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.canvas.mapSettings().visibleExtent()
        request = QgsFeatureRequest()
        request.setFilterRect(rect)
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('type', self.task))

        for f in self.electorate_layer.getFeatures(request):
            #    pole, dist = f.geometry().clipped(rect).poleOfInaccessibility(rect.width() / 30)
            pixel = self.toCanvasCoordinates(f.geometry().clipped(rect).centroid().asPoint())

            calc = QgsAggregateCalculator(self.meshblock_layer)
            calc.setFilter('staged_electorate={}'.format(f['electorate_id']))
            estimated_pop, ok = calc.calculate(QgsAggregateCalculator.Sum, 'offline_pop_{}'.format(self.task.lower()))  # pylint: disable=unused-variable

            text_string = ['{}'.format(f['name']),
                           '{}'.format(int(estimated_pop))]
            QgsTextRenderer().drawText(QPointF(pixel.x(), pixel.y()), 0, QgsTextRenderer.AlignCenter,
                                       text_string, render_context, self.text_format)

        image_painter.end()

        painter.drawImage(0, 0, self.image)


class CentroidDecoratorFactory(DecoratorFactory):
    """
    Factory for CentroidDecorator
    """

    def __init__(self, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer, task: str):
        super().__init__()
        self.electorate_layer = electorate_layer
        self.meshblock_layer = meshblock_layer
        self.task = task

    def create_decorator(self, canvas: QgsMapCanvas):
        """
        Creates a new QgsMapCanvasItem decorator
        :param canvas: associated map canvas
        :return: QgsMapCanvasItem to display on map if decorations
        are desired
        """
        return CentroidDecorator(canvas, electorate_layer=self.electorate_layer, meshblock_layer=self.meshblock_layer, task=self.task)
