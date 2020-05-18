import unittest
import os
import time
import datetime
from PyFile import file


class TestFile(unittest.TestCase):
    def setUp(self) -> None:
        self.test = file.File("test_file.txt", mode='w+')

    def tearDown(self) -> None:
        self.test.delete()

    def test_ext(self):
        self.assertIsInstance(self.test.ext, str)
        self.assertTrue(self.test.ext.startswith('.'))
        self.assertEqual(len(self.test.ext), 4)

    def test_mode(self):
        self.assertEqual(self.test.mode, 'w+')
        self.assertIsInstance(self.test.mode, str)

    def test_owner(self):
        self.assertIn(self.test.owner, [os.getlogin(), os.path.expanduser("~")
                                                    .replace('\\', '/')
                                                    .split('/')[-1]])
        self.assertIsInstance(self.test.owner, str)

    def test_rel_path(self):
        self.assertIsInstance(self.test.rel_path, str)
        self.assertEqual(os.path.exists(self.test.rel_path), True)

    def test_abs_path(self):
        self.assertIsInstance(self.test.abs_path, str)
        self.assertEqual(os.path.exists(self.test.abs_path), True)

    def test_last_modified(self):
        self.assertAlmostEqual(self.test.last_modified, time.time(), places=1)
        self.assertIsInstance(self.test.last_modified, float)

    def test_size(self):
        self.assertEqual(self.test.size, 0)
        self.test.open()
        self.test.write('#' * 100)
        self.test.close()
        self.assertEqual(self.test.size, 100)

    def test_modified(self):
        self.assertFalse(self.test.modified)
        self.test.open()
        self.test.write('#' * 100)
        self.test.close()
        self.assertTrue(self.test.modified)



if __name__ == '__main__':
    unittest.main()
