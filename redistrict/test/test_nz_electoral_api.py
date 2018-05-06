# coding=utf-8
"""Redistricting NZ API test.

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

import http.server
import time
import json
import os
import threading
import unittest
from io import BytesIO
from functools import partial

from qgis.PyQt.QtCore import QEventLoop

from redistrict.linz.nz_electoral_api import (BoundaryRequest, ConcordanceItem,
                                              NzElectoralApi)


class Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP test handler

    POST: add X-Echo header with POST'ed data

    Query string args:

    - delay=<int> seconds for delay
    - error_code=<int> send this error code

    """


    def _patch_path(self):
        if len(self.path.split('/')) > 2:
            self.path = '_'.join(self.path.rsplit('/', 1))
        self.path = './' + self.path
        try:
            self.qs = {k.split('=')[0]: k.split('=')[1]
                       for k in self.path.split('?')[1].split('&')}
            self.path = self.path.split('?')[0]
        except:
            self.qs = {}
        self.path += '.json'
        if 'delay' in self.qs:
            time.sleep(int(self.qs['delay']))


    def _code(self):
        return int(self.qs.get('error_code', 200))

    def do_GET(self):
        self._patch_path()
        self.send_response(self._code())
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = BytesIO()
        with open(self.path, 'rb') as f:
            response.write(f.read())
        self.wfile.write(response.getvalue())

    def do_POST(self):
        """Echoes payload in the header"""
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


class NzElectoralApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.chdir(os.path.join(os.path.dirname(
            __file__), 'data', 'nz_electoral_api'))
        cls.httpd = http.server.HTTPServer(('localhost', 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.httpd_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.httpd_thread.setDaemon(True)
        cls.httpd_thread.start()
        cls.api = NzElectoralApi('http://localhost:%s' % cls.port)
        cls.last_result = None

    def _parse_result(self, api_method, result, *args, in_args=[], **kwargs):

        content = result['content']
        self.last_result = result
        if result['status_code'] == 200:
            try:
                with open(api_method + '.json') as f:
                    self.assertEqual(content, json.load(f))
            except FileNotFoundError:
                with open(api_method.replace('Results', '') + '_' + in_args[0] + '.json') as f:
                    self.assertEqual(content, json.load(f))

            # If POST
            if 'X-Echo' in result['headers']:
                self.assertEqual(json.loads(result['headers']['X-Echo'].decode(
                    'utf-8')), json.loads(self.api._encode_payload(in_args[0]).decode('utf-8')))

    def _parse_async_result(self, api_method, nam, *args, in_args=[], **kwargs):
        self._parse_result(api_method, self.api.parse_async(nam), *args, in_args=in_args, **kwargs)

    def _call(self, api_method, *args, **kwargs):

        if kwargs.get('blocking', False):
            result = getattr(self.api, api_method)(*args, **kwargs)
            self._parse_result(api_method, result, in_args=args, **kwargs)
        else:
            el = QEventLoop()
            nam = getattr(self.api, api_method)(*args, **kwargs)
            nam.reply.finished.connect(partial(self._parse_async_result, api_method, nam, in_args=args))
            nam.reply.finished.connect(el.quit)
            el.exec_(QEventLoop.ExcludeUserInputEvents)

    def test_status(self):
        self._call('status', blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChanges(self):
        concordance = [
            ConcordanceItem("0001234", "N01"),
            ConcordanceItem("0001235", "N01"),
            ConcordanceItem("0001236", "N02"),
        ]
        request = BoundaryRequest(concordance, "north")
        self._call('boundaryChanges', request, blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChangesResults(self):
        requestId = "4479c81b-d21d-4f7d-8db8-85491473a274"
        self._call('boundaryChangesResults', requestId, blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_status_async(self):
        self._call('status')
        self.assertEqual(self.last_result['status_code'], 200)

    def test_status_async_error404(self):
        self.api.set_qs('error_code=404')
        self._call('status')
        self.api.set_qs('')
        self.assertEqual(self.last_result['status_code'], 404)

    def test_boundaryChanges_async(self):
        concordance = [
            ConcordanceItem("0001234", "N01"),
            ConcordanceItem("0001235", "N01"),
            ConcordanceItem("0001236", "N02"),
        ]
        request = BoundaryRequest(concordance, "north")
        self._call('boundaryChanges', request)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChangesResults_async(self):
        requestId = "4479c81b-d21d-4f7d-8db8-85491473a274"
        self._call('boundaryChangesResults', requestId)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_api_usage_async(self):
        """Standard async API usage"""
        api = NzElectoralApi('http://localhost:%s' % self.port)
        nam = api.status()
        self.last_result = ''
        expected = {
            "version" : "1.1.5",
            "gmsVersion" : "LINZ_Output_20180108_2018_V1_00"
        }
        el = QEventLoop()

        def f(nam):
            self.last_result = api.parse_async(nam)['content']

        nam.reply.finished.connect(partial(f, nam))
        nam.reply.finished.connect(el.quit)
        el.exec_(QEventLoop.ExcludeUserInputEvents)
        self.assertEqual(self.last_result, expected)

    def test_api_usage(self):
        """Standard sync API usage"""
        api = NzElectoralApi('http://localhost:%s' % self.port)
        result = api.status(blocking=True)
        self.last_result = ''
        expected = {
            "version" : "1.1.5",
            "gmsVersion" : "LINZ_Output_20180108_2018_V1_00"
        }
        self.assertEqual(result['content'], expected)


if __name__ == "__main__":
    suite = unittest.makeSuite(NzElectoralApiTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
