# -*- coding: utf-8 -*-
"""LINZ Redistricting Plugin - Stats NZ API Request Queue

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

from functools import partial
from typing import Union
from qgis.core import QgsSettings
from qgis.PyQt.QtCore import QObject, pyqtSignal, QTimer
from redistrict.linz.networkaccessmanager import NetworkAccessManager
from redistrict.linz.nz_electoral_api import NzElectoralApi, BoundaryRequest

PROCESS_QUEUE_FREQUENCY_SECONDS = 10


class ApiRequestQueue(QObject):
    """
    A managed queue for ongoing API network requests
    """

    result_fetched = pyqtSignal(dict)
    error = pyqtSignal(BoundaryRequest, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.boundary_change_queue = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_queue)
        self.set_frequency(QgsSettings().value('redistrict/check_every', '30', int, QgsSettings.Plugins))

    def set_frequency(self, frequency: int):
        """
        Sets the frequency to check for completed results
        :param frequency: seconds between checks
        """
        self.timer.stop()
        self.timer.start(frequency * 1000)

    def append_request(self, connector: NzElectoralApi, request: BoundaryRequest):
        """
        Appends a new BoundaryRequest to the queue.
        :param connector: API connector
        :param request: Boundary request object
        """
        result = connector.boundaryChanges(request)
        if isinstance(result, str):
            # no need to wait - we already have a result (i.e. blocking request)
            self.boundary_change_queue.append((connector, request, result))
            self.process_queue()
        else:
            result.reply.finished.connect(partial(self.finished_boundary_request, connector, result, request))

    def clear(self):
        """
        Clears all requests from the queue
        """
        self.boundary_change_queue = []

    def finished_boundary_request(self, connector: NzElectoralApi, request: NetworkAccessManager, boundary_request: BoundaryRequest):
        """
        Triggered when a non-blocking boundary request is finished
        :param connector: API connector
        :param request: completed request
        """
        response = connector.parse_async(request)
        if response['status'] != 200:
            self.error.emit(boundary_request, response['reason'])
            return
        request_id = response['content']
        self.boundary_change_queue.append((connector, boundary_request, request_id))

    def process_queue(self):
        """
        Processes the outstanding queue, checking if any requests have finished calculation
        """
        for (connector, boundary_request, request_id) in self.boundary_change_queue:
            self.check_for_result(connector, boundary_request, request_id)

    def remove_from_queue(self, request_id):
        """
        Removes a request from the queue
        :param request_id: id of request
        """
        self.boundary_change_queue = [c for c in self.boundary_change_queue if c[1] != request_id]

    def check_for_result(self, connector: NzElectoralApi, boundary_request: BoundaryRequest, request_id: str):
        """
        Checks if a boundary request has finished calculating
        :param connector: API connector
        :param boundary_request: original boundary request
        :param request_id: ID of request
        """
        request = connector.boundaryChangesResults(request_id)
        if isinstance(request, dict):
            # no need to wait - we already have a result (i.e. blocking request)
            self.check_boundary_result_reply(request_id, request)
        else:
            request.reply.finished.connect(
                partial(self.finished_boundary_result_request, connector, boundary_request, request_id, request))

    def finished_boundary_result_request(self, connector: NzElectoralApi,
                                         boundary_request: BoundaryRequest,
                                         request_id: str,
                                         request: NetworkAccessManager):
        """
        Triggered when a boundary change result network request has finished
        :param connector: API connector
        :param boundary_request: original boundary request
        :param request_id: ID of request
        :param request: completed request
        """
        results = connector.parse_async(request)['content']
        if results['status'] != 200:
            self.remove_from_queue(request_id)
            self.error.emit(boundary_request, results['reason'])
            return
        self.check_boundary_result_reply(request_id, results)

    def check_boundary_result_reply(self, request_id: str, reply: Union[dict, str]):
        """
        Checks whether the result of a boundary request is a completed result
        :param request_id: ID of request
        :param reply: reply to check
        """
        if isinstance(reply, str) and reply.startswith('Calculation in progress'):
            # not finished...
            return

        self.remove_from_queue(request_id)
        self.result_fetched.emit(reply)
