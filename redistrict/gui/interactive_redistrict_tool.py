# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Interactive Redistricting Tool

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

from qgis.PyQt.QtCore import (Qt,
                              QCoreApplication)
from qgis.core import (Qgis,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsPointLocator,
                       QgsTolerance)
from qgis.gui import (QgsMapTool,
                      QgsSnapIndicator)
from qgis.utils import iface


class UniqueFeatureEdgeMatchCollectingFilter(QgsPointLocator.MatchFilter):
    """
    A snapping filter which collects all nearby edges from unique
    features. Required because by default the snapper only returns
    a single match (the closest), yet we want to know ALL unique edges
    within the tolerance.
    """

    def __init__(self, tolerance):
        """
        Constructor for filter
        :param tolerance: maximum distance from cursor to edge allowed
        """
        super().__init__()
        self.matches = []
        self.tolerance = tolerance

    def acceptMatch(self, match):
        """
        Tests current match for validity, but also collects a list of unique
        matches
        :param match: snapping match candidate
        """
        if match.distance() > self.tolerance:
            return False

        # do we already have a match with this layer/feature combination?
        duplicate_matches = [m for m in self.matches if
                             m.layer() == match.layer() and m.featureId() == match.featureId()]
        if not duplicate_matches:
            # if not, record this match
            self.matches.append(match)

        # we always return True for valid matches, even if we consider them a duplicate
        # this allows the snapper to compare distances and always return the closest match
        return True

    def get_matches(self):
        """
        Returns the full list of unique layer/feature matches
        """
        return self.matches


class DecoratorFactory:
    """
    Factory class for decorators drawn during the interactive redistrict tool
    operation
    """

    def __init__(self):
        pass

    def create_decorator(self, canvas):  # pylint: disable=unused-argument
        """
        Creates a new QgsMapCanvasItem decorator
        :param canvas: associated map canvas
        :return: QgsMapCanvasItem to display on map if decorations
        are desired
        """
        return None


