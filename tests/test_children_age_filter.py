"""End-to-end facts for the youngest-child × party size × time comparison."""
import json
import re
from html.parser import HTMLParser

from scripts import build_site as m


class ChildRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag != "li":
            return
        values = dict(attrs)
        if "data-child-game" in values:
            self.rows.append(values)


def eligible():
    # The scene is intentionally bounded to 6–12 year-old age controls and
    # actual compatibility with at least one supported group size 2–6.
    return [
        g for g in m.GAMES if g["age"] <= 12
        and any(m.supports_players(g, n) for n in range(2, 7))
    ]


def test_age_filter_uses_all_real_catalog_entries_and_only_valid_metadata():
    html = m.children_age_filter()
    parser = ChildRows()
    parser.feed(html)
    expected = eligible()
    assert len(expected) > 12  # Different from the 12-card editorial shortlist.
    assert len(parser.rows) == len(expected)
    assert [r["data-child-game"] for r in parser.rows] == [g["game_id"] for g in expected]
    for row, g in zip(parser.rows, expected):
        assert int(row["data-child-age"]) == g["age"]
        assert int(row["data-child-minutes"]) == g["play_time_max"]
        supported = [int(n) for n in row["data-child-players"].split()]
        assert supported == [n for n in range(2, 7) if m.supports_players(g, n)]
        assert f'href="{m.u("games/" + g["game_id"] + "/")}"' in html
        assert f'data-game-id="{g["game_id"]}"' in html
        assert f'data-source="children_age_filter"' in html


def test_fallback_is_6_years_2_people_20_minutes_and_does_not_claim_ranking():
    html = m.children_age_filter()
    parser = ChildRows()
    parser.feed(html)
    default_ids = {
        g["game_id"] for g in eligible()
        if g["age"] <= 6 and m.supports_players(g, 2) and g["play_time_max"] <= 20
    }
    displayed_ids = {r["data-child-game"] for r in parser.rows if "hidden" not in r}
    assert default_ids and displayed_ids == default_ids
    assert f'id="children-choice-count">{len(default_ids)}本' in html
    assert 'id="children-choice-form"' in html
    assert 'id="children-choice-empty" hidden' in html
    assert '<noscript>' in html and "全作品から探す" in html
    assert "人気順や実際に遊んだ評価ではありません" in html
    assert "学年・理解度" in html and "ルール説明・準備" in html
    assert 'data-track="game_detail_click"' in html
    assert '<option value="6" selected>' in html
    assert '<option value="2" selected>' in html
    assert '<option value="20" selected>' in html


def test_all_age_counts_are_consistent_with_source_catalog():
    expected_counts = {
        age: sum(1 for g in eligible() if g["age"] <= age)
        for age in range(6, 13)
    }
    # Minimum known coverage from the 83-game baseline; expansions are allowed.
    assert expected_counts[6] >= 14
    assert expected_counts[8] >= 47
    assert expected_counts[6] < expected_counts[8] <= expected_counts[10] <= expected_counts[12]



def test_nine_year_age_option_is_available_without_assuming_grade_or_reviews():
    html = m.children_age_filter()
    options = re.findall(r'<option value="(\d+)"(?: selected)?>\d+歳</option>', html)
    assert options == [str(n) for n in range(6, 13)]
    assert html.count('<option value="9">9歳</option>') == 1
    age9 = [g for g in eligible() if g["age"] == 9]
    assert [g["game_id"] for g in age9] == ["scout", "insider-game"]
    for g in age9:
        assert f'href="{m.u("games/" + g["game_id"] + "/")}"' in html
        assert g["title"] in html
    # A four-player 20-minute selection at nine includes both newly eligible
    # games that an eight-year-old's age selection correctly excludes.
    def selected(age):
        return [g["game_id"] for g in eligible()
                if g["age"] <= age
                and m.supports_players(g, 4)
                and g["play_time_max"] <= 20]
    assert set(selected(9)) - set(selected(8)) == {"scout", "insider-game"}
    assert "小学校の学年や9歳の子に必ず合うという保証ではありません" in html
    assert "最年少の子どもの年齢を6〜12歳の1歳刻み" in html

def test_only_children_scene_changes_and_schema_remains_true():
    child = next(s for s in m.SCENES if s["scene_id"] == "children")
    html = m.scene_page(child)
    assert html.count('id="children-age-compare"') == 1
    assert "6〜12歳の子どもの年齢・人数・時間から候補を絞る" in html
    assert "6〜12歳・人数・時間で比較" in html
    assert "assets/children-filter.js" in html
    assert '<link rel="canonical" href="' + m.canon("scenes/children/") + '"' in html
    # Initial ItemList remains the published 12 representatives, not an invented ranking.
    ranked = m.scene_representatives(child)
    assert len(ranked) == 12
    schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
    assert len(schema["itemListElement"]) == len(ranked)
    assert [x["name"] for x in schema["itemListElement"]] == [g["title"] for g in ranked]
    for sid in ("two-player", "solo", "family", "short"):
        other = m.scene_page(next(s for s in m.SCENES if s["scene_id"] == sid))
        assert 'id="children-age-compare"' not in other
        assert "children-filter.js" not in other

def test_nine_year_quick_filter_uses_existing_controls_without_child_age_telemetry():
    from pathlib import Path
    html = m.children_age_filter()
    js = Path("assets/children-filter.js").read_text(encoding="utf-8")
    assert html.count('id="children-nine-quick" hidden') == 1
    assert "9歳・2人・30分以内の候補を表示" in html
    assert "nineQuick.hidden=false" in js
    for assignment in ("ages.value='9'", "players.value='2'", "times.value='30'"):
        assert assignment in js
    assert "track('nine_year_quick',render())" in js
    assert "child_age:" not in js and "age:ages.value" not in js
    matching = [g for g in eligible() if g["age"] <= 9
                and m.supports_players(g, 2) and g["play_time_max"] <= 30]
    assert matching
    assert 'id="children-choice-reset"' in html
    assert "ages.value='6'" in js and "players.value='2'" in js


def test_four_player_family_comparison_uses_exact_catalog_constraints():
    html = m.family_four_player_choices()
    expected = [g for g in m.GAMES if m.supports_players(g, 4)
                and g["play_time_max"] <= 30 and g["age"] <= 12]
    actual = re.findall(r'data-family-game="([^"]+)"', html)
    assert expected
    assert len(actual) == len(set(actual)) == len(expected)
    assert set(actual) == {g["game_id"] for g in expected}
    assert "gobblet-gobblers" not in actual
    for low, high in ((0, 5), (6, 7), (8, 9), (10, 12)):
        group = [g["game_id"] for g in expected if low <= g["age"] <= high]
        if group:
            assert any(re.findall(r'data-family-game="([^"]+)"', block) == group
                       for block in html.split("</details>"))
    for g in expected:
        assert f'href="{m.u("games/" + g["game_id"] + "/")}"' in html
        assert f'対象{g["age"]}歳〜' in html
    assert 'data-source="family_four_player"' in html
    assert "人気順・実遊評価ではありません" in html
    assert "<details open>" in html
    for scene in m.SCENES:
        page = m.scene_page(scene)
        assert ('id="family-four-player"' in page) == (scene["scene_id"] == "family")
        if scene["scene_id"] == "family":
            assert 'href="#family-four-player"' in page
            assert 'id="children-age-compare"' not in page
