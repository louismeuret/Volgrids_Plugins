import os
from pathlib import Path
from abc import ABC, abstractmethod

import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class App(ABC):
    _APP_NAME = "FreyacliApp" # override these values
    _VERSION = "0.1.0"

    # --------------------------------------------------------------------------
    def __init__(self, args: list[str], path_fyr: str|Path, path_fyh: str|Path):
        try:
            fy.WIDTH_TERMINAL, _ = os.get_terminal_size()
            if not fy.WIDTH_TERMINAL: fy.WIDTH_TERMINAL = 1
        except OSError:
            ### [NOTE] this can happen when e.g. using > in a shell
            #### In that case just use a default width value.
            fy.WIDTH_TERMINAL = 80
            fy.VALID_TERMINAL = False

        fy_parser = fy.FreyaParser.from_files(path_fyr, path_fyh)
        self.args = fy.ArgsParser(fy_parser, self._APP_NAME, self._VERSION)
        self.args.parse_args(args)


    # --------------------------------------------------------------------------
    @abstractmethod
    def run(self):
        """
        Override this method to implement the logic of the app.
        """
        pass


    # --------------------------------------------------------------------------
    def get_path_to_root(self) -> list[str]:
        return self.args.get_path_to_root()


    # --------------------------------------------------------------------------
    def arg_keys(self) -> list[str]:
        return self.args.arg_keys()


    # --------------------------------------------------------------------------
    def help_and_exit(self, exit_code: int, *err_messages: str):
        self.args.help_and_exit(exit_code, *err_messages)


    # --------------------------------------------------------------------------
    def get_arg_bool(self, key: str, default = None) -> bool:
        """This method is for helping with intended usage, **no asertion is performed** (value was already parsed/asserted earlier). Flags with no value attached always store a boolean value."""
        return self.args.get_arg_value(key, default)


    # --------------------------------------------------------------------------
    def get_arg_str(self, key: str, default = None, is_list: bool = False) -> str:
        """This method is for helping with intended usage, **no asertion is performed** (value was already parsed/asserted earlier). When an optional positional value is absent, the actual stored value will be `None`.
        When an optional flag value is absent, the actual stored value will be `True` (since the flag was used, but no value was attached)."""
        val = self.args.get_arg_value(key, default)
        if not is_list: return val
        return self._val_as_list(val, default)


    # --------------------------------------------------------------------------
    def get_arg_path(self,
            key: str, default = None, is_list: bool = False,
            assertion: fy.PathAssertion | None = None, allow_none: bool = False
        ) -> Path:
        """
        When an optional positional value is absent, the actual stored value will be `None`.
        When an optional flag value is absent, the actual stored value will be `True` (since the flag was used, but no value was attached).
        If `assertion` is provided, the returned path(s) will be asserted with the provided assertion function. If the assertion fails, an error message will be printed and the app will exit.
        `allow_none` is passed to the assertion function, and it allows `None` values to pass the assertion if set to `True`.
        """
        val = self.args.get_arg_value(key, default)
        if not is_list: return self._asserted_path(val, assertion, allow_none)
        return [self._asserted_path(v, assertion, allow_none) for v in self._val_as_list(val, default)]


    # --------------------------------------------------------------------------
    def get_arg_int(self, key: str, default = None, is_list: bool = False) -> int:
        """This method is for helping with intended usage, **no asertion is performed** (value was already parsed/asserted earlier). When an optional positional value is absent, the actual stored value will be `None`.
        When an optional flag value is absent, the actual stored value will be `True` (since the flag was used, but no value was attached)."""
        val = self.args.get_arg_value(key, default)
        if not is_list: return val
        return self._val_as_list(val, default)


    # --------------------------------------------------------------------------
    def get_arg_float(self, key: str, default = None, is_list: bool = False) -> float:
        """This method is for helping with intended usage, **no asertion is performed** (value was already parsed/asserted earlier). When an optional positional value is absent, the actual stored value will be `None`.
        When an optional flag value is absent, the actual stored value will be `True` (since the flag was used, but no value was attached)."""
        val = self.args.get_arg_value(key, default)
        if not is_list: return val
        return self._val_as_list(val, default)


    # --------------------------------------------------------------------------
    def _asserted_path(self,
        path: Path|None, assertion: fy.PathAssertion|None, allow_none: bool
    ) -> Path|None:
        if assertion is None: return path
        err = assertion(path, allow_none)
        if isinstance(err, fy.ArgDTypeError):
            self.help_and_exit(1, err.err_message)
        return path


    # --------------------------------------------------------------------------
    @staticmethod
    def _val_as_list(val, default):
        if val is None: return default
        if isinstance(val, list): return val
        return [val]


# //////////////////////////////////////////////////////////////////////////////
