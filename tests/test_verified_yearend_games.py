"""Exact editions backed by publisher and retailer specifications, 2026-11-27."""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants

def test_yearend_game_specs_and_exact_purchases():
    games = {g["game_id"]: g for g in GAMES}
    cases = [
        ("dominion-2nd", (2, 4, 30, 30, 14), "4981932023069", "https://hobbyjapan.games/dominion_2nd/", "ホビージャパン ドミニオン:第二版 日本語版", ["ホビージャパン ドミニオン 陰謀 第二版 日本語版","ホビージャパン ドミニオン 第二版","ドミニオン 第二版 日本語版","ホビージャパン ドミニオン 第二版 日本語版 海辺"]),
        ("deep-sea-adventure-boost", (2, 6, 30, 30, 8), "4571394093757", "https://oinkgames.com/ja/games/analog/deep-sea-adventure-boost/", "オインクゲームズ 海底探険 深版", ["オインクゲームズ 海底探険","オインクゲームズ 海底探険 深版 ジッパーバッグ","海底探険 深版 ボードゲーム"]),
        ("telestrations-2nd", (4, 8, 30, 30, 12), "4560450500865", "https://tendaysgames.shop/?pid=147417014", "テンデイズゲームズ テレストレーション 第2版 日本語版", ["テンデイズゲームズ テレストレーション 初版","テンデイズゲームズ テレストレーション 第2版 6人用","テレストレーション 第2版 ボードゲーム"]),
    ]
    for gid, specs, jan, source, good, bad in cases:
        g = games[gid]
        assert tuple(g[k] for k in ("players_min","players_max","play_time_min","play_time_max","age")) == specs
        assert g["specs_source"] == source
        assert query_variants(g)[0] == jan
        assert match_item(g, {"itemName": good})[0]
        for name in bad + [good + " 拡張", good + " 中古", good + " 英語版", good + " カードスリーブ"]:
            assert not match_item(g, {"itemName": name})[0], (gid, name)
