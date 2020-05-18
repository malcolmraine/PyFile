import unittest
import os
import time
from PyFile import file


# Many of these tests only check basic equality and type.

class TestFile(unittest.TestCase):
    def setUp(self):
        self.filename = "test_file.txt"
        self.test = file.File(self.filename, open_file=True, mode="w+")

    def tearDown(self):
        self.test.close()
        self.test.delete()
        self.test = None

    def test_init(self):
        pass

    def test_basename(self):
        self.assertEqual(self.test.basename, self.filename)
        self.assertIsInstance(self.test.basename, str)

    def test_dirname(self):
        self.assertEqual(self.test.dirname, os.path.abspath("."))
        self.assertIsInstance(self.test.dirname, str)
        self.assertTrue(os.path.isdir(self.test.dirname))

    def test_filename(self):
        self.assertEqual(self.test.filename, "test_file")
        self.assertIsInstance(self.test.filename, str)

    def test_ext(self):
        self.assertIsInstance(self.test.ext, str)
        self.assertTrue(self.test.ext.startswith("."))
        self.assertEqual(len(self.test.ext), 4)

    def test_mode(self):
        self.assertEqual(self.test.mode, "w+")
        self.assertIsInstance(self.test.mode, str)

    def test_owner(self):
        self.assertIn(
            self.test.owner,
            [os.getlogin(), os.path.expanduser("~").replace("\\", "/").split("/")[-1]],
        )
        self.assertIsInstance(self.test.owner, str)

    def test_group(self):
        pass

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
        self.test.write("#" * 100)
        self.test.close()
        self.assertEqual(self.test.size, 100)

    def test_modified(self):
        self.assertFalse(self.test.modified)
        self.test.write("#" * 100)
        self.test.close()
        self.assertTrue(self.test.modified)

    def test_line_cnt(self):
        self.assertEqual(self.test.line_cnt, 0)
        self.test.write("#" * 100)
        # self.assertEqual(self.test.line_cnt, 1)
        # self.test.write("#" * 100)
        # self.assertEqual(self.test.line_cnt, 2)
        # self.test.write("#" * 100)
        # self.assertEqual(self.test.line_cnt, 3)

    def test_stat(self):
        pass

    def test_chmod(self):
        pass

    def test_touch(self):
        pass

    def test_open(self):
        self.assertTrue(self.test.is_open)
        self.test.close()
        self.assertFalse(self.test.is_open)
        self.test.open()
        self.assertTrue(self.test.is_open)

    def test_close(self):
        self.assertTrue(self.test.is_open)
        self.test.close()
        self.assertFalse(self.test.is_open)

    def test_md5(self):
        # Test when file is empty.
        self.assertIsInstance(self.test.md5(), str)
        self.assertEqual(len(self.test.md5()), 32)

        # Test when the number of bytes of the file are less than the hash block size.
        self.test.write("#" * 1000)
        self.assertIsInstance(self.test.md5(), str)
        self.assertEqual(len(self.test.md5()), 32)

        # Test when the number of bytes in the file exceeds the hash block size.
        self.test.write("#" * 100000)
        self.assertIsInstance(self.test.md5(), str)
        self.assertEqual(len(self.test.md5()), 32)

    def test_sha256(self):
        # Test when file is empty.
        self.assertIsInstance(self.test.sha256(), str)
        self.assertEqual(len(self.test.sha256()), 64)

        # Test when the number of bytes of the file are less than the hash block size.
        self.test.write("#" * 1000)
        self.assertIsInstance(self.test.sha256(), str)
        self.assertEqual(len(self.test.sha256()), 64)

        # Test when the number of bytes in the file exceeds the hash block size.
        self.test.write("#" * 100000)
        self.assertIsInstance(self.test.sha256(), str)
        self.assertEqual(len(self.test.sha256()), 64)

    def test_delete(self):
        self.assertTrue(os.path.exists(self.test.abs_path))
        self.assertTrue(os.path.isfile(self.test.abs_path))
        self.test.delete()
        self.assertFalse(os.path.exists(self.test.abs_path))
        self.assertFalse(os.path.isfile(self.test.abs_path))

    def test_read(self):
        self.assertEqual(len(self.test.read()), 0)
        self.assertEqual(len(self.test.read(0)), 0)
        self.test.write("#" * 100)
        # self.assertEqual(len(self.test.read()), 100)
        self.assertEqual(len(self.test.read(-1)), 0)

    def test_readlines(self):
        self.assertIsInstance(self.test.readlines(), list)
        self.assertEqual(len(self.test.readlines()), 0)

    def test_write(self):
        pass

    def test_backup(self):
        pass

    def test_grep(self):
        pass


if __name__ == "__main__":
    unittest.main()
