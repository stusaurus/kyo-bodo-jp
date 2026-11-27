"""Publisher age corrections and specific Japanese base-game identity."""
from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, query_variants

def test_publisher_age_and_sources():
    by_id = {g["game_id"]:g for g in GAMES}
    for gid, specs, source in (
        ("mandala",(2,2,20,20,7),"https://hobbyjapan.games/mandala/"),
        ("ticket-ride-europe",(2,5,30,60,13),"https://hobbyjapan.games/ttr_euro/"),
    ):
        g=by_id[gid]
        assert tuple(g[k] for k in ("players_min","players_max","play_time_min","play_time_max","age")) == specs
        assert g["specs_source"] == source
    assert query_variants(by_id["ticket-ride-europe"])[0]=="0824968617137"

def test_retail_identity_is_specific_and_rejects_related_products():
    by_id = {g["game_id"]:g for g in GAMES}
    for gid, good, bad in (
        ("mandala","ホビージャパン｜Hobby JAPAN 【再販】マンダラ 日本語版",[
            "マンダラ 日本語版", "ホビージャパン｜Hobby JAPAN 【再販】マンダラ 日本語版 中古",
            "ホビージャパン｜Hobby JAPAN 【再販】マンダラ 日本語版 キーホルダー",
            "ホビージャパン マンダラ 日本語版 タロットクロス"]),
        ("ticket-ride-europe","ホビージャパン チケット・トゥ・ライド ヨーロッパ (日本語版) (2-5人用 30-60分 13才以上向け) ボードゲーム",[
            "チケット・トゥ・ライド ヨーロッパ", "チケット・トゥ・ライド アメリカ 日本語版",
            "チケット・トゥ・ライド ヨーロッパ 15周年記念版 日本語版",
            "チケット・トゥ・ライド ヨーロッパ 1912 日本語版",
            "中古 チケット・トゥ・ライド ヨーロッパ 日本語版"]),
    ):
        g=by_id[gid]
        assert match_item(g,{"itemName":good})[0],gid
        for name in bad:
            assert not match_item(g,{"itemName":name})[0],(gid,name)
