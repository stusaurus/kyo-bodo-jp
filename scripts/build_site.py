#!/usr/bin/env python3
# Hero asset refresh: validated WebP source v2.
import hashlib, html, json, os, shutil, urllib.parse, sys
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
HERO_ASSET=ROOT/"assets"/"hero-kyo-bodo.webp"
SCENE_ASSET=ROOT/"assets"/"scene-sprite.webp"
BY_ID={g["game_id"]:g for g in GAMES}

def e(x): return html.escape(str(x),quote=True)
def u(p=""): return BASE+p.lstrip("/")
def canon(p=""): return SITE_URL+p.lstrip("/")

def asset(name):
    path=ROOT/"assets"/name
    version=hashlib.sha256(path.read_bytes()).hexdigest()[:12] if path.exists() else "1"
    return u("assets/"+name)+"?v="+version

SCENE_ART={"two-player":1,"couple":1,"family":2,"children":3,"friends":4,"large-group":4,"first-meeting":4,"drinking":4,"short":5,"long":1,"think":1,"laugh":4,"cooperative":6,"beginner":2}
MAIN_SCENES=[("two-player","2人で","ふたりの時間に",1),("family","家族で","みんなで、もう1回",2),("children","小学生と","大人も一緒に夢中",3),("large-group","大人数で","笑い声の真ん中に",4),("short","短時間で","ちょっとの時間も楽しく",5),("cooperative","協力して","一緒にできた、がうれしい",6)]

BRAND_MARK='<svg class="brand-mark" viewBox="0 0 48 48" aria-hidden="true"><g fill="#386fc1"><rect x="14" y="2" width="23" height="23" rx="6" transform="rotate(12 25 13)"/><rect x="2" y="20" width="22" height="22" rx="6" transform="rotate(-12 13 31)"/></g><rect x="25" y="24" width="21" height="21" rx="6" fill="#eb612e" transform="rotate(12 35 34)"/><g fill="#fff"><circle cx="21" cy="9" r="1.7"/><circle cx="29" cy="10.5" r="1.7"/><circle cx="24.5" cy="14" r="1.7"/><circle cx="20" cy="17" r="1.7"/><circle cx="28" cy="18.5" r="1.7"/><circle cx="8" cy="27" r="1.7"/><circle cx="16" cy="25.5" r="1.7"/><circle cx="12" cy="31" r="1.7"/><circle cx="9" cy="36.5" r="1.7"/><circle cx="17" cy="35" r="1.7"/><circle cx="31" cy="29" r="1.7"/><circle cx="39" cy="31" r="1.7"/><circle cx="34.5" cy="35" r="1.7"/><circle cx="30" cy="39" r="1.7"/><circle cx="38" cy="41" r="1.7"/></g></svg>'
PLACEHOLDER='<div class="game-placeholder" aria-label="商品画像は未取得"><svg class="placeholder-dice" viewBox="0 0 80 80" fill="none" aria-hidden="true"><rect x="15" y="15" width="50" height="50" rx="13" stroke="currentColor" stroke-width="2"/><g fill="currentColor"><circle cx="28" cy="28" r="3"/><circle cx="52" cy="28" r="3"/><circle cx="40" cy="40" r="3"/><circle cx="28" cy="52" r="3"/><circle cx="52" cy="52" r="3"/></g></svg></div>'

def scene_navigation():
    return '<div class="scene-grid" style="--scene-sprite:url(\''+asset("scene-sprite.webp")+'\')">'+''.join(f'<a class="scene-card" href="{u("scenes/"+sid+"/")}"><div class="scene-art s{art}" aria-hidden="true"></div><div class="scene-copy"><span><strong>{title}</strong><small>{sub}</small></span><i class="scene-arrow" aria-hidden="true">→</i></div></a>' for sid,title,sub,art in MAIN_SCENES)+'</div>'

CSS=(ROOT/"assets/styles.css").read_text(encoding="utf-8")

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

DIAGNOSIS=(ROOT/"assets/diagnosis.js").read_text(encoding="utf-8")

TODAY=(ROOT/"assets/today.js").read_text(encoding="utf-8")

