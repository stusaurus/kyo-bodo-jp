(function(){
var root=document.getElementById("diagnosisApp");if(!root)return;var B=(window.KYO_BODO_CONFIG||{}).basePath||"/kyo-bodo-jp/";
var qs=[
["who","誰と遊ぶ？",[["couple","夫婦・カップル"],["family","家族"],["friends","友達"],["children","子ども"],["large","大人数"],["first","初対面がいる"]]],
["players","何人で遊ぶ？",[["2", "2人"], ["3", "3人"], ["4", "4人"], ["5", "5人"], ["6", "6人"], ["7", "7人"], ["8", "8人"], ["9", "9人"], ["10", "10人"], ["11", "11人"], ["12", "12人"], ["13", "13人"], ["14", "14人"]]],
["mood","どんな時間にしたい？",[["laugh","とにかく笑いたい"],["compete","真剣に勝負したい"],["think","頭を使いたい"],["coop","みんなで協力したい"],["relax","ゆるく遊びたい"],["chat","会話を楽しみたい"]]],
["time","どのくらい遊べる？",[["15","10〜15分"],["30","30分くらい"],["60","1時間くらい"],["120","じっくり"]]],
["difficulty","難しいルールは？",[["1","苦手"],["3","少しならOK"],["5","問題なし"]]],
["balance","運と実力なら？",[["luck","運多め"],["half","半々"],["skill","実力重視"]]]
],a={},i=0,games=[],links={};
var placeholder="<div class=\"game-placeholder\" aria-label=\"\u5546\u54c1\u753b\u50cf\u306f\u672a\u53d6\u5f97\"><svg class=\"placeholder-dice\" viewBox=\"0 0 80 80\" fill=\"none\" aria-hidden=\"true\"><rect x=\"15\" y=\"15\" width=\"50\" height=\"50\" rx=\"13\" stroke=\"currentColor\" stroke-width=\"2\"/><g fill=\"currentColor\"><circle cx=\"28\" cy=\"28\" r=\"3\"/><circle cx=\"52\" cy=\"28\" r=\"3\"/><circle cx=\"40\" cy=\"40\" r=\"3\"/><circle cx=\"28\" cy=\"52\" r=\"3\"/><circle cx=\"52\" cy=\"52\" r=\"3\"/></g></svg></div>";
var questionSub=["遊ぶ人の顔を思い浮かべて。","みんなで一緒に遊べる1本を。","今日ほしいのはどんな時間？","今ある時間に無理なく収まるものを。","ルール説明も、気軽に？じっくり？","最後は、好きな遊び方を。"];
function label(key,val){var q=qs.filter(function(x){return x[0]===key})[0],z=q&&q[2].filter(function(x){return x[0]===val})[0];return z?z[1]:val}
function score(g){
var n=Number(a.players||4);if(!(g.players_min<=n&&g.players_max>=n))return -9999;if(g.play_time_max>Number(a.time||30))return -9999;if(a.mood==="coop"&&!g.cooperative)return -9999;var s=60,w=a.who;
if(w==="couple")s+=g.couple*7;else if(w==="family")s+=g.family*7;else if(w==="friends")s+=(g.conversation+g.party+g.excitement)*3;else if(w==="children")s+=g.children*7;else if(w==="large")s+=(g.large_group+g.party)*5;else if(w==="first")s+=(g.beginner+g.conversation+g.party)*4;
var m=a.mood;if(m==="laugh")s+=(g.excitement+g.party+g.conversation)*4;else if(m==="compete")s+=(g.strategy+g.excitement)*5;else if(m==="think")s+=g.strategy*8;else if(m==="coop")s+=g.cooperation*9;else if(m==="relax")s+=g.beginner*5+(6-g.difficulty)*4;else if(m==="chat")s+=g.conversation*8;
var t=Number(a.time||30);if(t<=15)s+=Math.max(0,20-Math.max(0,g.play_time_min-15)*2);else if(t<=30)s+=Math.max(0,18-Math.abs(g.play_time_max-30)/3);else if(t<=60)s+=Math.max(0,16-Math.abs(g.play_time_max-60)/5);else s+=g.play_time_max>=45?18:5;
var d=Number(a.difficulty||3);s+=Math.max(0,18-Math.abs(g.difficulty-d)*6);
if(a.balance==="luck")s+=g.luck*5+(6-g.strategy)*2;else if(a.balance==="skill")s+=g.strategy*6+(6-g.luck)*2;else s+=12-Math.abs(g.strategy-g.luck)*3;return s}
function relaxedScore(g){
var n=Number(a.players||4);if(!(g.players_min<=n&&g.players_max>=n))return -9999;if(a.mood==="coop"&&!g.cooperative)return -9999;
var t=Number(a.time||30),over=g.play_time_max-t;if(over<=0)return score(g);
var allowance=t<=15?15:t<=30?15:t<=60?30:0;if(over>allowance)return -9999;
var old=a.time,s;a.time=String(Math.max(t,g.play_time_max));s=score(g);a.time=old;
return s-25-over*1.5}
function reasonParts(g){var p=[a.players+"人で遊べる",g.play_time_min+"〜"+g.play_time_max+"分"];
var field={couple:"couple",family:"family",children:"children",large:"large_group"}[a.who];if(field&&g[field]>=4)p.push(label("who",a.who)+"向き");
if(g.beginner>=4)p.push("初めてでも入りやすい");if(g.cooperation>=4)p.push("協力して遊べる");if(g.conversation>=4)p.push("会話を楽しめる");if(g.strategy>=4)p.push("じっくり考えられる");if(g.excitement>=4)p.push("盛り上がりやすい");return p.slice(0,5)}
function rak(g){var x=links[g.game_id]||{};return x.url||"https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/"}
function resultMarkup(g,k,isRelaxed){
  var lk=links[g.game_id]||{},image=lk.image_url?'<img class="result-image" src="'+window.kyoProductImage(lk.image_url)+'" alt="'+g.title+'の商品画像" decoding="async">':placeholder;
  kyoTrack("game_result_view",{game_id:g.game_id,rank:k+1,players:a.players,who:a.who,mood:a.mood});
  var detail='<a class="text-link" data-track="game_detail_click" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" href="'+B+'games/'+g.game_id+'/">1分ルールを見る <span aria-hidden="true">→</span></a>';
  var shop='<a class="'+(k===0?'btn rakuten':'text-link')+'" data-affiliate="rakuten" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+rak(g)+'">'+(lk.url?'楽天で商品を見る':'楽天で探す')+' <span aria-hidden="true">↗</span></a>';
  var relaxedNote=isRelaxed?'<div class="small" style="margin:0 0 8px;font-weight:700">時間を少し広げるなら</div>':'';
  return '<article class="result-card '+(k===0?'winner':'')+'"><div class="result-layout"><div class="result-media">'+image+'</div><div class="result-copy">'+relaxedNote+'<div class="rank">'+(k===0?'今日の第一候補':'0'+(k+1))+'</div><h3>'+g.title+'</h3><p class="result-appeal">'+g.appeal+'</p>'+'<p class="result-reasons">'+reasonParts(g).join(' ／ ')+'</p>'+'<div class="card-meta"><span>'+g.players_min+'〜'+g.players_max+'人</span><span>'+g.play_time_min+'〜'+g.play_time_max+'分</span><span>'+g.age+'歳〜</span></div><div class="card-actions">'+(k===0?shop+detail:detail+shop)+'</div>'+(k===0?'<p class="small" style="margin:12px 0 0">PR：販売ページで版・在庫をご確認ください。</p>':'')+'</div></div>'+(k===0?'<details class="result-rules"><summary>遊び方をここで見る</summary><ol class="howto">'+g.how_to_play.map(function(z){return '<li>'+z+'</li>'}).join('')+'</ol></details>':'')+'</article>';
}
function results(){
  var exact=games.map(function(g){return [g,score(g)]}).filter(function(x){return x[1]>-100}).sort(function(x,y){return y[1]-x[1]});
  var exactIds={};exact.forEach(function(x){exactIds[x[0].game_id]=true});
  var r=exact.slice(0,5).map(function(x){return [x[0],x[1],false]});
  if(r.length<5){
    var relaxed=games.map(function(g){return [g,relaxedScore(g)]}).filter(function(x){return !exactIds[x[0].game_id]&&x[1]>-100}).sort(function(x,y){return y[1]-x[1]}).slice(0,5-r.length);
    relaxed.forEach(function(x){r.push([x[0],x[1],true])});
  }
  var relaxedCount=r.filter(function(x){return x[2]}).length;
  kyoTrack("diagnosis_complete",{players:a.players,who:a.who,mood:a.mood,desired_time:a.time,difficulty:a.difficulty,balance:a.balance,exact_result_count:Math.min(exact.length,5),relaxed_result_count:relaxedCount,result_ids:r.map(function(x){return x[0].game_id}).join(",")});
  if(relaxedCount)kyoTrack("diagnosis_relaxed_results",{players:a.players,who:a.who,mood:a.mood,desired_time:a.time,exact_result_count:Math.min(exact.length,5),relaxed_result_count:relaxedCount});
  root.className='results-state';
  root.parentElement.classList.add('results-wrap');
  document.querySelector('.diagnosis-header').classList.add('has-results');
  document.querySelector('.diagnosis-heading').textContent='あなたたちの、今日の1本。';
  document.querySelector('.diagnosis-subtitle').textContent='今のメンバーに、今の気分に。';
  var intro=relaxedCount?'<div class="result-intro"><h2 class="sr-only" tabindex="-1">今日は、これで遊ぼう。</h2><p>まずは条件ぴったりの候補。足りない分だけ、遊ぶ時間を少し広げた候補も載せています。</p></div>':'<div class="result-intro"><h2 class="sr-only" tabindex="-1">今日は、これで遊ぼう。</h2><p>今日の条件に合う候補から選ぼう。</p></div>';
  root.innerHTML=intro+(r.length?resultMarkup(r[0][0],0,r[0][2]):'<p>人数・時間・協力の条件を満たす候補がありません。遊べる時間を延ばすなど、条件を変えてお試しください。</p>')+(r.length>1?'<h2 class="results-alternatives-title">こんな1本も、きっと楽しい。</h2><div class="result-alternatives">'+r.slice(1).map(function(x,k){return resultMarkup(x[0],k+1,x[2])}).join('')+'</div>':'')+'<div class="result-retry"><p>同じメンバーでも、気分が変われば遊びも変わる。</p><a class="btn secondary" href="'+B+'diagnosis/">条件を変えてもう一度</a></div>';
  root.querySelector('h2').focus({preventScroll:true});
  window.scrollTo({top:0,behavior:'instant'});
}
function render(){
  if(i>=qs.length){results();return}
  var q=qs[i],pct=Math.round(i/qs.length*100),scene=[1,4,2,5,3,6][i];
  root.className='diagnosis-state';root.setAttribute('aria-busy','false');
  root.innerHTML='<div class="question-status"><span class="eyebrow">JUST GO WITH YOUR FEELING</span><span class="step-counter">0'+(i+1)+' / 06</span></div><div class="progress" role="progressbar" aria-label="診断の進み具合" aria-valuemin="0" aria-valuemax="6" aria-valuenow="'+i+'"><b style="width:'+pct+'%"></b></div><div class="diagnosis-visual-shell"><div class="question-visual q'+(i+1)+'"><div class="scene-art s'+scene+'" aria-hidden="true"></div><div class="question-visual-label">一緒に遊ぶ時間を、思い浮かべて。</div></div><div class="question-panel"><h2 tabindex="-1">'+q[1]+'</h2><p class="small">'+questionSub[i]+'</p><div class="answers '+(q[0]==='players'?'player-answers':'')+'">'+q[2].map(function(o){return '<button class="answer" data-v="'+o[0]+'"><strong>'+o[1]+'</strong><span class="answer-arrow" aria-hidden="true">→</span></button>'}).join('')+'</div><p class="diag-tip">直感で選んでOK。タップして次へ進みます。</p>'+(i>0?'<button class="question-back">← ひとつ前の質問へ</button>':'')+'</div></div>';
  root.querySelector('h2').focus({preventScroll:true});
  root.querySelectorAll('.answer').forEach(function(b){b.onclick=function(){a[q[0]]=b.dataset.v;kyoTrack('diagnosis_answer',{question_id:q[0],answer_value:b.dataset.v,step:i+1});i++;render()}});
  var back=root.querySelector('.question-back');if(back)back.onclick=function(){i--;render()};
}

Promise.all([fetch(B+"data/games.json").then(function(r){return r.json()}),fetch(B+"data/rakuten.json").then(function(r){return r.json()}).catch(function(){return {}})]).then(function(x){games=x[0];links=x[1];kyoTrack("diagnosis_start",{conversion_source:new URLSearchParams(location.search).get("src")||"direct"});render()}).catch(function(){root.setAttribute("aria-busy","false");root.innerHTML='<p>診断を読み込めませんでした。ページを再読み込みするか、<a href="'+B+'scenes/">シーンから探す</a>をご利用ください。</p>'});
})();
