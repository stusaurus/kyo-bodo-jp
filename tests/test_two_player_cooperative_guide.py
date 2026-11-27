from data.catalog_qa_baseline import TWO_PLAYER_COOP_COUNT
"""A distinct indexable guide for 2-person cooperative board games, not a thin duplicate."""
import json
import re

from scripts import build_site as m


PATH = "guides/two-player-cooperative/"


def eligible():
    return [g for g in m.GAMES if m.supports_players(g, 2) and g["cooperative"]]


def test_guide_contains_all_factual_two_player_cooperative_games_once():
    games = eligible()
    assert len(games) == TWO_PLAYER_COOP_COUNT  # Reviewed catalog baseline.
    html = m.two_player_cooperative_guide()
    pattern = re.compile(r'<tr data-cooperative-game="([^"]+)">')
    expected = (
        [g["game_id"] for g in games if g["play_time_max"] <= 20]
        + [g["game_id"] for g in games if 20 < g["play_time_max"] <= 30]
        + [g["game_id"] for g in games if g["play_time_max"] > 30]
    )
    assert pattern.findall(html) == expected
    assert len(set(pattern.findall(html))) == len(games)
    assert "勝ち負けを競う代わりに" in html
    assert "人気順位・実際に遊んだ評価ではありません" in html
    assert "2人での遊び心地を保証" in html
    assert "購入する版の説明をご確認ください" in html
    assert "価格・在庫・販売版は変動" in html
    for g in games:
        assert f'data-game-id="{g["game_id"]}"' in html
        assert f'href="{m.u("games/" + g["game_id"] + "/")}"' in html
        assert m.player_label(g) in html
        assert f'{g["age"]}歳〜' in html
    for g in m.GAMES:
        if g not in games:
            assert f'<tr data-cooperative-game="{g["game_id"]}">' not in html


def test_time_groups_are_complete_exclusive_and_use_upper_bound():
    games = eligible()
    short = [g for g in games if g["play_time_max"] <= 20]
    medium = [g for g in games if 20 < g["play_time_max"] <= 30]
    long = [g for g in games if g["play_time_max"] > 30]
    assert short and medium and long
    assert len(short)+len(medium)+len(long) == len(games)
    html=m.two_player_cooperative_guide()
    for phrase,count in (("20分以内",len(short)),
                         ("21〜30分",len(medium)),
                         ("30分を超える",len(long))):
        assert phrase+f"（{count}本）" in html
    assert html.count("scene-data-table") == 3


def test_context_explanations_are_source_bounded_not_fabricated_rankings():
    html = m.two_player_cooperative_guide()
    pairs = {
        "sky-team":"ダイスを相談せず配置",
        "codenames-duet":"交互の一言ヒント",
        "the-mind":"相談せず数字カード",
        "bandido":"道カードをつなぎながら脱出口",
    }
    for gid, phrase in pairs.items():
        assert gid in {g["game_id"] for g in eligible()}
        assert phrase in html
        assert f'data-source="two_player_cooperative_examples"' in html
        assert f'data-game-id="{gid}"' in html
    exact_count=sum(g["players_min"] == g["players_max"] == 2 for g in eligible())
    assert f"2人だけの協力ゲームは<strong>{exact_count}本</strong>" in html


def test_indexable_unique_page_has_links_and_correct_structured_data():
    html = m.two_player_cooperative_guide()
    assert html.count("<h1>")==1
    assert m.canon(PATH) in html
    assert '<link rel="canonical" href="' + m.canon(PATH) + '"' in html
    assert "2人で協力するボードゲーム比較｜時間・会話・遊び方から選ぶ" in html
    script=re.search(r'<script type="application/ld\+json">(.*?)</script>', html)
    assert script
    data=json.loads(script.group(1))
    games=eligible()
    assert data["@type"]=="ItemList"
    assert len(data["itemListElement"])==len(games)
    assert [item["name"] for item in data["itemListElement"]]==[g["title"] for g in games]
    assert [item["url"] for item in data["itemListElement"]]==[
        m.canon("games/" + g["game_id"] + "/") for g in games]
    for link in ("scenes/two-player/","scenes/cooperative/",
                 "diagnosis/?src=two_player_cooperative_guide&preset=two-coop"):
        assert m.u(link) in html
    assert f'href="{m.u(PATH)}"' in m.home()
    two=m.scene_page(next(s for s in m.SCENES if s["scene_id"]=="two-player"))
    assert f'href="{m.u(PATH)}"' in two
    # Preserve the distinct older scene, not replace it with a thin duplicate.
    assert "2人専用と2人対応" in two or "2人だけ対応" in two
    assert "2人で遊ぶ、条件から3本を見つける" in two


def test_cooperative_flag_not_editorial_cooperation_score():
    games=eligible()
    assert all(g["cooperative"] for g in games)
    assert "coyote" not in {g["game_id"] for g in games}
    assert "cockroach-poker" not in {g["game_id"] for g in games}
    assert "haigyo" not in {g["game_id"] for g in games}
    assert "just-one" not in {g["game_id"] for g in games}  # 3+ only
    assert "sky-team" in {g["game_id"] for g in games}
