from pathlib import Path

import volgrids._vendors.freyacli as fy
import volgrids._vendors.molutils as mu

# //////////////////////////////////////////////////////////////////////////////
class AppMain(fy.App):
    _APP_NAME = "molutils"
    _VERSION = mu.__version__

    # --------------------------------------------------------------------------
    def __init__(self,  argv: list[str]):
        dir_ui = Path(__file__).parent
        super().__init__(
            args = argv,
            path_fyr = dir_ui / "fy_rules.fyr",
            path_fyh = dir_ui / "fy_help.fyh",
        )
        self.subcommands = self.get_path_to_root()


    # --------------------------------------------------------------------------
    def run(self):
        command = self.subcommands.pop(0)
        if command == "list"   : return mu.List(self).run()
        if command == "count"  : return mu.Count(self).run()
        if command == "extract": return mu.Extract(self).run()
        if command == "remove" : return mu.Remove(self).run()
        if command == "select" : return self._run_select()
        if command == "merge"  : return self._run_merge()
        raise ValueError(f"Unknown command: {command}")


    # --------------------------------------------------------------------------
    def _run_select(self):
        query = self.get_arg_str("query")
        path_in = self.get_arg_path("path_in", assertion = fy.PathAssertion.FILE_IN)
        path_out = self.get_arg_path("path_out", assertion = fy.PathAssertion.FILE_OUT)
        paths_traj = self.get_arg_path("paths_traj",
            assertion = fy.PathAssertion.FILE_IN, allow_none = True,
            is_list = True
        )

        import MDAnalysis as mda
        mda.Universe(path_in).select_atoms(query).write(path_out)

        if paths_traj is None: return

        path_traj_in, path_traj_out = paths_traj
        u = mda.Universe(path_in, path_traj_in)
        u.select_atoms(query).write(str(path_traj_out), frames = "all")


    # --------------------------------------------------------------------------
    def _run_merge(self):
        paths_in = self.get_arg_path("paths_in", assertion = fy.PathAssertion.FILE_IN, is_list = True)
        path_out = self.get_arg_path("path_out", assertion = fy.PathAssertion.FILE_OUT)
        data = mu.ParserPDB.join_lines(
            line for path_in in paths_in
            for line in mu.ParserPDB.from_file(path_in).iter_atoms()
        )
        path_out.write_text(data)


# //////////////////////////////////////////////////////////////////////////////
