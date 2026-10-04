import json, subprocess
from pathlib import Path
from data.catalog import GAMES
ROOT=Path(__file__).resolve().parents[1]

def test_all_diagnosis_conditions_respect_members_time_and_cooperation():
    js=(ROOT/'assets/diagnosis.js').read_text()
    logic=js[js.index('function score('):js.index('\nfunction rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    let count=0;
    for(let n=2;n<=14;n++)for(let t of [15,30,60,120])for(let mood of ['laugh','compete','think','coop','relax','chat']){
      a={players:String(n),time:String(t),mood,who:'family',difficulty:'1',balance:'half'};
      for(let g of games)if(score(g)>-100){
        if(g.players_min>n||g.players_max<n||g.play_time_max>t||(mood==='coop'&&g.cooperation<4))throw Error(g.game_id);
        let reasons=reasonParts(g);
        if(reasons.includes('coop')||reasons.includes('family向き')&&g.family<4)throw Error('unsupported reason');count++;
      }
    }
    console.log(count+' eligible recommendations checked');
    '''
    result=subprocess.run(['node','-e',program],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_relaxed_results_keep_players_and_cooperation_hard_and_fill_common_short_case():
    js=(ROOT/'assets/diagnosis.js').read_text()
    logic=js[js.index('function score('):js.index('\nfunction rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    a={players:'2',time:'15',mood:'coop',who:'couple',difficulty:'1',balance:'half'};
    let exact=games.map(g=>[g,score(g)]).filter(x=>x[1]>-100).sort((x,y)=>y[1]-x[1]);
    let ids=new Set(exact.map(x=>x[0].game_id));
    let relaxed=games.map(g=>[g,relaxedScore(g)]).filter(x=>!ids.has(x[0].game_id)&&x[1]>-100).sort((x,y)=>y[1]-x[1]).slice(0,5-exact.length);
    let result=exact.slice(0,5).concat(relaxed);
    if(result.length!==5)throw Error('expected five results');
    for(let [g] of result){
      if(!(g.players_min<=2&&g.players_max>=2))throw Error('player constraint relaxed');
      if(!g.cooperative)throw Error('cooperation constraint relaxed');
    }
    console.log(result.map(x=>x[0].game_id).join(','));
    '''
    result=subprocess.run(['node','-e',program],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
