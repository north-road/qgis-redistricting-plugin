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
import json
import os
import threading
import unittest
from functools import partial

from qgis.PyQt.QtCore import QEventLoop

from redistrict.linz.nz_electoral_api import (BoundaryRequest,
                                              ConcordanceItem,
                                              NzElectoralApi,
                                              Handler)


# pylint: disable=broad-except,attribute-defined-outside-init


class NzElectoralApiTest(unittest.TestCase):
    """Test the NzElectoralApi"""

    DATA_DIR = 'nz_electoral_api'
    API_VERSION = '1.1.5'
    REQUEST_ID = "4479c81b-d21d-4f7d-8db8-85491473a274"

    @classmethod
    def setUpClass(cls):
        """Class setup"""
        os.chdir(os.path.join(os.path.dirname(
            __file__), 'data', cls.DATA_DIR))
        cls.httpd = http.server.HTTPServer(('localhost', 0), Handler)
        cls.port = cls.httpd.server_address[1]
        cls.httpd_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.httpd_thread.setDaemon(True)
        cls.httpd_thread.start()
        cls.api = NzElectoralApi('http://localhost:%s' % cls.port)
        cls.last_result = None

    def _parse_result(self, api_method, result, *args, in_args=[], **kwargs):
        """Parse the result and check them"""
        # pylint: disable=unused-argument
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
                    'utf-8')), json.loads(self.api.encode_payload(in_args[0]).decode('utf-8')))

    def _parse_async_result(self, api_method, nam, *args, in_args=[], **kwargs):
        """Parse the async results"""
        self._parse_result(api_method, self.api.parse_async(
            nam), *args, in_args=in_args, **kwargs)

    def _call(self, api_method, *args, **kwargs):
        """Make the API call"""
        if kwargs.get('blocking', False):
            result = getattr(self.api, api_method)(*args, **kwargs)
            self._parse_result(api_method, result, in_args=args, **kwargs)
        else:
            el = QEventLoop()
            nam = getattr(self.api, api_method)(*args, **kwargs)
            nam.reply.finished.connect(
                partial(self._parse_async_result, api_method, nam, in_args=args))
            nam.reply.finished.connect(el.quit)
            el.exec_(QEventLoop.ExcludeUserInputEvents)

    def test_concordance(self):
        """
        Test creating concordance items
        """
        item = ConcordanceItem("0001234", electorate='N01', task='GN')
        self.assertEqual(item.electorate, 'N01')
        self.assertEqual(item.unformatted_electorate, 'N01')
        item = ConcordanceItem("0001234", electorate='01', task='GN')
        self.assertEqual(item.electorate, 'N01')
        self.assertEqual(item.unformatted_electorate, '01')
        item = ConcordanceItem("0001234", electorate='01', task='GS')
        self.assertEqual(item.electorate, 'S01')
        self.assertEqual(item.unformatted_electorate, '01')
        item = ConcordanceItem("0001234", electorate='01', task='M')
        self.assertEqual(item.electorate, 'M01')
        self.assertEqual(item.unformatted_electorate, '01')

    def test_status(self):
        """Test status API call"""
        self._call('status', blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChanges(self):
        """Test boundaryChanges API call"""
        concordance = [
            ConcordanceItem("0001234", "01", 'GN'),
            ConcordanceItem("0001235", "01", 'GN'),
            ConcordanceItem("0001236", "02", 'GN'),
        ]
        request = BoundaryRequest(concordance, "north")
        self._call('boundaryChanges', request, blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChangesResults(self):
        """Test boundaryChanges get results API call"""
        requestId = self.REQUEST_ID
        self._call('boundaryChangesResults', requestId, blocking=True)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_status_async(self):
        """Test status API call in async mode"""
        self._call('status')
        self.assertEqual(self.last_result['status_code'], 200)

    def test_status_async_error404(self):
        """Test status API call with a 404 code in async mode"""
        self.api.set_qs('error_code=404')
        self._call('status')
        self.api.set_qs('')
        self.assertEqual(self.last_result['status_code'], 404)

    def test_boundaryChanges_async(self):
        """Test boundaryChanges API call in async mode"""
        concordance = [
            ConcordanceItem("0001234", "N01", 'GN'),
            ConcordanceItem("0001235", "N01", 'GN'),
            ConcordanceItem("0001236", "N02", 'GN'),
        ]
        request = BoundaryRequest(concordance, "north")
        self._call('boundaryChanges', request)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_boundaryChangesResults_async(self):
        """Test boundaryChanges get results API call in async mode"""
        requestId = self.REQUEST_ID
        self._call('boundaryChangesResults', requestId)
        self.assertEqual(self.last_result['status_code'], 200)

    def test_api_usage_async(self):
        """Test standard async API usage"""
        api = NzElectoralApi('http://localhost:%s' % self.port)
        nam = api.status()
        self.last_result = ''
        expected = {
            "version": self.API_VERSION,
            "gmsVersion": "LINZ_Output_20180108_2018_V1_00"
        }
        el = QEventLoop()

        def f(nam):
            """Wrapper"""
            self.last_result = api.parse_async(nam)['content']

        nam.reply.finished.connect(partial(f, nam))
        nam.reply.finished.connect(el.quit)
        el.exec_(QEventLoop.ExcludeUserInputEvents)
        self.assertEqual(self.last_result, expected)

    def test_api_usage(self):
        """Test standard sync API usage"""
        api = NzElectoralApi('http://localhost:%s' % self.port)
        result = api.status(blocking=True)
        self.last_result = ''
        expected = {
            "version": self.API_VERSION,
            "gmsVersion": "LINZ_Output_20180108_2018_V1_00"
        }
        self.assertEqual(result['content'], expected)


class NzElectoralApiTestMock(NzElectoralApiTest):
    """Test the NzElectoralApi from real data saved into files"""

    API_VERSION = '1.6.0.2120'
    DATA_DIR = 'nz_electoral_api_mock'
    REQUEST_ID = "e60b8fb4-3eed-4e2e-8c0b-36b5be9f61dd"


if __name__ == "__main__":
    suite = unittest.makeSuite(NzElectoralApiTest)
    suite.addTest(NzElectoralApiTestMock)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
