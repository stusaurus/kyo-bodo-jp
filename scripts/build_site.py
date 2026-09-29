#!/usr/bin/env python3
import html, json, os, shutil, urllib.parse, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES
SITE=ROOT/"site"
BASE=os.environ.get("SITE_BASE_PATH","/kyo-bodo-jp/")
if not BASE.startswith("/"): BASE="/"+BASE
if not BASE.endswith("/"): BASE+="/"
ORIGIN=os.environ.get("SITE_ORIGIN","https://stusaurus.github.io").rstrip("/")
GA=os.environ.get("GA_MEASUREMENT_ID","").strip()
SITE_URL=ORIGIN+BASE
SCENES=json.loads((ROOT/"data/scenes.json").read_text(encoding="utf-8"))
CACHE_PATH=ROOT/"data/rakuten_cache.json"
RAKUTEN=json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
BY_ID={g["game_id"]:g for g in GAMES}

def e(x): return html.escape(str(x),quote=True)
def u(p=""): return BASE+p.lstrip("/")
def canon(p=""): return SITE_URL+p.lstrip("/")

CSS="""
:root{--ink:#172033;--muted:#667085;--paper:#fffdf8;--card:#fff;--navy:#233046;--orange:#f26b4a;--blue:#4967d9;--line:#e7e2d9;--soft:#f4f1ea;--shadow:0 12px 32px rgba(26,33,52,.08)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",Meiryo,sans-serif;line-height:1.65}a{color:inherit}.site-header{position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;align-items:center;padding:12px 18px;background:rgba(255,253,248,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}.brand{display:flex;gap:8px;align-items:center;text-decoration:none;font-weight:900;font-size:19px}.brand b{color:var(--orange)}nav{display:flex;gap:12px}nav a{text-decoration:none;font-size:13px;font-weight:800}.hero,.page-hero,.section{max-width:1040px;margin:auto;padding-left:20px;padding-right:20px}.hero{padding-top:56px;padding-bottom:30px}.page-hero{padding-top:38px;padding-bottom:15px}.hero h1{font-size:clamp(46px,12vw,88px);line-height:.95;letter-spacing:-.055em;margin:8px 0 18px}.hero h1 span{display:block;color:var(--orange);font-size:.34em;letter-spacing:.02em;margin-bottom:9px}.hero p,.page-hero p{max-width:700px;color:#3e485c}.page-hero h1{font-size:clamp(34px,8vw,56px);line-height:1.05;margin:8px 0}.eyebrow{font-size:12px;font-weight:900;letter-spacing:.09em;color:var(--blue)}.section{padding-top:28px;padding-bottom:28px}.section h2{font-size:28px;margin:0 0 5px}.section-sub,.small{color:var(--muted);font-size:13px}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:10px 16px;border-radius:13px;text-decoration:none;font-weight:900;border:1px solid transparent;cursor:pointer;font:inherit}.primary{background:var(--navy);color:white}.secondary{background:white;border-color:var(--line)}.rakuten{background:#bf0000;color:white}.large{min-height:54px;padding:13px 22px;font-size:17px}.hero-actions,.card-actions,.chips{display:flex;gap:10px;flex-wrap:wrap}.trust-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:28px}.trust,.panel,.game-card{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}.trust{padding:14px}.trust strong{display:block}.today-box{background:var(--navy);color:white;border-radius:24px;padding:22px}.today-box .small,.today-box .section-sub{color:#d4d8e3}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.game-card{overflow:hidden}.game-card-body{padding:16px}.game-card h3{font-size:21px;margin:3px 0}.game-card .appeal{margin:5px 0 10px}.game-placeholder{height:135px;display:grid;place-items:center;background:linear-gradient(135deg,#f7e0d8,#e7ecff);font-size:42px}.game-thumb{width:100%;height:150px;object-fit:contain;background:#fff}.chip{display:inline-flex;padding:9px 12px;border-radius:999px;border:1px solid var(--line);background:#fff;text-decoration:none;font-size:13px;font-weight:800}.all-games{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}.all-games a{background:white;border:1px solid var(--line);border-radius:14px;padding:12px;text-decoration:none}.diagnosis-wrap{max-width:720px;margin:auto;padding:15px 20px 50px}.progress{height:7px;background:#e9e6df;border-radius:999px;overflow:hidden;margin:10px 0 24px}.progress b{display:block;height:100%;background:var(--orange)}.question h2{font-size:28px}.answers{display:grid;gap:10px}.answer{width:100%;padding:15px;text-align:left;border:1px solid var(--line);border-radius:14px;background:white;font-size:16px;font-weight:800}.result-card{background:white;border:1px solid var(--line);border-radius:18px;padding:18px;margin:12px 0;box-shadow:var(--shadow)}.rank{font-size:12px;font-weight:900;color:var(--orange)}.howto{padding-left:22px}.detail-layout{display:grid;grid-template-columns:1.7fr 1fr;gap:18px}.panel{padding:18px}.specs{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.spec{background:var(--soft);border-radius:12px;padding:10px}.spec b{display:block;font-size:12px;color:var(--muted)}.axis{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:8px 0}.dots{letter-spacing:2px}.breadcrumb{font-size:12px;color:var(--muted)}footer{margin-top:35px;background:#172033;color:white;padding:28px 20px}footer>div,footer>p{max-width:1040px;margin:8px auto}@media(max-width:760px){nav a:nth-child(3){display:none}.grid{grid-template-columns:1fr}.trust-row{grid-template-columns:1fr}.all-games{grid-template-columns:1fr}.detail-layout{grid-template-columns:1fr}.hero{padding-top:38px}.card-actions .btn{flex:1}.today-box{padding:16px}}
"""

