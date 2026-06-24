import sys
from pathlib import Path

try:
    import molutils as mu
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import molutils as mu

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def main():
    mu.AppMain(sys.argv).run()


################################################################################
if __name__ == "__main__":
    main()


################################################################################
