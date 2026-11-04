/* Three factual choices, optional local memory, and a small saved-game shelf.
   Never imply limited stock, a guaranteed deal, or a personalised purchase verdict. */
(function () {
  "use strict";
  var MODES = {
    all: {label:"今日のおまかせ",note:"本日の候補。人気順位・価格順位ではありません。"},
    two: {label:"2人で",note:"公式の対象人数に2人を含むゲームだけを表示。"},
    family: {label:"家族で",note:"掲載カタログで家族向け評価が高いゲームから選出。"},
    short: {label:"30分以内",note:"掲載の目安プレイ時間が最大30分以内のゲームだけを表示。"}
  };
  var SAVE_KEY = "kyo_bodo_saved_games_v1";
  var MODE_KEY = "kyo_bodo_today_mode_v1";
  function num(n) { return Number(n) || 0; }
  function eligible(g,mode) {
    if (mode==="two") return num(g.players_min)<=2 &&
      (g.players_max==null ? g.players_open_ended===true && !!g.players_source : num(g.players_max)>=2);
    if (mode==="family") return num(g.family)>=4;
    if (mode==="short") return num(g.play_time_max)>0 && num(g.play_time_max)<=30;
    return true;
  }
  function score(g,mode,now) {
    var day=now.getDay(), m=now.getMonth()+1, s=0;
    if (day===5) s+=num(g.party)*4+num(g.excitement)*3+num(g.conversation)*2;
    else if(day===6) s+=num(g.strategy)*3+(num(g.play_time_max)>=30?10:0)+num(g.family)*2;
    else if(day===0) s+=num(g.family)*4+num(g.children)*2+num(g.cooperation)*2;
    else s+=num(g.short_play)*4+num(g.beginner)*2+num(g.couple)*2;
    if(m===12||m===1) s+=num(g.family)*2+num(g.large_group)*2+num(g.party)*2;
    if(m===7||m===8) s+=num(g.children)*3+num(g.family)*2;
    if(mode==="two") s+=num(g.couple)*5;
    if(mode==="family") s+=num(g.family)*5+num(g.beginner);
    if(mode==="short") s+=num(g.short_play)*5;
    return s;
  }
  function selectGames(games,mode,now) {
    mode=MODES[mode]?mode:"all";
    var seed=Number(String(now.getFullYear())+String(now.getMonth()+1).padStart(2,"0")+String(now.getDate()).padStart(2,"0"));
    var pool=games.filter(function(g){return eligible(g,mode)})
      .sort(function(a,b){return score(b,mode,now)-score(a,mode,now)||String(a.game_id).localeCompare(String(b.game_id))})
      .slice(0,12), picks=[];
    while(picks.length<3&&pool.length){
      var idx=(seed+picks.length*7)%pool.length, pick=pool.splice(idx,1)[0];
      picks.push(pick);
      var diverse=pool.filter(function(g){
        return !(num(g.strategy)>=4&&num(pick.strategy)>=4) &&
          !(num(g.cooperation)>=4&&num(pick.cooperation)>=4) &&
          !(num(g.party)>=4&&num(pick.party)>=4);
      });
      if(diverse.length>=3-picks.length) pool=diverse;
    }
    return picks;
  }
  function reason(g,mode,now) {
    if(mode==="two") return "2人対応・"+num(g.play_time_min)+"〜"+num(g.play_time_max)+"分";
    if(mode==="family") return "家族向けの掲載評価から";
    if(mode==="short") return "目安の最長プレイ時間 "+num(g.play_time_max)+"分";
    var day=now.getDay();
    if(day===5)return "金曜の夜に、盛り上がるタイプ";
    if(day===6)return "土曜に少しじっくり";
    if(day===0)return "日曜の家族時間に";
    if(num(g.short_play)>=4)return "平日の夜でも遊びやすいタイプ";
    return "今日の候補のひとつ";
  }
  function escapeText(s) {
    return String(s==null?"":s).replace(/[&<>"']/g,function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  if(typeof module!=="undefined" && module.exports) {
    module.exports={eligible:eligible,score:score,selectGames:selectGames,reason:reason};
  }
  if(typeof document==="undefined")return;
  var root=document.getElementById("todayGames");
  var controls=document.getElementById("todayChoiceControls");
  var savedRoot=document.getElementById("todaySavedGames");
  if(!root||!controls||!savedRoot)return;
  var B=(window.KYO_BODO_CONFIG||{}).basePath||"/kyo-bodo-jp/";
  var now=new Date(new Date().toLocaleString("en-US",{timeZone:"Asia/Tokyo"}));
  var placeholder='<div class="game-placeholder" aria-label="商品画像は未取得"><svg class="placeholder-dice" viewBox="0 0 80 80" fill="none" aria-hidden="true"><rect x="15" y="15" width="50" height="50" rx="13" stroke="currentColor" stroke-width="2"/><g fill="currentColor"><circle cx="28" cy="28" r="3"/><circle cx="52" cy="28" r="3"/><circle cx="40" cy="40" r="3"/><circle cx="28" cy="52" r="3"/><circle cx="52" cy="52" r="3"/></g></svg></div>';
  var games=[],byId={},links={},saved=[],mode="all",remember=false;
  function storageGet(key) {try{return localStorage.getItem(key)}catch(_){return null}}
  function storageSet(key,value) {try{localStorage.setItem(key,value)}catch(_){}}
  function storageRemove(key) {try{localStorage.removeItem(key)}catch(_){}}
  function track(name,data) {if(typeof window.kyoTrack==="function")window.kyoTrack(name,data)}
  function showControls() {
    controls.hidden=false;
    controls.innerHTML='<div class="today-choice-row" role="group" aria-label="おすすめを絞り込む">'+
      Object.keys(MODES).map(function(id){return '<button type="button" class="today-choice-button" data-today-mode="'+id+'" aria-pressed="'+(id===mode?'true':'false')+'">'+MODES[id].label+'</button>'}).join("")+
      '</div><div class="today-choice-foot"><span data-today-mode-note>'+MODES[mode].note+'</span>'+
      '<button type="button" class="today-remember" data-today-remember aria-pressed="'+remember+'">'+(remember?'この条件を記憶中・解除する':'この条件を次回も使う')+'</button></div>';
  }
  function renderSaved() {
    var found=saved.filter(function(id){return Object.prototype.hasOwnProperty.call(byId,id)});
    savedRoot.hidden=!found.length;
    savedRoot.innerHTML=!found.length?'':('<div class="today-saved-head"><h3>あとで比べる '+found.length+'本</h3><p>この端末内だけに保存。ゲームの紹介から購入先を確認できます。</p></div><div class="today-saved-links">'+
      found.map(function(id){return '<span class="today-saved-item"><a href="'+escapeText(B+'games/'+encodeURIComponent(id)+'/')+'">'+escapeText(byId[id].title)+'</a><button type="button" data-today-remove="'+escapeText(id)+'" aria-label="'+escapeText(byId[id].title)+'を保存から外す">×</button></span>'}).join("")+'</div>');
  }
  function render() {
    var selected=selectGames(games,mode,now);
    root.innerHTML=selected.length?'<div class="today-grid">'+selected.map(function(g,k){
      var l=links[g.game_id]||{};
      var search="https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/";
      var url=typeof l.url==="string"&&/^https:\/\//.test(l.url)?l.url:search;
      var imageUrl=l.image_url;
      if(imageUrl&&typeof window.kyoProductImage==="function")imageUrl=window.kyoProductImage(imageUrl);
      var art=imageUrl?'<img class="game-thumb" src="'+escapeText(imageUrl)+'" alt="'+escapeText(g.title)+'の商品画像" loading="lazy" decoding="async">':placeholder;
      var id=String(g.game_id),isSaved=saved.indexOf(id)>=0;
      return '<article class="today-pick '+(k===0?'featured':'')+'"><div class="game-media">'+art+'</div><div class="today-pick-body">'+
        (k===0?'<div class="eyebrow">まずは、この候補から</div>':'')+
        '<div class="today-reason">'+escapeText(reason(g,mode,now))+'</div><h3>'+escapeText(g.title)+'</h3><p>'+escapeText(g.appeal)+'</p>'+
        '<div class="card-meta"><span>'+escapeText(g.players_label)+'</span><span>'+num(g.play_time_min)+'〜'+num(g.play_time_max)+'分</span></div>'+
        '<div class="card-actions"><a class="'+(k===0?'btn primary':'text-link')+'" data-track="game_detail_click" data-game-id="'+escapeText(id)+'" data-source="today_'+mode+'" data-rank="'+(k+1)+'" href="'+escapeText(B+'games/'+encodeURIComponent(id)+'/')+'">特徴・遊び方を見る →</a>'+
        '<a class="text-link" data-affiliate="rakuten" data-game-id="'+escapeText(id)+'" data-source="today_'+mode+'" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+escapeText(url)+'">'+(l.url?'楽天で確認':'楽天で探す')+' ↗</a>'+
        '<button type="button" class="today-save-button" aria-pressed="'+isSaved+'" data-today-save="'+escapeText(id)+'">'+(isSaved?'保存済み ✓':'あとで比べる ＋')+'</button></div></div></article>';
    }).join("")+'</div>':'<p class="small">この条件に合う掲載ゲームがありません。<a href="'+escapeText(B+'games/')+'">ゲーム一覧から探す</a></p>';
    renderSaved();
    track("daily_recommendation_view",{game_ids:selected.map(function(g){return g.game_id}).join(","),view_mode:mode,result_count:selected.length,weekday:now.getDay(),month:now.getMonth()+1});
  }
  controls.addEventListener("click",function(e){
    var b=e.target.closest("button");
    if(!b)return;
    if(b.dataset.todayMode&&MODES[b.dataset.todayMode]){
      if(mode!==b.dataset.todayMode){
        mode=b.dataset.todayMode;
        if(remember)storageSet(MODE_KEY,mode);
        showControls();render();
        track("today_choice_change",{view_mode:mode});
      }
    }else if(b.hasAttribute("data-today-remember")){
      remember=!remember;
      if(remember)storageSet(MODE_KEY,mode);
      else storageRemove(MODE_KEY);
      showControls();
      track("today_choice_remember_toggle",{enabled:remember?"1":"0",view_mode:mode});
    }
  });
  root.addEventListener("click",function(e){
    var b=e.target.closest("button[data-today-save]");if(!b)return;
    var id=b.dataset.todaySave;
    if(!Object.prototype.hasOwnProperty.call(byId,id))return;
    var index=saved.indexOf(id);
    if(index>=0)saved.splice(index,1);
    else if(saved.length<12)saved.push(id);
    else return; // Never report saving when the local shelf is at capacity.
    storageSet(SAVE_KEY,JSON.stringify(saved));
    render();
    track("today_save_toggle",{game_id:id,saved:index<0?"1":"0",view_mode:mode});
  });
  savedRoot.addEventListener("click",function(e){
    var b=e.target.closest("button[data-today-remove]");if(!b)return;
    var id=b.dataset.todayRemove;
    saved=saved.filter(function(x){return x!==id});
    storageSet(SAVE_KEY,JSON.stringify(saved));render();
    track("today_save_toggle",{game_id:id,saved:"0",view_mode:mode});
  });
  Promise.all([
    fetch(B+"data/games.json").then(function(r){if(!r.ok)throw Error("games unavailable");return r.json()}),
    fetch(B+"data/rakuten.json").then(function(r){if(!r.ok)throw Error("links unavailable");return r.json()}).catch(function(){return {}})
  ]).then(function(values){
    if(!Array.isArray(values[0])||!values[0].length)throw Error("no games");
    games=values[0];
    games.forEach(function(g){if(g&&typeof g.game_id==="string")byId[g.game_id]=g});
    links=values[1]||{};
    try{var existing=JSON.parse(storageGet(SAVE_KEY)||"[]");if(Array.isArray(existing))saved=existing.filter(function(id){return typeof id==="string"&&Object.prototype.hasOwnProperty.call(byId,id)}).slice(0,12)}catch(_){}
    var previous=storageGet(MODE_KEY);if(MODES[previous]){mode=previous;remember=true}
    showControls();render();
  }).catch(function(){
    // Keep the original server-rendered three familiar games visible on fetch failure.
    controls.hidden=true;savedRoot.hidden=true;
    track("today_cards_fallback",{reason:"data_unavailable"});
  });
})();
