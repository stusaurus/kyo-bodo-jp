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
