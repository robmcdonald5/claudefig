"""Allow running claudefig as a module: python -m claudefig."""

import sys

from claudefig.cli import main

if __name__ == "__main__":
    sys.exit(main())
