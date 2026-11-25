"""Search-entry usability regressions for existing short-time scene, no new games/offers."""
from scripts import build_site as site


def scene(sid):
    return next(s for s in site.SCENES if s["scene_id"] == sid)


def s_title(sid):
    return scene(sid)["title"]


def test_short_scene_hero_links_to_existing_complete_finder():
    html = site.scene_page(scene("short"))
    count = sum(g["play_time_max"] <= 20 for g in site.GAMES)
    assert count == 35  # current verified catalog baseline, not a claimed popularity count
    assert html.count('id="short-time-finder"') == 1
    assert html.count('href="#short-time-finder"') == 1
    assert f"10・15・20分と人数から{count}本を絞り込む" in html
    assert html.index('href="#short-time-finder"') < html.index('id="short-time-finder"')
    assert html.index('href="#short-time-finder"') < html.index('class="section scene-quick-comparison"')
    assert 'id="short-time-minutes"' in html
    assert 'id="short-time-players"' in html
    assert 'id="short-time-age"' in html
    assert html.count('data-short-game="') == count
    assert '20分以内・短時間で遊べるボードゲームおすすめ' in html


def test_natural_japanese_scene_headings_are_visible_without_keyword_padding():
    expected = {
        "couple": "夫婦・カップルで遊ぶときの選び方",
        "short": "短時間で遊ぶときの選び方",
        "large-group": "大人数で遊ぶときの選び方",
        "drinking": "飲み会で遊ぶときの選び方",
        "cooperative": "協力ゲームを選ぶときの考え方",
        "beginner": "初心者と遊ぶときの選び方",
    }
    for sid, heading in expected.items():
        html = site.scene_page(scene(sid))
        assert '<h2>' + heading + '</h2>' in html
        assert html.count('class="section scene-selection-guide"') == 1
        if sid in ("short", "large-group", "drinking", "beginner"):
            assert s_title(sid) + "ときの選び方" not in html
    assert '<h2>2人で遊ぶときの選び方</h2>' in site.scene_page(scene("two-player"))
    assert '<h2>小学生と遊ぶときの選び方</h2>' in site.scene_page(scene("children"))


def test_short_time_entry_does_not_rewire_other_scenes_or_product_links():
    for sid in ("two-player", "children", "family", "couple", "solo"):
        html = site.scene_page(scene(sid))
        assert 'href="#short-time-finder"' not in html
    short_html = site.scene_page(scene("short"))
    assert 'data-track="game_detail_click"' in short_html
    assert 'data-game-id="dobble"' in short_html
    assert short_html.count('<h1>') == 1
    assert 'href="' + site.canon("scenes/short/") + '"' in short_html
    # This is only a content/navigation change, not a new affiliate offer.
    assert 'href="https://search.rakuten.co.jp/search/mall/' in site.game_page(
        site.BY_ID["qwirkle"]
    ) or site.RAKUTEN.get("qwirkle", {}).get("url")
