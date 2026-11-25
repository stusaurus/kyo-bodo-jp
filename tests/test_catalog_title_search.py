"""Catalog title search remains crawlable and does not transmit search terms."""
from pathlib import Path
from scripts import build_site as site
from data.catalog import GAMES

def test_all_titles_remain_static_and_indexable():
    markup=site.games_index()
    assert len(GAMES)==91
    assert markup.count('data-search-title=')==len(GAMES)
    assert markup.count('class="catalog-card game-list-card"')==len(GAMES)
    assert 'id="catalogTitleSearch"' in markup
    assert 'id="catalogSearchReset"' in markup
    assert 'id="catalogEmpty"' in markup
    assert 'aria-controls="gamesGrid"' in markup
    assert 'assets/catalog-search.js' in markup
    assert 'rel="canonical" href="'+site.canon("games/")+'"' in markup
    for gid in ('nana-toridori','catan','ito','nmbr9','houseki-ippai'):
        g=site.BY_ID[gid]
        assert f'data-search-title="{site.e(g["title"])}"' in markup
        assert f'href="{site.u("games/"+gid+"/")}"' in markup

def test_filter_and_search_query_stay_separate_from_analytics():
    js=(Path(site.ROOT)/"assets/catalog-search.js").read_text(encoding="utf-8")
    assert "game_filter_use" in js
    assert "search_query" not in js
    assert "search_term" not in js
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "kyoTrack('game_filter_use',{filter:active})" in js
    assert "field.addEventListener('input',render)" in js
    assert "eligible(c)&&normalize(c.dataset.searchTitle).includes(query)" in js
    assert "c.hidden=!show" in js
