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
