"""Manufacturer lists a separate branded mirror: never advertise it as the board game.
Sources: https://oinkgames.com/ja/games/analog/eggsposed/
https://books.rakuten.co.jp/rb/18826971/ (JAN 4571394095485).
The retail listing is not proof of a live affiliate offer.
"""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants


def test_eggsposed_game_not_branded_merchandise():
    game = next(g for g in GAMES if g["game_id"] == "eggsposed")
    assert query_variants(game)[0] == "4571394095485"
    assert match_item(game, {"itemName": "オインクゲームズ ばれたま ボードゲーム"})[0]
    for label in ("こっそりミラー", "手鏡", "mirror", "キーホルダー", "アクリルスタンド", "缶バッジ"):
        assert not match_item(game, {"itemName": f"オインクゲームズ ばれたま {label}"})[0]
