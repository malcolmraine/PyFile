import unittest
import os
from PyFile import file


class TestFile(unittest.TestCase):
    def test_abs_path(self):
        test = file.File("test_file.txt", mode='w+')
        print(test.abs_path)
        self.assertIsInstance(test.abs_path, str)
        self.assertEqual(os.path.exists(test.abs_path), True)
        test.delete()


if __name__ == '__main__':
    unittest.main()
