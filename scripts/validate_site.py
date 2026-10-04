#!/usr/bin/env python3
"""Fail deployment on broken generated discovery files or internal navigation."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json, xml.etree.ElementTree as ET, sys
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site';BASE='/kyo-bodo-jp/';ORIGIN='https://stusaurus.github.io'
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES
class Page(HTMLParser):
    def __init__(self): super().__init__();self.links=[];self.canonical=[];self.h1=0;self.schemas=[];self.schema=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if tag=='script' and a.get('type')=='application/ld+json':self.schema=True
    def handle_data(self,data):
        if self.schema: self.schemas.append(json.loads(data))
    def handle_endtag(self,tag):
        if tag=='script':self.schema=False
urls=set()
for path in SITE.rglob('*.html'):
    rel=path.relative_to(SITE).as_posix()
    if rel.startswith('google'):continue
    p=Page();p.feed(path.read_text());assert p.h1==1,(rel,'H1')
    expected=ORIGIN+BASE+(rel[:-10] if rel.endswith('index.html') else rel)
    if rel=='404.html':continue
    assert p.canonical==[expected],(rel,p.canonical,expected);urls.add(expected)
    for link in p.links:
        dest=urlparse(link)
        if not dest.path.startswith(BASE) or dest.netloc not in ('','stusaurus.github.io'):continue
        target=SITE/unquote(dest.path[len(BASE):])
        if target.is_dir():target=target/'index.html'
        assert target.exists(),(rel,link)
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
listed={x.text for x in ET.parse(SITE/'sitemap.xml').findall('s:url/s:loc',ns)}
assert urls==listed,(urls-listed,listed-urls)
assert 'Sitemap: '+ORIGIN+BASE+'sitemap.xml' in (SITE/'robots.txt').read_text()
games_data=json.loads((SITE/'data/games.json').read_text())
assert len(games_data)==len(GAMES),(len(games_data),len(GAMES))
print(f'Validated {len(urls)} pages: internal links, H1, canonical, JSON-LD, sitemap, robots and {len(GAMES)} games')
