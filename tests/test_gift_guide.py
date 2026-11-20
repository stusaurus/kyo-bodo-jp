"""Gift discovery must use real catalog facts without fake sales or popularity."""
import importlib.util
import json
import re
from html import unescape
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_kyo_gift", ROOT / "scripts" / "build_site.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
from scripts.gift_guide import GIFT_GROUPS, gift_groups


def page():
    return m.render_gift_guide(m.BY_ID, m.supports_players, m.card, m.shell,
                               m.e, m.u, m.canon, m.player_label, m.format_play_time)


def test_gift_guide_contains_nine_distinct_age_and_player_qualified_games():
    selections = gift_groups(m.BY_ID, m.supports_players)
    assert [s["age"] for s, _ in selections] == [6, 8, 10]
    ids = [g["game_id"] for _, games in selections for g in games]
    assert len(ids) == len(set(ids)) == 9
    for group, games in selections:
        assert len(games) == 3
        for g in games:
            assert g["age"] <= group["age"]
            assert m.supports_players(g, 2)
            assert len(g["how_to_play"]) == 3
            assert g["play_time_min"] <= g["play_time_max"]
    assert len(m.GAMES) == 88


def test_gift_guide_has_factual_comparison_and_internal_purchase_safe_links():
    html = page()
    assert html.count('class="section gift-age"') == 3
    assert html.count('data-gift-detail="') == 9
    assert html.count('data-gift-detail="') == 9
    assert html.count('data-track="game_detail_click"') >= 18
    assert html.count('data-source="gift_guide"') >= 9
    assert 'role="region"' in html
    assert html.count("表は横にスクロールして、対象年齢・遊び方の一手まで確認できます。") == 3
    assert "人気ランキング・実際に遊んだ体験談・売れ筋順位ではありません" in html
    assert "価格・送料・在庫・到着予定日" in html
    assert "アフィリエイト広告が含まれる場合があります" in html
    for group, games in gift_groups(m.BY_ID, m.supports_players):
        age = group["age"]
        assert f'id="age-{age}"' in html
        assert f'id="gift-age-{age}"' in html
        for g in games:
            assert f'data-gift-detail="{g["game_id"]}" href="{m.u("games/" + g["game_id"] + "/")}"' in html
            assert f'data-game-id="{g["game_id"]}" data-source="gift_guide"' in html
            assert m.e(g["title"]) in html
            assert m.format_play_time(g) in html
            assert f'{g["age"]}歳〜' in html
            assert m.e(g["how_to_play"][1]) in html
    assert "販売店で最終確認" in html


def test_gift_guide_canonical_and_schema_avoid_fake_ranking():
    html = page()
    title = unescape(re.search(r"<title>(.*?)</title>", html).group(1))
    desc = unescape(re.search(r'<meta name="description" content="(.*?)">', html).group(1))
    assert "プレゼント" in title and "年齢" in title
    assert "クリスマス" in desc and "誕生日" in desc
    assert html.count("<h1>") == 1
    assert m.canon("guides/gift-board-games/") in html
    schemas = [json.loads(x) for x in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S)]
    item = next(x for x in schemas if x.get("@type") == "ItemList")
    elements = item["itemListElement"]
    assert len(elements) == 9
    assert [x["position"] for x in elements] == list(range(1, 10))
    assert len({x["url"] for x in elements}) == 9
    assert all(x["url"].startswith(m.canon("games/")) for x in elements)
    assert '"aggregateRating"' not in html
    assert '"offers"' not in html


def test_gift_guide_is_discoverable_from_home_children_family():
    target = m.u("guides/gift-board-games/")
    assert target in m.home()
    for sid in ("children", "family"):
        scene = next(s for s in m.SCENES if s["scene_id"] == sid)
        assert target in m.scene_page(scene)
    assert m.u("scenes/children/") in page()
    assert m.u("scenes/solo/") in page()


def test_invalid_edition_specs_fail_closed_before_publication():
    by_id = {k: dict(v) for k, v in m.BY_ID.items()}
    by_id["nine-tiles"]["age"] = 12
    with pytest.raises(ValueError, match="Ineligible gift choice"):
        gift_groups(by_id, m.supports_players)


def test_nine_gift_detail_pages_return_to_existing_age_based_comparison():
    target = m.u("guides/gift-board-games/")
    gift_ids = {gid for group in GIFT_GROUPS for gid in group["ids"]}
    assert len(gift_ids) == 9
    for gid in gift_ids:
        html = m.game_page(m.BY_ID[gid])
        panel = html.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
        assert panel.count('data-source="game_detail_gift"') == 1, gid
        assert panel.count('href="' + target + '"') == 1, gid
        assert 'data-track="guide_entry"' in panel, gid
        assert '年齢・人数から9作品を比較する' in panel, gid
        assert '人気ランキング' not in panel, gid
        # The return link is ordinary site navigation, not a verified product.
        gift_link = panel.split('data-source="game_detail_gift"', 1)[1]
        gift_link = gift_link.split("</a>", 1)[0]
        assert 'data-affiliate=' not in gift_link, gid
        assert 'target="_blank"' not in gift_link, gid
    assert all(gid in m.BY_ID for gid in gift_ids)


def test_non_gift_game_detail_pages_have_no_unrelated_gift_call_to_action():
    gift_ids = {gid for group in GIFT_GROUPS for gid in group["ids"]}
    non_gift = [g for g in m.GAMES if g["game_id"] not in gift_ids]
    assert len(non_gift) == len(m.GAMES) - 9
    for game in non_gift:
        html = m.game_page(game)
        assert 'data-source="game_detail_gift"' not in html, game["game_id"]
        assert 'class="small gift-recompare"' not in html, game["game_id"]


def test_gift_detail_recomparison_does_not_change_offer_identity(monkeypatch):
    game = m.BY_ID["dobble"]
    product_url = "https://hb.afl.rakuten.co.jp/hgc/test-gift/"
    monkeypatch.setattr(m, "RAKUTEN", {"dobble": {
        "url": product_url,
        "item_url": "https://item.rakuten.co.jp/shop/real/",
        "image_url": "", "preorder": False,
    }})
    html = m.game_page(game)
    panel = html.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    assert 'href="' + product_url + '"' in panel
    assert panel.count('data-affiliate="rakuten"') == 1
    assert 'rel="sponsored noopener"' in panel
    assert panel.count('data-source="game_detail_gift"') == 1
    assert 'href="' + m.u("guides/gift-board-games/") + '"' in panel
