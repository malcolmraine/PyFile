#!/usr/bin/env python
"""
File: file.py
Description:
Author: Malcolm Hall
Version: 1

MIT License

Copyright (c) 2020 Malcolm Hall

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import os
import pathlib
from functools import lru_cache
from enum import Enum
from hashlib import sha256, md5
import zipfile
import re
from PyFile.config import HASH_BLOCK_SIZE
from PyFile import utilities


FILE_MODES: set = {
    "r",
    "rb",
    "r+",
    "rb+",
    "w",
    "wb",
    "w+",
    "wb+",
    "a",
    "ab",
    "a+",
    "ab+",
}
CREATE_MODES: set = {"w", "wb", "w+", "wb+", "a", "ab", "a+", "ab+"}


class HashType(Enum):
    STRING = 0
    BYTES = 1


class FileClass(Enum):
    HIDDEN = 0
    TEMPORARY = 1
    HIDDEN_TEMP = 2
    NORMAL = 3


class File(object):
    __slots__ = [
        "_path",
        "_mode",
        "_path_obj",
        "cached_stamp",
        "_file_io_obj",
        "exists",
        "is_open",
        "file_class",
        "deleted",
        "backup_file",
        "_stat",
    ]

    def __init__(self, path: str, open_file=True, mode="r", temporary=False):
        self._path: str = path
        self._mode: str = mode
        self._path_obj: pathlib.Path or None = None
        self.cached_stamp: float = -1
        self._file_io_obj = None
        self.exists: bool = True
        self.is_open: bool = False
        self.file_class: FileClass or None = None
        self.deleted: bool = False
        self.backup_file: str or None = None
        self._stat = None

        if not os.path.exists(path) and mode in CREATE_MODES:
            open(path, mode).close()

        if os.path.exists(path) and os.path.isfile(path):
            self._path_obj: pathlib.Path = pathlib.Path(path)
            self._stat = os.stat(self.abs_path)

            if open_file:
                self.open(mode)

            if self.basename[0].startswith("."):
                if temporary:
                    self.file_class = FileClass.HIDDEN_TEMP
                else:
                    self.file_class = FileClass.HIDDEN
            elif not self.basename[0].startswith("."):
                if temporary:
                    self.file_class = FileClass.TEMPORARY
                else:
                    self.file_class = FileClass.NORMAL

        self.cached_stamp: float = os.stat(self.abs_path).st_mtime
        self.exists: bool = True

    def __del__(self):
        """
        Destructor for the class instance. Deletes the related file if it is marked as temporary.

        :return: No return value
        """
        self.close()
        if (
            self.file_class == FileClass.TEMPORARY
            or self.file_class == FileClass.HIDDEN_TEMP
        ):
            self.delete()

    @property
    @lru_cache(maxsize=1)
    def basename(self) -> str:
        """
        Property returning the name of the file with the extension.

        :return: String containing the name of the file.
        """
        return str(self._path_obj.name)

    @property
    @lru_cache(maxsize=1)
    def dirname(self) -> str:
        """
        Property returning the directory the file is located in.

        :return: String containing the name of the file.
        """
        return self.abs_path[: -(len(self.basename) + 1)]

    @property
    @lru_cache(maxsize=1)
    def filename(self) -> str:
        """
        Property returning the name of the file without the extension.

        :return: String containing the name of the file.
        """
        return self.basename[: -(len(self.ext) + 1)]

    @property
    @lru_cache(maxsize=1)
    def ext(self) -> str:
        """
        Property returning the extension of the file

        :return: String containing the extension of the file.
        """
        return self.basename.split(".")[-1]

    @property
    def mode(self) -> str:
        """
        Getter for the mode property.

        :return: string
        """
        return self._mode

    @mode.setter
    def mode(self, value) -> None:
        """
        Setter for the mode property.

        :param value: File mode to set.
        :return: No return value.
        """
        if value in FILE_MODES:
            self._mode = value
        else:
            raise Exception(f"Invalid file access mode: '{value}'")

    @property
    @lru_cache(maxsize=1)
    def owner(self) -> str:
        """
        Property returning the owner of the file.

        :return: string
        """
        return self._path_obj.owner()

    @property
    @lru_cache(maxsize=1)
    def group(self) -> str:
        """
        Property returning the group the file belongs to.

        :return: string
        """
        return self._path_obj.group()

    @property
    @lru_cache(maxsize=1)
    def abs_path(self) -> str:
        """
        Property returning the absolute path of the file.

        :return:
        """
        return str(self._path_obj.absolute())

    @property
    @lru_cache(maxsize=1)
    def relative_path(self) -> str:
        """
        Property returning the path of the file relative to the current directory.

        :return: String containing the relative path
        """
        return str(self._path_obj.relative_to("./"))

    @property
    def last_modified(self) -> float:
        """
        Property returning the modification timestamp of the file

        :return: Float
        """
        return self._stat.st_mtime

    @property
    def size(self) -> int:
        """
        Property returning the size of the file in bytes

        :return: Integer
        """
        return self._stat.st_size

    @property
    def modified(self) -> bool:
        """
        Property returning a boolean indicating whether the file has been modified.

        :return: Boolean indicating whether the file has been modified.
        """
        return self.cached_stamp < self._stat.st_mtime

    @property
    def line_cnt(self) -> int:
        """
        Property returning the line count of the file.

        :return: Integer
        """
        return self._line_cnt(self._stat.st_mtime)

    @lru_cache(maxsize=1)
    def _line_cnt(self, m_time) -> int:
        """
        Helper function to allow the line_cnt property to use LRU caching.
        :param m_time:
        :return:
        """
        return len(self.readlines())

    @property
    def stat(self) -> os.stat:
        """
        Returns os.stat object for the file.

        :return: os.stat object
        """
        return os.stat(self.abs_path)

    def chmod(self, mode: str or int) -> str or int:
        """
        Wrapper for builtin chmod

        :param mode: File mode
        :return: Output form os.chmod function call.
        """
        if isinstance(mode, str):
            self._mode = mode
            return self._mode
        elif isinstance(mode, int):
            return os.chmod(self.abs_path, mode)

    def touch(self) -> float:
        """
        Updates the cached modification timestamp and creates the file if it doesn't exist.

        :return: The updated timestamp.
        """
        if self.exists:
            os.utime(self._path, None)
        else:
            self.open("a")
            self.close()
        return self.last_modified

    def open(self, mode=None) -> bool:
        """
        Opens the file. Basically wrapper for the builtin open() function.

        :return: Boolean indicating successful operation.
        """
        try:
            self._file_io_obj = open(
                self.abs_path, mode if mode is not None else self.mode
            )
            self.is_open = True
            return self.is_open
        except Exception as ex:
            raise ex

    def close(self) -> bool:
        """
        Closes the file. Basically a wrapper for the builtin in close() function.

        :return: Boolean indicating successful operation.
        """
        if self.is_open:
            self._file_io_obj.close()
            self.is_open = False
            return True
        else:
            return False

    def md5(self, hash_type=HashType.STRING) -> str or int or hex or bytes:
        """
        Calculate and return the MD5 hash of the file contents.
        The hash is updated using 65535 blocks of bytes from the file.

        :return: Hash of the file contents.
        """
        return self._get_hash(self.last_modified, md5, hash_type)

    def sha256(self, hash_type=HashType.STRING) -> str or int or hex or bytes:
        """
        Calculate and return the SHA256 hash of the file contents.
        The hash is updated using 65535 blocks of bytes from the file.

        :return: Hash of the file contents
        """
        return self._get_hash(self.last_modified, sha256, hash_type)

    @lru_cache(maxsize=1)
    def _get_hash(self, m_time: float, hash_func: sha256 or md5, hash_type: HashType) -> hex or str:
        """
        Private function to allow the hash calculation to use LRU caching.
        If the file has not been modified and a hash has previously been calculated,
        we can just use the previous value rather than recalculating the hash.

        :param m_time: st_mtime or last modified time.
        :param hash_func: Type of hash function to use (MD5 or SHA256)
        :param hash_type: String or hex return type.
        :return: String or hex value containing the hash for the file contents.
        """
        close_before_returning = False

        if not self.is_open:
            close_before_returning = True
            self.open("r")

        file_buf: str = self._file_io_obj.read(HASH_BLOCK_SIZE)

        while len(file_buf):
            hash_func().update(bytes(file_buf.encode("utf-8")))
            file_buf = self._file_io_obj.read(HASH_BLOCK_SIZE)

        if close_before_returning:
            self.close()

        if hash_type == HashType.STRING:
            return hash_func().hexdigest()
        elif hash_type == HashType.BYTES:
            return hash_func().digest()

    def delete(self) -> bool:
        """
        Deletes the related file

        :return: boolean indicating successful deletion
        """
        try:
            self.close()
            os.remove(self.abs_path)
            return True
        except (PermissionError, FileNotFoundError, FileExistsError):
            return False

    def read(self, n=None) -> str:
        """
        Wrapper for builtin read function.

        :param n: Number of characters to read.
        :return: string
        """
        if n is not None:
            return self._file_io_obj.read(n)
        else:
            return self._file_io_obj.read()

    def readlines(self) -> list:
        """
        Wrapper for builtin readlines function.

        :return: list containing the lines from the file.
        """
        if not self.is_open:
            with open(self.abs_path, "r") as file:
                return file.readlines()
        else:
            return self._file_io_obj.readlines()

    def write(self, string) -> int:
        """
        Wrapper for the builting file object write function.

        :param string:
        :return:
        """
        self._get_hash.cache_clear()
        return self._file_io_obj.write(string)

    def backup(self, directory="") -> str:
        """
        Creates a backup of the file. This is a ZIP directory that includes a hash
        of the file contents.

        :param directory:
        :return:
        """
        timestamp: str = utilities.get_formatted_datetime()
        self.backup_file: str = f"{directory}{timestamp}_{self.basename}.bak"

        # We want to include a hash of the file's contents for integrity checks.
        hash_file_name: str = f"{directory}{timestamp}.SHA256"
        hash_file = open(hash_file_name, "w+")
        hash_file.write(self.sha256())
        hash_file.close()

        if not os.path.exists(directory) and directory != "":
            os.makedirs(directory)

        # Zip the files together
        with zipfile.ZipFile(self.backup_file, "w", zipfile.ZIP_DEFLATED) as backup:
            backup.write(self.relative_path)
            backup.write(hash_file_name)

        os.remove(hash_file_name)
        return self.backup_file

    def grep(self, regex: str) -> list:
        """
        Basic grep functionality for the file contents.

        :param regex: Regular expression to match.
        :return: List containing all matching lines.
        """
        matches: list = []
        for line in self.readlines():
            if re.search(re.compile(regex), line):
                matches.append(line)
        return matches

    def truncate(self, n=None) -> None:
        """
        Truncates the file to a specified size. Defaults to clearing the whole file.

        :param n: Number of byte to truncate to.
        :return: No return value.
        """
        if n is None and self._file_io_obj is not None:
            self._file_io_obj.truncate(0)
        elif self._file_io_obj is not None:
            self._file_io_obj.truncate(n)
