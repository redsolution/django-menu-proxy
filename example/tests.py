import unittest
from django.test import Client

class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_views(self):
        client = Client()
        self.assertEqual(client.get('/notfound').status_code, 404)
#        self.assertEqual(client.get('/page/index/').content , '')
        
    def tearDown(self):
        pass
