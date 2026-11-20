"""Whole-catalog preflight for game -> buying CTA and diagnosis eligibility.

These checks use the real static renderer / JS score and do not fabricate
Rakuten offers, prices, stock, purchases or verified human visitors.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess

from scripts import build_site as site

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))

    def by_class(self, *names):
        target = set(names)
        return [
            a for a in self.anchors
            if target.issubset(set(a.get("class", "").split()))
        ]


def test_all_88_game_detail_and_card_outbound_offers_match_the_same_source():
    assert len(site.GAMES) == 88
    assert len({g["game_id"] for g in site.GAMES}) == len(site.GAMES)
    for g in site.GAMES:
        gid = g["game_id"]
        url, image, label = site.load_rakuten(g)
        verified = bool(site.RAKUTEN.get(gid, {}).get("url"))
        page = Links()
        page.feed(site.game_page(g))
        hero = page.by_class("game-hero-purchase-link")
        panel = page.by_class("btn", "rakuten", "large")
        assert len(hero) == len(panel) == 1, gid
        card = Links()
        card.feed(site.card(g, source="all_game_audit"))
        cards = card.by_class("btn", "secondary")
        assert len(cards) == 1, gid
        expected_rel = "sponsored noopener" if verified else "noopener"
        for a in [hero[0], panel[0], cards[0]]:
            assert a["href"] == url, (gid, a.get("href"), url)
            assert a["rel"] == expected_rel, gid
            assert a["data-game-id"] == gid, gid
            if verified:
                assert a.get("data-affiliate") == "rakuten", gid
                assert a.get("data-track") is None, gid
            else:
                assert a.get("data-affiliate") is None, gid
                assert a.get("data-track") == "rakuten_search_click", gid
        assert label == ("楽天で探す" if not verified else label)
        assert site.canon("games/" + gid + "/") in site.game_page(g)


def test_all_88_games_respect_competitive_and_cooperative_choice_for_every_group():
    js = (ROOT / "assets" / "diagnosis.js").read_text(encoding="utf-8")
    logic = js[js.index("function score("):js.index("\nfunction rak(")]
    program = (
        "var games=" + json.dumps(site.GAMES, ensure_ascii=False) +
        ";var a={};function label(k,v){return v};" + logic + r"""
    const contexts=['couple','family','friends','children','large','first'];
    let tested=0;
    for(const who of contexts) for(let players=2;players<=14;players++)
      for(const time of [15,30,60,120]) for(const mood of ['compete','coop']){
        a={who,players:String(players),time:String(time),mood,difficulty:'1',balance:'half'};
        for(const g of games){
          const exact=score(g)>-100,relaxed=relaxedScore(g)>-100;
          if((exact||relaxed)&&!supportsPlayers(g,players))
            throw Error('wrong player count '+g.game_id);
          if((exact||relaxed)&&mood==='compete'&&g.cooperative)
            throw Error('cooperative game in group competition '+who+' '+g.game_id);
          if((exact||relaxed)&&mood==='coop'&&!g.cooperative)
            throw Error('non-cooperative game in cooperation '+who+' '+g.game_id);
          if(exact&&g.play_time_max>time)
            throw Error('exact result exceeds time '+g.game_id);
          tested++;
        }
      }
    if(tested!==contexts.length*13*4*2*games.length)
      throw Error('unexpected coverage count '+tested);
    console.log('GROUP_DX_ALL_GAMES checked='+tested);
    """
    )
    result = subprocess.run(
        ["node", "-e", program],
        capture_output=True, text=True, timeout=15, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "GROUP_DX_ALL_GAMES checked=" in result.stdout
