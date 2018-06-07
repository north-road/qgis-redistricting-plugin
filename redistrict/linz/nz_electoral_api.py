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
from redistrict.linz.networkaccessmanager import NetworkAccessManager, RequestsException
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import QgsMessageLog, QgsNetworkAccessManager


# API Version
GMS_VERSION = "LINZ_Output_20180108_2018_V1_00"


class ConcordanceItem():
    """ConcordanceItem struct
    """

    def __init__(self, censusStandardMeshblock, electorate):
        """Initialise a ConcordanceItem

        Example:

            {"censusStandardMeshblock": "0001234", "electorate": "N01"},

        :param censusStandardMeshblock: block id
        :type censusStandardMeshblock: str
        :param electorate: electorate id
        :type electorate: str
        """

        self.censusStandardMeshblock = censusStandardMeshblock
        self.electorate = electorate


class BoundaryRequest():
    """BoundaryRequest struct
    """
    def __init__(self, concordance, area, gmsVersion=GMS_VERSION):
        """Initialise a BoundaryRequest

        :param concordance: one or more ConcordanceItem
        :type concordance: array
        :param type: name of the area [M,GN,GS]
        :type type: str
        :param gmsVersion: API version, defaults to GMS_VERSION
        :param gmsVersion: str, optional
        """

        self.type = area
        self.gmsVersion = gmsVersion
        self.concordance = concordance


class NzElectoralApi(QObject):
    """Interacts with the NZ Electoral API
    """

    finished = pyqtSignal(dict)

    POST = 'post'
    GET = 'get'

    def __init__(self, base_url, authcfg=None, debug=False):
        """Construct the API with base URL

        :param base_url: base URL for the API endpoint
        :type base_url: str
        :param authcfg: authentication configuration id, defaults to None
        :param authcfg: str, optional
        :param debug: log network calls and messages in the message logs, defaults to False
        :param debug: bool
        """
        super().__init__()
        self.authcfg = authcfg
        self.base_url = base_url
        self.debug = debug
        self.qs = ''
        # Just in case case the user entered wrong credentials in previous attempt ...
        QgsNetworkAccessManager.instance().clearAccessCache()

    def check(self):
        """Check connection and credentials"""
        try:
            result = self.status(blocking=True)
            return result['status_code'] == 200
        except Exception as e:  # pylint: disable=W0703
            QgsMessageLog.logMessage("%s" % e, "REDISTRICT")
            return False

    def set_qs(self, qs):
        """Set the query string: mainly used for testing

        :param qs: the query string
        :type qs: str
        """
        self.qs = qs

    @classmethod
    def encode_payload(cls, payload):
        """Transform the payload to JSON

        :param payload: the payload object
        :type payload: dict
        :return: JSON encoded
        :rtype: str
        """

        return json.dumps(payload.__dict__, default=lambda x: x.__dict__).encode('utf-8')

    @classmethod
    def parse_async(cls, nam):
        """Transform into JSON the content component of the response

        :param nam: network access manager wrapper instance
        :type nam: NetworkAccessManager
        :return: transformed result
        :rtype: dict
        """
        result = nam.httpResult()
        try:
            result['content'] = json.loads(result['content'].decode('utf-8'))
        except json.decoder.JSONDecodeError:
            result['content'] = {}
        return result

    def _base_call(self, path, payload=None, blocking=False):
        """Base call

        This call can work in blocking (sync) or non-blocking mode (async)

        :param path: the path to call
        :type path: str
        :param payload: the payload for post calls, defaults to None
        :param payload: str, optional
        :param blocking: if the call needs to be synchronous, defaults to False
        :param blocking: bool, optional
        :return: response dictionary or NetworkAccessManager
        :rtype: dict if in blocking mode, NetworkAccessManager if not
        """
        if payload is not None:
            method = self.POST
        else:
            method = self.GET

        path = os.path.join(self.base_url, path)
        nam = NetworkAccessManager(self.authcfg, debug=self.debug)

        if payload is not None:
            payload = self.encode_payload(payload)

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
        """Call the status method of the API

        :param blocking: if the call needs to be synchronous, defaults to False
        :param blocking: bool, optional
        :return: response dictionary or NetworkAccessManager
        :rtype: dict if in blocking mode, NetworkAccessManager if not
        """
        path = "status"
        return self._base_call(path, blocking=blocking)

    def boundaryChanges(self, boundaryRequest, blocking=False):
        """Call the boundaryChange method of the API,
        sends changed data and gets a requestId in return.
        The requestId can be used to retrieve the results
        with boundaryChangesResults

        :param blocking: if the call needs to be synchronous, defaults to False
        :param blocking: bool, optional
        :return: response requestId or NetworkAccessManager
        :rtype: str if in blocking mode, NetworkAccessManager if not
        """
        path = "boundaryChanges"
        return self._base_call(path, payload=boundaryRequest, blocking=blocking)

    def boundaryChangesResults(self, boundaryRequestId, blocking=False):
        """Call the boundaryChange method of the API with a  boundaryRequestId and retrieves the updated results.

        Response codes
            200
            Boundary change calculation has completed successfully. BoundaryResponse
            202
            Calculation is in progress. String
            422
            Validation error ErrorResponse

        :param blocking: if the call needs to be synchronous, defaults to False
        :param blocking: bool, optional
        :return: response requestId or NetworkAccessManager
        :rtype: dict if in blocking mode, NetworkAccessManager if not

        """
        path = os.path.join("boundaryChanges", boundaryRequestId)
        return self._base_call(path, blocking=blocking)
