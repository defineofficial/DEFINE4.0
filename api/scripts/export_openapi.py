"""Write docs/openapi.json from the running app definition.

Run from the api folder:  python scripts/export_openapi.py
Frontend and code generation read that file, so re-run it whenever schemas.py changes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

out = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {out}")