CSS += """
.hero-shell{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:28px;padding:34px;background:linear-gradient(135deg,#fff 0%,#fff8f1 52%,#eef1ff 100%);box-shadow:var(--shadow)}
.hero-shell:after{content:"🎲";position:absolute;right:-22px;top:-34px;font-size:150px;opacity:.07;transform:rotate(14deg)}
.hero-kicker{display:inline-flex;align-items:center;gap:7px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 11px;font-size:12px;font-weight:900}
.hero-note{margin-top:12px;font-size:13px;color:var(--muted)}
.quick-entry{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:18px}
.quick-entry a{display:block;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:15px;padding:14px;transition:.18s transform,.18s box-shadow}
.quick-entry a:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.quick-entry b{display:block;font-size:16px}.quick-entry span{font-size:12px;color:var(--muted)}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.step-card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px}
.step-no{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--navy);color:#fff;font-size:12px;font-weight:900;margin-bottom:8px}
.game-card{transition:.18s transform,.18s box-shadow}.game-card:hover{transform:translateY(-2px);box-shadow:0 16px 38px rgba(26,33,52,.12)}
.game-media{position:relative;background:#fff}.game-badge{position:absolute;left:10px;top:10px;background:rgba(23,32,51,.9);color:#fff;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:900}
.fit-tags{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.fit-tag{display:inline-flex;background:#f6f7fb;border:1px solid #e6e9f2;border-radius:999px;padding:5px 8px;font-size:11px;font-weight:800;color:#49546a}
.card-meta{display:flex;gap:8px;flex-wrap:wrap;color:var(--muted);font-size:12px;font-weight:700}
.result-intro{background:linear-gradient(135deg,#fff5ee,#f2f4ff);border:1px solid var(--line);border-radius:18px;padding:15px;margin-bottom:16px}
.result-card.winner{border:2px solid var(--orange);box-shadow:0 18px 42px rgba(242,107,74,.14)}.result-card.winner:before{content:"まず見るならこれ";position:absolute;right:0;top:0;background:var(--orange);color:#fff;padding:7px 12px;border-radius:0 0 0 12px;font-size:11px;font-weight:900}.result-card{position:relative}
.result-layout{display:grid;grid-template-columns:118px 1fr;gap:14px}.result-image{width:118px;height:118px;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:14px}
.reason-list{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.reason-pill{background:#fff4ed;color:#9e4029;border-radius:999px;padding:5px 8px;font-size:11px;font-weight:900}
.filter-bar{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}.filter-btn{border:1px solid var(--line);background:#fff;border-radius:999px;padding:8px 12px;font-weight:800;cursor:pointer}.filter-btn.active{background:var(--navy);color:#fff;border-color:var(--navy)}
.games-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.game-list-card{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:15px;padding:14px;text-decoration:none}.game-list-card:hover{box-shadow:var(--shadow)}
.detail-summary{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:14px 0}.decision-box{border-radius:15px;padding:14px;background:#f7f8fc}.decision-box.good{background:#eef8f1}.decision-box h3{margin:0 0 5px;font-size:15px}.decision-box p{margin:0;font-size:13px}
.product-panel{position:sticky;top:78px}.product-availability{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:800;margin:8px 0 12px}.dot-live,.dot-search{width:8px;height:8px;border-radius:50%}.dot-live{background:#2b9d5b}.dot-search{background:#d89b2b}
.section-lead{display:flex;justify-content:space-between;align-items:end;gap:16px;margin-bottom:12px}.mini-callout{font-size:12px;color:var(--muted);max-width:350px}
@media(max-width:760px){.hero-shell{padding:24px 18px}.quick-entry{grid-template-columns:repeat(2,1fr)}.steps{grid-template-columns:1fr}.result-layout{grid-template-columns:88px 1fr}.result-image{width:88px;height:88px}.games-grid{grid-template-columns:1fr}.detail-summary{grid-template-columns:1fr}.product-panel{position:static}.section-lead{display:block}}
"""

