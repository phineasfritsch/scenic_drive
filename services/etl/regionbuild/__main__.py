"""`python -m regionbuild` - see regionbuild/cli.py. ops/etl-region is the entry point that runs it."""
import sys

from regionbuild.cli import main

if __name__ == "__main__":
    sys.exit(main())
