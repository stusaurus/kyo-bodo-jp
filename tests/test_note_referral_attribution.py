"""Campaign funnel instrumentation must not inflate revenue or collect extra identity."""
from scripts import build_site as m


def test_note_campaign_is_allowlisted_and_session_scoped():
    js = m.ANALYTICS
    assert 'note_campaign_landing' in js
    assert 'two_player_trial_20261118' in js
    assert 'p.get("utm_source")==="note"' in js
    assert 'p.get("utm_medium")==="referral"' in js
    assert 'p.get("utm_content")==="coop_guide"' in js
    assert 'sessionStorage.getItem(noteKey)' in js
    assert 'sessionStorage.setItem(noteKey' in js
    assert '30*60*1000' in js
    assert 'noteLandingNew' in js
    assert 'data.entry_channel="note_campaign"' in js
    assert 'data.entry_campaign=noteEntry.campaign' in js
    assert 'data.entry_content=noteEntry.content' in js
    assert 'data.operator_test=op?"1":"0"' in js


def test_existing_affiliate_vs_search_only_events_are_unchanged():
    js = m.ANALYTICS
    assert 'if(a.dataset.track)kyoTrack(a.dataset.track' in js
    assert 'if(a.dataset.affiliate)kyoTrack("affiliate_click"' in js
    assert '"rakuten_search_click"' not in js.split('if(a.dataset.affiliate)')[1], (
        "Search-only should continue through data-track, not affiliate_click"
    )
    for game_id in ("the-game", "lama", "take-it-easy"):
        game = m.BY_ID[game_id]
        page = m.game_page(game)
        # Related cards have their own offers: verify only this game's product CTA.
        cta = page.split('class="btn rakuten large"', 1)[1].split("</a>", 1)[0]
        assert 'data-track="rakuten_search_click"' in cta or 'data-affiliate="rakuten"' in cta
        assert not ('data-affiliate="rakuten"' in cta and 'data-track="rakuten_search_click"' in cta)


def test_campaign_tracking_does_not_collect_query_or_referrer():
    js=m.ANALYTICS
    tracked=js[js.index('var noteKey='):js.index('window.dataLayer=')]
    assert 'location.search' not in tracked
    assert 'document.referrer' not in tracked
    assert 'utm_term' not in tracked
    assert 'email' not in tracked
    assert 'landing_path:location.pathname' in tracked