ANALYTICS="""
(function(){
var cfg=window.KYO_BODO_CONFIG||{},id=cfg.gaMeasurementId||"",op=false,p=new URLSearchParams(location.search);
try{op=localStorage.getItem("kyo_bodo_operator_test")==="1"}catch(_){}
if(p.get("test")==="1"||p.get("test")==="0"){op=p.get("test")==="1";try{if(op)localStorage.setItem("kyo_bodo_operator_test","1");else localStorage.removeItem("kyo_bodo_operator_test")}catch(_){}}
window.dataLayer=window.dataLayer||[];window.gtag=window.gtag||function(){dataLayer.push(arguments)};
if(id){var s=document.createElement("script");s.async=true;s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(id);document.head.appendChild(s);gtag("js",new Date());gtag("config",id)}
window.kyoTrack=function(name,data){data=data||{};if(op)data.operator_test="1";gtag("event",name,data)};
document.addEventListener("click",function(ev){var a=ev.target.closest&&ev.target.closest("a");if(!a)return;
if(a.dataset.track)kyoTrack(a.dataset.track,{game_id:a.dataset.gameId||"",conversion_source:a.dataset.source||"",rank:a.dataset.rank||""});
if(a.dataset.affiliate)kyoTrack("affiliate_click",{affiliate:a.dataset.affiliate,game_id:a.dataset.gameId||"",conversion_source:a.dataset.source||"",rank:a.dataset.rank||"",link_url:a.href,page_path:location.pathname});
});
})();
"""

DIAGNOSIS="""
(function(){
var root=document.getElementById("diagnosisApp");if(!root)return;var B=(window.KYO_BODO_CONFIG||{}).basePath||"/kyo-bodo-jp/";
var qs=[
["who","誰と遊ぶ？",[["couple","夫婦・カップル"],["family","家族"],["friends","友達"],["children","子ども"],["large","大人数"],["first","初対面がいる"]]],
["players","何人で遊ぶ？",[["2","2人"],["4","3〜4人"],["6","5〜6人"],["8","7人以上"]]],
["mood","どんな時間にしたい？",[["laugh","とにかく笑いたい"],["compete","真剣に勝負したい"],["think","頭を使いたい"],["coop","みんなで協力したい"],["relax","ゆるく遊びたい"],["chat","会話を楽しみたい"]]],
["time","どのくらい遊べる？",[["15","10〜15分"],["30","30分くらい"],["60","1時間くらい"],["120","じっくり"]]],
["difficulty","難しいルールは？",[["1","苦手"],["3","少しならOK"],["5","問題なし"]]],
["balance","運と実力なら？",[["luck","運多め"],["half","半々"],["skill","実力重視"]]]
],a={},i=0,games=[],links={};
function label(key,val){var q=qs.filter(function(x){return x[0]===key})[0],z=q&&q[2].filter(function(x){return x[0]===val})[0];return z?z[1]:val}
function score(g){
var n=Number(a.players||4);if(!(g.players_min<=n&&g.players_max>=n))return -9999;var s=60,w=a.who;
if(w==="couple")s+=g.couple*7;else if(w==="family")s+=g.family*7;else if(w==="friends")s+=(g.conversation+g.party+g.excitement)*3;else if(w==="children")s+=g.children*7;else if(w==="large")s+=(g.large_group+g.party)*5;else if(w==="first")s+=(g.beginner+g.conversation+g.party)*4;
var m=a.mood;if(m==="laugh")s+=(g.excitement+g.party+g.conversation)*4;else if(m==="compete")s+=(g.strategy+g.excitement)*5;else if(m==="think")s+=g.strategy*8;else if(m==="coop")s+=g.cooperation*9;else if(m==="relax")s+=g.beginner*5+(6-g.difficulty)*4;else if(m==="chat")s+=g.conversation*8;
var t=Number(a.time||30);if(t<=15)s+=Math.max(0,20-Math.max(0,g.play_time_min-15)*2);else if(t<=30)s+=Math.max(0,18-Math.abs(g.play_time_max-30)/3);else if(t<=60)s+=Math.max(0,16-Math.abs(g.play_time_max-60)/5);else s+=g.play_time_max>=45?18:5;
var d=Number(a.difficulty||3);s+=Math.max(0,18-Math.abs(g.difficulty-d)*6);
if(a.balance==="luck")s+=g.luck*5+(6-g.strategy)*2;else if(a.balance==="skill")s+=g.strategy*6+(6-g.luck)*2;else s+=12-Math.abs(g.strategy-g.luck)*3;return s}
function reasonParts(g){var p=[];if(a.who)p.push(label("who",a.who)+"向き");if(a.mood)p.push(label("mood",a.mood));if(g.play_time_max<=30)p.push("30分以内");if(g.beginner>=4)p.push("初めてでも入りやすい");if(g.cooperation>=4)p.push("協力して遊べる");if(g.conversation>=4)p.push("会話が弾む");return p.slice(0,4)}
function fitTags(g){var x=[];if(g.beginner>=4)x.push("初心者");if(g.couple>=4)x.push("2人");if(g.family>=4)x.push("家族");if(g.children>=4)x.push("小学生");if(g.excitement>=4)x.push("盛り上がる");if(g.strategy>=4)x.push("考える");if(g.cooperation>=4)x.push("協力");return x.slice(0,3)}
function rak(g){var x=links[g.game_id]||{};return x.url||"https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/"}
function results(){
var r=games.map(function(g){return [g,score(g)]}).filter(function(x){return x[1]>-100}).sort(function(x,y){return y[1]-x[1]}).slice(0,5);
kyoTrack("diagnosis_complete",{players:a.players,who:a.who,mood:a.mood,desired_time:a.time,difficulty:a.difficulty,balance:a.balance,result_ids:r.map(function(x){return x[0].game_id}).join(",")});
root.innerHTML='<div class="result-intro"><div class="eyebrow">YOUR PICKS</div><h2>今日なら、この5本。</h2><p>1位は条件とのバランスが最も良い候補。迷ったらまず1位の「1分ルール」を見て、遊ぶ姿が想像できるかで決めてください。</p></div>'+
r.map(function(x,k){var g=x[0],lk=links[g.game_id]||{},img=lk.image_url?'<img class="result-image" src="'+lk.image_url+'" alt="'+g.title+'の商品画像">':'<div class="result-image game-placeholder">🎲</div>';kyoTrack("game_result_view",{game_id:g.game_id,rank:k+1,players:a.players,who:a.who,mood:a.mood});return '<article class="result-card '+(k===0?'winner':'')+'"><div class="rank">第 '+(k+1)+' 候補</div><div class="result-layout">'+img+'<div><h3>'+g.title+'</h3><p><strong>'+g.appeal+'</strong></p><div class="reason-list">'+reasonParts(g).map(function(z){return '<span class="reason-pill">'+z+'</span>'}).join("")+'</div><div class="fit-tags">'+fitTags(g).map(function(z){return '<span class="fit-tag"># '+z+'</span>'}).join("")+'</div></div></div><div class="card-meta"><span>👥 '+g.players_min+'〜'+g.players_max+'人</span><span>⏱ '+g.play_time_min+'〜'+g.play_time_max+'分</span><span>🎂 '+g.age+'歳〜</span></div><h4>ざっくり遊び方</h4><ol class="howto">'+g.how_to_play.map(function(z){return '<li>'+z+'</li>'}).join("")+'</ol><div class="card-actions"><a class="btn primary" data-track="game_detail_click" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" href="'+B+'games/'+g.game_id+'/">1分ルールを見る</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+rak(g)+'">楽天で商品を見る</a></div></article>'}).join("")+
'<div class="panel"><strong>なんか違う？</strong><p class="small">同じメンバーでも「今日は笑いたい／今日は考えたい」で結果は変わります。</p><a class="btn secondary" href="'+B+'diagnosis/">条件を変えてもう一度</a></div>'
}
function render(){if(i>=qs.length){results();return}var q=qs[i],pct=Math.round(i/qs.length*100);root.innerHTML='<div class="small">QUESTION '+(i+1)+' / '+qs.length+'</div><div class="progress"><b style="width:'+pct+'%"></b></div><div class="question"><div class="eyebrow">30秒診断</div><h2>'+q[1]+'</h2><p class="small">考えすぎず、今日の気分に近いものを1つ。</p><div class="answers">'+q[2].map(function(o){return '<button class="answer" data-v="'+o[0]+'">'+o[1]+'</button>'}).join("")+'</div></div>';root.querySelectorAll(".answer").forEach(function(b){b.onclick=function(){a[q[0]]=b.dataset.v;kyoTrack("diagnosis_answer",{question_id:q[0],answer_value:b.dataset.v,step:i+1});i++;render()}})}
Promise.all([fetch(B+"data/games.json").then(function(r){return r.json()}),fetch(B+"data/rakuten.json").then(function(r){return r.json()}).catch(function(){return {}})]).then(function(x){games=x[0];links=x[1];kyoTrack("diagnosis_start",{source:new URLSearchParams(location.search).get("src")||"direct"});render()});
})();
"""