class InteractiveRedistrictingTool(QgsMapTool):
    """
    A map tool for interactive redistricting operations
    """

    def __init__(self, canvas,
                 handler,
                 district_registry,
                 decorator_factory=None):
        """
        Constructor for map tool
        :param canvas: linked map canvas
        :param handler: redistricting handler object
        :param district_registry: associated district registry
        :param decorator_factory: optional factory for creating map decorations
        during the redistricting operation (e.g. population displays)
        """
        super().__init__(canvas)
        self.handler = handler
        self.district_registry = district_registry
        self.decorator_factory = decorator_factory

        self.snap_indicator = QgsSnapIndicator(self.canvas())
        self.pop_decorator = None

        self.is_active = False
        self.districts = None
        self.current_district = None
        self.click_point = None
        self.modified = set()
        self.handler.redistrict_occured.connect(self.update_decorator)

    def get_district_boundary_matches(self, point):
        """
        Returns a list of snapping matches corresponding to boundaries
        between existing districts
        :param point: map point to snap from
        """

        # use QGIS cursor tolerance setting
        tolerance = QgsTolerance.vertexSearchRadius(self.canvas().mapSettings())

        # collect matching edges
        locator = self.canvas().snappingUtils().locatorForLayer(self.handler.target_layer)
        match_filter = UniqueFeatureEdgeMatchCollectingFilter(tolerance)
        locator.nearestEdge(point, tolerance, match_filter)
        return match_filter.get_matches()

    def get_district_area_match(self, point):
        """
        Returns a possible snapping match corresponding to the area under
        the cursor
        :param point: map point to snap from
        """
        locator = self.canvas().snappingUtils().locatorForLayer(self.handler.target_layer)
        tolerance = QgsTolerance.vertexSearchRadius(self.canvas().mapSettings())
        match = locator.nearestArea(point, tolerance)
        return match

    def get_districts_from_matches(self, matches):
        """
        Returns a list of districts corresponding to a list of snapping matches
        :param matches: snapping matches to scan
        :return: list of district values
        """
        features = self.get_target_features_from_matches(matches)
        return set([f[self.handler.target_field] for f in features])

    def get_target_features_from_matches(self, matches):
        """
        Returns an iterator of target features corresponding to a list of snapping
        matches.
        :param matches: snapping matches to scan
        :return: list of target features
        """
        feature_ids = [match.featureId() for match in matches]
        return self.handler.target_layer.getFeatures(QgsFeatureRequest().setFilterFids(feature_ids))

    def matches_are_valid_for_boundary(self, matches):
        """
        Returns true if a list of matches corresponds to a valid
        district boundary point
        :param matches: list of matches to test
        :return: True if matches correspond to a district boundary
        """

        # valid boundaries consist of two distinct districts
        districts = self.get_districts_from_matches(matches)
        return len(districts) == 2

    def canvasMoveEvent(self, event):  # pylint: disable=missing-docstring
        if not self.is_active:
            # snapping tool - show indicator
            matches = self.get_district_boundary_matches(event.mapPoint())
            if self.matches_are_valid_for_boundary(matches):
                # we require exactly 2 matches from different districts -- cursor must be over a border
                # of two features
                self.snap_indicator.setMatch(matches[0])
            else:
                self.snap_indicator.setMatch(QgsPointLocator.Match())
        elif self.districts:
            dist = self.click_point.distance(event.mapPoint())
            if dist < QgsTolerance.vertexSearchRadius(self.canvas().mapSettings()):
                return
            match = self.get_district_area_match(event.mapPoint())
            p = QgsGeometry.fromPointXY(event.mapPoint())
            targets = [m for m in self.get_target_features_from_matches([match]) if
                       m.id() not in self.modified and m.geometry().intersects(p)]
            if len(targets) == 1:
                target = targets[0]
                old_district = target[self.handler.target_field]
                if not self.current_district:
                    candidates = [d for d in self.districts if d != old_district]
                    if candidates:
                        self.current_district = candidates[0]
                if self.current_district and old_district and self.current_district != old_district:
                    if not self.modified:
                        # first modified district - push edit command
                        self.handler.begin_edit_group(
                            QCoreApplication.translate('LinzRedistrict', 'Redistrict to {}').format(
                                self.district_registry.get_district_title(self.current_district)))

                    self.modified.add(target.id())
                    self.handler.assign_district([target.id()], self.current_district)

    def report_success(self):
        """
        Shows a redistrict successful message in the messagebar, if available
        """
        if iface is not None:
            iface.messageBar().pushMessage(
                self.tr('Redistricted to {}').format(self.district_registry.get_district_title(self.current_district)),
                level=Qgis.Success)

    def keyPressEvent(self, event):  # pylint: disable=missing-docstring
        if event.key() == Qt.Key_Escape and not event.isAutoRepeat():
            self.cancel()

    def cancel(self):
        """
        Cancels an active redistricting operation
        """
        if self.is_active:
            if self.modified:
                self.handler.discard_edit_group()
            self.finalize_operation()

    def finalize_operation(self):
        """
        Finalizes and cleans up after an active redistricting operation
        """
        if self.pop_decorator is not None:
            self.canvas().scene().removeItem(self.pop_decorator)
            self.pop_decorator = None
            self.canvas().update()
        self.is_active = False
        self.districts = None
        self.current_district = None

    def canvasPressEvent(self, event):  # pylint: disable=missing-docstring
        if event.button() == Qt.MiddleButton:
            return
        elif event.button() == Qt.RightButton:
            self.cancel()
            return

        if self.is_active:
            if self.modified:
                self.handler.end_edit_group()
                self.report_success()
            self.finalize_operation()
        elif event.button() == Qt.LeftButton:
            matches = self.get_district_boundary_matches(event.mapPoint())
            districts = self.get_districts_from_matches(matches)
            valid = False
            if not self.matches_are_valid_for_boundary(matches):
                match = self.get_district_area_match(event.mapPoint())
                districts = self.get_districts_from_matches([match])
                if districts:
                    valid = True
            else:
                valid = True

            self.current_district = None
            self.modified = set()
            if valid:
                self.is_active = True
                self.click_point = event.mapPoint()
                self.snap_indicator.setMatch(QgsPointLocator.Match())
                self.districts = districts
                if self.decorator_factory is not None:
                    self.pop_decorator = self.decorator_factory.create_decorator(self.canvas())
                self.canvas().update()

    def update_decorator(self):
        """
        Triggers a redraw of the canvas decorator
        """
        if self.pop_decorator is not None and hasattr(self.pop_decorator, 'redraw'):
            self.pop_decorator.redraw()
