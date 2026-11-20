"""The mobile conversion shortcut must preserve Rakuten verified/search boundaries."""
import re
from urllib.parse import urlsplit

from scripts import build_site as b


def hero_link(html):
    assert html.count('class="game-hero-purchase"') == 1
    region = html.split('class="game-hero-purchase"', 1)[1].split("</div>", 1)[0]
    matches = re.findall(r'<a\s+([^>]+)>', region)
    assert len(matches) == 1
    attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', matches[0]))
    return attrs, region


def panel_link(html):
    region = html.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', region.split('<a class="btn rakuten large"', 1)[1].split('>', 1)[0]))
    return attrs


def test_all_88_game_pages_have_one_safe_mobile_shortcut(monkeypatch):
    monkeypatch.setattr(b, "RAKUTEN", {})
    for g in b.GAMES:
        html = b.game_page(g)
        mobile, region = hero_link(html)
        panel = panel_link(html)
        assert mobile["class"] == "btn rakuten game-hero-purchase-link"
        assert mobile["href"] == panel["href"]
        assert mobile["target"] == "_blank"
        assert mobile["rel"] == panel["rel"] == "noopener"
        assert mobile["data-track"] == panel["data-track"] == "rakuten_search_click"
        assert "data-affiliate" not in mobile
        assert mobile["data-game-id"] == g["game_id"]
        assert mobile["data-source"] == "game_detail_hero"
        assert panel["data-source"] == "game_detail"
        assert urlsplit(mobile["href"]).netloc == "search.rakuten.co.jp"
        assert "楽天で探す" in region
        assert "別作品・拡張版・中古品" in region
        assert "PR：" not in region


def test_verified_link_reuses_actual_offer_without_search_fallback(monkeypatch):
    game = b.BY_ID["the-game"]
    url = "https://hb.afl.rakuten.co.jp/hgc/test-verified/"
    monkeypatch.setattr(b, "RAKUTEN", {game["game_id"]: {
        "url": url, "item_url": "https://item.rakuten.co.jp/shop/game/",
        "image_url": "", "preorder": False,
    }})
    html = b.game_page(game)
    mobile, region = hero_link(html)
    panel = panel_link(html)
    assert mobile["href"] == panel["href"] == url
    assert mobile["data-affiliate"] == panel["data-affiliate"] == "rakuten"
    assert "data-track" not in mobile
    assert "data-track" not in panel
    assert mobile["rel"] == panel["rel"] == "sponsored noopener"
    assert "楽天で見る" in region
    assert "PR：購入前に販売ページで版・対象年齢・在庫を確認してください" in region
    assert html.count('data-source="game_detail_hero"') == 1


def test_preorder_wording_and_disclosure_is_same_in_both_positions(monkeypatch):
    game = b.BY_ID["the-game"]
    monkeypatch.setattr(b, "RAKUTEN", {game["game_id"]: {
        "url": "https://hb.afl.rakuten.co.jp/hgc/preorder/",
        "item_url": "https://item.rakuten.co.jp/shop/game/",
        "image_url": "", "preorder": True,
    }})
    html = b.game_page(game)
    mobile, region = hero_link(html)
    panel = panel_link(html)
    assert mobile["href"] == panel["href"]
    assert "楽天で予約状況を確認" in region
    assert mobile["rel"] == "sponsored noopener"
    assert "PR：" in region
    assert "受付状況・発送予定・キャンセル条件" in html


def test_shortcut_is_not_desktop_duplicate_and_is_mobile_legible():
    css = b.CSS
    assert ".game-hero-purchase { display:none; }" in css
    mobile_start = css.index(".game-hero-purchase { display:flex;")
    assert css.rfind("@media(max-width:760px)", 0, mobile_start) != -1 or (
        css.rfind("@media (max-width:760px)", 0, mobile_start) != -1
    )
    assert ".game-hero-purchase .btn { width:100%; min-height:48px;" in css
    assert "game-hero-purchase p" in css


def test_mobile_shortcut_precedes_offers_panel_without_deleting_rules():
    html = b.game_page(b.BY_ID["dobble"])
    assert html.index('class="game-hero-purchase"') < html.index('class="game-hero-art"')
    assert html.index('class="game-hero-purchase"') < html.index('<div class="product-panel">')
    assert "1分で分かる遊び方" in html
    assert "診断で他の候補も見る" in html
