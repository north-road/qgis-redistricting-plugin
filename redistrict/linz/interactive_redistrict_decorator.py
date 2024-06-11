"""
LINZ Redistricting Plugin - Decorator for electorates
"""

from qgis.PyQt.QtCore import (
    QSizeF,
    QPointF
)
from qgis.PyQt.QtGui import (
    QImage,
    QPainter
)
from qgis.core import (
    QgsSettings,
    QgsFeatureRequest,
    QgsExpression,
    QgsTextFormat,
    QgsRenderContext,
    QgsTextRenderer,
    QgsVectorLayer,
    NULL
)
from qgis.gui import (
    QgsMapCanvas,
    QgsMapCanvasItem
)
from redistrict.gui.interactive_redistrict_tool import DecoratorFactory
from redistrict.linz.linz_district_registry import LinzElectoralDistrictRegistry


class CentroidDecorator(QgsMapCanvasItem):
    """
    Decorates centroids of features with population statistics
    """

    def __init__(self, canvas: QgsMapCanvas, electorate_layer: QgsVectorLayer,
                 meshblock_layer: QgsVectorLayer, task: str, quota: int):
        """
        Constructor
        :param canvas: map canvas
        :param electorate_layer: electorates layer
        :param meshblock_layer: meshblocks layer
        :param task: current task
        :param quota: target quota
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
        self.quota = quota
        self.original_populations = {}
        self.new_populations = {}

    def redraw(self, handler):
        """
        Forces a redraw of the cached image
        """
        self.image = None

        if not self.original_populations:
            # first run, get initial estimates
            request = QgsFeatureRequest()
            request.setFilterExpression(QgsExpression.createFieldEqualityExpression('type', self.task))
            request.setFlags(QgsFeatureRequest.NoGeometry)
            for f in self.electorate_layer.getFeatures(request):
                estimated_pop = f.attribute(handler.stats_nz_pop_field_index)
                if estimated_pop is None or estimated_pop == NULL:
                    # otherwise just use existing estimated pop as starting point
                    estimated_pop = f.attribute(handler.estimated_pop_idx)
                self.original_populations[f.id()] = estimated_pop

        # step 1: get all electorate features corresponding to affected electorates
        electorate_features = {f[handler.electorate_layer_field]: f for f in
                               handler.get_affected_districts(
                                   [handler.electorate_layer_field, handler.stats_nz_pop_field, 'estimated_pop'],
                                   needs_geometry=False)}

        self.new_populations = {}

        for district in handler.pending_affected_districts.keys():  # pylint: disable=consider-iterating-dictionary
            # use stats nz pop as initial estimate, if available
            estimated_pop = electorate_features[district].attribute(handler.stats_nz_pop_field_index)
            if estimated_pop is None or estimated_pop == NULL:
                # otherwise just use existing estimated pop as starting point
                estimated_pop = electorate_features[district].attribute(handler.estimated_pop_idx)
            # add new bits
            estimated_pop = handler.grow_population_with_added_meshblocks(district, estimated_pop)
            # minus lost bits
            estimated_pop = handler.shrink_population_by_removed_meshblocks(district, estimated_pop)

            self.new_populations[electorate_features[district].id()] = estimated_pop

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

            estimated_pop = self.new_populations[f.id()] if f.id() in self.new_populations else \
            self.original_populations[f.id()]

            variance = LinzElectoralDistrictRegistry.get_variation_from_quota_percent(self.quota, estimated_pop)
            variance_dir_string = '+' if variance > 0 else ''
            text_string = [f'{f['name']}',
                           f'{int(estimated_pop)}',
                           f'{variance_dir_string}{variance}%']
            QgsTextRenderer().drawText(QPointF(pixel.x(), pixel.y()), 0, QgsTextRenderer.AlignCenter,
                                       text_string, render_context, self.text_format)

        image_painter.end()

        painter.drawImage(0, 0, self.image)


class CentroidDecoratorFactory(DecoratorFactory):
    """
    Factory for CentroidDecorator
    """

    def __init__(self, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer, task: str, quota: int):
        super().__init__()
        self.electorate_layer = electorate_layer
        self.meshblock_layer = meshblock_layer
        self.task = task
        self.quota = quota

    def create_decorator(self, canvas: QgsMapCanvas):
        """
        Creates a new QgsMapCanvasItem decorator
        :param canvas: associated map canvas
        :return: QgsMapCanvasItem to display on map if decorations
        are desired
        """
        if QgsSettings().value('redistrict/show_overlays', False, bool, QgsSettings.Plugins):
            return CentroidDecorator(canvas, electorate_layer=self.electorate_layer,
                                     meshblock_layer=self.meshblock_layer, task=self.task, quota=self.quota)

        return None
