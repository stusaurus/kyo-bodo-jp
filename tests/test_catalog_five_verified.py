"""Five Japanese board games added only after checking product-version specifications.

Source: Japanese publisher / authorized distributor pages on 2026-11-19.
Gameplay blurbs are descriptions of rules, not firsthand testing, popularity or stock.
"""
from data.catalog import GAMES, supports_players
from scripts import build_site as site
from scripts.fetch_rakuten import match_item

ADDED = {
    "nana-toridori": (2, 6, 10, 20, 6,
                     "https://arclightgames.jp/product/767toridori/"),
    "incan-gold-rediscovered": (3, 8, 20, 40, 8,
                               "https://arclightgames.jp/product/298whp/"),
    "ciao-ciao": (2, 4, 20, 25, 8,
                  "https://mobiusgames.shop-pro.jp/?pid=144935571"),
    "nmbr9": (1, 4, 20, 20, 8,
             "https://mobiusgames.shop-pro.jp/?pid=145075144"),
    "houseki-ippai": (2, 6, 5, 5, 4,
                      "https://arclightgames.jp/product/576houseki/"),
}


def test_five_verified_editions_have_no_duplicate_records():
    ids = [g["game_id"] for g in GAMES]
    assert len(ids) == len(set(ids)) == 91
    assert set(ADDED).issubset(ids)
    for gid, (*facts, src) in ADDED.items():
        g = site.BY_ID[gid]
        assert tuple(g[k] for k in ("players_min", "players_max",
                                    "play_time_min", "play_time_max", "age")) == tuple(facts)
        assert g["specs_source"] == src
        assert len(g["how_to_play"]) == 3
        assert g["cooperative"] is False
        assert g["rakuten_query"]
        assert not g.get("players_open_ended")
        assert 1 <= g["players_min"] <= g["players_max"] <= 8


def test_short_play_family_and_solo_cohorts_expand_consistently():
    short = [g for g in GAMES if g["play_time_max"] <= 20]
    solo = [g for g in GAMES if supports_players(g, 1)]
    assert len(short) == 35
    assert len(solo) == 14
    assert {"nana-toridori", "nmbr9", "houseki-ippai"} <= {
        g["game_id"] for g in short
    }
    assert "nmbr9" in {g["game_id"] for g in solo}
    assert not supports_players(site.BY_ID["incan-gold-rediscovered"], 2)
    assert supports_players(site.BY_ID["incan-gold-rediscovered"], 8)
    assert not supports_players(site.BY_ID["nana-toridori"], 1)
    assert supports_players(site.BY_ID["nana-toridori"], 2)
    assert supports_players(site.BY_ID["houseki-ippai"], 4)
    assert site.BY_ID["houseki-ippai"]["age"] == 4


def test_every_new_detail_renders_proven_specs_and_safe_outbound(monkeypatch):
    # All five must remain usable before the Rakuten API returns any safe matches.
    # Manufacturer proof is NOT proof of a live affiliate product.
    monkeypatch.setattr(site, "RAKUTEN", {})
    for gid, (_, _, tmin, tmax, age, source) in ADDED.items():
        g = site.BY_ID[gid]
        html = site.game_page(g)
        assert f'href="{site.u("games/" + gid + "/")}"' not in html or (
            site.canon("games/" + gid + "/") in html)
        assert f'<h1>{site.e(g["title"])}</h1>' in html
        assert f'href="{source}"' in html
        assert 'target="_blank" rel="noopener noreferrer"' in html
        assert '人数・所要時間・対象年齢の確認元' in html
        assert f'{site.format_play_time(g)}' in html
        assert f'{age}歳〜' in html
        assert "掲載作品と一致する販売商品を確認できていません" in html
        panel = html.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
        assert 'data-track="rakuten_search_click"' in panel
        assert 'data-affiliate="rakuten"' not in panel
        assert 'rel="sponsored noopener"' not in panel
        assert "PR：" not in panel


def test_new_game_pages_link_from_catalog_and_avoid_unverified_reviews():
    markup = site.games_index()
    for gid in ADDED:
        assert f'/kyo-bodo-jp/games/{gid}/' in markup
        g = site.BY_ID[gid]
        assert g["description"] == g["appeal"]
        assert "実際に遊んだ" not in g["appeal"]
    # The source-supported 2025 edition is separate from an older Incan Gold box.
    assert site.BY_ID["incan-gold-rediscovered"]["title"] == "インカの黄金 再発掘"
    assert "再発掘" in site.BY_ID["incan-gold-rediscovered"]["rakuten_query"]


def test_five_product_identities_never_accept_named_non_game_goods_or_older_edition():
    cases = [
        ("nana-toridori", "ナナトリドリ アークライト カードゲーム", True),
        ("nana-toridori", "ナナトリドリ キーホルダー", False),
        ("incan-gold-rediscovered", "インカの黄金 再発掘 日本語版 アークライト", True),
        ("incan-gold-rediscovered", "インカの黄金 新版 完全日本語版", False),
        ("incan-gold-rediscovered", "インカの黄金 再発掘 英語版 ボードゲーム", False),
        ("ciao-ciao", "チャオチャオ メビウス ボードゲーム", True),
        ("ciao-ciao", "チャオチャオ 食器セット", False),
        ("nmbr9", "ナンバーナイン NMBR9 日本語版 メビウスゲームズ", True),
        ("nmbr9", "NMBR9 Abacus ボードゲーム", True),
        ("nmbr9", "ナンバーナイン 数字シール", False),
        ("houseki-ippai", "宝石がいっぱい！ アークライト カードゲーム", True),
        ("houseki-ippai", "宝石がいっぱい！ おもちゃ ネックレス", False),
    ]
    for gid, listing, should_accept in cases:
        approved, reason, _ = match_item(site.BY_ID[gid], {"itemName": listing})
        assert approved is should_accept, (gid, listing, reason)


def test_every_new_game_prevents_accessory_only_advertising():
    for gid in ADDED:
        game = site.BY_ID[gid]
        for bad in ("カードスリーブ", "中古", "拡張セット", "英語版"):
            title = f"{game['title']} {bad} ボードゲーム"
            matched, _, _ = match_item(game, {"itemName": title})
            assert not matched, (gid, bad)


def test_three_new_party_games_are_sourced_and_safely_matched():
    facts = {
        "animal-old-maid": (2, 6, 15, 15, 6, "アークライト"),
        "ding": (2, 7, 10, 10, 8, "アークライト"),
        "eggsposed": (3, 8, 20, 20, 9, "オインクゲームズ"),
    }
    for gid, (*expected, publisher) in facts.items():
        game = site.BY_ID[gid]
        assert tuple(game[k] for k in ("players_min", "players_max", "play_time_min", "play_time_max", "age")) == tuple(expected)
        assert game["specs_source"].startswith("https://")
        assert not game["cooperative"]
        assert match_item(game, {"itemName": f"{publisher} {game['title']} ボードゲーム"})[0]
        assert not match_item(game, {"itemName": f"{game['title']} ボードゲーム"})[0]
        for bad in ("中古", "拡張セット", "カードスリーブ", "英語版", "2個セット"):
            assert not match_item(game, {"itemName": f"{publisher} {game['title']} {bad}"})[0]
        assert f'/kyo-bodo-jp/games/{gid}/' in site.games_index()
