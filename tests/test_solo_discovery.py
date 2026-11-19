"""Solo discovery must include every catalog title supporting one player."""
import json
from data.catalog import GAMES, supports_players
from scripts.build_site import SCENES, scene_representatives, scene_score, scene_page, games_index, home, scenes_index

def test_solo_scene_is_unique_and_factual():
    solo = [s for s in SCENES if s["scene_id"] == "solo"]
    assert len(solo) == 1
    assert solo[0]["rule"] == {"type": "players", "value": 1}
    eligible = [g for g in GAMES if supports_players(g, 1)]
    assert len(eligible) >= 10
    assert any(g["game_id"] == "ark-nova" for g in eligible)
    ranked = scene_representatives(solo[0])
    assert [g["game_id"] for g in ranked] == [g["game_id"] for g in eligible], "Do not silently truncate solo titles"
    assert all(scene_score(g, solo[0]) == 100 for g in ranked)
    assert all(scene_score(g, solo[0]) == 0 for g in GAMES if not supports_players(g, 1))

def test_solo_scene_and_filter_have_real_links_and_correct_count():
    solo = next(s for s in SCENES if s["scene_id"] == "solo")
    eligible = [g for g in GAMES if supports_players(g, 1)]
    html = scene_page(solo)
    assert "<h1>1人で遊ぶ<br>ボードゲーム</h1>" in html
    assert "ソロ用ルール" in html
    assert "PLAY SOLO" in html
    assert "/kyo-bodo-jp/diagnosis/?src=scene_page" in html
    assert html.count('<article class="game-card">') == len(eligible)
    for game in eligible:
        assert f'/kyo-bodo-jp/games/{game["game_id"]}/' in html
    item_list = html.split('<script type="application/ld+json">')[1].split('</script>')[0]
    schema = json.loads(item_list)
    assert schema["@type"] == "ItemList"
    assert len(schema["itemListElement"]) == len(eligible)
    listing = games_index()
    assert 'data-filter="solo"' in listing
    assert listing.count('data-solo="1"') == len(eligible)
    assert "c.dataset.solo" in listing


def test_solo_discovery_has_direct_home_entry_without_replacing_other_choices():
    eligible = [g for g in GAMES if supports_players(g, 1)]
    landing = home()
    assert len(eligible) == 14
    # Home now points to the real solo comparison without a two-click detour.
    assert landing.count('href="/kyo-bodo-jp/scenes/solo/"') == 1
    assert f"1人対応の全{len(eligible)}本を遊び方・時間から見比べる" in landing
    assert "ソロ用ルールは購入する版で確認してください" in landing
    assert "/kyo-bodo-jp/guides/two-player-cooperative/" in landing
    assert "/kyo-bodo-jp/scenes/two-player/" in landing
    assert "/kyo-bodo-jp/scenes/short/" in landing
    assert "/kyo-bodo-jp/scenes/children/" in landing
    assert "2人で遊ぶ予定なら" in landing
    # Existing scene directory and its solo link continue to be available.
    assert 'href="/kyo-bodo-jp/scenes/solo/"' in scenes_index()
    assert "人気No.1" not in landing
