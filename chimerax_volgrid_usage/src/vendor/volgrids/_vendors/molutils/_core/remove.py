import volgrids._vendors.freyacli as fy
import volgrids._vendors.molutils as mu

# //////////////////////////////////////////////////////////////////////////////
class Remove(mu.AppSubcommand):
    # -------------------------------------------------------------------------- UI SECTION
    def run(self):
        command = self.main.subcommands.pop(0)

        if command == "altlocs" : return self.app_remove_altlocs()

        raise ValueError(f"Unknown command: {command}")


    # --------------------------------------------------------------------------
    def app_remove_altlocs(self):
        path_in  = self.main.get_arg_path("path_in",  assertion = fy.PathAssertion.FILE_IN)
        path_out = self.main.get_arg_path("path_out", assertion = fy.PathAssertion.FILE_OUT)
        out = mu.Remove.altlocs(path_in.read_text())
        path_out.write_text(out)


    # --------------------------------------------------------------------------
    @classmethod
    def altlocs(cls, data: str) -> str:
        pdb = mu.ParserPDB(data)

        out = []
        seen_altlocs = set()
        for line in pdb.iter_atoms():
            altloc = mu.ParserPDB.get_altloc(line)
            if altloc == " ":
                out.append(line)
                continue

            resid = mu.ChainResid.from_pdb(line).get_dotstr()
            name = mu.ParserPDB.get_atomname(line)
            key = (resid, name)
            if key in seen_altlocs: continue

            seen_altlocs.add(key)
            out.append(mu.ParserPDB.set_altloc(line, " "))

        return mu.ParserPDB.join_lines(out)


# //////////////////////////////////////////////////////////////////////////////
