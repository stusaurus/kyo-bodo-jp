#!/usr/bin/env python3
import html, json, os, shutil, urllib.parse
from pathlib import Path
from data.catalog import GAMES

ROOT=Path(__file__).resolve().parents[1]
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
function label(key,val){var q=qs.filter(function(x){return x[0]===key})[0];var z=q[2].filter(function(x){return x[0]===val})[0];return z?z[1]:val}
function score(g){
var n=Number(a.players||4);if(!(g.players_min<=n&&g.players_max>=n))return -9999;var s=60;
var w=a.who;if(w==="couple")s+=g.couple*7;else if(w==="family")s+=g.family*7;else if(w==="friends")s+=(g.conversation+g.party+g.excitement)*3;else if(w==="children")s+=g.children*7;else if(w==="large")s+=(g.large_group+g.party)*5;else if(w==="first")s+=(g.beginner+g.conversation+g.party)*4;
var m=a.mood;if(m==="laugh")s+=(g.excitement+g.party+g.conversation)*4;else if(m==="compete")s+=(g.strategy+g.excitement)*5;else if(m==="think")s+=g.strategy*8;else if(m==="coop")s+=g.cooperation*9;else if(m==="relax")s+=g.beginner*5+(6-g.difficulty)*4;else if(m==="chat")s+=g.conversation*8;
var t=Number(a.time||30);if(t<=15)s+=Math.max(0,20-Math.max(0,g.play_time_min-15)*2);else if(t<=30)s+=Math.max(0,18-Math.abs(g.play_time_max-30)/3);else if(t<=60)s+=Math.max(0,16-Math.abs(g.play_time_max-60)/5);else s+=g.play_time_max>=45?18:5;
var d=Number(a.difficulty||3);s+=Math.max(0,18-Math.abs(g.difficulty-d)*6);
if(a.balance==="luck")s+=g.luck*5+(6-g.strategy)*2;else if(a.balance==="skill")s+=g.strategy*6+(6-g.luck)*2;else s+=12-Math.abs(g.strategy-g.luck)*3;
return s}
function reason(g){var parts=[label("who",a.who),label("mood",a.mood)];if(g.play_time_max<=30)parts.push("短めで始めやすい");if(g.beginner>=4)parts.push("ルールが入りやすい");if(g.cooperation>=4)parts.push("協力感が強い");return parts.slice(0,3).join("・")}
function rak(g){var x=links[g.game_id]||{};return x.url||"https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/"}
function results(){
var r=games.map(function(g){return [g,score(g)]}).filter(function(x){return x[1]>-100}).sort(function(x,y){return y[1]-x[1]}).slice(0,5);
kyoTrack("diagnosis_complete",{players:a.players,who:a.who,mood:a.mood,desired_time:a.time,difficulty:a.difficulty,balance:a.balance,result_ids:r.map(function(x){return x[0].game_id}).join(",")});
root.innerHTML='<div class="eyebrow">RESULT</div><h2>あなたたちに合うゲーム BEST '+r.length+'</h2><p class="small">「遊んでいる姿が想像できるか」を優先して選びました。</p>'+r.map(function(x,k){var g=x[0];kyoTrack("game_result_view",{game_id:g.game_id,rank:k+1,players:a.players,who:a.who,mood:a.mood});return '<article class="result-card"><div class="rank">BEST '+(k+1)+'</div><h3>'+g.title+'</h3><p><strong>'+g.appeal+'</strong></p><p class="small">合う理由：'+reason(g)+'</p><div class="chips"><span class="chip">'+g.players_min+'〜'+g.players_max+'人</span><span class="chip">'+g.play_time_min+'〜'+g.play_time_max+'分</span><span class="chip">'+g.age+'歳〜</span></div><h4>1分で分かる遊び方</h4><ol class="howto">'+g.how_to_play.map(function(z){return '<li>'+z+'</li>'}).join("")+'</ol><div class="card-actions"><a class="btn secondary" data-track="game_detail_click" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" href="'+B+'games/'+g.game_id+'/">詳しく見る</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="'+g.game_id+'" data-source="diagnosis_result" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+rak(g)+'">楽天で見る</a></div></article>'}).join("")+'<a class="btn secondary" href="'+B+'diagnosis/">もう一度診断する</a>'
}
function render(){
if(i>=qs.length){results();return}var q=qs[i],pct=Math.round(i/qs.length*100);root.innerHTML='<div class="small">'+(i+1)+' / '+qs.length+'</div><div class="progress"><b style="width:'+pct+'%"></b></div><div class="question"><h2>'+q[1]+'</h2><div class="answers">'+q[2].map(function(o){return '<button class="answer" data-v="'+o[0]+'">'+o[1]+'</button>'}).join("")+'</div></div>';root.querySelectorAll(".answer").forEach(function(b){b.onclick=function(){a[q[0]]=b.dataset.v;kyoTrack("diagnosis_answer",{question_id:q[0],answer_value:b.dataset.v,step:i+1});i++;render()}})
}
Promise.all([fetch(B+"data/games.json").then(function(r){return r.json()}),fetch(B+"data/rakuten.json").then(function(r){return r.json()}).catch(function(){return {}})]).then(function(x){games=x[0];links=x[1];kyoTrack("diagnosis_start",{source:new URLSearchParams(location.search).get("src")||"direct"});render()});
})();
"""

TODAY="""
(function(){var root=document.getElementById("todayGames");if(!root)return;var B=(window.KYO_BODO_CONFIG||{}).basePath||"/kyo-bodo-jp/",d=new Date();
function sc(g){var day=d.getDay(),m=d.getMonth()+1,s=0;if(day===5)s+=g.party*4+g.excitement*3+g.conversation*2;else if(day===6)s+=g.strategy*3+(g.play_time_max>=30?10:0)+g.family*2;else if(day===0)s+=g.family*4+g.children*2+g.cooperation*2;else s+=g.short_play*4+g.beginner*2+g.couple*2;if(m===12||m===1)s+=g.family*2+g.large_group*2+g.party*2;if(m===7||m===8)s+=g.children*3+g.family*2;return s}
Promise.all([fetch(B+"data/games.json").then(function(r){return r.json()}),fetch(B+"data/rakuten.json").then(function(r){return r.json()}).catch(function(){return {}})]).then(function(x){var games=x[0],links=x[1],seed=Number(String(d.getFullYear())+String(d.getMonth()+1).padStart(2,"0")+String(d.getDate()).padStart(2,"0")),pool=games.map(function(g){g._s=sc(g);return g}).sort(function(a,b){return b._s-a._s}).slice(0,12),p=[];while(p.length<3&&pool.length)p.push(pool.splice((seed+p.length*7)%pool.length,1)[0]);root.innerHTML=p.map(function(g,k){var l=links[g.game_id]||{},r=l.url||"https://search.rakuten.co.jp/search/mall/"+encodeURIComponent(g.rakuten_query||g.title)+"/";return '<article class="game-card"><div class="game-placeholder">🎲</div><div class="game-card-body"><div class="eyebrow">今日の'+(k+1)+'本目</div><h3>'+g.title+'</h3><p>'+g.appeal+'</p><p class="small">'+g.players_min+'〜'+g.players_max+'人 ・ '+g.play_time_min+'〜'+g.play_time_max+'分</p><div class="card-actions"><a class="btn secondary" data-track="game_detail_click" data-game-id="'+g.game_id+'" data-source="today_pick" href="'+B+'games/'+g.game_id+'/">詳しく</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="'+g.game_id+'" data-source="today_pick" data-rank="'+(k+1)+'" target="_blank" rel="sponsored noopener" href="'+r+'">楽天で見る</a></div></div></article>'}).join("");kyoTrack("daily_recommendation_view",{game_ids:p.map(function(g){return g.game_id}).join(","),weekday:d.getDay(),month:d.getMonth()+1})});
})();
"""

def load_rakuten(g):
    x=RAKUTEN.get(g["game_id"],{})
    if x.get("url"): return x["url"],x.get("image_url",""),"楽天で見る"
    q=urllib.parse.quote(g.get("rakuten_query") or g["title"])
    return "https://search.rakuten.co.jp/search/mall/"+q+"/","","楽天で探す"

def shell(title,desc,body,path="",extra=""):
    full=("きょうボド｜今日なにやる？" if title=="きょうボド" else title+"｜きょうボド")
    cfg=json.dumps({"basePath":BASE,"gaMeasurementId":GA},ensure_ascii=False)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon(path))}"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon(path))}"><meta property="og:type" content="website"><meta name="theme-color" content="#233046"><link rel="stylesheet" href="{u("assets/styles.css")}">{extra}<script>window.KYO_BODO_CONFIG={cfg};</script><script defer src="{u("assets/analytics.js")}"></script></head><body><header class="site-header"><a class="brand" href="{u()}"><b>◆</b>きょうボド</a><nav><a href="{u("diagnosis/")}">診断</a><a href="{u("scenes/")}">シーン</a><a href="{u("games/")}">ゲーム一覧</a></nav></header><main>{body}</main><footer><div><strong>きょうボド — 今日なにやる？</strong></div><p>掲載情報はゲーム選びの参考情報です。対象年齢・人数・ルール・在庫は商品版や販売店で最終確認してください。</p><p class="small">当サイトはアフィリエイト広告を利用する場合があります。</p></footer></body></html>'''

def card(g,source="list",rank=""):
    r,img,label=load_rakuten(g)
    art=f'<img class="game-thumb" src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy">' if img else '<div class="game-placeholder">🎲</div>'
    return f'''<article class="game-card">{art}<div class="game-card-body"><div class="eyebrow">{g["players_min"]}〜{g["players_max"]}人 ・ {g["play_time_min"]}〜{g["play_time_max"]}分</div><h3>{e(g["title"])}</h3><p>{e(g["appeal"])}</p><div class="card-actions"><a class="btn secondary" data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" href="{u("games/"+g["game_id"]+"/")}">詳しく</a><a class="btn rakuten" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" data-rank="{e(rank)}" target="_blank" rel="sponsored noopener" href="{e(r)}">{label}</a></div></div></article>'''

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
    body=f'''<section class="hero"><div class="eyebrow">BOARD GAME FINDER</div><h1><span>きょうボド</span>今日なにやる？</h1><p>人数と今の気分に答えるだけ。定番・人気ゲームから、今日のメンバーに合う1本を30秒で見つけます。</p><div class="hero-actions"><a class="btn primary large" href="{u("diagnosis/?src=hero")}">30秒で診断する</a><a class="btn secondary large" href="#scenes">シーンから探す</a></div><div class="trust-row"><div class="trust"><strong>6問だけ</strong><span class="small">心理テスト感覚</span></div><div class="trust"><strong>1分ルール</strong><span class="small">買う前に遊び方が分かる</span></div><div class="trust"><strong>{len(GAMES)}ゲーム</strong><span class="small">数より選びやすさ</span></div></div></section><section class="section"><div class="today-box"><h2>今日のおすすめ3本</h2><p class="section-sub">曜日と季節に合わせて候補を入れ替えます。</p><div class="grid" id="todayGames"><p>おすすめを選んでいます…</p></div></div></section><section class="section" id="scenes"><div class="eyebrow">SCENE</div><h2>シーンから探す</h2><div class="chips">{chips}</div></section><section class="section"><div class="eyebrow">START HERE</div><h2>まず見てほしい定番</h2><div class="grid">{pop}</div></section><script defer src="{u("assets/today.js")}"></script>'''
    return shell("きょうボド","人数・気分・時間から、自分たちに合うボードゲームを30秒で診断。遊び方を1分で確認して購入候補へ。",body)

def diagnosis():
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / 診断</div><div class="eyebrow">DIAGNOSIS</div><h1>あなたたちに合うボードゲーム診断</h1><p>6問に答えると、人数・時間・気分・難易度・運と実力の好みからおすすめを選びます。</p></section><section class="diagnosis-wrap"><div id="diagnosisApp"><p>診断を読み込んでいます…</p></div></section><script defer src="{u("assets/diagnosis.js")}"></script>'''
    return shell("ボードゲーム診断","6問で今日のメンバーに合うボードゲームを診断します。",body,"diagnosis/")

def games_index():
    rows="".join(f'<a href="{u("games/"+g["game_id"]+"/")}"><strong>{e(g["title"])}</strong><br><span class="small">{g["players_min"]}〜{g["players_max"]}人 ・ {g["play_time_min"]}〜{g["play_time_max"]}分</span></a>' for g in GAMES)
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / ゲーム一覧</div><div class="eyebrow">GAMES</div><h1>掲載ゲーム一覧</h1><p>{len(GAMES)}本から、遊ぶかどうかを判断するための情報だけを簡潔に。</p></section><section class="section"><div class="all-games">{rows}</div></section>'''
    return shell("ゲーム一覧","きょうボド掲載ゲーム一覧。人数・時間・特徴から詳細を確認できます。",body,"games/")

def game_page(g):
    r,img,label=load_rakuten(g)
    similar=sorted([x for x in GAMES if x["game_id"]!=g["game_id"]],key=lambda x:abs(x["strategy"]-g["strategy"])+abs(x["excitement"]-g["excitement"])+abs(x["players_min"]-g["players_min"]))[:3]
    axes=[("難しさ","difficulty"),("戦略性","strategy"),("運要素","luck"),("会話量","conversation"),("盛り上がり","excitement"),("協力度","cooperation"),("初心者向け","beginner")]
    axis="".join(f'<div class="axis"><span>{n}</span><span class="dots">{"●"*g[k]}{"○"*(5-g[k])}</span></div>' for n,k in axes)
    art=f'<img class="game-thumb" style="height:250px" src="{e(img)}" alt="{e(g["title"])}の商品画像">' if img else '<div class="game-placeholder" style="height:250px">🎲</div>'
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("games/")}">ゲーム</a> / {e(g["title"])}</div><div class="eyebrow">GAME</div><h1>{e(g["title"])}</h1><p><strong>{e(g["appeal"])}</strong></p></section><section class="section"><div class="detail-layout"><div><div class="panel"><h2>どんなゲーム？</h2><p>{e(g["description"])}</p><div class="specs"><div class="spec"><b>人数</b>{g["players_min"]}〜{g["players_max"]}人</div><div class="spec"><b>時間</b>{g["play_time_min"]}〜{g["play_time_max"]}分</div><div class="spec"><b>対象年齢</b>{g["age"]}歳〜</div><div class="spec"><b>タイプ</b>{"協力寄り" if g["cooperation"]>=4 else "対戦・競争寄り"}</div></div><h2>1分で分かる遊び方</h2><ol class="howto">{"".join("<li>"+e(z)+"</li>" for z in g["how_to_play"])}</ol><h2>こんな時におすすめ</h2><div class="chips">{"".join("<span class=chip>"+e(z)+"</span>" for z in g["recommended_scene"])}</div></div><div class="panel" style="margin-top:18px"><h2>似た候補</h2><div class="grid">{"".join(card(x,"similar") for x in similar)}</div></div></div><aside><div class="panel">{art}{axis}<p class="small">PR：購入前に販売ページで版・対象年齢・在庫を確認してください。</p><a class="btn rakuten large" style="width:100%" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="game_detail" target="_blank" rel="sponsored noopener" href="{e(r)}">{label}</a></div></aside></div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("game_detail_view",{{game_id:{json.dumps(g["game_id"])},page_path:location.pathname}})}})</script>'''
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
    write("sitemap.xml",xml);write("robots.txt","User-agent: *\\nAllow: /\\nSitemap: "+canon("sitemap.xml")+"\\n")
    write("404.html",shell("ページが見つかりません","ページが見つかりません。",'<section class="page-hero"><h1>ページが見つかりません</h1><a class="btn primary" href="'+u()+'">トップへ</a></section>'))
    print("built",len(paths),"indexable URLs in",SITE)

if __name__=="__main__": main()
