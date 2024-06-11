"""
Redistricting NZ API test.
"""


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
        cls.httpd_thread.daemon = True
        cls.httpd_thread.start()
        cls.api = NzElectoralApi(f'http://localhost:{cls.port}')
        cls.last_result = None

    def test_format_meshblock_number(self):
        """
        Test formatting a meshblock number to format required by stats api
        """
        self.assertEqual(ConcordanceItem.format_meshblock_number('1'), '0000001')
        self.assertEqual(ConcordanceItem.format_meshblock_number('11'), '0000011')
        self.assertEqual(ConcordanceItem.format_meshblock_number('111111'), '0111111')
        self.assertEqual(ConcordanceItem.format_meshblock_number('1111111'), '1111111')

    def test_format_electorate_id(self):
        """
        Test formatting an electorate id to format required by stats api
        """
        self.assertEqual(ConcordanceItem.format_electorate_id('M01', 'M'), 'M01')
        self.assertEqual(ConcordanceItem.format_electorate_id('S02', 'GS'), 'S02')
        self.assertEqual(ConcordanceItem.format_electorate_id('N02', 'GN'), 'N02')
        self.assertEqual(ConcordanceItem.format_electorate_id('2', 'GS'), 'S02')
        self.assertEqual(ConcordanceItem.format_electorate_id('12', 'GS'), 'S12')

    def test_deformat_electorate_id(self):
        """
        Test deformatting an electorate id from stats api format
        """
        self.assertEqual(ConcordanceItem.deformat_electorate_id('M01'), '1')
        self.assertEqual(ConcordanceItem.deformat_electorate_id('S02'), '2')
        self.assertEqual(ConcordanceItem.deformat_electorate_id('N02'), '2')
        self.assertEqual(ConcordanceItem.deformat_electorate_id('S12'), '12')

    # pylint: disable=unused-argument
    def _parse_result(self, api_method, result, *args, in_args=None, **kwargs):
        """Parse the result and check them"""
        if not in_args:
            in_args = []
        content = result['content']
        self.last_result = result
        if result['status_code'] == 200:
            try:
                with open(api_method + '.json', encoding='utf8') as f:
                    self.assertEqual(content, json.load(f))
            except FileNotFoundError:
                with open(api_method.replace('Results', '') + '_' + in_args[0] + '.json',
                          encoding='utf8') as f:
                    self.assertEqual(content, json.load(f))

            # If POST
            if 'X-Echo' in result['headers']:
                self.assertEqual(json.loads(result['headers']['X-Echo'].decode(
                    'utf-8')), json.loads(self.api.encode_payload(in_args[0]).decode('utf-8')))
    # pylint: enable=unused-argument

    def _parse_async_result(self, api_method, nam, *args, in_args=None, **kwargs):
        """Parse the async results"""
        if not in_args:
            in_args = []
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
        item = ConcordanceItem("0001234", electorate='01', task='GN')
        self.assertEqual(item.electorate, 'N01')
        item = ConcordanceItem("0001234", electorate='01', task='GS')
        self.assertEqual(item.electorate, 'S01')
        item = ConcordanceItem("0001234", electorate='01', task='M')
        self.assertEqual(item.electorate, 'M01')

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
        api = NzElectoralApi(f'http://localhost:{self.port}')
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
        api = NzElectoralApi(f'http://localhost:{self.port}')
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
