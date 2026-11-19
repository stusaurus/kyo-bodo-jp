"""Short-time comparison is complete, source-grounded and safe without JavaScript."""
from pathlib import Path
import re
from scripts import build_site as site

EXPECTED = [g for g in site.GAMES if g["play_time_max"] <= 20]


def test_full_short_catalog_not_just_twelve_examples():
    assert len(site.GAMES) == 83
    assert len(EXPECTED) == 28
    html = site.short_time_finder()
    ids = re.findall(r'data-short-game="([^"]+)"', html)
    assert ids == [g["game_id"] for g in EXPECTED]
    assert len(set(ids)) == 28
    assert "全83作品" in html
    assert "全28本" in html
    assert "人気順・実際の試遊評価ではありません" in html


def test_each_short_game_has_factual_conditions_and_live_detail_link():
    html = site.short_time_finder()
    for g in EXPECTED:
        gid = g["game_id"]
        supported = " ".join(str(n) for n in (1, 2, 3, 4, 5, 6, 8)
                             if site.supports_players(g, n))
        assert f'data-short-game="{gid}"' in html
        assert f'data-short-players="{supported}"' in html
        assert f'data-short-minutes="{g["play_time_max"]}"' in html
        assert f'data-short-age="{g["age"]}"' in html
        assert f'href="{site.u("games/" + gid + "/")}"' in html
        assert f'data-game-id="{gid}"' in html
    assert all(g["play_time_max"] <= 20 for g in EXPECTED)
    assert 'data-source="short_time_finder"' in html


def test_short_scene_renders_existing_comparison_and_new_complete_finder():
    scene = next(s for s in site.SCENES if s["scene_id"] == "short")
    html = site.scene_page(scene)
    assert html.count('id="short-time-finder"') == 1
    assert 'id="short-time-form"' in html
    assert 'id="short-time-minutes"' in html
    assert 'id="short-time-players"' in html
    assert 'id="short-time-age"' in html
    assert 'id="short-time-count"' in html
    assert 'id="short-time-empty"' in html
    assert 'id="short-time-reset"' in html
    assert 'short-filter.js' in html
    assert html.count('data-short-game="') == 28
    assert 'scene-quick-comparison' in html
    assert html.count('data-short-minutes=') == 28
    assert 'data-track="game_detail_click"' in html
    assert 'rel="canonical" href="' + site.canon("scenes/short/") + '"' in html
    assert '20分以内・短時間で遊べるボードゲームおすすめ' in html


def test_other_scenes_and_search_tracking_are_not_repurposed():
    for sid in ("two-player", "solo", "children", "family"):
        scene = next(s for s in site.SCENES if s["scene_id"] == sid)
        assert 'id="short-time-finder"' not in site.scene_page(scene)
    js = (Path(site.ROOT) / "assets/short-filter.js").read_text(encoding="utf-8")
    assert "sessionStorage" not in js
    assert "localStorage" not in js
    assert "short_filter_change" in js
    assert "result_count" in js
    assert "filter_dimension" in js
    assert "age.value" in js  # local display filtering, not collection
    assert "child_age:" not in js and "age:age.value" not in js
