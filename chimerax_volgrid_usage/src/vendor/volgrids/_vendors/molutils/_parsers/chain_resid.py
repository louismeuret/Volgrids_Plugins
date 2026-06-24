import volgrids._vendors.molutils as mu

# //////////////////////////////////////////////////////////////////////////////
class ChainResid:
    def __init__(self, chain: str, resid: str):
        self.chain = chain
        self.resid = resid


    # --------------------------------------------------------------------------
    @classmethod
    def from_pdb(cls, line: str) -> "ChainResid":
        """Parses an ATOM/HETATM line (PDB format) and returns a ChainResid instance."""
        return cls(mu.ParserPDB.get_chainid(line), mu.ParserPDB.get_resid(line))


    # --------------------------------------------------------------------------
    @classmethod
    def from_dotstr(cls, dotstr: str) -> "ChainResid":
        """Parses a string in the format `chainid.resid`."""
        parts = dotstr.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid format for ChainResid: {dotstr}. Expected format: `chainid.resid`.")
        chain, resid = parts
        return cls(chain, resid)


    # --------------------------------------------------------------------------
    def get_dotstr(self) -> str:
        """Returns a string in the format `chainid.resid`."""
        return f"{self.chain}.{self.resid}"


# //////////////////////////////////////////////////////////////////////////////
