"""
LINZ Redistricting Plugin - Core Utilities
"""

from typing import List

from qgis.core import (
    Qgis,
    QgsGeometry,
    QgsVectorLayer,
    QgsRuleBasedLabeling,
    QgsVectorLayerSimpleLabeling,
    QgsWkbTypes
)


class CoreUtils:
    """
    Utilities for core plugin components
    """

    @staticmethod
    def enable_labels_for_layer(layer: QgsVectorLayer, enabled: bool = True):
        """
        Either enables or disables the labels for a layer. Works with standard labels and rule based labels
        :param layer: layer to edit
        :param enabled: whether labels should be enabled
        """
        labeling = layer.labeling()

        if isinstance(labeling, QgsRuleBasedLabeling):

            def enable_label_rules(rule: QgsRuleBasedLabeling.Rule):
                """
                Recursively enable rule based labeling
                """
                rule.setActive(enabled)
                for c in rule.children():
                    enable_label_rules(c)

            enable_label_rules(labeling.rootRule())
        elif isinstance(labeling, QgsVectorLayerSimpleLabeling):
            settings = labeling.settings()
            settings.drawLabels = False
            labeling.setSettings(settings)

        layer.triggerRepaint()

    @staticmethod
    def union_geometries(geometries: List[QgsGeometry]) -> QgsGeometry:
        """
        Unions geometries, using the optimal method available
        """
        if Qgis.QGIS_VERSION_INT >= 34100:
            # use optimized GEOS coverage union method
            # this is only possible for polygons, which should be safe to
            # assume, unless we are running the test suite!
            if all(g.type() == QgsWkbTypes.PolygonGeometry for g in
                   geometries):
                collected_multi_polygon = QgsGeometry.collectGeometry(geometries)
                # use low-level API so that we can specify a 0.005m tolerance, to avoid
                # slivers
                geos_engine = QgsGeometry.createGeometryEngine(collected_multi_polygon.constGet(), 0.005)
                geom, err = geos_engine.unionCoverage()
                return QgsGeometry(geom)
        elif Qgis.QGIS_VERSION_INT >= 33600:
            # use optimized GEOS coverage union method
            # this is only possible for polygons, which should be safe to
            # assume, unless we are running the test suite!
            if all(g.type() == QgsWkbTypes.PolygonGeometry for g in
                   geometries):
                return QgsGeometry.unionCoverage(
                    QgsGeometry.collectGeometry(geometries)
                )

        return QgsGeometry.unaryUnion(
            geometries
        )
