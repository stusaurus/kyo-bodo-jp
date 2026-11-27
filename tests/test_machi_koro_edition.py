"""Machi Koro June 2025 renewal must match its exact retail edition."""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants

def test_machi_koro_2025_edition():
    g = next(g for g in GAMES if g["game_id"] == "machi-koro")
    assert (g["players_min"],g["players_max"],g["play_time_min"],g["play_time_max"],g["age"]) == (2,5,30,30,7)
    assert g["specs_source"] == "https://prtimes.jp/main/html/rd/p/000000016.000086022.html"
    assert query_variants(g)[0] == "4560463140249"
    assert match_item(g, {"itemName":"グランディング(Grounding) 街コロ(新装版) (2-5人用 30分 7才以上向け) ボードゲーム"})[0]
    for name in ("グランディング 街コロ ボードゲーム","街コロ 新装版 ボードゲーム","グランディング 街コロ 新装版 街コロプラスシャープ","グランディング 街コロ 新装版 拡張","グランディング 街コロ 新装版 中古"):
        assert not match_item(g, {"itemName":name})[0],name
