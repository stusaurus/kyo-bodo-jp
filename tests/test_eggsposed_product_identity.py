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


def test_animal_old_maid_jan_preserves_publisher_identity():
    # Manufacturer release: https://prtimes.jp/main/html/rd/p/000000007.000041113.html
    game = next(g for g in GAMES if g["game_id"] == "animal-old-maid")
    assert query_variants(game)[0] == "4542325120453"
    assert match_item(game, {"itemName": "アークライト どうぶつババ抜き (2-6人用 15分 6才以上向け) ボードゲーム"})[0]
    for name in ("どうぶつババ抜き ボードゲーム", "アークライト どうぶつババ抜き 中古", "アークライト どうぶつババ抜き 2個セット"):
        assert not match_item(game, {"itemName": name})[0]
