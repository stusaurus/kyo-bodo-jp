"""Reviewed publisher facts and product identity for the 100-game milestone."""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants

def test_new_game_facts_and_match_constraints():
    games = {g["game_id"]: g for g in GAMES}
    cases = [
        ("geister", (2, 2, 20, 20, 10), "4580215110153", "https://mobiusgames.shop-pro.jp/?pid=144929015", "メビウスゲームズ ガイスター Geister ボードゲーム", ["ガイスター ぬいぐるみ","メビウスゲームズ ガイスター ミニ","ガイスター ボードゲーム"]),
        ("penguin-party", (2, 6, 15, 15, 6), "4562365270864", "https://www.newgamesorder.jp/games/penguinparty", "ニューゲームズオーダー ペンギンパーティ 新装版", ["ペンギンパーティ カードゲーム","ニューゲームズオーダー ペンギンパーティ プールパーティ"]),
        ("magic-maze-pocket", (2, 8, 15, 15, 8), "0790757739697", "https://gamemarket.jp/game/186831", "心火GAMES マジックメイズ・ポケット 日本語版", ["心火GAMES マジックメイズ 日本語版","心火GAMES マジックメイズ・ポケット","マジックメイズ・ポケット 日本語版"]),
    ]
    for gid, specs, jan, source, good, bad in cases:
        g = games[gid]
        assert tuple(g[k] for k in ("players_min","players_max","play_time_min","play_time_max","age")) == specs
        assert g["specs_source"] == source
        assert query_variants(g)[0] == jan
        assert match_item(g, {"itemName": good})[0]
        for name in bad + [good + " 中古", good + " 拡張版", good + " 英語版", good + " カードスリーブ"]:
            assert not match_item(g, {"itemName": name})[0], (gid, name)
    assert games["magic-maze-pocket"]["cooperative"]
    assert not games["geister"]["cooperative"]
    assert not games["penguin-party"]["cooperative"]