TODAY="""
(function(){var root=document.getElementById("todayGames");if(!root)return;var B=(window.KYO_BODO_CONFIG||{}).basePath||"/kyo-bodo-jp/",d=new Date();
function sc(g){var day=d.getDay(),m=d.getMonth()+1,s=0;if(day===5)s+=g.party*4+g.excitement*3+g.conversation*2;else if(day===6)s+=g.strategy*3+(g.play_time_max>=30?10:0)+g.family*2;else if(day===0)s+=g.family*4+g.children*2+g.cooperation*2;else s+=g.short_play*4+g.beginner*2+g.couple*2;if(m===12||m===1)s+=g.family*2+g.large_group*2+g.party*2;if(m===7||m===8)s+=g.children*3+g.family*2;return s}
function why(g){var day=d.getDay();if(day===5)return "金曜の夜に、盛り上がり重視";if(day===6)return "土曜に少しじっくり";if(day===0)return "日曜の家族時間に";if(g.short_play>=4)return "平日の夜でも遊びやすい";return "今日のバランス候補"}
Promise.all([fetch(B+"data/games.json").then(function(r){return r.json()}),fetch(B+"data/rakuten.json").then(function(r){return r.json()}).catch(function(){return {}})]).then(function(x){var games=x[0],links=x[1],seed=Number(String(d.getFullYear())+String(d.getMonth()+1).padStart(2,"0")+String(d.getDate()).padStart(2,"0")),pool=games.map(function(g){g._s=sc(g);return g}).sort(function(a,b){return b._s-a._s}).slice(0,12),p=[];while(p.length<3&&pool.length)p.push(pool.splice((seed+p.length*7)%pool.length,1)[0]);root.innerHTML=p.map(function(g,k){var l=links[g.game_id]||{},r=l.url||"https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/",art=l.image_url?'<img class="game-thumb" src="'+l.image_url+'" alt="'+g.title+'の商品画像" loading="lazy">':'<div class="game-placeholder">🎲</div>';return '<article class="game-card"><div class="game-media">'+art+'<span class="game-badge">'+why(g)+'</span></div><div class="game-card-body"><div class="eyebrow">今日の'+(k+1)+'本目</div><h3>'+g.title+'</h3><p>'+g.appeal+'</p><div class="card-meta"><span>👥 '+g.players_min+'〜'+g.players_max+'人</span><span>⏱ '+g.play_time_min+'〜'+g.play_time_max+'分</span></div><div class="card-actions"><a class="btn primary" data-track="game_detail_click" data-game-id="'+g.game_id+'" data-source="today_pick" href="'+B+'games/'+g.game_id+'/">どんなゲーム？</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="'+g.game_id+'" data-source="today_pick" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+r+'">楽天で見る</a></div></div></article>'}).join("");kyoTrack("daily_recommendation_view",{game_ids:p.map(function(g){return g.game_id}).join(","),weekday:d.getDay(),month:d.getMonth()+1})});
})();
"""

