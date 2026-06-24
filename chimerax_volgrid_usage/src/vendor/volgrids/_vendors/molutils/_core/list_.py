from pathlib import Path

import volgrids._vendors.freyacli as fy
import volgrids._vendors.molutils as mu

# //////////////////////////////////////////////////////////////////////////////
class List(mu.AppSubcommand):
    # -------------------------------------------------------------------------- UI SECTION
    def run(self):
        command = self.main.subcommands.pop(0)

        if command == "chains": return self.app_list_chains()
        if command == "residues": return self.app_list_residues()

        raise ValueError(f"Unknown command: {command}")


    # --------------------------------------------------------------------------
    def app_list_chains(self):
        path_in = self.main.get_arg_path("path_in", assertion = fy.PathAssertion.FILE_IN)
        first_only = self.main.get_arg_bool("first_only")
        print(*mu.List.chains(path_in, first_only = first_only))


    # --------------------------------------------------------------------------
    def app_list_residues(self):
        path_in = self.main.get_arg_path("path_in", assertion = fy.PathAssertion.FILE_IN)
        print(*mu.List.residues(path_in))


    # -------------------------------------------------------------------------- LOGIC SECTION
    @classmethod
    def chains(cls, path_pdb: Path, do_sort: bool = True, first_only: bool = False) -> list[str]:
        pdb = mu.ParserPDB.from_file(path_pdb)
        gen_chain_ids = (mu.ParserPDB.get_chainid(line) for line in pdb.iter_atoms())
        if first_only: return mu.ParserPDB.safe_next(gen_chain_ids)
        if do_sort: return sorted(set(gen_chain_ids))
        return list(set(gen_chain_ids))


    # --------------------------------------------------------------------------
    @classmethod
    def residues(cls, path_pdb: Path, do_sort: bool = True) -> list[str]:
        """Returns list of unique residue identifiers in the format "chainid.resid"."""
        pdb = mu.ParserPDB.from_file(path_pdb)
        gen_residues = (mu.ChainResid.from_pdb(line).get_dotstr() for line in pdb.iter_atoms())
        if do_sort: return sorted(set(gen_residues))
        return list(set(gen_residues))


# //////////////////////////////////////////////////////////////////////////////
