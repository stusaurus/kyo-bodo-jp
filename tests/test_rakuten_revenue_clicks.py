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