def load_rakuten(g):
    x=RAKUTEN.get(g["game_id"],{})
    if x.get("url"): return x["url"],x.get("image_url",""),"楽天で見る"
    q=urllib.parse.quote(g.get("rakuten_query") or g["title"])
    return "https://search.rakuten.co.jp/search/mall/"+q+"/","","楽天で探す"


def fit_tags(g):
    pairs=[
        (g.get("beginner",0),"初心者向け"),(g.get("couple",0),"2人・夫婦向け"),
        (g.get("family",0),"家族向け"),(g.get("children",0),"小学生と"),
        (g.get("conversation",0),"会話が弾む"),(g.get("excitement",0),"盛り上がる"),
        (g.get("strategy",0),"考えごたえ"),(g.get("cooperation",0),"協力"),
        (g.get("short_play",0),"短時間"),(g.get("large_group",0),"大人数"),
    ]
    pairs.sort(key=lambda x:x[0],reverse=True)
    out=[]
    for score,label in pairs:
        if score>=4 and label not in out: out.append(label)
        if len(out)>=3: break
    return out or ["遊びやすい"]

def fit_copy(g):
    if g.get("cooperation",0)>=4: return "勝ち負けより、相談しながら一緒に達成したい日に。"
    if g.get("excitement",0)>=4 and g.get("conversation",0)>=4: return "みんなで声を出して笑いたい日や、場を温めたい時に。"
    if g.get("strategy",0)>=4: return "運だけでなく、自分の選択でしっかり勝負したい日に。"
    if g.get("couple",0)>=4: return "2人で落ち着いて遊びたい夜や、夫婦・カップル時間に。"
    if g.get("children",0)>=4: return "子どもと一緒に、大人も手加減しすぎず遊びたい日に。"
    return "ルール説明に時間をかけず、気軽に1本遊びたい日に。"

def caution_copy(g):
    if g.get("difficulty",0)>=4: return "最初の説明を短く済ませたいメンバーだけなら、より軽いゲームも候補。"
    if g.get("play_time_max",0)>=60: return "短時間でサッと終えたい日には少し重めです。"
    if g.get("conversation",0)<=2 and g.get("strategy",0)>=4: return "雑談中心でワイワイしたい日には、会話系ゲームの方が合います。"
    if g.get("excitement",0)<=2: return "大声で盛り上がるパーティー感を求める日には別候補もあり。"
    return "好みが分かれそうなら、診断結果の2〜3位も見比べるのがおすすめ。"

def card_badge(g):
    return fit_tags(g)[0]

