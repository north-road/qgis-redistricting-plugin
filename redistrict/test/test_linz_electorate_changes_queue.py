"""
LINZ Electorate Changes Queue test.
"""

import unittest
from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsGeometry,
                       QgsRectangle,
                       NULL)
from redistrict.linz.electorate_changes_queue import (
    ElectorateEditQueue
)
from redistrict.test.test_linz_redistrict_handler import make_user_log_layer
from redistrict.test.utilities import normalized_wkt


class LINZElectorateQueueTest(unittest.TestCase):
    """Test ElectorateEditQueue."""

    def testQueue(self):  # pylint: disable=too-many-statements
        """
        Test queue operations
        """
        user_log_layer = make_user_log_layer()
        district_layer = QgsVectorLayer(
            "Polygon?crs=EPSG:4326&field=fld1:string&field=estimated_pop:int&field=stats_nz_pop:int&field=stats_nz_var_20:int&field=stats_nz_var_23:int&field=invalid:int&field=invalid_reason:string",
            "source", "memory")
        d = QgsFeature()
        d.setAttributes(["test1", NULL, 11111, 12, 13, 1, 'x'])
        d.setGeometry(QgsGeometry.fromRect(QgsRectangle(5, 0, 10, 5)))
        d2 = QgsFeature()
        d2.setAttributes(["test2", NULL, 11112, 22, 23, 0, 'y'])
        d2.setGeometry(QgsGeometry.unaryUnion(
            [QgsGeometry.fromRect(QgsRectangle(5, 5, 10, 10)), QgsGeometry.fromRect(QgsRectangle(0, 10, 10, 15))]))
        d3 = QgsFeature()
        d3.setAttributes(["test3", NULL, 11113, 32, 33, 1, 'z'])
        d3.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 5, 5, 10)))
        d4 = QgsFeature()
        d4.setAttributes(["test4", NULL, 11114, 42, 43, 0, 'xx'])
        d4.setGeometry(QgsGeometry.fromRect(QgsRectangle(0, 0, 5, 5)))
        d5 = QgsFeature()
        d5.setAttributes(["aaa", NULL, 11115, 52, 53, 1, 'yy'])
        success, [d, d2, d3, d4, d5] = district_layer.dataProvider().addFeatures([d, d2, d3, d4, d5])
        self.assertTrue(success)

        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['test1', NULL, 11111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((5 0, 5 5, 10 5, 10 0, 5 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])

        queue = ElectorateEditQueue(electorate_layer=district_layer, user_log_layer=user_log_layer)
        self.assertFalse(queue.back())
        self.assertFalse(queue.forward())

        self.assertEqual(user_log_layer.featureCount(), 0)
        user_log_f1 = QgsFeature(user_log_layer.fields())
        user_log_f1['username'] = 'test user'
        user_log_f2 = QgsFeature(user_log_layer.fields())
        user_log_f2['username'] = 'test user2'

        queue.push_changes({d.id(): {0: 'xtest1', 2: 21111}},
                           {d.id(): QgsGeometry.fromRect(QgsRectangle(115, 0, 110, 5))}, [user_log_f1, user_log_f2])
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], ['test user', 'test user2'])

        user_log_f3 = QgsFeature(user_log_layer.fields())
        user_log_f3['username'] = 'test user3'
        user_log_f4 = QgsFeature(user_log_layer.fields())
        user_log_f4['username'] = 'test user4'

        queue.push_changes({d2.id(): {0: 'xtest2', 2: 31111},
                            d3.id(): {0: 'xtest3', 3: 42222}},
                           {d2.id(): QgsGeometry.fromRect(QgsRectangle(215, 0, 210, 25)),
                            d3.id(): QgsGeometry.fromRect(QgsRectangle(110, 1, 150, 4))}, [user_log_f3, user_log_f4])
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['xtest2', NULL, 31111, 22, 23, 0, 'y'],
                          ['xtest3', NULL, 11113, 42222, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((210 0, 210 25, 215 25, 215 0, 210 0))',
                          'Polygon ((110 1, 110 4, 150 4, 150 1, 110 1))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()],
                         ['test user', 'test user2', 'test user3', 'test user4'])

        self.assertFalse(queue.forward())

        self.assertTrue(queue.back())
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], ['test user', 'test user2'])

        self.assertTrue(queue.back())

        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['test1', NULL, 11111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((5 0, 5 5, 10 5, 10 0, 5 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], [])

        self.assertFalse(queue.back())

        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['test1', NULL, 11111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((5 0, 5 5, 10 5, 10 0, 5 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], [])

        self.assertTrue(queue.forward())
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], ['test user', 'test user2'])

        self.assertTrue(queue.forward())
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['xtest2', NULL, 31111, 22, 23, 0, 'y'],
                          ['xtest3', NULL, 11113, 42222, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((210 0, 210 25, 215 25, 215 0, 210 0))',
                          'Polygon ((110 1, 110 4, 150 4, 150 1, 110 1))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()],
                         ['test user', 'test user2', 'test user3', 'test user4'])

        self.assertFalse(queue.forward())
        self.assertTrue(queue.back())
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], ['test user', 'test user2'])

        queue.forward()
        queue.rollback()
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['test1', NULL, 11111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((5 0, 5 5, 10 5, 10 0, 5 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], [])

        self.assertTrue(queue.forward())
        self.assertEqual([f.attributes() for f in district_layer.getFeatures()],
                         [['xtest1', NULL, 21111, 12, 13, 1, 'x'],
                          ['test2', NULL, 11112, 22, 23, 0, 'y'],
                          ['test3', NULL, 11113, 32, 33, 1, 'z'],
                          ['test4', NULL, 11114, 42, 43, 0, 'xx'],
                          ['aaa', NULL, 11115, 52, 53, 1, 'yy']])
        self.assertEqual([normalized_wkt(f.geometry()) for f in district_layer.getFeatures()],
                         ['Polygon ((110 0, 110 5, 115 5, 115 0, 110 0))',
                          'Polygon ((0 10, 0 15, 10 15, 10 10, 10 5, 5 5, 5 10, 0 10))',
                          'Polygon ((0 5, 0 10, 5 10, 5 5, 0 5))',
                          'Polygon ((0 0, 0 5, 5 5, 5 0, 0 0))',
                          ''])
        self.assertEqual([f['username'] for f in user_log_layer.getFeatures()], ['test user', 'test user2'])


if __name__ == "__main__":
    suite = unittest.makeSuite(LINZElectorateQueueTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
