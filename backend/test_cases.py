#Unit tests for all the backend controllers
# To run this, from the root directory run: python -m unittest discover backend

import sys
from unittest.mock import MagicMock, patch
sys.modules['flask_caching'] = MagicMock()  # Mock flask_caching so that there's no import errors

import unittest
from backend.data_metrics import Controller

class TestController(unittest.TestCase):
    def setUp(self):
        self.controller = Controller()

    @patch.object(Controller, 'get_privacyspy_data', return_value=[{"name": "TestApp", "score": 8, "icon": "test.png", "rubric": [], "slug": "testapp", "parent": None, "sources": ["https://example.com/policy"]}])
    def test_get_privacyspy_data_success(self, mock_privspy):
        result = self.controller.get_privacyspy_data()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["name"], "TestApp")

    @patch.object(Controller, 'get_privacyspy_info', return_value=[{"company": "TestApp", "policy_score": 7, "icon": "test.png", "rubric": [], "slug": "testapp"}])
    def test_get_privacyspy_info_exact(self, mock_privinfo):
        res = self.controller.get_privacyspy_info("TestApp")
        self.assertIsInstance(res, list)
        self.assertIn("company", res[0])

    @patch.object(Controller, 'get_tosdr_data', return_value={"name": "TestApp", "rating": "B", "image": "img.png", "documents": [{"name": "policy", "url": "https://test.com/policy"}], "points": []})
    def test_get_tosdr_data_success(self, mock_tosdr):
        res = self.controller.get_tosdr_data("TestApp")
        self.assertIsInstance(res, dict)
        self.assertEqual(res["rating"], "B")

    def test_grade_site(self):
        self.assertEqual(self.controller.grade_site('A'), 9)
        self.assertEqual(self.controller.grade_site('B'), 7)
        self.assertEqual(self.controller.grade_site('E'), 1)
        self.assertEqual(self.controller.grade_site('Unknown'), 0)

    def test_grade_site_values(self):
        grades = {'A':9, 'B':7, 'C':5, 'D':3, 'E':1, 'N/A':0}
        for rating, expected in grades.items():
            self.assertEqual(self.controller.grade_site(rating), expected)
        self.assertEqual(self.controller.grade_site('Z'), 0)

    @patch.object(Controller, 'overall_privacy_score', return_value=7.5)
    def test_overall_privacy_score(self, mock_privscore):
        privacyspy_data = [{"policy_score": 8}]
        tosdr_data = {"rating": "B"}
        score = self.controller.overall_privacy_score(privacyspy_data, tosdr_data)
        self.assertEqual(score, 7.5)


    @patch.object(Controller, 'get_policy_urls', return_value={"privacyspy": ["https://ps.com/p1", "https://ps.com/p2"], "tosdr": ["https://tosdr.com/policy"]})
    def test_get_policy_urls(self, mock_policyurls):
        privacyspy_data = [{"sources": ["https://ps.com/p1", "https://ps.com/p2"]}]
        tosdr_data = {"documents": [{"name": "Policy", "url": "https://tosdr.com/policy"}]}
        result = self.controller.get_policy_urls(privacyspy_data, tosdr_data)
        self.assertIsInstance(result, dict)
        self.assertIn("privacyspy", result)
        self.assertIn("tosdr", result)

    @patch.object(Controller, 'get_site_image', return_value="test.png")
    def test_get_site_image(self, mock_img):
        privacyspy_data = [{"icon": "test.png"}]
        tosdr_data = {"image": "http://example.com/img.png"}
        result = self.controller.get_site_image(privacyspy_data, tosdr_data)
        self.assertTrue(isinstance(result,str))
        self.assertTrue(result.endswith(".png"))

if __name__ == '__main__':
    unittest.main()