def shell(title,desc,body,path="",extra=""):
    full=("きょうボド｜今日なにやる？" if title=="きょうボド" else title+"｜きょうボド")
    cfg=json.dumps({"basePath":BASE,"gaMeasurementId":GA},ensure_ascii=False)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon(path))}"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon(path))}"><meta property="og:type" content="website"><meta name="theme-color" content="#233046"><link rel="stylesheet" href="{u("assets/styles.css")}">{extra}<script>window.KYO_BODO_CONFIG={cfg};</script><script defer src="{u("assets/analytics.js")}"></script></head><body><header class="site-header"><a class="brand" href="{u()}"><b>◆</b>きょうボド</a><nav><a href="{u("diagnosis/")}">診断</a><a href="{u("scenes/")}">シーン</a><a href="{u("games/")}">ゲーム一覧</a></nav></header><main>{body}</main><footer><div><strong>きょうボド — 今日なにやる？</strong></div><p>掲載情報はゲーム選びの参考情報です。対象年齢・人数・ルール・在庫は商品版や販売店で最終確認してください。</p><p class="small">当サイトはアフィリエイト広告を利用する場合があります。</p></footer></body></html>'''

def card(g,source="list",rank=""):
    r,img,label=load_rakuten(g)
    art=f'<img class="game-thumb" src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy">' if img else '<div class="game-placeholder">🎲</div>'
    tags="".join(f'<span class="fit-tag"># {e(t)}</span>' for t in fit_tags(g))
    return f'''<article class="game-card"><div class="game-media">{art}<span class="game-badge">{e(card_badge(g))}</span></div><div class="game-card-body"><h3>{e(g["title"])}</h3><p>{e(g["appeal"])}</p><div class="fit-tags">{tags}</div><div class="card-meta"><span>👥 {g["players_min"]}〜{g["players_max"]}人</span><span>⏱ {g["play_time_min"]}〜{g["play_time_max"]}分</span><span>🎂 {g["age"]}歳〜</span></div><div class="card-actions"><a class="btn primary" data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" href="{u("games/"+g["game_id"]+"/")}">どんなゲーム？</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" data-rank="{e(rank)}" target="_blank" rel="sponsored noopener" href="{e(r)}">{label}</a></div></div></article>'''

def scene_score(g,s):
    r=s["rule"];t=r["type"]
    if t=="players": return 100 if g["players_min"]<=r["value"]<=g["players_max"] else 0
    if t=="field": return g.get(r["field"],0)*20
    if t=="tag": return 100 if r["tag"] in g.get("tags",[]) else 0
    if t=="formula": return sum(g.get(f,0) for f in r["fields"])/len(r["fields"])*20
    if t=="long": return min(100,max(0,(g["play_time_max"]-20)*2+g["strategy"]*7))
    return 0

def home():
    chips="".join(f'<a class="chip" href="{u("scenes/"+s["scene_id"]+"/")}">{e(s["title"])}</a>' for s in SCENES)
    ids=["ito","catan","splendor","nanjamonja","gobblet-gobblers","dobble"]
    pop="".join(card(BY_ID[x],"popular") for x in ids if x in BY_ID)
    body=f'''<section class="hero"><div class="hero-shell"><div class="hero-kicker">🎯 6問・約30秒</div><h1><span>きょうボド</span>今日なにやる？</h1><p><strong>「何でもいい」が一番むずかしい。</strong><br>人数・時間・今の気分から、今日のメンバーに合うボードゲームを5本まで絞ります。</p><div class="hero-actions"><a class="btn primary large" href="{u("diagnosis/?src=hero")}">今のメンバーで診断する</a><a class="btn secondary large" href="#scenes">条件から直接探す</a></div><div class="hero-note">会員登録なし・無料。結果には「1分で分かる遊び方」も表示します。</div><div class="quick-entry"><a href="{u("scenes/two-player/")}"><b>👥 2人で</b><span>夫婦・カップルにも</span></a><a href="{u("scenes/children/")}"><b>🧒 小学生と</b><span>家族で遊びやすい</span></a><a href="{u("scenes/large-group/")}"><b>🎉 大人数で</b><span>集まりを盛り上げる</span></a><a href="{u("scenes/beginner/")}"><b>🌱 初心者で</b><span>説明が短いものから</span></a></div></div></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">HOW IT WORKS</div><h2>「選ぶ」時間を短くする</h2></div><p class="mini-callout">詳しい知識がなくても、遊ぶ相手と気分が分かれば十分です。</p></div><div class="steps"><div class="step-card"><span class="step-no">1</span><h3>今日の条件を答える</h3><p class="small">誰と・何人で・何分くらい・どんな気分か。</p></div><div class="step-card"><span class="step-no">2</span><h3>5本まで絞る</h3><p class="small">人数を必須条件にして、気分や難しさを重ねて選びます。</p></div><div class="step-card"><span class="step-no">3</span><h3>1分ルールで決める</h3><p class="small">「遊んでいる姿が想像できた」1本を選べばOK。</p></div></div></section>
<section class="section"><div class="today-box"><div class="section-lead"><div><div class="eyebrow">TODAY</div><h2>今日のおすすめ3本</h2></div><p class="section-sub">曜日・季節から、今夜選びやすい候補を入れ替えます。</p></div><div class="grid" id="todayGames"><p>おすすめを選んでいます…</p></div></div></section>
<section class="section" id="scenes"><div class="section-lead"><div><div class="eyebrow">SCENE</div><h2>状況が決まっているなら、すぐ探す</h2></div><p class="mini-callout">「2人」「小学生」「短時間」など、検索しやすい入口を用意しています。</p></div><div class="chips">{chips}</div></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">START HERE</div><h2>迷ったら、この定番から</h2></div><p class="mini-callout">ジャンルが偏らないよう、入り口として使いやすい6本を選んでいます。</p></div><div class="grid">{pop}</div></section><script defer src="{u("assets/today.js")}"></script>'''
    return shell("きょうボド","ボードゲーム選びに迷ったら。人数・気分・時間の6問から、今日のメンバーに合う5本を30秒で診断。1分ルールで遊び方まで分かります。",body)

