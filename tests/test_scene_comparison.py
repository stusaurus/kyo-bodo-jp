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
