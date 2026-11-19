"""Existing opt-in saved shelf can lead to two-item comparison without URL tracking."""
from pathlib import Path
from scripts import build_site as site

ROOT=Path(__file__).resolve().parents[1]

def test_saved_compare_has_generic_url_and_only_appears_after_two_saves():
    js=(ROOT/"assets/today.js").read_text(encoding="utf-8")
    assert 'found.length>=2' in js
    assert 'today-saved-compare' in js
    assert "B+'games/#savedCompare'" in js
    assert "最後に保存した2本を自動選択" in js
    assert "kyo_bodo_saved_games_v1" in js
    assert "saved.splice" in js # Existing reversible local shelf must remain.
    assert "encodeURIComponent(id)" in js # Individual saved detail links unchanged.
    assert "games/#savedCompare?" not in js
    assert "games/?compare" not in js

def test_existing_selection_only_read_when_shelf_fragment_requested():
    js=(ROOT/"assets/catalog-compare.js").read_text(encoding="utf-8")
    assert "window.location.hash==='#savedCompare'" in js
    assert "window.localStorage.getItem('kyo_bodo_saved_games_v1')" in js
    assert "Array.from(new Set(" in js
    assert "ids.slice(-2)" in js
    assert "games.has(id)" in js
    assert "比較対象は変更" not in js or "別の作品にも変更できます" in js
    assert "result.before(note)" in js
    assert "root.scrollIntoView({block:'start'})" in js
    assert "localStorage.setItem" not in js
    assert "sessionStorage" not in js
    assert "window.kyoTrack('catalog_compare_use',{compared_count:2})" in js
    assert "window.location.search" not in js
    assert "history.replaceState" not in js

def test_existing_catalog_and_home_remain_crawlable_without_js():
    assert len(site.GAMES)==88
    home=site.home()
    assert 'id="todaySavedGames"' in home
    catalog=site.games_index()
    assert 'id="catalogCompareFirst"' in catalog
    assert 'id="catalogCompareSecond"' in catalog
    assert catalog.count('class="catalog-card game-list-card"')==88
    assert 'assets/catalog-compare.js' in catalog
