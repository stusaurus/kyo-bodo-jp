#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.fetch_rakuten import GAMES, match_item, valid_url
cache=json.loads((ROOT/"data"/"rakuten_cache.json").read_text(encoding="utf-8"))
report=json.loads((ROOT/"data"/"rakuten_audit.json").read_text(encoding="utf-8"))
games=report.get("games",{})
normal=report.get("normal_count",0)
total=report.get("total_games",0)
dups=report.get("duplicate_groups") or {}

expected=len(GAMES)
assert total==expected, f"expected {expected} games, got {total}"
assert len(games)==expected, f"audit rows missing: {len(games)}/{expected}"
assert normal==len(cache), "audit/cache count mismatch"
errors=[gid for gid,row in games.items() if row.get("reason","").startswith("error:")]
assert len(errors)<max(10, expected//4), f"systemic Rakuten API failure: {len(errors)}/{expected}; keep previous deployment"
for game in GAMES:
    hit=cache.get(game["game_id"])
    if not hit: continue
    assert match_item(game,{"itemName":hit.get("item_name","")})[0], game["game_id"]
    assert valid_url(hit.get("url")) and valid_url(hit.get("item_url")), game["game_id"]
    assert hit.get("image_url","").startswith("https://"), f"{game["game_id"]}: missing image"
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
