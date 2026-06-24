from pathlib import Path

# //////////////////////////////////////////////////////////////////////////////
class ParserPDB:
    LENGTH_RECORD = 80
    IDX0_ATOMNAME = 12
    IDX1_ATOMNAME = 16
    IDX_ALTLOC = 16
    IDX_CHAIN_ID = 21
    IDX0_RESID = 22
    IDX1_RESID = 26

    # --------------------------------------------------------------------------
    def __init__(self, data_pdb: str):
        self.data = data_pdb.splitlines()


    # --------------------------------------------------------------------------
    @classmethod
    def from_file(cls, path_pdb: Path):
        return cls(path_pdb.read_text())


    # --------------------------------------------------------------------------
    @classmethod
    def join_lines(cls, lines: list[str]) -> str:
        return '\n'.join(lines) + "\nEND"


    # --------------------------------------------------------------------------
    def iter_atoms(self):
        return (
            line for line in self.data
            if line.startswith("ATOM") or line.startswith("HETATM")
        )


    # --------------------------------------------------------------------------
    @classmethod
    def safe_next(cls, gen):
        try: return next(gen)
        except StopIteration: raise ValueError(f"No ATOM records found in PDB file")


    # --------------------------------------------------------------------------
    @classmethod
    def get_atomname(cls, line: str) -> str:
        try: return line[cls.IDX0_ATOMNAME:cls.IDX1_ATOMNAME].strip()
        except IndexError: raise ValueError(f"Unexpected format of ATOM records in PDB file")


    # --------------------------------------------------------------------------
    @classmethod
    def get_chainid(cls, line: str) -> str:
        try: return line[cls.IDX_CHAIN_ID]
        except IndexError: raise ValueError(f"Unexpected format of ATOM records in PDB file")


    # --------------------------------------------------------------------------
    @classmethod
    def get_resid(cls, line: str) -> str:
        return line[cls.IDX0_RESID:cls.IDX1_RESID].strip()


    # --------------------------------------------------------------------------
    @classmethod
    def get_altloc(cls, line: str) -> str:
        try: return line[cls.IDX_ALTLOC]
        except IndexError: raise ValueError(f"Unexpected format of ATOM records in PDB file")


    # --------------------------------------------------------------------------
    @classmethod
    def set_altloc(cls, line: str, altloc: str) -> str:
        if len(altloc) != 1: raise ValueError(f"altloc must be a single character")
        try: return line[:cls.IDX_ALTLOC] + altloc + line[cls.IDX_ALTLOC+1:]
        except IndexError: raise ValueError(f"Unexpected format of ATOM records in PDB file")


# //////////////////////////////////////////////////////////////////////////////
