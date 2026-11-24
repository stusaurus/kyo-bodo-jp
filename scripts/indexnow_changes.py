"""Compute IndexNow notifications before deployment; send only after deployment."""
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

BASE = "https://stusaurus.github.io/kyo-bodo-jp/"
HOST = "stusaurus.github.io"
MANIFEST = "indexnow-content-manifest.json"
PLAN = Path("indexnow-plan.json")
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_url(url):
    parts = urlsplit(url)
    if not url.startswith(BASE) or parts.query or parts.fragment:
        raise ValueError("URL outside site scope")
    relative = unquote(url[len(BASE):])
    if "\\" in relative or any(x in (".", "..") for x in relative.split("/")):
        raise ValueError("unsafe path")
    return relative

def sitemap_urls(data):
    root = ET.fromstring(data)
    if root.tag != NS + "urlset":
        raise ValueError("unexpected sitemap")
    urls = [node.text for node in root.findall(NS + "url/" + NS + "loc")]
    if not urls or len(urls) != len(set(urls)):
        raise ValueError("empty or duplicate sitemap")
    for url in urls:
        validate_url(url)
    return urls

def manifest_for(site):
    urls = sitemap_urls((site / "sitemap.xml").read_bytes())
    result = {}
    for url in urls:
        rel = validate_url(url)
        path = site / rel
        if not rel or rel.endswith("/"):
            path = path / "index.html"
        result[url] = digest(path.read_bytes())
    return result

def changes(previous, current):
    return sorted(url for url in previous.keys() | current.keys()
                  if previous.get(url) != current.get(url))

def read_public(url):
    with urlopen(Request(url, headers={"Cache-Control": "no-cache",
                                       "User-Agent": "kyo-bodo-indexnow/1.0"}), timeout=30) as r:
        return r.read()

def previous_manifest(current):
    try:
        previous = json.loads(read_public(BASE + MANIFEST))
    except HTTPError as exc:
        if exc.code != 404:
            raise
        # First deployment with a manifest: compare real live HTML, not guesses.
        from concurrent.futures import ThreadPoolExecutor
        urls = sitemap_urls(read_public(BASE + "sitemap.xml"))
        previous = {url: "removed" for url in urls if url not in current}
        common = [url for url in urls if url in current]
        with ThreadPoolExecutor(max_workers=4) as pool:
            previous.update(zip(common, pool.map(lambda u: digest(read_public(u)), common)))
        return previous
    if not isinstance(previous, dict) or not previous:
        raise ValueError("invalid previous manifest")
    for url, checksum in previous.items():
        validate_url(url)
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            raise ValueError("invalid checksum")
    return previous

def prepare():
    site = Path("site")
    current = manifest_for(site)
    previous = previous_manifest(current)
    manifest_bytes = (json.dumps(current, sort_keys=True) + "\n").encode()
    (site / MANIFEST).write_bytes(manifest_bytes)
    urls = changes(previous, current)
    PLAN.write_text(json.dumps({"manifest_sha256": digest(manifest_bytes),
                                "urls": urls}, indent=2), encoding="utf-8")
    print("IndexNow plan:", len(urls), "changed/added/deleted URLs;", len(current), "current pages")

def notify():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if digest(read_public(BASE + MANIFEST)) != plan["manifest_sha256"]:
        raise RuntimeError("published manifest does not match deployment")
    urls = plan["urls"]
    if len(urls) != len(set(urls)):
        raise ValueError("duplicate notification URLs")
    for url in urls:
        validate_url(url)
    if not urls:
        print("IndexNow: no changed URLs; notification skipped")
        return
    key = os.environ["INDEXNOW_KEY"]
    key_url = BASE + key + ".txt"
    if read_public(key_url).decode().strip() != key:
        raise RuntimeError("IndexNow key verification failed")
    for start in range(0, len(urls), 10000):
        batch = urls[start:start+10000]
        request = Request("https://api.indexnow.org/IndexNow",
                          data=json.dumps({"host": HOST, "key": key,
                                           "keyLocation": key_url, "urlList": batch}).encode(),
                          headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 202):
                raise RuntimeError("unexpected IndexNow response")
            print("IndexNow", response.status, "changed URLs", len(batch))

if __name__ == "__main__":
    import sys
    {"prepare": prepare, "notify": notify}[sys.argv[1]]()
