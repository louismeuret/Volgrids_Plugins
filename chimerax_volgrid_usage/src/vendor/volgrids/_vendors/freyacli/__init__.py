from ._version import __version__

from ._misc.freya_syntax_error import FreyaSyntaxError
from ._misc.arg_dtype_error import ArgDTypeError
from ._misc.help_str import HelpStr

from ._utils.color import Color
from ._utils.path_assertion import PathAssertion

from ._arguments.arg_count import ArgCount
from ._arguments.arg_dtype import ArgDType
from ._arguments.argument_rule import ArgumentRule
from ._arguments.subcommand import Subcommand

from ._parsers.freya_parser import FreyaParser
from ._parsers.args_parser import ArgsParser

from ._core.app import App
from ._utils.utils_app import FreyacliUtilsApp as _FreyacliUtilsApp

WIDTH_TERMINAL: int = 1 # automatically set to the current terminal width when App is initialized
VALID_TERMINAL: bool = True # set to False when the terminal is not valid (e.g. when running in an environment without a terminal)
