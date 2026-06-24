import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class Color:
    _BLACK_PLAIN = "\033[30m"
    _RED_PLAIN = "\033[31m"
    _GREEN_PLAIN = "\033[32m"
    _YELLOW_PLAIN = "\033[33m"
    _BLUE_PLAIN = "\033[34m"
    _MAGENTA_PLAIN = "\033[35m"
    _CYAN_PLAIN = "\033[36m"
    _WHITE_PLAIN = "\033[37m"

    _BLACK_BRIGHT = "\033[90m"
    _RED_BRIGHT = "\033[91m"
    _GREEN_BRIGHT = "\033[92m"
    _YELLOW_BRIGHT = "\033[93m"
    _BLUE_BRIGHT = "\033[94m"
    _MAGENTA_BRIGHT = "\033[95m"
    _CYAN_BRIGHT = "\033[96m"
    _WHITE_BRIGHT = "\033[97m"

    # --------------------------------------------------------------------------
    @classmethod
    def black(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._BLACK_BRIGHT if bright else cls._BLACK_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def red(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._RED_BRIGHT if bright else cls._RED_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def green(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._GREEN_BRIGHT if bright else cls._GREEN_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def yellow(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._YELLOW_BRIGHT if bright else cls._YELLOW_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def blue(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._BLUE_BRIGHT if bright else cls._BLUE_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def magenta(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._MAGENTA_BRIGHT if bright else cls._MAGENTA_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def cyan(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._CYAN_BRIGHT if bright else cls._CYAN_PLAIN
        return f"{color}{s}\033[0m"

    # --------------------------------------------------------------------------
    @classmethod
    def white(cls, s: str, bright = True) -> str:
        if not fy.VALID_TERMINAL: return s
        color = cls._WHITE_BRIGHT if bright else cls._WHITE_PLAIN
        return f"{color}{s}\033[0m"


# //////////////////////////////////////////////////////////////////////////////
