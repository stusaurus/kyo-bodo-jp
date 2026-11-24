import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import pytest
from scripts import indexnow_changes as m

def test_delta_includes_added_changed_deleted_and_excludes_unchanged():
    a,b,c,d = [m.BASE+x+"/" for x in "abcd"]
    assert m.changes({a:"1",b:"2",c:"3"}, {a:"1",b:"4",d:"5"}) == [b,c,d]
    assert m.changes({a:"1"}, {a:"1"}) == []

def test_manifest_contains_only_sitemap_pages(tmp_path):
    (tmp_path/"index.html").write_text("home")
    (tmp_path/"games").mkdir()
    (tmp_path/"games/index.html").write_text("games")
    (tmp_path/"404.html").write_text("error")
    (tmp_path/"sitemap.xml").write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+m.BASE+'</loc></url><url><loc>'+m.BASE+'games/</loc></url></urlset>')
    assert m.manifest_for(tmp_path) == {m.BASE:m.digest(b"home"), m.BASE+"games/":m.digest(b"games")}

@pytest.mark.parametrize("url", ["https://other.example/", "https://stusaurus.github.io/daily-cost-jp/", m.BASE+"../other/", m.BASE+"%2e%2e/other/",m.BASE+"?x=1"])
def test_reject_other_site_or_unsafe_url(url):
    with pytest.raises(ValueError):
        m.validate_url(url)

def test_initial_baseline_compares_live_content():
    a,b,c = [m.BASE+x+"/" for x in "abc"]
    def read(url):
        if url.endswith(m.MANIFEST):
            raise HTTPError(url,404,"missing",{},None)
        if url.endswith("sitemap.xml"):
            return ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+
                    ''.join('<url><loc>'+u+'</loc></url>' for u in (a,b))+'</urlset>').encode()
        assert url == a
        return b"unchanged"
    current = {a:m.digest(b"unchanged"),c:m.digest(b"new")}
    with patch.object(m,"read_public",side_effect=read):
        assert m.changes(m.previous_manifest(current),current) == [b,c]

def test_notify_no_changes_makes_no_submission(tmp_path):
    plan = tmp_path/"plan.json"
    plan.write_text(json.dumps({"manifest_sha256":m.digest(b"manifest"),"urls":[]}))
    with patch.object(m,"PLAN",plan), patch.object(m,"read_public",return_value=b"manifest"), patch.object(m,"urlopen") as send:
        m.notify()
        send.assert_not_called()

def test_notify_mismatched_deployment_is_rejected(tmp_path):
    plan = tmp_path/"plan.json"
    plan.write_text(json.dumps({"manifest_sha256":m.digest(b"expected"),"urls":[m.BASE]}))
    with patch.object(m,"PLAN",plan), patch.object(m,"read_public",return_value=b"wrong"), patch.object(m,"urlopen") as send:
        with pytest.raises(RuntimeError):
            m.notify()
        send.assert_not_called()
