"""Family game specifications and conservative Japanese product matching."""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants

def test_verified_family_game_specifications_and_product_identity():
    games = {g["game_id"]: g for g in GAMES}
    cases = [
        ("pig-10", (2, 8, 15, 15, 6), "4580215110122", "https://mobiusgames.shop-pro.jp/?pid=145076352", "メビウスゲームズ ぴっぐテン 日本語版", ["ぴっぐテン 日本語版","メビウスゲームズ ぴっぐテン","メビウスゲームズ ぴっぐテン 日本語版 ぬいぐるみ"]),
        ("zogen", (2, 6, 20, 20, 6), "4571394090701", "https://oinkgames.com/ja/games/analog/zogen/", "オインクゲームズ ゾーゲン カードゲーム", ["ゾーゲン カードゲーム","オインクゲームズ ゾーゲン キーホルダー"]),
        ("king-of-tokyo-new", (2, 6, 30, 30, 8), "4981932022680", "https://hobbyjapan.games/shin_kot/", "ホビージャパン 新・キング・オブ・トーキョー 日本語版", ["ホビージャパン キング・オブ・トーキョー 日本語版","ホビージャパン 新・キング・オブ・トーキョー 日本語版 モンスターパック","ホビージャパン 新・キング・オブ・トーキョー 日本語版 邪悪覚醒","ホビージャパン 新・キング・オブ・トーキョー"]),
    ]
    for gid, specs, jan, source, good, bad in cases:
        g = games[gid]
        assert tuple(g[k] for k in ("players_min","players_max","play_time_min","play_time_max","age")) == specs
        assert g["specs_source"] == source
        assert query_variants(g)[0] == jan
        assert match_item(g, {"itemName": good})[0]
        for name in bad + [good + " 中古", good + " 拡張版", good + " 英語版", good + " カードスリーブ"]:
            assert not match_item(g, {"itemName": name})[0], (gid, name)
