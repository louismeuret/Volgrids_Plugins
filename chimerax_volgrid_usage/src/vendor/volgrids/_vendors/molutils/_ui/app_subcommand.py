from abc import ABC, abstractmethod

import volgrids._vendors.molutils as mu

# //////////////////////////////////////////////////////////////////////////////
class AppSubcommand(ABC):
    """
    Base class for all subcommands of the molutils suite of applications.
    They hold a reference to the unique `AppMain` instance, which they can use to access the CLI arguments.
    """

    # --------------------------------------------------------------------------
    def __init__(self, app_main: "mu.AppMain"):
        self.main = app_main


    # --------------------------------------------------------------------------
    @abstractmethod
    def run(self):
        raise NotImplementedError()


# //////////////////////////////////////////////////////////////////////////////
