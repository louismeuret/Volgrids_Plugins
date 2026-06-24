from enum import Enum, auto
from pathlib import Path

import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class ArgDType(Enum):
    NONE   = auto()
    TOGGLE = auto()
    STR    = auto()
    PATH   = auto()
    INT    = auto()
    FLOAT  = auto()

    # --------------------------------------------------------------------------
    @classmethod
    def from_str(cls, s: str | None) -> "ArgDType":
        if s is None: return cls.NONE
        s = s.lower()
        if not s:        return cls.TOGGLE
        if s == "str":   return cls.STR
        if s == "path":  return cls.PATH
        if s == "float": return cls.FLOAT
        if s == "int":   return cls.INT
        raise fy.FreyaSyntaxError(f"Invalid flag type specified: '{s}'")


    # --------------------------------------------------------------------------
    def stores_data(self) -> bool:
        return self != ArgDType.NONE and self != ArgDType.TOGGLE

    # --------------------------------------------------------------------------
    def parse_value(self, arg_name: str, raw_value: str) -> fy.ArgDTypeError |\
        bool|str|Path|int|float:

        if self == ArgDType.NONE:
            raise fy.FreyaSyntaxError(f"Argument doesn't accept any values, but somehow got '{raw_value}'.")

        if self == ArgDType.TOGGLE:
            raise fy.FreyaSyntaxError(f"Argument is a flag of type TOGGLE and doesn't accept any values, but somehow got '{raw_value}'.")

        if self == ArgDType.STR:
            return raw_value.strip('"').strip("'")

        if self == ArgDType.PATH:
            return Path(raw_value)

        if self == ArgDType.INT:
            try: return int(raw_value)
            except ValueError: return fy.ArgDTypeError(
                f"Argument '{arg_name}' expected an integer value, but got '{raw_value}'."
            )

        if self == ArgDType.FLOAT:
            try: return float(raw_value)
            except ValueError: return fy.ArgDTypeError(
                f"Argument '{arg_name}' expected a float value, but got '{raw_value}'."
            )


# //////////////////////////////////////////////////////////////////////////////