def load_rakuten(g):
    x=RAKUTEN.get(g["game_id"],{})
    if x.get("url"):
        image=x.get("image_url","")
        if image.startswith("https://thumbnail.image.rakuten.co.jp/"):
            image=image.replace("_ex=128x128","_ex=320x320")
        return x["url"],image,"楽天で見る"
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
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon(path))}"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon(path))}"><meta property="og:type" content="website"><meta property="og:image" content="{e(canon("assets/hero-kyo-bodo.webp"))}"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#fffaf2"><link rel="stylesheet" href="{asset("styles.css")}">{extra}<script>window.KYO_BODO_CONFIG={cfg};</script><script defer src="{u("assets/analytics.js")}"></script><script defer src="{asset("media.js")}"></script></head><body><header class="site-header"><div class="header-inner"><a class="brand" href="{u()}" aria-label="きょうボド ホーム">{BRAND_MARK}<span><span class="brand-word">きょう<em>ボド</em></span><span class="brand-sub">今日なにやる？</span></span></a><nav aria-label="メインナビゲーション"><a href="{u("diagnosis/")}">診断</a><a href="{u("scenes/")}">シーン</a><a href="{u("games/")}">ゲーム一覧</a></nav></div></header><main>{body}</main><footer><div class="footer-inner"><div class="footer-brand">きょうボド <span class="small">今日なにやる？</span></div><div class="footer-nav"><a href="{u("diagnosis/")}">診断する</a><a href="{u("scenes/")}">シーンから探す</a><a href="{u("games/")}">50本のゲームを見る</a></div><p>掲載情報はゲーム選びの参考情報です。対象年齢・人数・ルール・在庫は商品版や販売店で最終確認してください。</p><p>当サイトはアフィリエイト広告を利用する場合があります。</p></div></footer></body></html>'''


def card(g,source="list",rank=""):
    r,img,label=load_rakuten(g)
    art=f'<img class="game-thumb" src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy" decoding="async">' if img else PLACEHOLDER
    return f'''<article class="game-card"><div class="game-media">{art}</div><div class="game-card-body"><h3>{e(g["title"])}</h3><p>{e(g["appeal"])}</p><div class="card-meta"><span>{g["players_min"]}〜{g["players_max"]}人</span><span>{g["play_time_min"]}〜{g["play_time_max"]}分</span><span>{g["age"]}歳〜</span></div><div class="card-actions"><a class="text-link" data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" href="{u("games/"+g["game_id"]+"/")}">どんなゲーム？ <span class="arrow" aria-hidden="true">→</span></a><a class="btn secondary" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" data-rank="{e(rank)}" target="_blank" rel="sponsored noopener" href="{e(r)}">{label}</a></div></div></article>'''


def scene_score(g,s):
    r=s["rule"];t=r["type"]
    if t=="players": return 100 if g["players_min"]<=r["value"]<=g["players_max"] else 0
    if t=="field": return g.get(r["field"],0)*20
    if t=="tag": return 100 if r["tag"] in g.get("tags",[]) else 0
    if t=="formula": return sum(g.get(f,0) for f in r["fields"])/len(r["fields"])*20
    if t=="long": return min(100,max(0,(g["play_time_max"]-20)*2+g["strategy"]*7))
    return 0

def home():
    pop="".join(card(BY_ID[x],"popular") for x in ["ito","catan","splendor"])
    body=f'''<section class="hero"><div class="hero-shell"><div class="hero-copy"><div class="hero-message"><p class="hero-eyebrow">みんなで遊ぶと、今日がちょっと特別に。</p><h1><span>今日</span>なにやる？</h1><p class="hero-summary">人数・気分・時間から、<span>今日の1本をすぐ見つける。</span></p></div><div class="hero-action-block"><div class="hero-actions"><a class="btn primary large" href="{u("diagnosis/?src=hero")}">今のメンバーで診断する <span aria-hidden="true">→</span></a><a class="btn secondary" href="#scenes">シーンから探す <span aria-hidden="true">↓</span></a></div><p class="hero-note">6問・約30秒　／　登録不要　／　1分ルールつき</p></div></div><figure class="hero-visual"><img src="{asset("hero-kyo-bodo.webp")}" alt="暖かな光の中で、家族がテーブルを囲んでボードゲームを楽しむイラスト" width="1536" height="1024" fetchpriority="high" decoding="async"></figure></div></section>
<section class="section scene-section" id="scenes"><div class="section-lead"><div><div class="eyebrow">PLAY TOGETHER</div><h2>今日は、誰と遊ぶ？</h2></div><a class="text-link" href="{u("scenes/")}">すべてのシーン <span class="arrow" aria-hidden="true">→</span></a></div>{scene_navigation()}</section>
<section class="today-section"><div class="today-inner"><div class="section-lead"><div><div class="eyebrow">TODAY'S PICKS</div><h2>今日のおすすめ3本</h2></div><p class="section-sub">いつもの時間に、ひとつ遊びを。</p></div><div id="todayGames"><p class="small">今日のおすすめを読み込んでいます…</p></div></div></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">FIND YOUR GAME</div><h2>「選ぶ」時間を短くする</h2></div></div><div class="steps"><div class="step-card"><span class="step-no">01</span><h3>今のメンバーを教えて</h3><p>人数・時間・気分を、6問で。</p></div><div class="step-card"><span class="step-no">02</span><h3>今日に合う候補が見つかる</h3><p>あなたたちに合う5本をご提案。</p></div><div class="step-card"><span class="step-no">03</span><h3>1分ルールで、遊ぶ姿を想像</h3><p>楽しそうと思ったら、その1本を。</p></div></div><div class="steps-action"><a class="text-link" href="{u("diagnosis/?src=how_it_works")}">今日の1本を診断する <span class="arrow" aria-hidden="true">→</span></a></div></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">TIMELESS FAVORITES</div><h2>迷ったら、この定番から</h2></div><a class="text-link" href="{u("games/")}">50本のゲーム <span class="arrow" aria-hidden="true">→</span></a></div><div class="grid popular-grid">{pop}</div></section><script defer src="{asset("today.js")}"></script>'''
    return shell("きょうボド","ボードゲーム選びに迷ったら。人数・気分・時間の6問から、今日のメンバーに合う5本を30秒で診断。1分ルールで遊び方まで分かります。",body)


