#!/usr/bin/env python3
import json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "data" / "games.json"
OUT = ROOT / "data" / "rakuten_cache.json"
APP_ID = os.environ.get("RAKUTEN_APPLICATION_ID", "").strip()
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "").strip()
ENDPOINT = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"


def norm(s: str) -> str:
    return re.sub(r"[\s　・:：!！?？()（）\-ー_]+", "", (s or "").lower())


def item_score(game, item):
    name = norm(item.get("itemName", ""))
    if not name:
        return -999
    score = 0
    title = norm(game["title"])
    if title and title in name:
        score += 30
    for token in [t for t in re.split(r"[\s　]+", game.get("rakuten_query", "")) if len(t) >= 2]:
        if norm(token) in name:
            score += 5
    for bad in game.get("rakuten_exclude", []):
        if norm(bad) and norm(bad) in name:
            score -= 60
    if "中古" in item.get("itemName", ""):
        score -= 80
    if item.get("affiliateUrl"):
        score += 4
    if item.get("mediumImageUrls"):
        score += 2
    if (item.get("reviewCount") or 0) >= 10:
        score += 1
    return score


def fetch_game(game):
    params = {
        "applicationId": APP_ID,
        "keyword": game["rakuten_query"],
        "hits": 10,
        "availability": 1,
        "imageFlag": 1,
        "format": "json",
        "formatVersion": 2,
        "elements": "itemName,itemCode,itemUrl,affiliateUrl,mediumImageUrls,reviewAverage,reviewCount,shopName",
    }
    if AFFILIATE_ID:
        params["affiliateId"] = AFFILIATE_ID
    req = urllib.request.Request(
        ENDPOINT + "?" + urllib.parse.urlencode(params),
        headers={
            "accessKey": ACCESS_KEY,
            "Origin": "https://stusaurus.github.io",
            "Referer": "https://stusaurus.github.io/kyo-bodo-jp/",
            "User-Agent": "kyo-bodo-jp/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8"))
    items = payload.get("Items") or payload.get("items") or []
    items = [x.get("Item", x.get("item", x)) if isinstance(x, dict) else {} for x in items]
    if not items:
        return None
    best = max(items, key=lambda x: item_score(game, x))
    if item_score(game, best) < 0:
        return None
    images = best.get("mediumImageUrls") or []
    image = ""
    if images:
        first = images[0]
        image = first.get("imageUrl", "") if isinstance(first, dict) else str(first)
    return {
        "item_name": best.get("itemName", ""),
        "item_code": best.get("itemCode", ""),
        "url": best.get("affiliateUrl") or best.get("itemUrl") or "",
        "image_url": image,
        "shop_name": best.get("shopName", ""),
        "review_average": best.get("reviewAverage"),
        "review_count": best.get("reviewCount"),
    }


def main():
    if not APP_ID or not ACCESS_KEY:
        print("Rakuten credentials are not configured; keeping non-affiliate search fallbacks.")
        OUT.write_text("{}\n", encoding="utf-8")
        return 0
    games = json.loads(GAMES.read_text(encoding="utf-8"))
    out = {}
    failures = 0
    for i, game in enumerate(games, 1):
        try:
            hit = fetch_game(game)
            if hit:
                out[game["game_id"]] = hit
                print(f"[{i}/{len(games)}] {game['title']}: OK")
            else:
                failures += 1
                print(f"[{i}/{len(games)}] {game['title']}: no confident match")
        except Exception as e:
            failures += 1
            print(f"[{i}/{len(games)}] {game['title']}: {e}", file=sys.stderr)
        time.sleep(0.25)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved {len(out)} links; {failures} unresolved")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
