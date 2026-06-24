import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class ArgCount:
    """
    `FYR` syntax follows a similarity to regex conventions for specifying amount of expected arguments.

    - `n` -> exactly n
        - `min_nvalues = n`, `val_optional = False`, `unlimited = False`
        - `FYR` example: `~sphere[s,sphere]4.FLOAT`
            - this means that `-s` must be passed with exactly `4` float values.
        - Automatic help string:
            - n = 1: `<value>`
            - n > 1: `<value(n)>`

    - `n?` -> 0 or n
        - `min_nvalues = n`, `val_optional = True`, `unlimited = False`
        - `FYR` example: `~out_mrc[m,mrc]1?.PATH`
            - this means `-m` can be passed with exactly `1` value or without a value.
        - Automatic help string:
            - n = 1: `[<value>]`
            - n > 1: `[<value(n)>]`

    - `*` -> 0 or more
        - `min_nvalues = 0`, `val_optional = True`, `unlimited = True`
        - `FYR` example: `~configs[c,config]*.STR`
            - this means that `-c` can be passed with or without values. Amount of values is arbitrary.
        - Automatic help string: `[<value...>]`

    - `n+` -> n or more
        - `min_nvalues = n`, `val_optional = False`, `unlimited = True`
        - `FYR` example: `~resids[i,resids]1+.STR`
            - this means that `-i` must be passed with *at least* `1` value.
        - Automatic help string:
            - n = 1: `<value...>`
            - n > 1: `<value(n)[...]>`
    """

    # --------------------------------------------------------------------------
    def __init__(self, min_nvalues: int = 0, val_optional: bool = False, unlimited: bool = False):
        self.min_nvalues  = min_nvalues  # 0 for *, n otherwise
        self.val_optional = val_optional # True for n? and *, False for n and n+
        self.unlimited    = unlimited    # True for * and n+, False for n and n?


    # --------------------------------------------------------------------------
    @classmethod
    def from_str(cls, string: str) -> "ArgCount":
        def _safe_substr(s: str) -> str:
            substr = s[:-1]
            if not substr: raise fy.FreyaSyntaxError(
                f"Invalid argument count specification: '{s}'."+\
                "Expected format examples: '3', '3?', '*', '3+'."+\
                "Number is mandatory for all formats except '*', which always means '0 or more'."
            )
            return substr

        def _safe_int(s: str) -> int:
            try: return int(s)
            except ValueError: raise fy.FreyaSyntaxError(
                f"Invalid number in argument count specification: '{s}'."+\
                "Expected format examples: '3', '3?', '*', '3+'."+\
                "Number is mandatory for all formats except '*', which always means '0 or more'."
            )

        if string.endswith("?"): return cls(
            min_nvalues = _safe_int(_safe_substr(string)),
            unlimited = False,
            val_optional = True
        )
        if string.endswith("*"): return cls(
            min_nvalues = 0,
            unlimited = True,
            val_optional = True
        )
        if string.endswith("+"): return cls(
            min_nvalues = _safe_int(_safe_substr(string)),
            unlimited = True,
            val_optional = False
        )
        return cls(
            min_nvalues = _safe_int(string),
            unlimited = False,
            val_optional = False
        )


    # --------------------------------------------------------------------------
    def get_help_str(self, buffer: str) -> str:
        if self.val_optional:
            if self.unlimited: return f"[<{buffer}...>]"     # * case
            if self.min_nvalues == 1: return f"[<{buffer}>]" # n? case with n=1
            return f"[<{buffer}({self.min_nvalues})>]"       # n? case with n>1

        if self.unlimited:
            if self.min_nvalues == 1: return f"<{buffer}...>" # n+ case with n=1
            return f"<{buffer}({self.min_nvalues})[...]>"     # n+ case with n>1

        if self.min_nvalues == 1: return f"<{buffer}>" # n case with n=1
        return f"<{buffer}({self.min_nvalues})>"       # n case with n>1


    # --------------------------------------------------------------------------
    def needs_single_value(self) -> bool:
        return (self.min_nvalues <= 1) and (not self.unlimited)


    # --------------------------------------------------------------------------
    def is_full(self, nvalues: int) -> bool:
        """Returns `True` for an argument that shouldn't take more values."""
        if self.unlimited: return False
        return nvalues >= self.min_nvalues


    # --------------------------------------------------------------------------
    def has_enough_values(self, nvalues: int) -> bool:
        """Returns `True` for an argument that has already received enough values."""
        if self.val_optional: return True
        if self.unlimited: return nvalues >= self.min_nvalues
        return nvalues == self.min_nvalues


# //////////////////////////////////////////////////////////////////////////////
