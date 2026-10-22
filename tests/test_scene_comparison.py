import json
import re
from test_site_presentation import m

def test_comparison_preserves_ranked_itemlist_and_catalog_values():
    for sid in ('two-player', 'short'):
        scene = next(s for s in m.SCENES if s['scene_id'] == sid)
        ranked = sorted(m.GAMES, key=lambda g: m.scene_score(g, scene), reverse=True)
        ranked = [g for g in ranked if m.scene_score(g, scene) >= 50][:12]
        page = m.scene_page(scene)
        schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page).group(1))
        table = page.split('<tbody>')[1].split('</tbody>')[0]
        assert table.count('<tr>') == len(ranked)
        assert [x['name'] for x in schema['itemListElement']] == [g['title'] for g in ranked]
        for row, game in zip(table.split('</tr>'), ranked):
            assert m.e(game['title']) in row
            assert f"{game['play_time_min']}〜{game['play_time_max']}分" in row
            assert ('協力' if game['cooperative'] else '対戦') in row
            if sid == 'two-player': assert m.supports_players(game,2)
            else: assert game['play_time_max'] <= 20

def test_short_snippet_matches_existing_twenty_minute_filter():
    scene = next(s for s in m.SCENES if s['scene_id'] == 'short')
    page = m.scene_page(scene)
    assert '20分以内・短時間' in page
    assert '30分以内' not in page

def test_other_scenes_are_outside_the_pilot():
    for scene in m.SCENES:
        if scene['scene_id'] not in ('two-player','short'):
            assert m.scene_comparison_table(scene, m.GAMES[:3]) == ''


def test_two_player_catalog_order_is_not_a_quality_ranking():
    scene = next(s for s in m.SCENES if s['scene_id'] == 'two-player')
    ranked = [g for g in m.GAMES if m.scene_score(g, scene) >= 50][:12]
    assert [g['game_id'] for g in ranked] == [
        'carcassonne','splendor','dobble','ito','ito-rainbow','nanjamonja',
        'codenames-duet','love-letter','coyote','ubongo','blokus','word-basket']
    assert {m.scene_score(g,scene) for g in ranked} == {100}
    page = m.scene_page(scene)
    assert 'カタログ掲載順に紹介' in page
    assert 'おすすめ度の高い順' not in page
    assert '2人専用</td>' not in page
    assert '2人以上' in page and '人数の公式情報' in page


def test_open_ended_player_count_requires_explicit_publisher_evidence():
    duet = m.BY_ID['codenames-duet']
    assert duet['players_max'] is None
    assert m.player_label(duet) == '2人以上'
    assert all(m.supports_players(duet,n) for n in range(2,15))
    assert not m.supports_players(duet,1)
    unknown = dict(duet,players_source='')
    assert not m.supports_players(unknown,3)
    assert m.player_label(unknown) == '人数未確認'
    assert not m.supports_players(dict(duet,players_open_ended=False),3)
    assert m.player_label(dict(duet,players_max=2)) == '2人対応'


def test_two_player_choices_use_full_catalog_and_exact_conditions():
    scene = next(s for s in m.SCENES if s['scene_id'] == 'two-player')
    guide = m.scene_selection_guide(scene, m.GAMES[:12])
    groups = re.findall(r'<details class="two-player-choices">(.*?)</ul></details>', guide)
    assert len(groups) == 2
    eligible = [g for g in m.GAMES if m.supports_players(g, 2)]
    expected = [
        [g for g in eligible if g['players_min'] == g['players_max'] == 2],
        [g for g in eligible if g['cooperative'] and g['play_time_max'] <= 20],
    ]
    for group, games in zip(groups, expected):
        assert re.findall(r'data-choice-game="([^"]+)"', group) == [g['game_id'] for g in games]
        assert f'（{len(games)}本）' in group
        for game in games:
            assert m.u('games/' + game['game_id'] + '/') in group
            assert f'{game["play_time_min"]}〜{game["play_time_max"]}分' in group
            assert f'対象{game["age"]}歳〜' in group
            for step in game['how_to_play']:
                assert f'<li>{m.e(step)}</li>' in group
        assert group.count('class="choice-rules"') == len(games)
    # Known valid choices were unreachable in the old 12-card shortlist.
    assert 'data-choice-game="sky-team"' in groups[0]
    assert 'data-choice-game="sky-team"' in groups[1]
    assert 'data-choice-game="codenames-duet"' not in groups[0]
    assert 'data-choice-game="codenames-duet"' in groups[1]
    assert 'data-choice-game="pandemic"' not in guide
    assert '人気順・優劣の順位ではありません' in guide


def test_other_scene_guides_keep_existing_three_picks():
    scene = next(s for s in m.SCENES if s['scene_id'] == 'short')
    guide = m.scene_selection_guide(scene, m.GAMES[:3])
    assert '掲載データから見比べる3本' in guide
    assert 'two-player-choices' not in guide


def test_duet_edition_values_and_short_filter_match_current_japanese_publisher():
    from scripts.fetch_rakuten import match_item
    duet = m.BY_ID['codenames-duet']
    assert duet['edition'] == '2025年新版 日本語版'
    assert (duet['play_time_min'],duet['play_time_max'],duet['age']) == (15,15,11)
    assert duet['players_source'] == 'https://hobbyjapan.games/codename_duet/'
    assert match_item(duet,{'itemName':'コードネーム：デュエット 2025年新版 日本語版'})[0]
    for title in ('コードネーム：デュエット 日本語版','コードネーム：デュエット 2018年版 日本語版',
                  'コードネーム：デュエット 2025年新版 英語版'):
        assert not match_item(duet,{'itemName':title})[0]
    short = next(s for s in m.SCENES if s['scene_id']=='short')
    assert m.scene_score(duet,short) >= 50
