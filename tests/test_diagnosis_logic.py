import json, subprocess
from pathlib import Path
from data.catalog import GAMES
ROOT=Path(__file__).resolve().parents[1]

def test_all_diagnosis_conditions_respect_members_time_and_cooperation():
    js=(ROOT/'assets/diagnosis.js').read_text()
    logic=js[js.index('function ageFits('):js.index('\nfunction rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    let count=0;
    for(let n=2;n<=14;n++)for(let t of [15,30,60,120])for(let mood of ['laugh','compete','think','coop','relax','chat']){
      a={players:String(n),time:String(t),mood,who:'family',difficulty:'1',balance:'half'};
      for(let g of games)if(score(g)>-100){
        if(!supportsPlayers(g,n)||g.play_time_max>t||(mood==='coop'&&g.cooperation<4))throw Error(g.game_id);
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
    logic=js[js.index('function ageFits('):js.index('\nfunction rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    a={players:'2',time:'15',mood:'coop',who:'couple',difficulty:'1',balance:'half'};
    let exact=games.map(g=>[g,score(g)]).filter(x=>x[1]>-100).sort((x,y)=>y[1]-x[1]);
    let ids=new Set(exact.map(x=>x[0].game_id));
    let relaxed=games.map(g=>[g,relaxedScore(g)]).filter(x=>!ids.has(x[0].game_id)&&x[1]>-100).sort((x,y)=>y[1]-x[1]).slice(0,5-exact.length);
    let result=exact.slice(0,5).concat(relaxed);
    if(result.length!==5)throw Error('expected five results');
    for(let [g] of result){
      if(!(supportsPlayers(g,2)))throw Error('player constraint relaxed');
      if(!g.cooperative)throw Error('cooperation constraint relaxed');
    }
    console.log(result.map(x=>x[0].game_id).join(','));
    '''
    result=subprocess.run(['node','-e',program],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_competitive_group_results_exclude_cooperative_games_even_when_time_relaxed():
    js=(ROOT/'assets/diagnosis.js').read_text()
    logic=js[js.index('function ageFits('):js.index('\nfunction rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    for (let n=2;n<=14;n++) for (let t of [15,30,60,120]) {
      a={players:String(n),time:String(t),mood:'compete',who:'family',difficulty:'1',balance:'half'};
      for (let g of games) if ((score(g)>-100 || relaxedScore(g)>-100) && g.cooperative)
        throw Error('cooperative game in competitive results: '+g.game_id);
    }
    a={players:'4',time:'30',mood:'compete',who:'family',difficulty:'1',balance:'half'};
    let ranked=games.map(g=>[g,score(g)]).filter(x=>x[1]>-100).sort((x,y)=>y[1]-x[1]).slice(0,5);
    if(ranked.length!==5 || ranked.some(x=>x[0].cooperative))throw Error('reproduced family scenario');
    a={players:'1',time:'60',mood:'compete',who:'solo',difficulty:'1',balance:'half'};
    if (!games.some(g=>g.cooperative && score(g)>-100))throw Error('solo personal-record mode must remain available');
    '''
    result=subprocess.run(['node','-e',program],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_youngest_player_age_is_hard_condition_in_exact_and_relaxed_results():
    js=(ROOT/'assets/diagnosis.js').read_text()
    logic=js[js.index('function ageFits('):js.index('function rak(')]
    program='var games='+json.dumps(GAMES,ensure_ascii=False)+';var a={};function label(k,v){return v};'+logic+'''
    for(const who of ['family','children'])for(let age=4;age<=14;age++)for(const n of [2,4,6]){
      a={who,players:String(n),min_age:String(age),time:'15',mood:'compete',difficulty:'1',balance:'half'};
      for(const g of games)if(score(g)>-100||relaxedScore(g)>-100){
        if(g.age>age||!supportsPlayers(g,n)||g.cooperative)throw Error('underage/mismatch '+g.game_id);
      }
    }
    a={who:'children',players:'2',min_age:'5',time:'30',mood:'compete',difficulty:'1',balance:'half'};
    if(score(games.find(g=>g.game_id==='testplay-no'))>-100)throw Error('13+ recommended to five-year-old');
    if(score(games.find(g=>g.game_id==='gobblet-gobblers'))<=-100)throw Error('age eligible game rejected');
    a.min_age='skip';
    if(!ageFits(games.find(g=>g.game_id==='testplay-no')))throw Error('adult-only option broken');
    console.log('age hard gate verified');
    '''
    result=subprocess.run(['node','-e',program],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_child_age_question_is_conditional_and_not_sent_to_analytics():
    js=(ROOT/'assets/diagnosis.js').read_text()
    assert "a.who==='family'||a.who==='children'" in js
    assert "q[0]!=='min_age'" in js
    assert "delete a.min_age" in js
    assert "||!ageFits(g)" in js
    assert "掲載版の対象年齢" in js
    assert "年齢の条件は緩めず" in js
