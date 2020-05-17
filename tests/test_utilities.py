import unittest
from PyFile import utilities


class TestUtilities(unittest.TestCase):
    def test_get_formatted_datetime(self):
        self.assertIsInstance(utilities.get_formatted_datetime(), str)
        self.assertEqual(len(utilities.get_formatted_datetime()), 21)


if __name__ == '__main__':
    unittest.main()
