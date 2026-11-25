"""Japanese publisher edition specs are the source of truth for purchase filters.

Sources verified 2026-11-21 against matching currently retained Rakuten offers.
The catalogue must not infer a playtime interval from a publisher's single estimate.
"""
from scripts import build_site as site


VERIFIED = {
    "dobble": (2, 8, 6, 15, "https://hobbyjapan.games/dobble/"),
    "splendor": (2, 4, 10, 30, "https://hobbyjapan.games/splendor/"),
    "gobblet-gobblers": (2, 2, 5, 5, "https://sugorokuya.jp/p/gobblet-gobblers"),
    "lost-cities": (2, 2, 10, 30, "https://www.groupsne.co.jp/products/bg/lostcities/original.html"),
}


def test_four_primary_sources_match_age_players_and_publisher_minutes():
    assert len(site.GAMES) == 91
    for gid, (pmin, pmax, age, duration, source) in VERIFIED.items():
        game = site.BY_ID[gid]
        assert (game["players_min"], game["players_max"], game["age"]) == (pmin, pmax, age), gid
        assert (game["play_time_min"], game["play_time_max"]) == (duration, duration), gid
        assert game["specs_source"] == source
        assert site.supports_players(game, 2)
        assert site.format_play_time(game) == str(duration) + "分"


def test_sources_are_visible_on_each_product_detail_without_extra_advertising():
    for gid, (_, _, _, duration, source) in VERIFIED.items():
        html = site.game_page(site.BY_ID[gid])
        assert html.count('href="' + source + '"') == 1
        assert '人数・所要時間・対象年齢の確認元' in html
        assert 'rel="noopener noreferrer"' in html
        assert 'data-track="rakuten_search_click"' in html or 'data-affiliate="rakuten"' in html
        assert ('<span><small>時間</small>' + str(duration) + '分</span>') in html
        assert '<link rel="canonical" href="' + site.canon("games/" + gid + "/") + '"' in html


def test_corrected_playtimes_propagate_to_real_pre_purchase_choices():
    splendor = site.BY_ID["splendor"]
    assert splendor["play_time_max"] == 30
    assert splendor["play_time_max"] <= 30
    assert splendor["play_time_max"] > 20  # Not in the 20-minute finder
    for gid in ("dobble", "gobblet-gobblers"):
        assert site.BY_ID[gid]["play_time_max"] <= 20
    html = site.games_index()
    for gid in VERIFIED:
        assert 'data-game-id="' + gid + '"' in html
    # These are publisher estimates, not actual game-session durations or stock claims.
    assert "価格の比較ではありません" in html
    assert "ゲーム一覧" in html


def test_publisher_specs_do_not_create_a_new_verified_rakuten_offer():
    for gid in VERIFIED:
        game = site.BY_ID[gid]
        assert "rakuten_query" in game
        assert "specs_source" in game
        # The official source is documentation, not an invented affiliate destination.
        assert game["specs_source"].startswith("https://")
        assert not game["specs_source"].startswith("https://hb.afl.rakuten.co.jp/")
