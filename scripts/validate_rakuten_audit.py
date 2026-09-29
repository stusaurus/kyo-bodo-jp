#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/"data"/"rakuten_audit.json").read_text(encoding="utf-8"))
games=report.get("games",{})
normal=report.get("normal_count",0)
total=report.get("total_games",0)
dups=report.get("duplicate_groups") or {}

assert total==50, f"expected 50 games, got {total}"
assert len(games)==50, f"audit rows missing: {len(games)}/50"
assert not dups, f"duplicate item codes found: {dups}"
for gid,row in games.items():
    if row.get("status")=="ok":
        assert row.get("item_code"), f"{gid}: missing item_code"
        assert row.get("item_url","").startswith("https://"), f"{gid}: invalid item_url"
        assert row.get("item_name"), f"{gid}: missing item_name"

print(f"Rakuten audit validated: {normal}/{total} safe current matches, {total-normal} unresolved, duplicates=0")
for gid,row in games.items():
    if row.get("status")!="ok":
        print(f"UNRESOLVED {gid}: {row.get('reason')}")
