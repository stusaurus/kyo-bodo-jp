"""Verified Rakuten purchase referrals must not be mixed with plain search exits."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from scripts import build_site as site

ROOT = Path(__file__).resolve().parents[1]


def test_static_purchase_and_search_links_are_distinct(monkeypatch):
    game = site.BY_ID["the-game"]
    monkeypatch.setattr(site, "RAKUTEN", {})
    card = site.card(game)
    detail = site.game_page(game)
    assert 'data-track="rakuten_search_click"' in card
    assert 'data-affiliate="rakuten"' not in card
    assert 'rel="noopener"' in card
    assert 'data-track="rakuten_search_click"' in detail
    assert 'data-affiliate="rakuten"' not in detail
    assert "楽天で探す" in detail
    assert "https://search.rakuten.co.jp/search/mall/" in detail

    monkeypatch.setattr(site, "RAKUTEN", {
        game["game_id"]: {
            "url": "https://hb.afl.rakuten.co.jp/hgc/example/",
            "item_url": "https://item.rakuten.co.jp/example/example/",
            "image_url": "",
        }
    })
    card = site.card(game)
    detail = site.game_page(game)
    assert 'data-affiliate="rakuten"' in card
    assert 'data-track="rakuten_search_click"' not in card
    assert 'rel="sponsored noopener"' in card
    assert 'data-affiliate="rakuten"' in detail
    assert 'data-track="rakuten_search_click"' in detail  # related games are unresolved
    assert "楽天で見る" in detail



@pytest.mark.parametrize("gid", [
    "take-it-easy", "mandala", "forbidden-island", "ice-cool",
    "resistance-avalon", "cascadia", "terraforming-mars", "sagrada",
])
def test_unverified_game_search_is_disclosed_without_false_ad_label(monkeypatch, gid):
    # No inventing affiliate URLs for the eight names without a safe Rakuten match.
    monkeypatch.setattr(site, "RAKUTEN", {})
    detail = site.game_page(site.BY_ID[gid])
    panel = detail.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    assert 'data-track="rakuten_search_click"' in panel
    assert 'data-affiliate="rakuten"' not in panel
    assert 'rel="noopener"' in panel
    assert 'rel="sponsored noopener"' not in panel
    assert "楽天で探す" in panel
    assert "楽天市場の通常検索へ移動します" in panel
    assert "掲載作品と一致する販売商品を確認できていません" in panel
    assert "別作品・拡張版・中古品" in panel
    assert "作品名・版・商品の状態・対象年齢" in panel
    assert "PR：" not in panel
    # Other cards may link to genuine offers. The site-wide disclosure remains.
    assert "当サイトはアフィリエイト広告を利用する場合があります" in detail


def test_verified_offer_disclosure_and_preorder_hold_without_product_image(monkeypatch):
    game = site.BY_ID["quarto"]
    monkeypatch.setattr(site, "RAKUTEN", {game["game_id"]: {
        "url": "https://hb.afl.rakuten.co.jp/hgc/example/",
        "item_url": "https://item.rakuten.co.jp/shop/example/",
        "image_url": "", "preorder": False
    }})
    detail = site.game_page(game)
    panel = detail.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    assert 'data-affiliate="rakuten"' in panel
    assert 'rel="sponsored noopener"' in panel
    assert "楽天の商品ページを取得済み" in panel
    assert "PR：購入前に販売ページで版・対象年齢・在庫を確認してください" in panel
    assert "検索結果には別作品・拡張版・中古品" not in panel
    assert "掲載作品と一致する販売商品を確認できていません" not in panel


def test_diagnosis_and_today_render_distinct_tracking_attributes():
    diagnosis = (ROOT / "assets/diagnosis.js").read_text(encoding="utf-8")
    today = (ROOT / "assets/today.js").read_text(encoding="utf-8")
    for source, product_guard in ((diagnosis, "lk.url"), (today, "l.url")):
        assert f"{product_guard}?'data-affiliate=" in source
        assert "'data-track=\"rakuten_search_click\"'" in source
        assert f"{product_guard}?'sponsored noopener':'noopener'" in source
        assert source.count('data-affiliate="rakuten"') == 1


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_browser_click_handler_keeps_search_out_of_affiliate_click():
    harness = r"""
