"""Regression checks for factual 2-person vs flexible-player landing guidance."""
import re
from scripts import build_site as site


def _scene(sid):
    return next(scene for scene in site.SCENES if scene["scene_id"] == sid)


def test_two_player_format_is_above_comparison_table_without_changing_seo():
    page = site.scene_page(_scene("two-player"))
    assert page.count('data-two-player-format') == 1
    assert 'id="two-player-comparison"' in page
    assert page.index("data-two-player-format") < page.index('id="two-player-comparison"')
    assert page.count('data-format-group=') == 2
    assert page.count('<h1') == 1
    assert '<link rel="canonical" href="https://stusaurus.github.io/kyo-bodo-jp/scenes/two-player/"' in page
    assert "掲載人数が2人だけ" in page
    assert "2人を含む複数人数に対応" in page
    assert "人気ランキングではありません" in page
    assert "2人で最も面白い" in page  # specifically cautions against overclaiming


def test_samples_and_counts_are_backed_by_catalog_player_ranges():
    html = site.two_player_format_guide()
    eligible = [g for g in site.GAMES if site.supports_players(g, 2)]
    only_two = [g for g in eligible if g['players_min'] == g['players_max'] == 2]
    flexible = [g for g in eligible if g not in only_two]
    assert only_two and flexible
    assert re.search(r'掲載人数が2人だけ\s*<small>' + str(len(only_two)) + r'本</small>', html)
    assert re.search(r'2人を含む複数人数に対応\s*<small>' + str(len(flexible)) + r'本</small>', html)
    assert html.count('data-two-player-sample') == min(3,len(only_two))+min(3,len(flexible))
    for g in only_two[:3]+flexible[:3]:
        assert 'href="/kyo-bodo-jp/games/' + g['game_id'] + '/"' in html
        assert str(g["play_time_min"]) + '〜' + str(g["play_time_max"]) + '分' in html
    assert '星5' not in html


def test_other_scenes_unchanged():
    family = site.scene_page(_scene("family"))
    assert 'data-two-player-format' not in family
    assert 'id="two-player-comparison"' not in family
    assert '夫婦・カップル' not in site.two_player_format_guide().split('<h2 id="two-player-format-title">')[0]