def diagnosis():
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / 診断</div><div class="eyebrow">DIAGNOSIS</div><h1>あなたたちに合うボードゲーム診断</h1><p>6問に答えると、人数・時間・気分・難易度・運と実力の好みからおすすめを選びます。</p></section><section class="diagnosis-wrap"><div id="diagnosisApp"><p>診断を読み込んでいます…</p></div></section><script defer src="{u("assets/diagnosis.js")}"></script>'''
    return shell("ボードゲーム診断","6問で今日のメンバーに合うボードゲームを診断します。",body,"diagnosis/")

def games_index():
    rows=[]
    for g in GAMES:
        tags=" ".join(f'<span class="fit-tag"># {e(t)}</span>' for t in fit_tags(g)[:2])
        attrs=f'data-pmin="{g["players_min"]}" data-pmax="{g["players_max"]}" data-short="{1 if g["play_time_max"]<=30 else 0}" data-family="{1 if g["family"]>=4 else 0}" data-beginner="{1 if g["beginner"]>=4 else 0}"'
        rows.append(f'<a class="game-list-card" {attrs} href="{u("games/"+g["game_id"]+"/")}"><div><strong>{e(g["title"])}</strong><div class="fit-tags">{tags}</div><span class="small">{g["players_min"]}〜{g["players_max"]}人 ・ {g["play_time_min"]}〜{g["play_time_max"]}分 ・ {g["age"]}歳〜</span></div><span aria-hidden="true">→</span></a>')
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / ゲーム一覧</div><div class="eyebrow">GAMES</div><h1>掲載ゲーム50本</h1><p>全部読む必要はありません。まず条件で絞って、気になったゲームだけ詳細を見てください。</p></section><section class="section"><div class="filter-bar"><button class="filter-btn active" data-filter="all">すべて</button><button class="filter-btn" data-filter="two">2人で遊べる</button><button class="filter-btn" data-filter="family">家族向け</button><button class="filter-btn" data-filter="short">30分以内</button><button class="filter-btn" data-filter="beginner">初心者向け</button></div><div class="games-grid" id="gamesGrid">{"".join(rows)}</div></section><script>document.addEventListener("click",function(ev){{var b=ev.target.closest(".filter-btn");if(!b)return;document.querySelectorAll(".filter-btn").forEach(function(x){{x.classList.remove("active")}});b.classList.add("active");var f=b.dataset.filter;document.querySelectorAll(".game-list-card").forEach(function(c){{var show=f==="all"||(f==="two"&&Number(c.dataset.pmin)<=2&&Number(c.dataset.pmax)>=2)||(f==="family"&&c.dataset.family==="1")||(f==="short"&&c.dataset.short==="1")||(f==="beginner"&&c.dataset.beginner==="1");c.style.display=show?"flex":"none"}});kyoTrack("game_filter_use",{{filter:f}})}})</script>'''
    return shell("ゲーム一覧","きょうボド掲載50ゲーム。2人、家族、30分以内、初心者向けなどから絞って探せます。",body,"games/")

