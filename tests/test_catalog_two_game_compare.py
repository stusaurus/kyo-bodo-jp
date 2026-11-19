"""Two-game comparison exposes only factual catalog attributes and verified detail links."""
from pathlib import Path
from data.catalog import GAMES
from scripts import build_site as site

ROOT=Path(__file__).resolve().parents[1]

def test_compare_controls_keep_all_88_crawlable_product_links():
    html=site.games_index()
    assert len(GAMES)==88
    assert html.count('class="catalog-card game-list-card"')==88
    assert html.count('class="catalog-compare"')==1
    assert 'id="catalogCompareFirst"' in html
    assert 'id="catalogCompareSecond"' in html
    assert 'id="catalogCompareResult"' in html
    assert 'aria-live="polite"' in html
    assert 'assets/catalog-compare.js' in html
    assert html.count('<option value="">作品を選んでください</option>')==2
    for g in GAMES:
        opt=f'<option value="{site.e(g["game_id"])}">{site.e(g["title"])}</option>'
        assert html.count(opt)==2, g["game_id"]
        assert f'href="{site.u("games/"+g["game_id"]+"/")}"' in html
    assert f'<link rel="canonical" href="{site.canon("games/")}"' in html
    assert "人気順や販売価格の比較ではありません" in html
    assert "比較にはJavaScriptが必要" in html

def test_comparison_js_never_persists_or_transmits_selection():
    js=(ROOT/"assets/catalog-compare.js").read_text(encoding="utf-8")
    assert "catalog_compare_use" in js
    assert "compared_count:2" in js
    assert "window.kyoTrack('catalog_compare_use',{compared_count:2})" in js
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "sendBeacon" not in js
    assert "new Map()" in js
    assert "textContent" in js
    assert "innerHTML" not in js
    assert "data/games.json" in js
    assert "players_open_ended" in js
    assert "g.players_max==null" in js
    assert "game_detail_click" in js
    assert "catalog_compare" in js
    assert "rakuten" not in js.lower(), "comparisons must link to vetted product details, not unreviewed vendor offers"

def test_exported_comparison_values_match_real_catalog():
    by_id={g["game_id"]:g for g in GAMES}
    a,b=by_id["nana-toridori"],by_id["nmbr9"]
    assert (a["players_min"],a["players_max"],a["play_time_min"],a["play_time_max"],a["age"]) == (2,6,10,20,6)
    assert (b["players_min"],b["players_max"],b["play_time_min"],b["play_time_max"],b["age"]) == (1,4,20,20,8)
    assert len(a["how_to_play"])==len(b["how_to_play"])==3
    assert all(1<=g["strategy"]<=5 and 1<=g["cooperation"]<=5 for g in (a,b))
