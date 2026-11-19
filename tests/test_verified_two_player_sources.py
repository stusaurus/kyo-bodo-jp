"""Verified two-player product facts as of 2026-11-19.

Data is checked against the Japanese distributor or reputable authorized store.
These are product specifications, not live Rakuten inventory or test-play claims.
"""
from scripts import build_site as site

FACTS = {
    "quarto": (2, 2, 15, 15, 6,
               "https://suppe.sugorokuya.jp/items/80138"),
    "patchwork": (2, 2, 30, 30, 8,
                  "https://hobbyjapan.games/patchwork/"),
    "jaipur": (2, 2, 30, 30, 12,
               "https://hobbyjapan.games/jaipur/"),
    "splendor-duel": (2, 2, 30, 30, 10,
                      "https://hobbyjapan.games/splendor_duel/"),
    "seven-wonders-duel": (2, 2, 30, 30, 10,
                           "https://hobbyjapan.games/7_wonders_duel/"),
}


def test_two_player_specs_use_version_appropriate_primary_sources():
    assert len(site.GAMES) == 83
    for gid, (pmin, pmax, tmin, tmax, age, source) in FACTS.items():
        g = site.BY_ID[gid]
        assert (g["players_min"], g["players_max"],
                g["play_time_min"], g["play_time_max"], g["age"]) == (
                    pmin, pmax, tmin, tmax, age), gid
        assert g["specs_source"] == source
        assert site.supports_players(g, 2)
        assert not g["cooperative"], gid
        assert site.format_play_time(g) == f"{tmax}分", gid


def test_two_player_product_pages_display_verifiable_sources_and_correct_times():
    for gid, (_, _, _, tmax, age, source) in FACTS.items():
        markup = site.game_page(site.BY_ID[gid])
        assert "人数・所要時間・対象年齢の確認元" in markup, gid
        assert f'href="{source}"' in markup, gid
        assert 'target="_blank" rel="noopener noreferrer"' in markup, gid
        assert f'<span><small>時間</small>{tmax}分</span>' in markup, gid
        assert f'<span><small>対象年齢</small>{age}歳〜</span>' in markup, gid
    assert sum(bool(g.get("specs_source")) for g in site.GAMES) >= 16


def test_two_player_quick_filter_uses_corrected_time_limits():
    markup = site.scene_page(next(s for s in site.SCENES if s["scene_id"] == "two-player"))
    for gid, tmax in (("quarto", 15), ("patchwork", 30)):
        assert site.BY_ID[gid]["play_time_max"] == tmax
        assert f'data-game-id="{gid}"' in markup
    # The catalog's 30-minute filter uses its proven maximum, not a subjective score.
    catalog = site.games_index()
    assert 'data-short="1"' in catalog
