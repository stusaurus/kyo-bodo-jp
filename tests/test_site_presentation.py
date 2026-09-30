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

def test_diagnosis_result_presentation_is_decision_focused():
    assert "今日なら、この5本。" in m.DIAGNOSIS
    assert "まず見るならこれ" in m.CSS
    assert "1分ルールを見る" in m.DIAGNOSIS
    assert "image_url" in m.DIAGNOSIS

def test_game_detail_has_fit_and_caution_guidance():
    page=m.game_page(m.GAMES[0])
    assert "3秒で「今日向き？」を判断" in page
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
    assert "answerIcons" in m.DIAGNOSIS
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
    assert "170px" in m.CSS
