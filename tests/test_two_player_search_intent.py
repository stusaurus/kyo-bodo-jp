"""SEO intent matching for factual two-player distinctions, not invented popularity."""
import importlib.util
import re
from pathlib import Path
from html import unescape

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("build_kyo",ROOT/"scripts"/"build_site.py")
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

def test_two_player_title_description_and_h1_answer_observed_query():
    scene=next(x for x in m.SCENES if x["scene_id"]=="two-player")
    page=m.scene_page(scene)
    title=unescape(re.search(r"<title>(.*?)</title>",page).group(1))
    desc=unescape(re.search(r'<meta name="description" content="(.*?)">',page).group(1))
    h1=unescape(re.search(r"<h1>(.*?)</h1>",page).group(1))
    assert "2人用ボードゲーム" in title
    assert "2人専用と2人対応" in title
    assert "2人でできるボードゲーム" in desc
    assert "人気順位ではありません" in desc
    assert "2人用・2人でも遊べる" in h1
    assert page.count("<h1>")==1
    assert 'href="'+m.canon("scenes/two-player/")+'"' in page
    assert "掲載人数が2人だけ" in page
    assert "2人を含む複数人数に対応" in page
    assert "人気ランキングではありません" in page

def test_no_promises_of_all_game_popularity_or_changes_to_other_scenes():
    scene=next(x for x in m.SCENES if x["scene_id"]=="two-player")
    page=m.scene_page(scene)
    assert "人気No.1" not in page
    assert "日本一" not in page
    assert "購入数第1位" not in page
    for other in m.SCENES:
        if other["scene_id"]=="two-player":continue
        html=m.scene_page(other)
        assert "2人用・2人でも遊べる" not in html
        assert "<h1>"+m.e(other["title"])+"<br>ボードゲーム</h1>" in html
