import sys
from pathlib import Path

try:
    import freyacli as fy
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import freyacli as fy

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def main():
    fy._FreyacliUtilsApp(sys.argv).run()


################################################################################
if __name__ == "__main__":
    main()


################################################################################
