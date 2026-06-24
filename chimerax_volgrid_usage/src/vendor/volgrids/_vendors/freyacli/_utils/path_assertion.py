import os
from enum import Enum, auto
from pathlib import Path

import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class PathAssertion(Enum):
    FILE_IN  = auto()
    FILE_OUT = auto()
    DIR_OUT  = auto()

    # --------------------------------------------------------------------------
    def __call__(self, path: Path|None, allow_none: bool = False) -> Path|None|fy.ArgDTypeError:
        """
        Returns an error message wrapped inside an `fy.ArgDTypeError` instance if the assertion fails.
        Returns the same input `Path` object if it passes.
        If path is `None` and `allow_none` is `True`, it returns `None`.
        """
        if allow_none and path is None: return None

        func = {
            PathAssertion.FILE_IN:  self._assert_file_in,
            PathAssertion.FILE_OUT: self._assert_file_out,
            PathAssertion.DIR_OUT:  self._assert_dir_out,
        }[self]
        return func(path)


    # --------------------------------------------------------------------------
    @classmethod
    def _assert_file_in(cls, path_file: Path | None) -> Path | None | fy.ArgDTypeError:
        path_file = cls._asserted_path_obj(path_file)
        if isinstance(path_file, fy.ArgDTypeError): return path_file

        if not path_file.exists():
            return fy.ArgDTypeError(f"The specified file path '{path_file}' does not exist.")
        if path_file.is_dir():
            return fy.ArgDTypeError(f"The specified file path '{path_file}' is a folder.")
        return path_file


    # --------------------------------------------------------------------------
    @classmethod
    def _assert_file_out(cls, path_file: Path | None) -> Path | None | fy.ArgDTypeError:
        path_file = cls._asserted_path_obj(path_file)
        if isinstance(path_file, fy.ArgDTypeError): return path_file

        if path_file.is_dir():
            return fy.ArgDTypeError(f"The specified file path '{path_file}' is a folder.")
        os.makedirs(path_file.parent, exist_ok = True)
        return path_file


    # --------------------------------------------------------------------------
    @classmethod
    def _assert_dir_out(cls, path_dir: Path | None) -> Path | None | fy.ArgDTypeError:
        path_dir = cls._asserted_path_obj(path_dir)
        if isinstance(path_dir, fy.ArgDTypeError): return path_dir

        if path_dir.is_file():
            return fy.ArgDTypeError(f"The specified folder path '{path_dir}' is a file.")
        os.makedirs(path_dir, exist_ok = True)
        return path_dir


    # --------------------------------------------------------------------------
    @staticmethod
    def _asserted_path_obj(path):
        if not isinstance(path, Path):
            try: path = Path(path)
            except TypeError: return fy.ArgDTypeError(f"The specified path '{path}' is not a valid path.")
        return path


# //////////////////////////////////////////////////////////////////////////////