const assert=require("node:assert/strict");
const vm=require("node:vm");
const source=JSON.parse(process.argv[1]);
const events=[];
let onClick=null;
const ctx={
 KYO_BODO_CONFIG:{gaMeasurementId:""},
 URLSearchParams,
 location:{search:"?test=1",pathname:"/kyo-bodo-jp/games/the-game/"},
 localStorage:{getItem:()=>null,setItem:()=>{},removeItem:()=>{}},
 sessionStorage:{getItem:()=>null,setItem:()=>{}},
 dataLayer:events,
 document:{
   addEventListener:(name,cb)=>{if(name==="click")onClick=cb;},
   createElement:()=>({}),head:{appendChild:()=>{}}
 }
};
ctx.window=ctx;
vm.runInNewContext(source,ctx,{timeout:1000});
assert.equal(typeof onClick,"function");
const click=(dataset,href)=>onClick({target:{closest:()=>({dataset,href})}});
click({track:"rakuten_search_click",gameId:"the-game",source:"game_detail"},"https://search.rakuten.co.jp/search/mall/the-game/");
let logged=events.filter(x=>x[0]==="event");
assert.equal(logged.length,1);
assert.equal(logged[0][1],"rakuten_search_click");
assert.equal(logged[0][2].operator_test,"1");
click({affiliate:"rakuten",gameId:"the-game",source:"game_detail"},"https://hb.afl.rakuten.co.jp/hgc/example/");
logged=events.filter(x=>x[0]==="event");
assert.equal(logged.length,2);
assert.equal(logged[1][1],"affiliate_click");
assert.equal(logged[1][2].operator_test,"1");
assert.equal(logged[1][2].conversion_source,"game_detail");
"""
    result = subprocess.run(
        ["node", "-e", harness, json.dumps(site.ANALYTICS)],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("gid,expected", [
    ("qwirkle", "クゥワークル 日本語版"),
    ("cascadia", "カスカディア 日本語版 ケンビル"),
    ("nmbr9", "ナンバーナイン NMBR9 ボードゲーム"),
])
def test_search_only_fallback_is_base_edition_specific_without_fake_affiliate(monkeypatch, gid, expected):
    from urllib.parse import quote
    monkeypatch.setattr(site, "RAKUTEN", {})
    game = site.BY_ID[gid]
    url, image, label = site.load_rakuten(game)
    assert url == "https://search.rakuten.co.jp/search/mall/" + quote(expected) + "/"
    assert not image
    assert label == "楽天で探す"
    detail = site.game_page(game)
    # Mobile top-of-page and normal panel must expose the identical safe search.
    assert detail.count('href="' + url + '"') >= 2
    panel = detail.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    assert 'data-track="rakuten_search_click"' in panel
    assert 'data-affiliate="rakuten"' not in panel
    assert 'rel="noopener"' in panel
    assert 'rel="sponsored noopener"' not in panel
    assert "掲載作品と一致する販売商品を確認できていません" in panel
    assert "検索結果には別作品・拡張版・中古品" in panel


def test_safe_search_hints_never_override_verified_rakuten_product(monkeypatch):
    game = site.BY_ID["qwirkle"]
    safe = "https://hb.afl.rakuten.co.jp/hgc/future-genuine-base/"
    monkeypatch.setattr(site, "RAKUTEN", {"qwirkle": {
        "url": safe,
        "item_url": "https://item.rakuten.co.jp/verifiedshop/base/",
        "image_url": "", "preorder": False,
    }})
    result_url, _, text = site.load_rakuten(game)
    assert result_url == safe
    assert text == "楽天で見る"
    assert site.outgoing_tracking(game) == ('data-affiliate="rakuten"', 'sponsored noopener')
    html = site.game_page(game)
    panel = html.split('<div class="product-panel">', 1)[1].split("</aside>", 1)[0]
    assert 'href="' + safe + '"' in panel
    assert 'data-affiliate="rakuten"' in panel
    assert "クゥワークル" not in panel


def test_unrelated_unverified_search_query_is_not_rewritten(monkeypatch):
    from urllib.parse import quote
    monkeypatch.setattr(site, "RAKUTEN", {})
    game = site.BY_ID["the-game"]
    url, _, label = site.load_rakuten(game)
    assert url == "https://search.rakuten.co.jp/search/mall/" + quote(game["rakuten_query"]) + "/"
    assert label == "楽天で探す"
