from pathlib import Path

import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class ArgumentRule:
    _INDENT_LONG_DESC = 8

    # --------------------------------------------------------------------------
    def __init__(self, raw_rule: str | None):
        self._raw_rule = raw_rule
        self.help_str: fy.HelpStr = fy.HelpStr()

        self._raw_user_values: list[str] = [] # raw string values provided by the user
        self._n_user_values: int = 0 # amount of values provided by the user so far
        self._was_used: bool = False # True when the flag of this argument was used at least once.

        self.name: str = ""               # name that will be displayed between <> (e.g. "<value>") in the help string, and used to fetch any given values
        self.is_positional: bool = False  # True when the argument doesn't need a preceding "flag" (e.g. just "<value>" instead of "--flag <value>")
        self.is_optional: bool = False    # display with surrounding [] in the help string (e.g. "[<value>]")
        self.flag_short: str = ""         # must be 1 character long. It's always used with a single preceding dash (e.g. "-f")
        self.flag_long: str = ""          # used with a double preceding dash (e.g. "--flag")
        self.default_value: str = ""      # when a default value is present, it's placed at the beginning of the respective help string, right after the flag type (e.g. "INT (default: 0)").
        self.arg_dtype = fy.ArgDType.NONE # placed at the beginning of the help string. TOGGLE type is used for flags with no arguments, and the respective type (e.g. STR, INT) is used for flags with arguments.
        self.arg_count = fy.ArgCount()    # contains information about the expected number of passed values and whether they are optional.

        if raw_rule is None: return

        self.is_optional = raw_rule.startswith('~')

        (buffer,
            self.default_value
        ) = self._parse_default_value(raw_rule)

        (buffer,
            self.name
        ) = self._parse_name(buffer)

        (buffer,
            self.is_positional,
            self.flag_short,
            self.flag_long
        ) = self._parse_flags(buffer)

        (buffer,
            self.arg_count
        ) = self._parse_arg_count(buffer)

        self.arg_dtype = fy.ArgDType.from_str(buffer)


    # --------------------------------------------------------------------------
    def register_user_value(self, value: str) -> bool:
        """Returns `True` when the argument is "full" (i.e. won't accept any more user values)"""

        if self.arg_dtype in (fy.ArgDType.INT, fy.ArgDType.FLOAT):
            ### for numeric types, split the raw user values, just in case they are received as a single space-separated string
            vals = value.strip('"').strip("'").split()
            self._raw_user_values.extend(vals)
            self._n_user_values += len(vals)
        else:
            self._raw_user_values.append(value)
            self._n_user_values += 1

        self.touch()
        return self.arg_count.is_full(self._n_user_values)


    # --------------------------------------------------------------------------
    def touch(self):
        """
        Marks the argument as used even if it doesn't receive any user values.
        Useful when dealing with flags with optional keyword arguments
        """
        self._was_used = True


    # --------------------------------------------------------------------------
    def parse_user_values(self) -> None | fy.ArgDTypeError |\
        bool|str|Path|int|float |\
        list[bool]|list[str]|list[Path]|list[int]|list[float]:
        """
        Parses the raw user values according to the argument type (e.g. `INT`, `STR`, etc.) and returns the parsed values in the respective types.
        When the argument accepts only 1 value, the value is returned directly instead of a `list`.
        A boolean is returned for flags of `TOGGLE` type. Alternatively, `True` can be returned when a flag is passed but its optional keyword argument isn't.
        An `ArgDTypeError` instance is returned when parsing fails due to invalid user input.
        `None` is returned for non-used optional arguments, be it positional or non-toggle flags (i.e. those that should receive values).
        """
        if self._was_used and not self.has_enough_values():
            s = 's' if self.arg_count.min_nvalues > 1 else ''
            return fy.ArgDTypeError(f"Expected {self.arg_count.min_nvalues} value{s} for argument '{self.name}', but got {len(self._raw_user_values)}.")

        parsed_values = [
            self.arg_dtype.parse_value(self.name, raw_value)
            for raw_value in self._raw_user_values
        ]

        if not parsed_values:
            if self._was_used: return True # used flag has value of "True"
            if self.is_positional: return None # unused optional positional argument has value of "None"
            if self.arg_dtype is fy.ArgDType.TOGGLE: return False # unused toggle flag has value of "False"
            return None # unused optional flag with arguments has value of "None"

        if self.arg_count.needs_single_value(): return parsed_values[0]
        return parsed_values


    # --------------------------------------------------------------------------
    def get_usage_str_positional(self) -> str:
        """
        Usage string is only relevant for positionals.
        Flag arguments are summarized as [options...] in the usage string.
        A more detailed description of them is provided in the longer help string.
        """
        if not self.is_positional:
            raise fy.FreyaSyntaxError(f"Usage string can only be generated for positional arguments, but got a flag argument ('{self._raw_rule}').")

        buffer = self.arg_count.get_help_str(self.name)
        return fy.Color.blue(buffer)


    # --------------------------------------------------------------------------
    def get_help_string_description(self) -> str:
        preffix = ""
        if self.is_optional: preffix += "[optional] "
        if self.arg_dtype.stores_data():
            preffix += self.arg_dtype.name
            if self.default_value: preffix += f" (default: {self.default_value})"
            preffix += ". "

        arg_desc = self._get_arg_description()
        long_desc = self.help_str.wrapped_text(
            indent = self._INDENT_LONG_DESC,
            width = fy.WIDTH_TERMINAL - self._INDENT_LONG_DESC,
            preffix = fy.Color.yellow(preffix)
        )
        return f"{arg_desc}\n{self._INDENT_LONG_DESC*' '}{long_desc}\n"

    # --------------------------------------------------------------------------
    def has_enough_values(self) -> bool:
        return self.arg_count.has_enough_values(self._n_user_values)


    # --------------------------------------------------------------------------
    def _parse_default_value(self, buffer: str) -> tuple[str, str]:
        idx = buffer.find('=')
        if idx == -1: return buffer, ''
        return buffer[:idx], buffer[idx+1:]


    # --------------------------------------------------------------------------
    def _parse_name(self, buffer: str) -> tuple[str, str]:
        name, buffer = self._safe_split_into_2(buffer, '[')
        return buffer, name[int(self.is_optional):]


    # --------------------------------------------------------------------------
    def _parse_flags(self, buffer: str) -> tuple[str, bool, str, str]:
        flags, buffer = self._safe_split_into_2(buffer, ']')
        if not flags: return buffer, True, '', ''

        flag_short, flag_long = self._safe_split_into_2(flags, ',')
        if len(flag_short) > 1:
            raise fy.FreyaSyntaxError(f"Short flags should be 1 character long, but got '{self.flag_short}'.")

        return buffer, False, flag_short, flag_long


    # --------------------------------------------------------------------------
    def _parse_arg_count(self, buffer: str) -> fy.ArgCount:
        if not buffer:
            if self.default_value:
                raise fy.FreyaSyntaxError(f"Flags with no arguments can't have a default value ('{self._raw_rule}')")
            if self.is_positional:
                raise fy.FreyaSyntaxError(f"Positional arguments must specify type and number of arguments ('{self._raw_rule}')")

            return "", fy.ArgCount()

        min_nvalues, buffer = self._safe_split_into_2(buffer, '.')
        arg_count = fy.ArgCount.from_str(min_nvalues)
        if self.is_positional:
            ### having a distinction between self.is_optional (e.g. "passing -x" is optional)
            ### vs arg_count.val_optional (e.g. "passing a value for -x" is optional)
            ### is only relevant for flags, not for positionals
            arg_count.val_optional = self.is_optional

        return buffer, arg_count


    # --------------------------------------------------------------------------
    def _safe_split_into_2(self, buffer: str, char_split: str) -> tuple[str, str]:
        splitted = buffer.split(char_split)
        if len(splitted) == 2: return splitted
        raise fy.FreyaSyntaxError(f"Invalid substring found inside argument rule: '{self._raw_rule}'")


    # --------------------------------------------------------------------------
    def _get_arg_description(self) -> str:
        buffer = self.arg_count.get_help_str(self.name)
        if self.is_positional: return fy.Color.blue("    " + buffer)

        buffer = f" {buffer}" if self.arg_dtype.stores_data() else ""

        if self.is_optional:
            str_flags_0 = "["
            str_flags_1 = "]"
        else:
            str_flags_0 = ""
            str_flags_1 = ""

        flag_short = f"-{self.flag_short}" if self.flag_short else ""
        flag_long  = f"--{self.flag_long}" if self.flag_long  else ""

        str_flags_0 += (
            f"{flag_short}, {flag_long}" if self.flag_long else flag_short
        ) if self.flag_short else flag_long

        buffer = f"    {fy.Color.green(str_flags_0)}{fy.Color.blue(buffer)}"
        if str_flags_1: buffer += fy.Color.green(str_flags_1)
        return buffer


# //////////////////////////////////////////////////////////////////////////////
