"""Pure recommendation constraints and server-side no-JS fallback."""
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("build_site_today",ROOT/"scripts"/"build_site.py")
site=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)

def test_home_keeps_real_three_cards_without_javascript():
    page=site.home()
    assert page.index('id="today-games"')<page.index('id="scenes"')
    assert 'id="todayChoiceControls" hidden' in page
    assert 'id="todaySavedGames" hidden' in page
    assert 'id="todayGames"' in page
    for title in ("ito","catan","splendor"):
        assert site.BY_ID[title]["title"] in page
    assert page.count('href="#today-games"')>=1

def test_filter_math_enforces_eligible_games_and_keeps_distinct_cards():
    code=r"""
const assert=require('node:assert/strict');
const m=require('./assets/today.js');
const dt=new Date('2026-11-04T12:00:00');
const g=[
{game_id:'solo',players_min:3,players_max:5,play_time_min:20,play_time_max:45,family:4},
{game_id:'two-a',players_min:2,players_max:2,play_time_min:10,play_time_max:20,family:4},
{game_id:'two-b',players_min:2,players_max:4,play_time_min:20,play_time_max:60,family:1},
{game_id:'short',players_min:1,players_max:4,play_time_min:10,play_time_max:25,family:2},
{game_id:'unverified-open',players_min:2,players_max:null,players_open_ended:true,play_time_max:15},
{game_id:'open-evidenced',players_min:2,players_max:null,players_open_ended:true,players_source:'publisher',play_time_min:15,play_time_max:25}
];
assert.equal(m.eligible(g[0],'two'),false);
assert.equal(m.eligible(g[4],'two'),false);
assert.equal(m.eligible(g[5],'two'),true);
for(const mode of ['all','two','family','short']){
 const picks=m.selectGames(g,mode,dt);
 assert(picks.length>=1&&picks.length<=3,mode);
 assert.equal(new Set(picks.map(x=>x.game_id)).size,picks.length);
 assert(picks.every(x=>m.eligible(x,mode)),mode);
 assert.deepEqual(picks,m.selectGames(g,mode,dt),mode);
}
assert.equal(m.eligible(g[2],'short'),false);
assert.equal(m.eligible(g[0],'family'),true);
assert.match(m.reason(g[1],'short',dt),/20分/);
assert.deepEqual(m.selectGames([], 'two',dt),[]);
"""
    result=subprocess.run(["node","--check","assets/today.js"],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run(["node","-e",code],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr

def test_decision_insights_integration():
    page=site.home()
    assert 'decision-insights.js' in page
    assert page.index('decision-insights.js') < page.index('today.js')
    code=r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const engine=require('./assets/decision-insights.js');
const catalog={game_id:'sample',players_min:2,players_max:4,play_time_max:30,age:8};
assert.equal(engine.fit(catalog,{players:2,minutes:30,youngestAge:8}).status,'eligible');
assert.equal(engine.fit(catalog,{youngestAge:7}).status,'excluded');
assert.equal(engine.fit({...catalog,age:undefined},{youngestAge:8}).status,'unverified');
const source=fs.readFileSync('./assets/today.js','utf8');
assert(source.includes('window.KyoDecisionInsights'));
assert(source.includes('data-decision-insight'));
assert(source.includes('data-decision-change'));
assert(source.includes('previousChoice'));
assert.equal(engine.compare({players:2},{players:2},{game_id:'a'},{game_id:'b'})[0].type,'rank_change');
assert.equal(engine.compare({players:2},{players:2},{game_id:'a'},{game_id:'a'}).length,0);
"""
    result=subprocess.run(["node","-e",code],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run(["node","tests/test_decision_insights.cjs"],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
