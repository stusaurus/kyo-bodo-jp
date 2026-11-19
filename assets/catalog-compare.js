/* Compare factual catalog metadata without invented prices, reviews or outgoing offers.
 * No personal selections are persisted or sent to GA4; only an anonymous use count.
 */
(function(){
  'use strict';
  var root=document.getElementById('catalogCompare');
  var first=document.getElementById('catalogCompareFirst');
  var second=document.getElementById('catalogCompareSecond');
  var result=document.getElementById('catalogCompareResult');
  if(!root||!first||!second||!result)return;
  var B=(window.KYO_BODO_CONFIG||{}).basePath||'/kyo-bodo-jp/';
  var games=new Map(),lastPair='';
  function node(tag,cls,txt){
    var el=document.createElement(tag);
    if(cls)el.className=cls;
    if(txt!==undefined)el.textContent=String(txt);
    return el;
  }
  function fact(list,label,value){
    var row=node('div','catalog-compare-fact');
    row.appendChild(node('dt','',label));
    row.appendChild(node('dd','',value));
    list.appendChild(row);
  }
  function range(min,max,unit){
    if(min==null||max==null)return '未確認';
    return min===max?String(min)+unit:String(min)+'〜'+String(max)+unit;
  }
  function players(g){
    if(g.players_label)return g.players_label;
    if(g.players_max==null)
      return g.players_open_ended===true&&g.players_source?g.players_min+'人以上':'人数未確認';
    return range(g.players_min,g.players_max,'人');
  }
  function renderCard(game){
    var article=node('article','catalog-compare-card');
    article.appendChild(node('h3','',game.title));
    var dl=node('dl','catalog-compare-facts');
    fact(dl,'人数',players(game));
    fact(dl,'プレイ時間',range(game.play_time_min,game.play_time_max,'分'));
    fact(dl,'対象年齢',game.age!=null?game.age+'歳〜':'未確認');
    fact(dl,'戦略性（独自目安）',game.strategy!=null?game.strategy+'/5':'未評価');
    fact(dl,'協力度（独自目安）',game.cooperation!=null?game.cooperation+'/5':'未評価');
    article.appendChild(dl);
    var rules=Array.isArray(game.how_to_play)?game.how_to_play:[];
    if(rules.length){
      article.appendChild(node('h4','','遊び方の流れ'));
      var list=node('ol','catalog-compare-rules');
      rules.slice(0,3).forEach(function(step){list.appendChild(node('li','',step))});
      article.appendChild(list);
    }
    var a=node('a','btn secondary','この作品の詳細を見る →');
    a.href=B+'games/'+encodeURIComponent(game.game_id)+'/';
    a.dataset.track='game_detail_click';
    a.dataset.gameId=game.game_id;
    a.dataset.source='catalog_compare';
    article.appendChild(a);
    return article;
  }
  function message(text){
    result.replaceChildren(node('p','small',text));
  }
  function render(){
    var id1=first.value,id2=second.value;
    if(!id1||!id2){
      lastPair='';
      message('比較したい2作品を選んでください。');
      return;
    }
    if(id1===id2){
      lastPair='';
      message('同じ作品が2つ選ばれています。別の作品を選んでください。');
      return;
    }
    var a=games.get(id1),b=games.get(id2);
    if(!a||!b){lastPair='';message('作品情報を確認できません。選び直してください。');return}
    var grid=node('div','catalog-compare-grid');
    grid.appendChild(renderCard(a));
    grid.appendChild(renderCard(b));
    result.replaceChildren(grid);
    var pair=[id1,id2].sort().join('|');
    if(pair!==lastPair&&typeof window.kyoTrack==='function'){
      window.kyoTrack('catalog_compare_use',{compared_count:2});
    }
    lastPair=pair;
  }
  fetch(B+'data/games.json',{credentials:'same-origin'})
    .then(function(response){if(!response.ok)throw Error('catalog unavailable');return response.json()})
    .then(function(data){
      if(!Array.isArray(data)||!data.length)throw Error('empty catalog');
      data.forEach(function(g){
        if(g&&typeof g.game_id==='string'&&typeof g.title==='string')games.set(g.game_id,g);
      });
      // Server-generated select options are the authoritative allowed IDs.
      Array.prototype.forEach.call(first.options,function(option){
        if(option.value&&!games.has(option.value))option.disabled=true;
      });
      Array.prototype.forEach.call(second.options,function(option){
        if(option.value&&!games.has(option.value))option.disabled=true;
      });
      root.hidden=false;
      first.addEventListener('change',render);
      second.addEventListener('change',render);
      render();
      // Only the explicit saved-shelf link triggers this read. Never put game
      // identifiers in the URL, or change the saved list from this page.
      if(window.location.hash==='#savedCompare'){
        var ids=[];
        try{
          var stored=JSON.parse(window.localStorage.getItem('kyo_bodo_saved_games_v1')||'[]');
          if(Array.isArray(stored)){
            ids=Array.from(new Set(stored.filter(function(id){
              return typeof id==='string'&&games.has(id);
            })));
          }
        }catch(_){}
        if(ids.length>=2){
          var chosen=ids.slice(-2);
          first.value=chosen[0];
          second.value=chosen[1];
          var note=node('p','small catalog-compare-loaded','保存した最後の2作品を選びました。別の作品にも変更できます。');
          result.before(note);
          render();
        }else{
          message('端末内の保存作品が2本未満です。比較したい2作品を選んでください。');
        }
        root.scrollIntoView({block:'start'});
      }
    })
    .catch(function(){
      root.hidden=false;
      first.disabled=true;
      second.disabled=true;
      message('比較データを読み込めませんでした。下の作品一覧から詳細をご覧ください。');
    });
})();