# scene-card implementation v2
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("build_site",ROOT/"scripts"/"build_site.py")
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

def test_home_has_clear_primary_flow():
    page=m.home()
    assert "今のメンバーで診断する" in page
    assert "選ぶ」時間を短くする" in page
    assert "2人で" in page
    assert "小学生と" in page
    assert "今日のおすすめ3本" in page
    assert f"{len(m.GAMES)}本のゲーム" in page
    assert "50本のゲーム" not in page
    assert "ボードゲーム診断とおすすめ" in page

def test_diagnosis_result_presentation_is_decision_focused():
    assert "今日の条件に合う候補から選ぼう。" in m.DIAGNOSIS
    assert "今日の第一候補" in m.DIAGNOSIS
    assert "1分ルールを見る" in m.DIAGNOSIS
    assert "image_url" in m.DIAGNOSIS

def test_game_detail_has_fit_and_caution_guidance():
    page=m.game_page(m.GAMES[0])
    assert g_description_present(page, m.GAMES[0])
    assert "こんな日に合う" in page
    assert "今日は別候補でも" in page
    assert "診断で他の候補も見る" in page

def test_games_index_has_mobile_friendly_filters():
    page=m.games_index()
    assert 'data-filter="two"' in page
    assert 'data-filter="family"' in page
    assert 'data-filter="short"' in page
    assert 'data-filter="beginner"' in page
    assert "game_filter_use" in page

def test_fit_tags_are_derived_for_every_game():
    for g in m.GAMES:
        tags=m.fit_tags(g)
        assert 1 <= len(tags) <= 3
        assert all(isinstance(x,str) and x for x in tags)


def test_home_uses_illustrated_hero_asset():
    page=m.home()
    assert "assets/hero-kyo-bodo.webp" in page
    assert "hero-visual" in page
    assert "登録不要" in page
    assert "1分ルールつき" in page
    assert m.HERO_ASSET.name=="hero-kyo-bodo.webp"


def test_home_has_illustrated_scene_cards():
    page=m.home()
    assert "scene-grid" in page
    assert "2人で" in page
    assert "家族で" in page
    assert "小学生と" in page
    assert "大人数で" in page
    assert "短時間で" in page
    assert "協力して" in page
    assert "SCENE_SPRITE_DATA" not in page
    assert "assets/scene-sprite.webp" in page
    assert m.SCENE_ASSET.name=="scene-sprite.webp"


def test_diagnosis_uses_visual_question_cards():
    page=m.diagnosis()
    assert "--scene-sprite:url(" in page
    assert "diagnosis-visual-shell" in m.CSS
    assert "question-visual q" in m.DIAGNOSIS
    assert 'role="progressbar"' in m.DIAGNOSIS
    assert "タップして次へ" in m.DIAGNOSIS

def test_home_has_six_visual_scene_cards():
    page=m.home()
    assert page.count('class="scene-card"') == 6
    for scene in ("two-player","family","children","large-group","short","cooperative"):
        assert f"scenes/{scene}/" in page


def test_today_recommendations_have_featured_layout():
    assert "today-grid" in m.CSS
    assert "今日のイチオシ" in m.TODAY
    assert "featured" in m.TODAY

def test_diagnosis_first_result_is_visually_prioritized():
    assert "今日の第一候補" in m.DIAGNOSIS
    assert ".result-card.winner" in m.CSS
    assert 'data-rank="' in m.DIAGNOSIS


def test_game_detail_uses_visual_hero():
    page=m.game_page(m.GAMES[0])
    assert "game-hero-card" in page
    assert "game-fast-facts" in page
    assert "game-hero-art" in page

def test_scene_pages_use_visual_hero():
    page=m.scene_page(m.SCENES[0])
    assert "scene-hero-card" in page
    assert "assets/scene-sprite.webp" in page
    assert "このシーンに合う" in page


def test_scene_selection_guide_uses_actual_catalog_and_related_existing_scenes():
    scene = next(x for x in m.SCENES if x["scene_id"] == "two-player")
    page = m.scene_page(scene)
    assert "掲載データから見比べる3本" in page
    assert "2人対応のゲームでも所要時間や会話量は異なります" in page
    assert m.u("scenes/couple/") in page
    assert m.u("scenes/short/") in page
    top = sorted(m.GAMES, key=lambda g: m.scene_score(g, scene), reverse=True)
    top = [g for g in top if m.scene_score(g, scene) >= 50][:3]
    for game in top:
        assert m.u("games/" + game["game_id"] + "/") in page


def test_scene_directory_uses_visual_tiles():
    page=m.scenes_index()
    for scene in m.SCENES:
        assert f'href="{m.u("scenes/" + scene["scene_id"] + "/")}"' in page
    assert page.count('class="scene-card"') == 6
    assert page.count('class="scene-directory-card"') == 8


def test_game_catalog_uses_visual_cards():
    page=m.games_index()
    assert 'class="games-catalog"' in page
    assert page.count('class="catalog-card game-list-card"') == len(m.GAMES)
    assert "catalog-media" in page
    assert "どんなゲーム？" in page


def g_description_present(page, game):
    return m.e(game["description"]) in page and all(m.e(step) in page for step in game["how_to_play"])


def test_all_game_details_keep_rules_and_attribution():
    for game in m.GAMES:
        page = m.game_page(game)
        assert g_description_present(page, game)
        assert f'data-game-id="{game["game_id"]}"' in page
        assert 'data-source="game_detail"' in page
        assert 'rel="sponsored noopener"' in page
        assert f'href="{m.canon("games/" + game["game_id"] + "/")}"' in page


def test_all_scene_pages_keep_ranked_links_and_structured_data():
    import json
    import re
    for scene in m.SCENES:
        page = m.scene_page(scene)
        schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page).group(1))
        assert schema["@type"] == "ItemList"
        for item in schema["itemListElement"]:
            gid = item["url"].rstrip("/").split("/")[-1]
            assert gid in m.BY_ID
            assert f'data-rank="{item["position"]}"' in page
            assert f'href="{m.u("games/" + gid + "/")}"' in page
        assert 'diagnosis/?src=scene_page' in page


def test_hero_and_scene_files_are_complete_high_resolution_webp():
    import struct
    for asset in (m.HERO_ASSET, m.SCENE_ASSET):
        blob = asset.read_bytes()
        assert blob[:4] == b"RIFF" and blob[8:12] == b"WEBP"
        assert struct.unpack_from("<I", blob, 4)[0] + 8 == len(blob), f"truncated asset: {asset.name}"
        marker = blob.index(b"\x9d\x01\x2a")
        width, height = struct.unpack_from("<HH", blob, marker + 3)
        assert width & 0x3FFF >= 1536
        assert height & 0x3FFF >= 1024
