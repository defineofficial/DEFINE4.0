"""EventReach API."""
from pathlib import Path

from dotenv import load_dotenv

# Read settings from a .env file in the repo root (or the current folder) before anything uses them.
# Values that are already set in the environment win over the file.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()
