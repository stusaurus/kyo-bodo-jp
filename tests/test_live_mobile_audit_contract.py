"""Protect the production browser audit from polluting real GA4 and route coverage regressions."""
from pathlib import Path
import re
import shutil
import subprocess
import textwrap

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/seo-live-mobile-audit.yml"

EXPECTED_PATHS = {
    "scenes/two-player/", "scenes/couple/", "scenes/children/", "scenes/short/", "scenes/solo/",
    "guides/two-player-cooperative/", "guides/gift-board-games/", "games/ito/", "games/mandala/",
    "games/quarto/", "games/nana-toridori/", "games/incan-gold-rediscovered/",
    "games/ciao-ciao/", "games/nmbr9/", "games/houseki-ippai/",
    "games/animal-old-maid/", "games/ding/", "games/eggsposed/",
    "scenes/family/", "scenes/large-group/",
}


def workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


def audit_js():
    source = workflow_text()
    match = re.search(r"node <<'AUDIT_NODE'\n(.*?)\n\s*AUDIT_NODE", source, flags=re.S)
    assert match, "Missing inline Playwright live audit script"
    return textwrap.dedent(match.group(1))


def test_existing_public_audit_covers_new_acquisition_and_purchase_pages():
    text = workflow_text()
    match = re.search(r'^\s*SEO_PATHS: "([^"]+)"\s*$', text, flags=re.M)
    assert match
    paths = match.group(1).split(",")
    assert len(paths) == len(set(paths)) == len(EXPECTED_PATHS)
    assert set(paths) == EXPECTED_PATHS
    assert "const paths=['',...process.env.SEO_PATHS.split(',')];" in text
    assert "for(const width of [320,390,1440])" in text
    assert "workflow_run:" in text and 'types: [completed]' in text
    assert "retention-days: 14" in text


def test_live_audit_blocks_ga4_transport_before_any_navigation():
    script = audit_js()
    route_pos = script.index("await context.route(")
    page_pos = script.index("const page=await context.newPage()")
    navigation_pos = script.index("await page.goto(url")
    assert route_pos < page_pos < navigation_pos
    assert "route.abort()" in script
    assert "blockedAnalyticsRequests++" in script
    assert "blockedAnalyticsRequests" in script.split("SEO_MOBILE_SUMMARY", 1)[1]
    # GA4 measurement protocol and tag-loader hosts must never reach Google.
    for hostname in (
        r"googletagmanager\.com", r"google-analytics\.com",
        r"analytics\.google\.com", r"stats\.g\.doubleclick\.net"
    ):
        assert hostname in script
    assert "route.continue()" not in script


def test_live_audit_fails_closed_on_wrong_catalog_or_advertising_classification():
    script = audit_js()
    assert "data.shortCount!==SHORT_COUNT" in script
    assert "require('./data/catalog_qa_baseline.json')" in script
    assert "actions/checkout@v4" in workflow_text()
    assert "20-minute comparison count ${data.shortCount} differs from reviewed ${SHORT_COUNT}" in script
    assert "solo comparison does not show 14 games" in script
    assert "data.coupleDecisionHeading" in script
    assert "data.coupleChoiceLinks.length!==expected.length" in script
    assert "scenes/couple/" in script
    assert "guides/gift-board-games/" in script
    assert "data.giftGroupCount!==3" in script
    assert "data.giftDetailLinks.length!==expected.length" in script
    assert "data.giftTableLinks.length!==expected.length" in script
    assert '.gift-age .gift-cards a[data-track=' in script
    assert '.gift-age .gift-table a[data-gift-detail][data-track=' in script
    assert "data.giftTableLinks.some((x,i)=>x.id!==expected[i]" in script
    assert "'dobble','nine-tiles','bandido'" in script
    assert "'harmonies','splendor-duel','the-crew-deep-sea'" in script
    assert "gift guide product choices or internal details are inconsistent" in script
    assert "new URL('games/'+expected[i]+'/',base).pathname" in script
    assert "'ito','codenames-duet','patchwork'" in script
    assert "data.soloCards!==14" in script
    assert "data.cooperativeRows!==15" in script
    assert "!data.childNine" in script
    assert "data.offer.affiliate==='rakuten'" in script
    assert "data.offer.track==='rakuten_search_click'" in script
    assert "data.offer.text.includes('通常検索へ移動します')" in script
    assert "data.offer.text.includes('PR：')" in script
    assert "issues.push('unclassified Rakuten outbound link')" in script
    assert "missing mobile product shortcut" in script
    assert "mobile shortcut differs from safe product panel" in script
    assert "mobile verified offer missing PR disclosure" in script
    assert "mobile search not clearly classified" in script
    assert "h.track!==o.track" in script
    assert "h.rel!==o.rel" in script
    assert "(show&&h.height<44)" in script
    assert "data.canonical!==url" in script
    assert "if(fatal.length)process.exitCode=1" in script


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is unavailable")
def test_inline_playwright_audit_script_parses_as_javascript():
    result = subprocess.run(["node", "--check", "-"], input=audit_js(),
                            text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
