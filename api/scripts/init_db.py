"""Create the database tables and load the template presets.

Run from the api folder:
    python scripts/init_db.py            create the tables if they are missing (safe to repeat)
    python scripts/init_db.py --reset    DEVELOPMENT ONLY: delete everything and start again
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402

import app  # noqa: E402,F401  (loads the .env file)
from app import dbsetup  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete all data in this database first")
    parser.add_argument("--allow-remote", action="store_true", help="allow --reset on a database that is not on this computer")
    args = parser.parse_args()

    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL is not set. Add it to .env first (see docs/database-setup-windows.md).")
        return 1
    if args.reset and input("This deletes ALL data in this database. Type 'yes' to continue: ").strip() != "yes":
        print("Cancelled. Nothing was changed.")
        return 1
    try:
        result = dbsetup.setup(url, reset=args.reset, allow_remote_reset=args.allow_remote)
    except psycopg.OperationalError as exc:
        print(f"Could not connect to the database:\n  {' '.join(str(exc).split())}")
        print("Check that PostgreSQL is running and that DATABASE_URL in .env is correct.")
        return 1
    except RuntimeError as exc:
        print(exc)
        return 1
    print(f"Tables {result}. The 4 template presets are loaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
