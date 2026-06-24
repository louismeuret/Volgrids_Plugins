from pathlib import Path

import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class FreyacliUtilsApp(fy.App):
    """
    Do not derive from this class. This is a utility app integrated in the package.
    For developing freyacli apps, derive from `fy.App` instead.
    """
    _APP_NAME = "freyacli"
    _VERSION = fy.__version__

    # --------------------------------------------------------------------------
    def __init__(self,  argv: list[str]):
        dir_ui = Path(__file__).parent
        super().__init__(
            args = argv,
            path_fyr = dir_ui / "utils_app.fyr",
            path_fyh = dir_ui / "utils_app.fyh",
        )
        self.subcommands = self.get_path_to_root()


    # --------------------------------------------------------------------------
    def run(self):
        command = self.subcommands.pop(0)
        if command == "summary": return self._run_summary()
        raise NotImplementedError(f"Unknown command: {command}")


    # --------------------------------------------------------------------------
    def _run_summary(self):
        app_name = self.get_arg_str("app_name")
        path_fyr = self.get_arg_path("path_fyr", assertion = fy.PathAssertion.FILE_IN)
        path_fyh = self.get_arg_path("path_fyh", assertion = fy.PathAssertion.FILE_IN)

        _fy_parser = fy.FreyaParser.from_files(path_fyr, path_fyh)
        _fy_parser.summarize_usage(app_name)


# //////////////////////////////////////////////////////////////////////////////
