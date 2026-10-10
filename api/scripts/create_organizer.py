"""Create an organizer or admin account.

Run from the api folder:
    python scripts/create_organizer.py --email you@example.com --name "Your Name" --admin

The password is asked for on screen, so it never lands in your shell history.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

import app  # noqa: E402,F401  (loads the .env file)
from app.auth import create_organizer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--admin", action="store_true", help="give this account the admin role")
    args = parser.parse_args()

    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL is not set. Add it to .env first (see docs/database-setup-windows.md).")
        return 1
    password = getpass.getpass("Password (at least 8 characters): ")
    if len(password) < 8:
        print("That password is too short. Use at least 8 characters.")
        return 1
    if getpass.getpass("Type it again: ") != password:
        print("The two passwords do not match.")
        return 1
    try:
        with psycopg.connect(url, row_factory=dict_row) as conn:
            row = create_organizer(conn, args.name, args.email, password, "admin" if args.admin else "organizer")
    except psycopg.errors.UniqueViolation:
        print("An account with this email already exists.")
        return 1
    except psycopg.errors.UndefinedTable:
        print("The tables do not exist yet. Run: python scripts/init_db.py")
        return 1
    except psycopg.OperationalError as exc:
        print(f"Could not connect to the database:\n  {' '.join(str(exc).split())}")
        return 1
    print(f"Created {row['role']} account for {row['email']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
