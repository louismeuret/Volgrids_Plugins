# //////////////////////////////////////////////////////////////////////////////
class FreyaSyntaxError(SyntaxError):
    """
    This error is meant to be seen only by developers of a `freyacli` application.
    It should be raised as a consequence of a malformed `fyr` or `fyh` string/file.
    For malformed command line arguments (i.e. what a user would see), the method `ArgsParser.help_and_exit()` should be used instead.
    """
    def __init__(self, msg):
        super().__init__(f"Error parsing FYR string. {msg}")


# //////////////////////////////////////////////////////////////////////////////
