import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class HelpStr:
    def __init__(self, string: str = ""):
        self.string = string


    # --------------------------------------------------------------------------
    def __repr__(self):
        return self.string


    # --------------------------------------------------------------------------
    def concat(self, s: str):
        if self.string and not self.string.endswith('\n'):
            self.string += ' '
        self.string += s


    # --------------------------------------------------------------------------
    def wrapped_text(self, indent: int, width: int, preffix: str = "") -> str:
        out = ""
        buffer = preffix + self.string.replace('\n', ' ')
        while buffer:
            if len(buffer) > width:
                row = buffer[:width]
                last_space = row[::-1].find(' ') + 1
                idx = len(row) - last_space
            else:
                idx = len(buffer)

            if out: out += f"\n{indent*' '}"
            out += buffer[:idx]
            buffer = buffer[idx+1:]

        return out


    # --------------------------------------------------------------------------
    def nl_surround(self) -> str:
        """Surrounds the string with newlines and wraps it to fit the terminal width."""
        if not self.string: return self.string
        return f"\n{self.wrapped_text(0, fy.WIDTH_TERMINAL)}\n"


    # --------------------------------------------------------------------------
    @staticmethod
    def pad_name(s: str, max_len: int) -> str:
        return f"    {s.ljust(max_len)}    "


# //////////////////////////////////////////////////////////////////////////////
