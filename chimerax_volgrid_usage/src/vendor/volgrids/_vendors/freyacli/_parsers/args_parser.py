from pathlib import Path

import volgrids._vendors.freyacli as fy

_RULE_NONE = fy.ArgumentRule(None)

# ------------------------------------------------------------------------------
def _could_be_negative(s: str) -> bool:
    """Allow negative arguments to be parsed as values, instead of mistaken as flags.
    Simply checks if the string starts with '-' followed by a digit or a dot."""
    if not s.startswith('-'): return False
    if len(s) < 2: return False
    return s[1].isdigit() or s[1] == '.'


# //////////////////////////////////////////////////////////////////////////////
class ArgsParser:
    def __init__(self, fy_parser: fy.FreyaParser, app_name: str, version: str):
        self._app_name: str = app_name
        self._version: str = version
        self._user_values = {}

        self._fy_parser: fy.FreyaParser = fy_parser
        self._current_node: fy.Subcommand = fy_parser.tree

        self._pending_posit: list[fy.ArgumentRule] = []
        self._current_rule: fy.ArgumentRule = _RULE_NONE
        self._processing_flag_val: bool = False

    # --------------------------------------------------------------------------
    def parse_args(self, args: list[str]):
        if not args: raise fy.FreyaSyntaxError(
            "Argument list shouldn't be empty. At least the application name should be specified (e.g. sys.argv[0])."
        )
        self.py_name = Path(args[0]).name
        self._parse_args(args[1:])


    # --------------------------------------------------------------------------
    def get_path_to_root(self) -> list[str]:
        return self._current_node.get_path_to_root()


    # --------------------------------------------------------------------------
    def arg_keys(self) -> list[str]:
        return list(self._user_values.keys())


    # --------------------------------------------------------------------------
    def arg_values(self) -> list:
        return list(self._user_values.values())


    # --------------------------------------------------------------------------
    def get_arg_value(self, key: str, default = None):
        if key not in self._user_values:
            raise KeyError(f"Key '{key}' not found in the stored argument values.")
        val = self._user_values[key]
        if val is None: return default
        if isinstance(val, list) and not val: return default
        return val

    # --------------------------------------------------------------------------
    def help_and_exit(self, exit_code: int, *err_messages: str):
        err_messages: list = list(err_messages)
        for i,err in enumerate(err_messages):
            err_messages[i] = fy.Color.red("ERROR: ", bright = False) + fy.Color.red(err)

        if err_messages: err_messages.append("")

        print('\n'.join((
            f"{self._app_name} ({fy.Color.yellow('v'+self._version)}). Usage:",
            self._current_node.str_help_long(self.py_name),
            *err_messages,
        )))
        exit(exit_code)


    # --------------------------------------------------------------------------
    def _parse_args(self, args: list[str]) -> None:
        self._current_node = self._fy_parser.tree

        while args:
            arg = args.pop(0)
            self._parse_subcommand(arg)
            if self._current_node.is_leaf(): break

        self._pending_posit = self._current_node.rules_posit.copy()

        for arg in args:
            self._parse_argument(arg)

        if not self._current_rule.has_enough_values():
            self.help_and_exit(1, f"Expected a value for the last flag '--{self._current_rule.flag_long}'.")

        if not self._current_node.is_leaf(): # [NOTE] execution of the app must currently happen at a leaf node
            self.help_and_exit(1)

        for rule in self._current_node.rules.values():
            if rule._raw_user_values: continue
            if rule.default_value:
                rule.register_user_value(rule.default_value)
                continue
            if rule.is_optional: continue
            self.help_and_exit(1, f"Missing required argument: '{rule.name}'.")

        self._user_values = {
            k: rule.parse_user_values() for k,rule in self._current_node.rules.items()
        }
        errors = [
            v.err_message for v in self._user_values.values()
            if isinstance(v, fy.ArgDTypeError)
        ]
        if not errors: return

        self.help_and_exit(1, *errors)


    # --------------------------------------------------------------------------
    def _parse_subcommand(self, next_subcommand: str):
        if next_subcommand in ("-h", "--help"):
            ### [NOTE] --help/-h is currently a reserved flag. [TODO] allow customization
            self.help_and_exit(0)

        if next_subcommand not in self._current_node.children:
            self.help_and_exit(1, f"Unrecognized command: '{next_subcommand}'.")

        self._current_node = self._current_node.get_child(next_subcommand)


    # --------------------------------------------------------------------------
    def _parse_argument(self, arg: str):
        if self._processing_flag_val:
            self._parse_arg_flag_value(arg)
            return

        ###### POSITIONAL ARGUMENTS
        if not arg.startswith('-') or _could_be_negative(arg):
            self._parse_arg_positional(arg)
            return

        ###### FLAGS (LONG NAME)
        if arg.startswith("--"):
            ### [NOTE] --help/-h is currently a reserved flag. [TODO] allow customization
            if "help" in arg: self.help_and_exit(0)
            self._parse_arg_flag_name(arg, arg[2:], is_short_name = False)
            return

        ###### FLAGS (SHORT NAME)
        if 'h' in arg: self.help_and_exit(0)
        for flag in arg[1:]: # allow concatenation of short flags (e.g. -abc == -a -b -c)
            self._parse_arg_flag_name(arg, flag, is_short_name = True)


    # --------------------------------------------------------------------------
    def _parse_arg_flag_name(self, arg: str, flag: str, is_short_name: bool):
        if self._processing_flag_val:
            self._assert_default_prev_flag(arg, flag)

        matches = self._current_node.get_args_with_flag(flag, is_short_name)
        if not matches:
            self.help_and_exit(1, f"Unrecognized flag: '{flag}' (provided as '{arg}').")

        self._set_current_rule(matches[0])

        self._processing_flag_val = self._current_rule.arg_dtype.stores_data()

        if not self._processing_flag_val:
            self._current_rule.touch()
            self._set_current_rule(_RULE_NONE)
            return


    # --------------------------------------------------------------------------
    def _parse_arg_flag_value(self, arg: str):
        if arg.startswith('-') and not _could_be_negative(arg):
            self._assert_default_prev_flag(arg, arg)
            is_short_name = not arg.startswith('--')
            flag = arg[1:] if is_short_name else arg[2:]
            self._parse_arg_flag_name(arg, flag, is_short_name)
            return

        flag_is_full = self._current_rule.register_user_value(arg)
        if flag_is_full:
            self._set_current_rule(_RULE_NONE)
            self._processing_flag_val = False


    # --------------------------------------------------------------------------
    def _parse_arg_positional(self, arg: str):
        if self._current_rule is _RULE_NONE:
            if not self._pending_posit:
                self.help_and_exit(1, f"Unexpected positional argument: '{arg}'.")
            self._set_current_rule(self._pending_posit.pop(0))

        posit_is_full = self._current_rule.register_user_value(arg)
        if posit_is_full:
            self._set_current_rule(_RULE_NONE)


    # --------------------------------------------------------------------------
    def _assert_default_prev_flag(self, arg: str, flag: str):
        """
        situation: a new flag is used before providing a value for the previous flag
        this is incorrect if the previous flag isn't a toggle (i.e. expects a value)
        and doesn't have a default value.
        """
        rule = self._current_rule
        if rule.has_enough_values(): return
        if not rule.default_value:
            self.help_and_exit(1, f"Expected a value for the previous flag '--{rule.flag_long}', before using '{flag}' (provided as '{arg}').")

        rule.register_user_value(rule.default_value)
        self._processing_flag_val = False
        self._set_current_rule(_RULE_NONE)


    # --------------------------------------------------------------------------
    def _set_current_rule(self, rule: fy.ArgumentRule):
        self._current_rule = rule
        self._current_rule.touch()


# //////////////////////////////////////////////////////////////////////////////