def diagnosis():
    body=f'''<section class="page-hero diagnosis-header"><div class="eyebrow">FIND YOUR GAME</div><h1 class="diagnosis-heading">今日の遊びを、見つけよう。</h1><p class="diagnosis-subtitle">6問だけ。今のメンバーと、今の気分で。</p></section><section class="diagnosis-wrap" style="--scene-sprite:url('{asset("scene-sprite.webp")}')"><div id="diagnosisApp" aria-busy="true"><p class="small">診断を読み込んでいます…</p></div><noscript><p>診断にはJavaScriptが必要です。<a href="{u("scenes/")}">シーンからゲームを探す</a>こともできます。</p></noscript></section><script defer src="{asset("diagnosis.js")}"></script>'''
    return shell("ボードゲーム診断","6問で今日のメンバーに合うボードゲームを診断します。",body,"diagnosis/")


def games_index():
    rows=[]
    for g in GAMES:
        _,img,_=load_rakuten(g)
        attrs=f'data-pmin="{g["players_min"]}" data-pmax="{g["players_max"]}" data-short="{1 if g["play_time_max"]<=30 else 0}" data-family="{1 if g["family"]>=4 else 0}" data-beginner="{1 if g["beginner"]>=4 else 0}"'
        art=f'<img src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy" decoding="async">' if img else PLACEHOLDER
        rows.append(f'<a class="catalog-card game-list-card" {attrs} data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="games_index" href="{u("games/"+g["game_id"]+"/")}"><div class="catalog-media">{art}</div><div class="catalog-body"><strong>{e(g["title"])}</strong><p>{e(g["appeal"])}</p><div class="catalog-meta">{g["players_min"]}〜{g["players_max"]}人　／　{g["play_time_min"]}〜{g["play_time_max"]}分</div><div class="catalog-arrow">どんなゲーム？ <span aria-hidden="true">→</span></div></div></a>')
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / ゲーム一覧</div><div class="eyebrow">THE GAME SHELF</div><h1>次に遊びたい、50本。</h1><p>気になった1本から、遊びの世界をのぞいてみよう。</p></section><section class="section"><div class="filter-bar" role="group" aria-label="ゲームの絞り込み"><button class="filter-btn active" aria-pressed="true" data-filter="all">すべて</button><button class="filter-btn" aria-pressed="false" data-filter="two">2人で遊べる</button><button class="filter-btn" aria-pressed="false" data-filter="family">家族向け</button><button class="filter-btn" aria-pressed="false" data-filter="short">30分以内</button><button class="filter-btn" aria-pressed="false" data-filter="beginner">初心者向け</button></div><p class="small filter-count" id="filterCount" aria-live="polite">50本のゲーム</p><div class="games-catalog" id="gamesGrid">{"".join(rows)}</div></section><script>document.addEventListener("click",function(ev){{var b=ev.target.closest(".filter-btn");if(!b)return;document.querySelectorAll(".filter-btn").forEach(function(x){{x.classList.remove("active");x.setAttribute("aria-pressed","false")}});b.classList.add("active");b.setAttribute("aria-pressed","true");var f=b.dataset.filter,count=0;document.querySelectorAll(".game-list-card").forEach(function(c){{var show=f==="all"||(f==="two"&&Number(c.dataset.pmin)<=2&&Number(c.dataset.pmax)>=2)||(f==="family"&&c.dataset.family==="1")||(f==="short"&&c.dataset.short==="1")||(f==="beginner"&&c.dataset.beginner==="1");c.hidden=!show;if(show)count++}});document.getElementById("filterCount").textContent=count+"本のゲーム";kyoTrack("game_filter_use",{{filter:f}})}})</script>'''
    return shell("ゲーム一覧","きょうボド掲載50ゲーム。2人、家族、30分以内、初心者向けなどから絞って探せます。",body,"games/")


def game_page(g):
    r,img,label=load_rakuten(g)
    similar=sorted([x for x in GAMES if x["game_id"]!=g["game_id"]],key=lambda x:abs(x["strategy"]-g["strategy"])+abs(x["excitement"]-g["excitement"])+abs(x["players_min"]-g["players_min"]))[:3]
    axes=[("難しさ","difficulty"),("戦略性","strategy"),("運要素","luck"),("会話量","conversation"),("盛り上がり","excitement"),("協力度","cooperation"),("初心者向け","beginner")]
    axis="".join(f'<div class="axis"><span>{n}</span><span class="dots" aria-label="5段階中{g[k]}">{"●"*g[k]}{"○"*(5-g[k])}</span></div>' for n,k in axes)
    hero_art=f'<img src="{e(img)}" alt="{e(g["title"])}の商品画像" decoding="async">' if img else PLACEHOLDER
    availability='楽天の商品ページを取得済み' if img else '商品は未確定です。楽天検索でご確認ください。'
    scenes=' ／ '.join(e(z) for z in g["recommended_scene"])
    body=f'''<section class="game-detail-hero"><div class="game-hero-card"><div class="game-hero-copy"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("games/")}">ゲーム</a> / {e(g["title"])}</div><div class="eyebrow">LET'S PLAY</div><h1>{e(g["title"])}</h1><p>{e(g["appeal"])}</p><div class="game-fast-facts"><span><small>人数</small>{g["players_min"]}〜{g["players_max"]}人</span><span><small>時間</small>{g["play_time_min"]}〜{g["play_time_max"]}分</span><span><small>対象年齢</small>{g["age"]}歳〜</span></div></div><div class="game-hero-art">{hero_art}</div></div></section><section class="section"><div class="detail-layout"><div class="detail-story"><div class="eyebrow">AT THE TABLE</div><h2>どんな時間になる？</h2><p>{e(g["description"])}</p><div class="detail-summary"><div class="decision-box"><h3>こんな日に合う</h3><p>{e(fit_copy(g))}</p></div><div class="decision-box"><h3>今日は別候補でも</h3><p>{e(caution_copy(g))}</p></div></div><div class="eyebrow">ONE-MINUTE RULES</div><h2>1分で分かる遊び方</h2><ol class="howto">{"".join("<li>"+e(z)+"</li>" for z in g["how_to_play"])}</ol><h2>こんな場面で</h2><p class="recommended-scenes">{scenes}</p><details class="game-profile"><summary>ゲームの特徴を詳しく</summary>{axis}<p class="small">タイプ：{"協力寄り" if g["cooperation"]>=4 else "対戦・競争寄り"}</p></details></div><aside><div class="product-panel"><div class="eyebrow">BRING IT TO YOUR TABLE</div><h2>このゲームを見てみる</h2><p class="small">版や対象年齢、在庫を確認して、今日のメンバーに合う1本を。</p><a class="btn rakuten large" data-affiliate="rakuten" data-game-id="{e(g["game_id"])}" data-source="game_detail" target="_blank" rel="sponsored noopener" href="{e(r)}">{label} <span aria-hidden="true">↗</span></a><div class="product-availability">{availability}</div><p class="small">PR：購入前に販売ページで版・対象年齢・在庫を確認してください。</p><a class="btn secondary" href="{u("diagnosis/?src=game_detail")}">診断で他の候補も見る</a></div></aside></div></section><section class="section related-section"><div class="section-lead"><div><div class="eyebrow">YOU MIGHT ALSO LIKE</div><h2>これと迷うなら</h2></div></div><div class="grid">{"".join(card(x,"similar") for x in similar)}</div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("game_detail_view",{{game_id:{json.dumps(g["game_id"])},page_path:location.pathname}})}})</script>'''
    game_url=canon("games/"+g["game_id"]+"/")
    schema=json.dumps({"@context":"https://schema.org","@graph":[
        {"@type":"WebPage","name":g["title"]+"｜きょうボド","description":g["description"],"url":game_url,"isPartOf":{"@type":"WebSite","name":"きょうボド","url":SITE_URL}},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"きょうボド","item":SITE_URL},
            {"@type":"ListItem","position":2,"name":"ゲーム一覧","item":canon("games/")},
            {"@type":"ListItem","position":3,"name":g["title"],"item":game_url}
        ]}
    ]},ensure_ascii=False)
    return shell(g["title"],g["appeal"],body,"games/"+g["game_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')


def scenes_index():
    selected={sid for sid,_,_,_ in MAIN_SCENES}
    more="".join(f'<a class="scene-directory-card" href="{u("scenes/"+x["scene_id"]+"/")}"><span><h3>{e(x["title"])}</h3><p>{e(x["intro"].split("。")[0])}。</p></span><span class="scene-arrow" aria-hidden="true">→</span></a>' for x in SCENES if x["scene_id"] not in selected)
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / シーン</div><div class="eyebrow">PLAY TOGETHER</div><h1>今日は、どんな集まり？</h1><p>一緒に遊ぶ人から。今日の気分から。ぴったりの入口を選ぼう。</p></section><section class="section">{scene_navigation()}<div class="scene-more-list">{more}</div></section><section class="section"><div class="eyebrow">CAN'T DECIDE?</div><h2>どれも気になるなら、診断で。</h2><p class="small">人数・気分・時間から、今日に合う候補を選びます。</p><a class="btn primary" href="{u("diagnosis/?src=scenes_index")}">今のメンバーで診断する <span aria-hidden="true">→</span></a></section>'''
    return shell("シーンから探す","2人、夫婦、家族、小学生、大人数、初心者、短時間、盛り上がる、協力などシーン別に探せます。",body,"scenes/")


def scene_page(s):
    ranked=sorted(GAMES,key=lambda g:scene_score(g,s),reverse=True)
    ranked=[g for g in ranked if scene_score(g,s)>=50][:12]
    scene_i=SCENE_ART[s["scene_id"]]
    body=f'''<section class="scene-page-hero" style="--scene-sprite:url('{asset("scene-sprite.webp")}')"><div class="scene-hero-card"><div class="scene-hero-copy"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("scenes/")}">シーン</a> / {e(s["title"])}</div><div class="eyebrow">PLAY TOGETHER</div><h1>{e(s["title"])}<br>ボードゲーム</h1><p>{e(s["intro"])}</p><a class="text-link" href="{u("diagnosis/?src=scene_page")}">このメンバーで診断する <span class="arrow" aria-hidden="true">→</span></a></div><div class="scene-art s{scene_i}" aria-hidden="true"></div></div></section><section class="section"><div class="scene-result-head"><div><div class="eyebrow">FOR THIS MOMENT</div><h2>このシーンに合う{len(ranked)}本</h2></div><span>おすすめ度の高い順に掲載</span></div><div class="grid">{"".join(card(g,"scene_page",i+1) for i,g in enumerate(ranked))}</div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("scene_view",{{scene_id:{json.dumps(s["scene_id"])},game_count:{len(ranked)}}})}})</script>'''
    schema=json.dumps({"@context":"https://schema.org","@type":"ItemList","name":s["title"]+"ボードゲーム","itemListElement":[{"@type":"ListItem","position":i+1,"url":canon("games/"+g["game_id"]+"/"),"name":g["title"]} for i,g in enumerate(ranked)]},ensure_ascii=False)
    return shell(s["title"]+"ボードゲーム",s["intro"],body,"scenes/"+s["scene_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')


def write(rel,text):
    p=SITE/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8")

def main():
    if SITE.exists(): shutil.rmtree(SITE)
    (SITE/"assets").mkdir(parents=True);(SITE/"data").mkdir(parents=True)
    shutil.copy2(ROOT/"assets/media.js",SITE/"assets/media.js")
    for verification in ROOT.glob("google*.html"): shutil.copy2(verification,SITE/verification.name)
    write("assets/styles.css",CSS);write("assets/analytics.js",ANALYTICS);write("assets/diagnosis.js",DIAGNOSIS);write("assets/today.js",TODAY)
    if HERO_ASSET.exists(): shutil.copy2(HERO_ASSET,SITE/"assets"/HERO_ASSET.name)
    if SCENE_ASSET.exists(): shutil.copy2(SCENE_ASSET,SITE/"assets"/SCENE_ASSET.name)
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
