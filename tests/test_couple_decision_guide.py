"""A focused couple discovery path without popularity or affiliate claims."""
import importlib.util
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_kyo_couple", ROOT / "scripts" / "build_site.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def scene(sid):
    return next(s for s in m.SCENES if s["scene_id"] == sid)


def test_couple_guide_has_three_real_two_player_choices():
    html = m.scene_page(scene("couple"))
    assert html.count('class="couple-choice-card"') == 3
    assert 'id="couple-choose-title"' in html
    assert 'aria-labelledby="couple-choose-title"' in html
    assert "カップル・夫婦で、今日はどう遊ぶ？" in html
    assert html.count('class="couple-choice-game-name"') == 3
    assert html.count("詳細・購入先を確認 →") == 3
    assert "コードネーム：デュエットの詳細を見る" not in html
    assert "人気順・実際の試遊評価ではありません" in html
    assert "購入する版の情報を確認" in html
    for gid in ("ito", "codenames-duet", "patchwork"):
        game = m.BY_ID[gid]
        assert m.supports_players(game, 2)
        href = m.u("games/" + gid + "/")
        assert (f'data-game-id="{gid}" data-source="couple_choice" href="{href}"'
                in html)
        assert m.e(game["title"]) in html
        assert m.e(m.player_label(game)) in html
        assert m.format_play_time(game) in html
        assert f'対象{game["age"]}歳〜' in html
        assert m.e(game["how_to_play"][1]) in html
    guide = html.split('id="couple-choose"', 1)[1].split("</section>", 1)[0]
    assert 'data-affiliate="rakuten"' not in guide
    assert 'data-track="game_detail_click"' in guide
    assert m.u("scenes/two-player/") in guide
    assert m.u("guides/two-player-cooperative/") in guide


def test_couple_snippet_answers_specific_query_without_claiming_reviews():
    html = m.scene_page(scene("couple"))
    title = unescape(re.search(r"<title>(.*?)</title>", html).group(1))
    desc = unescape(re.search(r'<meta name="description" content="(.*?)">', html).group(1))
    assert "カップル・夫婦" in title
    assert "2人用ボードゲーム" in title
    assert "会話・協力・対戦" in title
    assert "2人対応を確認した作品" in desc
    assert "人気No.1" not in html
    assert "実際に遊んだ" not in html
    assert html.count("<h1>") == 1
    assert m.canon("scenes/couple/") in html


def test_existing_two_player_page_links_to_couple_before_comparison():
    broad = m.scene_page(scene("two-player"))
    href = f'href="{m.u("scenes/couple/")}"'
    assert broad.count(href) >= 1
    assert "夫婦・カップルなら会話・協力・対戦から選ぶ" in broad
    assert broad.index("夫婦・カップルなら会話") < broad.index('id="two-player-comparison"')
    assert 'id="couple-choose"' not in broad


def test_non_couple_scenes_remain_unchanged_by_couple_section():
    for s in m.SCENES:
        if s["scene_id"] != "couple":
            assert 'id="couple-choose"' not in m.scene_page(s)
    assert len(m.GAMES) == 88
