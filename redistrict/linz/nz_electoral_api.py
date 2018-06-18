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
from typing import Union, Optional, List
import http.server
import threading
import time
from io import BytesIO

from redistrict.linz.networkaccessmanager import NetworkAccessManager, RequestsException
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import (QgsMessageLog,
                       QgsNetworkAccessManager,
                       QgsSettings)

# API Version
GMS_VERSION = "LINZ_Output_20180108_2018_V1_00"


class ConcordanceItem():
    """ConcordanceItem struct
    """

    def __init__(self, censusStandardMeshblock: str, electorate:str):
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

    def __init__(self, concordance: List[ConcordanceItem], area, gmsVersion: str=GMS_VERSION):
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

    def __init__(self, base_url: str, authcfg: str = None, debug=False):
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

    def check(self) -> bool:
        """Check connection and credentials"""
        try:
            result = self.status(blocking=True)
            return result['status_code'] == 200
        except Exception as e:  # pylint: disable=W0703
            QgsMessageLog.logMessage("%s" % e, "REDISTRICT")
            return False

    def set_qs(self, qs: str):
        """Set the query string: mainly used for testing

        :param qs: the query string
        :type qs: str
        """
        self.qs = qs

    @classmethod
    def encode_payload(cls, payload) -> str:
        """Transform the payload to JSON

        :param payload: the payload object
        :type payload: dict
        :return: JSON encoded
        :rtype: str
        """

        return json.dumps(payload.__dict__, default=lambda x: x.__dict__).encode('utf-8')

    @classmethod
    def parse_async(cls, nam) -> dict:
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

    def _base_call(self, path, payload=None, blocking=False) -> Union[dict, NetworkAccessManager]:
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

        path = self.base_url + '/' + path
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
                    blocking=False)

        return nam

    def status(self, blocking=False) -> Union[dict, NetworkAccessManager]:
        """Call the status method of the API

        :param blocking: if the call needs to be synchronous, defaults to False
        :param blocking: bool, optional
        :return: response dictionary or NetworkAccessManager
        :rtype: dict if in blocking mode, NetworkAccessManager if not
        """
        path = "status"
        return self._base_call(path, blocking=blocking)

    def boundaryChanges(self, boundaryRequest: BoundaryRequest, blocking=False) -> Union[str, NetworkAccessManager]:
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

    def boundaryChangesResults(self, boundaryRequestId, blocking=False) -> Union[dict, NetworkAccessManager]:
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
        path = "boundaryChanges" + '/' + boundaryRequestId
        return self._base_call(path, blocking=blocking)


class Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP test handler

    POST: add X-Echo header with POST'ed data

    Query string args:

    - delay=<int> seconds for delay
    - error_code=<int> send this error code

    """

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.path = None
        self.qs = None

    def _patch_path(self):
        """Patch the path"""
        if len(self.path.split('/')) > 2:
            self.path = '_'.join(self.path.rsplit('/', 1))
        if self.path.startswith('/'):
            self.path = self.path[1:]
        self.path = './' + self.path
        try:
            self.qs = {k.split('=')[0]: k.split('=')[1]
                       for k in self.path.split('?')[1].split('&')}
            self.path = self.path.split('?')[0]
        except Exception:  # pylint: disable=broad-except
            self.qs = {}
        self.path += '.json'
        if 'delay' in self.qs:
            time.sleep(int(self.qs['delay']))

    def _code(self):
        """Return the error code from query string"""
        return int(self.qs.get('error_code', 200))

    def do_GET(self):
        """GET handler
        """
        self._patch_path()
        self.send_response(self._code())
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = BytesIO()
        with open(self.path, 'rb') as f:
            response.write(f.read())
        self.wfile.write(response.getvalue())

    def do_POST(self):
        """POST handler: Echoes payload in the header"""
        self._patch_path()
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(self._code())
        self.send_header("X-Echo", data_string.decode('utf-8'))
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = BytesIO()
        with open(self.path, 'rb') as f:
            response.write(f.read())
        self.wfile.write(response.getvalue())


class MockStatsApi(NzElectoralApi):
    """Mock Statistics NZ API
    """

    DATA_DIR = 'mock_electoral_api'

    def __init__(self):
        """Construct a mock API
        """
        os.chdir(os.path.join(os.path.dirname(
            __file__), 'data', self.DATA_DIR))
        self.httpd = http.server.HTTPServer(('localhost', 0), Handler)
        self.port = self.httpd.server_address[1]
        self.httpd_thread = threading.Thread(target=self.httpd.serve_forever)
        self.httpd_thread.setDaemon(True)
        self.httpd_thread.start()
        super().__init__(base_url='http://localhost:%s' % self.port, authcfg=None, debug=True)


def get_api_connector(use_mock: Optional[bool] = None, authcfg: Optional[str] = None) -> NzElectoralApi:
    """
    Creates a new API connector (either real or mock, depending on user's settings

    :param use_mock: if True, always returns a mock connection. If False, always
    returns a real connection. If None, returns the connector matching the user's
    settings preference

    :param authcfg: if specified, overrides the stored authcfg key with the
    manually specified one
    """
    mock = QgsSettings().value('redistrict/use_mock_api', False, bool,
                               QgsSettings.Plugins) if use_mock is None else use_mock
    if mock:
        return MockStatsApi()

    auth_key = authcfg if authcfg is not None else QgsSettings().value('redistrict/auth_config_id', None, str, QgsSettings.Plugins)
    base_url = QgsSettings().value('redistrict/base_url', '', str, QgsSettings.Plugins)

    return NzElectoralApi(base_url=base_url, authcfg=auth_key)
