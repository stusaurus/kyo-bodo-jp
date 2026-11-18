"""The Game second-edition preorder: recover a genuine Rakuten offer without misleading buyers."""
from pathlib import Path
import pytest

from data.catalog import GAMES
from scripts.fetch_rakuten import match_item, is_preorder_listing, query_variants
from test_site_presentation import m

GAME = next(g for g in GAMES if g["game_id"] == "the-game")
VALID_URL = "https://hb.afl.rakuten.co.jp/hgc/example"


@pytest.mark.parametrize("name", [
    "【送料無料】【2026年12月4日再販予約】ザ・ゲーム第2版　完全日本語版",
    "ザ・ゲーム 第2版 完全日本語版",
    "ザ・ゲーム 第二版 完全日本語版",
    "アークライト ザ・ゲーム第2版 完全日本語版 ボードゲーム",
])
def test_genuine_second_edition_matches_without_generic_context(name):
    ok, reason, score = match_item(GAME, {"itemName": name, "affiliateUrl": VALID_URL})
    assert ok, (name, reason)
    assert score >= 100
    assert "4542325312223" in query_variants(GAME)


@pytest.mark.parametrize("name", [
    "ザ・ゲーム クワンチャイ・モリヤ版 完全日本語版",
    "ザ・ゲーム 第2版 日本語版",
    "ザ・ゲーム 第2版 完全日本語版 エクストリーム",
    "ザ・ゲーム第2版 完全日本語版 スリーブ",
    "【中古】ザ・ゲーム第2版 完全日本語版",
    "ザ・ゲーム 第2版 完全日本語版 英語版",
    "EXIT 脱出：ザ・ゲーム 第2版 完全日本語版",
    "ザ・ゲーム 【電子書籍】",
])
def test_invalid_sibling_or_non_base_listing_stays_rejected(name):
    ok, reason, _ = match_item(GAME, {"itemName": name})
    assert not ok, (name, reason)


@pytest.mark.parametrize("title,expected", [
    ("【2026年12月4日再販予約】ザ・ゲーム第2版 完全日本語版", True),
    ("【予約受付中】ザ・ゲーム第2版 完全日本語版", True),
    ("【再販】ザ・ゲーム第2版 完全日本語版", False),
    ("【再生産】ザ・ゲーム第2版 完全日本語版", False),
    ("ザ・ゲーム 第2版 完全日本語版", False),
])
def test_preorder_flag_requires_explicit_reservation_word(title, expected):
    assert is_preorder_listing(title) is expected


def test_preorder_and_nonpreorder_labels_are_truthful(monkeypatch):
    # Fixture is a hypothetical verified Rakuten API offer, not a fabricated live sale.
    listing = {"url": VALID_URL, "image_url": "", "preorder": True}
    monkeypatch.setitem(m.RAKUTEN, GAME["game_id"], listing)
    page = m.game_page(GAME)
    card = m.card(GAME, "scene_page", 1)
    assert "楽天で予約状況を確認" in page
    assert "楽天で予約状況を確認" in card
    assert "予約表示があります" in page
    assert "受付状況・発送予定・キャンセル条件" in page
    assert 'data-affiliate="rakuten"' in page.split('class="btn rakuten large"',1)[1].split("</a>",1)[0]
    assert 'rel="sponsored noopener"' in page.split('class="btn rakuten large"',1)[1].split("</a>",1)[0]

    monkeypatch.setitem(m.RAKUTEN, GAME["game_id"], {"url": VALID_URL, "image_url": "", "preorder": False})
    fresh_page = m.game_page(GAME)
    assert "楽天で予約状況を確認" not in fresh_page
    assert "楽天で見る" in fresh_page
    assert "予約表示があります" not in fresh_page


def test_fallback_search_is_not_counted_as_affiliate(monkeypatch):
    monkeypatch.setitem(m.RAKUTEN, GAME["game_id"], {})
    page = m.game_page(GAME)
    button = page.split('class="btn rakuten large"',1)[1].split("</a>",1)[0]
    assert 'data-track="rakuten_search_click"' in button
    assert 'data-affiliate="rakuten"' not in button
    assert "楽天で探す" in button


def test_client_side_ctas_disclose_preorder():
    root = Path(__file__).resolve().parents[1]
    for asset in ["assets/diagnosis.js", "assets/today.js"]:
        text = (root / asset).read_text(encoding="utf-8")
        assert "preorder?'楽天で予約状況を確認'" in text
        assert "rakuten_search_click" in text