def game_page(g):
    r,img,label=load_rakuten(g)
    similar=sorted([x for x in GAMES if x["game_id"]!=g["game_id"]],key=lambda x:abs(x["strategy"]-g["strategy"])+abs(x["excitement"]-g["excitement"])+abs(x["players_min"]-g["players_min"]))[:3]
    axes=[("難しさ","difficulty"),("戦略性","strategy"),("運要素","luck"),("会話量","conversation"),("盛り上がり","excitement"),("協力度","cooperation"),("初心者向け","beginner")]
    axis="".join(f'<div class="axis"><span>{n}</span><span class="dots">{"●"*g[k]}{"○"*(5-g[k])}</span></div>' for n,k in axes)
    art=f'<img class="game-thumb" style="height:250px" src="{e(img)}" alt="{e(g["title"])}の商品画像">' if img else '<div class="game-placeholder" style="height:250px">🎲</div>'
    tags="".join(f'<span class="fit-tag"># {e(t)}</span>' for t in fit_tags(g))
    availability='<span class="dot-live"></span>楽天の商品ページを取得済み' if img else '<span class="dot-search"></span>楽天検索から候補を確認'
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("games/")}">ゲーム</a> / {e(g["title"])}</div><div class="eyebrow">GAME GUIDE</div><h1>{e(g["title"])}</h1><p><strong>{e(g["appeal"])}</strong></p><div class="fit-tags">{tags}</div></section><section class="section"><div class="detail-layout"><div><div class="panel"><div class="section-lead"><div><div class="eyebrow">3-SECOND CHECK</div><h2>3秒で「今日向き？」を判断</h2></div></div><div class="specs"><div class="spec"><b>人数</b>{g["players_min"]}〜{g["players_max"]}人</div><div class="spec"><b>時間</b>{g["play_time_min"]}〜{g["play_time_max"]}分</div><div class="spec"><b>対象年齢</b>{g["age"]}歳〜</div><div class="spec"><b>タイプ</b>{"協力寄り" if g["cooperation"]>=4 else "対戦・競争寄り"}</div></div><div class="detail-summary"><div class="decision-box good"><h3>◎ こんな日に合う</h3><p>{e(fit_copy(g))}</p></div><div class="decision-box"><h3>△ 今日は別候補でも</h3><p>{e(caution_copy(g))}</p></div></div><h2>どんなゲーム？</h2><p>{e(g["description"])}</p><h2>1分で分かる遊び方</h2><ol class="howto">{"".join("<li>"+e(z)+"</li>" for z in g["how_to_play"])}</ol><h2>どんな場面で使いやすい？</h2><div class="chips">{"".join("<span class=chip>"+e(z)+"</span>" for z in g["recommended_scene"])}</div></div><div class="panel" style="margin-top:18px"><div class="section-lead"><div><div class="eyebrow">ALTERNATIVES</div><h2>これと迷うなら</h2></div><p class="mini-callout">似た遊び味の候補を3本。</p></div><div class="grid">{"".join(card(x,"similar") for x in similar)}</div></div></div><aside><div class="panel product-panel">{art}<div class="product-availability">{availability}</div>{axis}<p class="small">PR：購入前に販売ページで版・対象年齢・在庫を確認してください。</p><a class="btn rakuten large" style="width:100%" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="game_detail" target="_blank" rel="sponsored noopener" href="{e(r)}">{label}</a><a class="btn secondary" style="width:100%;margin-top:8px" href="{u("diagnosis/?src=game_detail")}">診断で他の候補も見る</a></div></aside></div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("game_detail_view",{{game_id:{json.dumps(g["game_id"])},page_path:location.pathname}})}})</script>'''
    schema=json.dumps({"@context":"https://schema.org","@type":"WebPage","name":g["title"]+"｜きょうボド","description":g["description"],"url":canon("games/"+g["game_id"]+"/")},ensure_ascii=False)
    return shell(g["title"],g["appeal"],body,"games/"+g["game_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')

def scenes_index():
    chips="".join(f'<a class="chip" href="{u("scenes/"+s["scene_id"]+"/")}">{e(s["title"])}</a>' for s in SCENES)
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / シーン</div><div class="eyebrow">SCENE</div><h1>シーンから探す</h1><p>人数や相手、今日の気分が決まっているならここから。</p></section><section class="section"><div class="chips">{chips}</div></section>'''
    return shell("シーンから探す","2人、夫婦、家族、小学生、大人数、初心者、短時間、盛り上がる、協力などシーン別に探せます。",body,"scenes/")

def scene_page(s):
    ranked=sorted(GAMES,key=lambda g:scene_score(g,s),reverse=True)
    ranked=[g for g in ranked if scene_score(g,s)>=50][:12]
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("scenes/")}">シーン</a> / {e(s["title"])}</div><div class="eyebrow">SCENE</div><h1>{e(s["title"])}ボードゲーム</h1><p>{e(s["intro"])}</p></section><section class="section"><div class="grid">{"".join(card(g,"scene_page",i+1) for i,g in enumerate(ranked))}</div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("scene_view",{{scene_id:{json.dumps(s["scene_id"])},game_count:{len(ranked)}}})}})</script>'''
    schema=json.dumps({"@context":"https://schema.org","@type":"ItemList","name":s["title"]+"ボードゲーム","itemListElement":[{"@type":"ListItem","position":i+1,"url":canon("games/"+g["game_id"]+"/"),"name":g["title"]} for i,g in enumerate(ranked)]},ensure_ascii=False)
    return shell(s["title"]+"ボードゲーム",s["intro"],body,"scenes/"+s["scene_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')

def write(rel,text):
    p=SITE/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8")

def main():
    if SITE.exists(): shutil.rmtree(SITE)
    (SITE/"assets").mkdir(parents=True);(SITE/"data").mkdir(parents=True)
    write("assets/styles.css",CSS);write("assets/analytics.js",ANALYTICS);write("assets/diagnosis.js",DIAGNOSIS);write("assets/today.js",TODAY)
    write("data/games.json",json.dumps(GAMES,ensure_ascii=False,separators=(",",":")))
    write("data/rakuten.json",json.dumps(RAKUTEN,ensure_ascii=False,separators=(",",":")))
    write("index.html",home());write("diagnosis/index.html",diagnosis());write("games/index.html",games_index());write("scenes/index.html",scenes_index())
    for g in GAMES: write("games/"+g["game_id"]+"/index.html",game_page(g))
    for s in SCENES: write("scenes/"+s["scene_id"]+"/index.html",scene_page(s))
    paths=["", "diagnosis/","games/","scenes/"]+["games/"+g["game_id"]+"/" for g in GAMES]+["scenes/"+s["scene_id"]+"/" for s in SCENES]
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join("<url><loc>"+e(canon(p))+"</loc></url>" for p in paths)+"</urlset>"
    write("sitemap.xml",xml);write("robots.txt","User-agent: *\nAllow: /\nSitemap: "+canon("sitemap.xml")+"\n")
    write("404.html",shell("ページが見つかりません","ページが見つかりません。",'<section class="page-hero"><h1>ページが見つかりません</h1><a class="btn primary" href="'+u()+'">トップへ</a></section>'))
    print("built",len(paths),"indexable URLs in",SITE)

if __name__=="__main__": main()
