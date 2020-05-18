import os
import pathlib
from enum import Enum
import hashlib
import time
import zipfile
import re
from pwd import getpwuid
from PyFile import config
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
    ]

    def __init__(self, path: str, open_file=True, mode="r", temporary=False):
        self._path: str = path
        self._mode: str = mode
        self._path_obj: pathlib.Path or None = None
        self.cached_stamp: float = -1
        self._file_io_obj = None
        self.exists: bool = True
        self.is_open: bool = False
        self.file_class = None
        self.deleted: bool = False
        self.backup_file = None

        if not os.path.exists(path) and mode in CREATE_MODES:
            open(path, mode).close()

        if os.path.exists(path) and os.path.isfile(path):
            self._path_obj: pathlib.Path = pathlib.Path(path)

            if open_file:
                self.open(mode)
                self.is_open = True

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
    def basename(self) -> str:
        """
        Property returning the name of the file with the extension.

        :return: String containing the name of the file.
        """
        return str(self._path_obj.name)

    @property
    def dirname(self) -> str:
        """
        Property returning the directory the file is located in.

        :return: String containing the name of the file.
        """
        return str(self.abs_path[: -len(self.basename)])

    @property
    def filename(self) -> str:
        """
        Property returning the name of the file without the extension.

        :return: String containing the name of the file.
        """
        print(self.ext)
        return str(self._path_obj.name)[: -len(self.ext)]

    @property
    def ext(self, period=True) -> str:
        """
        Property returning the extension of the file

        :return: String containing the extension of the file.
        """
        return ("." if period else "") + self.basename.split(".")[-1]

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value):
        if value in FILE_MODES:
            self._mode = value
        else:
            raise Exception(f"Invalid file access mode: '{value}'")

    @property
    def owner(self) -> str:
        return self._path_obj.owner()

    @property
    def group(self) -> str:
        return self._path_obj.group()

    @property
    def abs_path(self) -> str:
        """
        Property returning the absolute path of the file.

        :return:
        """
        return str(self._path_obj.absolute())

    @property
    def rel_path(self) -> str:
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
        return self.stat.st_mtime

    @property
    def size(self) -> int:
        """
        Property returning the size of the file in bytes

        :return: Integer
        """
        return self.stat.st_size

    @property
    def modified(self) -> bool:
        """
        Property returning a boolean indicating whether the file has been modified.

        :return: Boolean indicating whether the file has been modified.
        """
        return self.cached_stamp < self.last_modified

    @property
    def line_cnt(self) -> int:
        """
        Property returning the line count of the file.

        :return: Integer
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
            return True
        else:
            return False

    def md5(self, hash_type=HashType.STRING) -> str or int or hex or bytes:
        """
        Calculate and return the MD5 hash of the file contents.
        The hash is updated using 65535 blocks of bytes from the file.

        :return: Hash of the file contents.
        """
        file_buf = self.read(config.HASH_BLOCK_SIZE)
        hash_func = hashlib.md5
        while len(file_buf) > 0:
            hash_func().update(bytes(file_buf.encode("utf-8")))
            file_buf = self.read(config.HASH_BLOCK_SIZE)

        if hash_type == HashType.STRING:
            return hash_func().hexdigest()
        elif hash_type == HashType.BYTES:
            return hash_func().digest()

    def sha256(self, hash_type=HashType.STRING) -> str or int or hex or bytes:
        """
        Calculate and return the SHA256 hash of the file contents.
        The hash is updated using 65535 blocks of bytes from the file.

        :return: Hash of the file contents
        """
        file_buf = self.read(config.HASH_BLOCK_SIZE)
        hash_func = hashlib.sha256
        while len(file_buf) > 0:
            hash_func().update(bytes(file_buf.encode("utf-8")))
            file_buf = self.read(config.HASH_BLOCK_SIZE)

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

        :param string:
        :return:
        """
        return self._file_io_obj.write(string)

    def backup(self, directory=""):
        """

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
            backup.write(self.rel_path)
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
