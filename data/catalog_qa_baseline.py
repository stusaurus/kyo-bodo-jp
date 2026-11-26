"""Explicit reviewed QA baseline; update once when intentionally expanding the catalog."""
import json
from pathlib import Path

_BASELINE = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
CATALOG_COUNT = _BASELINE["catalog_count"]
SHORT_COUNT = _BASELINE["short_count"]
SOLO_COUNT = _BASELINE["solo_count"]
