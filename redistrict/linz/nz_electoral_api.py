# coding=utf-8
"""Redistricting NZ API.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = '(C) 2018 by Alessandro Pasotti'
__date__ = '05/05/2018'
__copyright__ = 'Copyright 2018, North Road'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import json
import os
from functools import partial
from redistrict.linz.networkaccessmanager import NetworkAccessManager, RequestsException
from qgis.PyQt.QtCore import QObject, pyqtSignal

# API Version
GMS_VERSION = "LINZ_Output_20180108_2018_V1_00"


class ConcordanceItem():

    def __init__(self, censusStandardMeshblock, electorate):
        """[summary]

        Arguments:
            self {[type]} -- [description]

        Example:

            "censusStandardMeshblock": "0001235", "electorate": "N01"

        """
        self.censusStandardMeshblock = censusStandardMeshblock
        self.electorate = electorate


class BoundaryRequest():

    def __init__(self, concordance, area, gmsVersion=GMS_VERSION):
        self.area = area
        self.gmsVersion = GMS_VERSION
        self.concordance = concordance


class NzElectoralApi(QObject):
    """Interacts with the NZ Electoral API
    """

    finished = pyqtSignal(dict)

    POST = 'post'
    GET = 'get'

    def __init__(self, base_url, authcfg=None):
        """Construct the API with base URL
        """
        super().__init__()
        self.authcfg = authcfg
        self.base_url = base_url
        self.qs = ''

    def set_qs(self, qs):
        self.qs = qs

    @classmethod
    def _encode_payload(cls, payload):
        return json.dumps(payload.__dict__, default=lambda x: x.__dict__).encode('utf-8')

    @classmethod
    def parse_async(self, nam):
        result = nam.httpResult()
        try:
            result['content'] = json.loads(result['content'].decode('utf-8'))
        except json.decoder.JSONDecodeError as e:
            result['content'] = {}
        return result

    def _base_call(self, path, payload=None, blocking=False):
        """Base call

        Status code is in result.status_code

        :param path: the path to call
        :type path: str
        :param payload: the payload for post calls, defaults to None
        :param payload: str, optional
        :return: response dictionary
        :rtype: dict
        """

        if payload is not None:
            method = self.POST
        else:
            method = self.GET

        path = os.path.join(self.base_url, path)
        nam = NetworkAccessManager(self.authcfg)

        if payload is not None:
            payload = self._encode_payload(payload)

        if self.qs:
            path += '?' + self.qs

        if blocking:
            try:
                (response, content) = nam.request(path,
                                                  method=method,
                                                  body=payload,
                                                  headers={
                                                      b'Content-Type': b'application/json'
                                                  })
                response['content'] = json.loads(content.decode('utf-8'))
            except RequestsException as e:
                # Handle exception
                response = {
                    'status_code': -1  # Unknown
                }
                response['content'] = json.dumps(str(e))
            return response

        # Async
        nam.request(path,
                    method=method,
                    body=payload,
                    headers={
                        b'Content-Type': b'application/json'
                    },
                    blocking=False
                    )

        return nam

    def status(self, blocking=False):
        path = "status"
        return self._base_call(path, blocking=blocking)

    def boundaryChanges(self, boundaryRequest, blocking=False):
        """Request a boundary change

        Returns:
            requestId: integer
        """
        path = "boundaryChanges"
        return self._base_call(path, payload=boundaryRequest, blocking=blocking)

    def boundaryChangesResults(self, boundaryRequestId, blocking=False):
        """
        Responses
            200
            Boundary change calculation has completed successfully. BoundaryResponse
            202
            Calculation is in progress. String
            422
            Validation error ErrorResponse
        """
        path = os.path.join("boundaryChanges", boundaryRequestId)
        return self._base_call(path, blocking=blocking)
