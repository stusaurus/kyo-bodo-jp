#!/usr/bin/env python3
# Hero asset refresh: validated WebP source v2.
import hashlib, html, json, os, shutil, urllib.parse, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES, supports_players, player_label
from scripts.fetch_rakuten import match_item, valid_url
from scripts.two_player_quick_filter import format_play_time, render_two_player_quick_filter
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
# Revalidate fetched data at the publishing boundary as well as at acquisition.
RAKUTEN={gid:x for gid,x in RAKUTEN.items() if gid in {g["game_id"] for g in GAMES} and valid_url(x.get("url")) and valid_url(x.get("item_url")) and match_item(next(g for g in GAMES if g["game_id"]==gid),{"itemName":x.get("item_name","")})[0]}
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

SCENE_ART={"two-player":1,"solo":5,"couple":1,"family":2,"children":3,"friends":4,"large-group":4,"first-meeting":4,"drinking":4,"short":5,"long":1,"think":1,"laugh":4,"cooperative":6,"beginner":2}
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
// Only the published note campaign is recognized. Query strings, referrers,
// user identifiers and child ages are never added to custom analytics events.
var noteKey="kyo_bodo_note_entry_v1",noteEntry=null,noteLandingNew=false;
var campaign="two_player_trial_20261118",now=Date.now();
try{
  var saved=JSON.parse(sessionStorage.getItem(noteKey)||"null");
  if(saved&&saved.campaign===campaign&&saved.at>0&&now>=saved.at&&now-saved.at<30*60*1000){
    noteEntry=saved;
  }else{
    sessionStorage.removeItem(noteKey);
  }
  if(p.get("utm_source")==="note"&&p.get("utm_medium")==="referral"&&p.get("utm_campaign")===campaign){
    if(!noteEntry){
      noteEntry={campaign:campaign,content:p.get("utm_content")==="coop_guide"?"coop_guide":"unspecified",landing_path:location.pathname,at:now};
      sessionStorage.setItem(noteKey,JSON.stringify(noteEntry));
      noteLandingNew=true;
    }
  }
}catch(_){}
window.dataLayer=window.dataLayer||[];window.gtag=window.gtag||function(){dataLayer.push(arguments)};
if(id){var s=document.createElement("script");s.async=true;s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(id);document.head.appendChild(s);gtag("js",new Date());gtag("config",id,{operator_test:op?"1":"0"})}
window.kyoTrack=function(name,data){data=data||{};data.page_path=location.pathname;data.operator_test=op?"1":"0";
if(noteEntry&&Date.now()-noteEntry.at<30*60*1000){
  data.entry_channel="note_campaign";
  data.entry_campaign=noteEntry.campaign;
  data.entry_content=noteEntry.content;
}
try{var ctx=JSON.parse(sessionStorage.getItem("kyo_bodo_journey")||"{}");if(data.conversion_source)ctx.conversion_source=data.conversion_source;if(name==="diagnosis_complete"){ctx.journey="diagnosis";ctx.players=data.players;ctx.mood=data.mood;ctx.desired_time=data.desired_time;}if(name==="scene_view"){ctx.journey="scene";ctx.scene_id=data.scene_id;}if(data.game_id)ctx.game_id=data.game_id;sessionStorage.setItem("kyo_bodo_journey",JSON.stringify(ctx));Object.keys(ctx).forEach(function(k){if(data[k]===undefined)data[k]=ctx[k]})}catch(_){}
if(name==="catalog_compare_use"){
  // Journey context may contain previously viewed game IDs. Keep only safe,
  // explicitly permitted fields for an anonymous two-title comparison.
  data={compared_count:data.compared_count===2?2:0,page_path:location.pathname,operator_test:op?"1":"0"};
  if(noteEntry&&Date.now()-noteEntry.at<30*60*1000){
    data.entry_channel="note_campaign";
    data.entry_campaign=noteEntry.campaign;
    data.entry_content=noteEntry.content;
  }
}
gtag("event",name,data)};
// Report a UTM-tagged note landing once per tab/session, not every reload.
// This is campaign attribution, not proof of a verified human or purchase.
if(noteLandingNew)window.kyoTrack("note_campaign_landing",{landing_path:location.pathname});
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
        return x["url"],image,("楽天で予約状況を確認" if x.get("preorder") else "楽天で見る")
    q=urllib.parse.quote(g.get("rakuten_query") or g["title"])
    return "https://search.rakuten.co.jp/search/mall/"+q+"/","","楽天で探す"


def outgoing_tracking(g):
    """Only confirmed product links count as potential affiliate referrals.

    An unresolved game goes to a plain Rakuten search, not an affiliate offer.
    """
    verified = bool(RAKUTEN.get(g["game_id"], {}).get("url"))
    return ('data-affiliate="rakuten"', 'sponsored noopener') if verified else ('data-track="rakuten_search_click"', 'noopener')


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
    if g.get("cooperation",0)>=4: return "みんなで同じ目標に挑み、一緒に達成したい日に。"
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
    full=(f"きょうボド｜今日なにやる？ ボードゲーム診断とおすすめ{len(GAMES)}本" if title=="きょうボド" else title+"｜きょうボド")
    cfg=json.dumps({"basePath":BASE,"gaMeasurementId":GA},ensure_ascii=False)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{e(canon(path))}"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(canon(path))}"><meta property="og:type" content="website"><meta property="og:image" content="{e(canon("assets/hero-kyo-bodo.webp"))}"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#fffaf2"><link rel="stylesheet" href="{asset("styles.css")}">{extra}<script>window.KYO_BODO_CONFIG={cfg};</script><script defer src="{u("assets/analytics.js")}"></script><script defer src="{asset("media.js")}"></script></head><body><header class="site-header"><div class="header-inner"><a class="brand" href="{u()}" aria-label="きょうボド ホーム">{BRAND_MARK}<span><span class="brand-word">きょう<em>ボド</em></span><span class="brand-sub">今日なにやる？</span></span></a><nav aria-label="メインナビゲーション"><a href="{u("diagnosis/")}">診断</a><a href="{u("scenes/")}">シーン</a><a href="{u("games/")}">ゲーム一覧</a></nav></div></header><main>{body}</main><footer><div class="footer-inner"><div class="footer-brand">きょうボド <span class="small">今日なにやる？</span></div><div class="footer-nav"><a href="{u("diagnosis/")}">診断する</a><a href="{u("scenes/")}">シーンから探す</a><a href="{u("games/")}">{len(GAMES)}本のゲームを見る</a></div><p>掲載情報はゲーム選びの参考情報です。対象年齢・人数・ルール・在庫は商品版や販売店で最終確認してください。</p><p>当サイトはアフィリエイト広告を利用する場合があります。</p></div></footer></body></html>'''


def edition_note(g):
    return f'<p class="small">比較対象：{e(g["edition"])}</p>' if g.get('edition') else ''


def card(g,source="list",rank=""):
    r,img,label=load_rakuten(g)
    tracking_attr, link_rel = outgoing_tracking(g)
    art=f'<img class="game-thumb" src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy" decoding="async">' if img else PLACEHOLDER
    return f'''<article class="game-card"><div class="game-media">{art}</div><div class="game-card-body"><h3>{e(g["title"])}</h3><p>{e(g["appeal"])}</p>{edition_note(g)}<div class="card-meta"><span>{e(player_label(g))}</span><span>{format_play_time(g)}</span><span>{g["age"]}歳〜</span></div><div class="card-actions"><a class="text-link" data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="{e(source)}" data-rank="{e(rank)}" href="{u("games/"+g["game_id"]+"/")}">どんなゲーム？ <span class="arrow" aria-hidden="true">→</span></a><a class="btn secondary" {tracking_attr} data-game-id="{e(g["game_id"])}" data-source="{e(source)}" data-rank="{e(rank)}" target="_blank" rel="{link_rel}" href="{e(r)}">{label}</a></div></div></article>'''


def scene_score(g,s):
    r=s["rule"];t=r["type"]
    sid=s["scene_id"]
    if sid=="cooperative" and not g["cooperative"]: return 0
    if sid=="large-group" and not supports_players(g,max(5,g["players_min"])): return 0
    if sid=="couple" and not supports_players(g,2): return 0
    if sid=="children" and g["age"]>12: return 0
    if sid=="short" and g["play_time_max"]>20: return 0
    if t=="players": return 100 if supports_players(g,r["value"]) else 0
    if t=="field": return g.get(r["field"],0)*20
    if t=="tag": return 100 if r["tag"] in g.get("tags",[]) else 0
    if t=="formula": return sum(g.get(f,0) for f in r["fields"])/len(r["fields"])*20
    if t=="long": return min(100,max(0,(g["play_time_max"]-20)*2+g["strategy"]*7))
    return 0

def home():
    pop="".join(card(BY_ID[x],"popular") for x in ["ito","catan","splendor"])
    solo_count=sum(1 for game in GAMES if supports_players(game,1))
    body=f'''<section class="hero"><div class="hero-shell"><div class="hero-copy"><div class="hero-message"><p class="hero-eyebrow">みんなで遊ぶと、今日がちょっと特別に。</p><h1><span>今日</span>なにやる？</h1><p class="hero-summary">まずは今日のおすすめから。<span>もっと絞りたい人だけ、人数・時間で診断。</span></p></div><div class="hero-action-block"><div class="hero-actions"><a class="btn primary large" href="#today-games">おすすめ3本を先に見る <span aria-hidden="true">↓</span></a><a class="btn secondary" href="{u("diagnosis/?src=hero")}">人数・時間でもっと絞る <span aria-hidden="true">→</span></a></div><p class="hero-note">診断しなくても選べます　／　診断は任意・6問　／　登録不要</p></div></div><figure class="hero-visual"><img src="{asset("hero-kyo-bodo.webp")}" alt="暖かな光の中で、家族がテーブルを囲んでボードゲームを楽しむイラスト" width="1536" height="1024" fetchpriority="high" decoding="async"></figure></div></section>
<section class="today-section" id="today-games" aria-label="今日のおすすめ商品"><div class="today-inner"><div class="section-lead"><div><div class="eyebrow">TODAY'S PICKS</div><h2>今日のおすすめ3本</h2></div><p class="section-sub">いつもの時間に、ひとつ遊びを。</p></div><div id="todayChoiceControls" hidden aria-label="今日の遊び方で絞り込む"></div><div id="todayGames" aria-live="polite"><p class="small">本日のおすすめを更新中。まずは定番の3本から選べます。</p><div class="grid popular-grid">{pop}</div></div><section class="today-saved-games" id="todaySavedGames" hidden aria-label="あとで比べるゲーム"></section></div></section>
<section class="section scene-section" id="scenes"><div class="section-lead"><div><div class="eyebrow">PLAY TOGETHER</div><h2>今日は、誰と遊ぶ？</h2></div><a class="text-link" href="{u("scenes/")}">すべてのシーン <span class="arrow" aria-hidden="true">→</span></a></div>{scene_navigation()}<p class="scene-growth-link">ひとりで遊ぶ日には、<a href="{u("scenes/solo/")}">1人対応の全{solo_count}本を遊び方・時間から見比べる</a>こともできます。ソロ用ルールは購入する版で確認してください。</p><p class="scene-growth-link">2人で遊ぶ予定なら、<a href="{u("scenes/two-player/")}">2人用ボードゲームの対戦・協力と遊び方を比べる</a>ところから。</p><p class="scene-growth-link">2人で同じ目標を目指すなら、<a href="{u("guides/two-player-cooperative/")}">協力ゲームを会話のしかた・時間から比べる</a>こともできます。</p></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">FIND YOUR GAME</div><h2>「選ぶ」時間を短くする</h2></div></div><div class="steps"><div class="step-card"><span class="step-no">01</span><h3>今のメンバーを教えて</h3><p>人数・時間・気分を、6問で。</p></div><div class="step-card"><span class="step-no">02</span><h3>今日に合う候補が見つかる</h3><p>あなたたちに合う5本をご提案。</p></div><div class="step-card"><span class="step-no">03</span><h3>1分ルールで、遊ぶ姿を想像</h3><p>楽しそうと思ったら、その1本を。</p></div></div><div class="steps-action"><a class="text-link" href="{u("diagnosis/?src=how_it_works")}">今日の1本を診断する <span class="arrow" aria-hidden="true">→</span></a></div></section>
<section class="section"><div class="section-lead"><div><div class="eyebrow">TIMELESS FAVORITES</div><h2>迷ったら、この定番から</h2></div><a class="text-link" href="{u("games/")}">{len(GAMES)}本のゲーム <span class="arrow" aria-hidden="true">→</span></a></div><div class="grid popular-grid">{pop}</div></section><script defer src="{asset("decision-insights.js")}"></script><script defer src="{asset("today.js")}"></script>'''
    return shell("きょうボド","ボードゲーム選びに迷ったら。人数・気分・時間の6問から、今日のメンバーに合う5本を30秒で診断。1分ルールで遊び方まで分かります。",body)


def diagnosis():
    body=f'''<section class="page-hero diagnosis-header"><div class="eyebrow">FIND YOUR GAME</div><h1 class="diagnosis-heading">今日の遊びを、見つけよう。</h1><p class="diagnosis-subtitle">6問だけ。今のメンバーと、今の気分で。</p></section><section class="diagnosis-wrap" style="--scene-sprite:url('{asset("scene-sprite.webp")}')"><div id="diagnosisApp" aria-busy="true"><p class="small">診断を読み込んでいます…</p></div><noscript><p>診断にはJavaScriptが必要です。<a href="{u("scenes/")}">シーンからゲームを探す</a>こともできます。</p></noscript></section><script defer src="{asset("diagnosis.js")}"></script>'''
    return shell("ボードゲーム診断","6問で今日のメンバーに合うボードゲームを診断します。",body,"diagnosis/")


def games_index():
    options = '<option value="">作品を選んでください</option>' + ''.join(
        f'<option value="{e(g["game_id"])}">{e(g["title"])}</option>' for g in GAMES
    )
    rows=[]
    for g in GAMES:
        _,img,_=load_rakuten(g)
        attrs=f'data-search-title="{e(g["title"])}" data-pmin="{g["players_min"]}" data-pmax="{g["players_max"]}" data-two="{1 if supports_players(g,2) else 0}" data-solo="{1 if supports_players(g,1) else 0}" data-short="{1 if g["play_time_max"]<=30 else 0}" data-family="{1 if g["family"]>=4 else 0}" data-beginner="{1 if g["beginner"]>=4 else 0}"'
        art=f'<img src="{e(img)}" alt="{e(g["title"])}の商品画像" loading="lazy" decoding="async">' if img else PLACEHOLDER
        rows.append(f'<a class="catalog-card game-list-card" {attrs} data-track="game_detail_click" data-game-id="{e(g["game_id"])}" data-source="games_index" href="{u("games/"+g["game_id"]+"/")}"><div class="catalog-media">{art}</div><div class="catalog-body"><strong>{e(g["title"])}</strong><p>{e(g["appeal"])}</p>{edition_note(g)}<div class="catalog-meta">{e(player_label(g))}　／　{format_play_time(g)}</div><div class="catalog-arrow">どんなゲーム？ <span aria-hidden="true">→</span></div></div></a>')
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / ゲーム一覧</div><div class="eyebrow">THE GAME SHELF</div><h1>次に遊びたい、{len(GAMES)}本。</h1><p>気になった1本から、遊びの世界をのぞいてみよう。</p></section><section class="section"><div class="catalog-search"><label for="catalogTitleSearch">作品名から探す</label><input id="catalogTitleSearch" type="search" autocomplete="off" placeholder="例：ナナトリドリ・カタン" aria-controls="gamesGrid" aria-describedby="filterCount"><button type="button" id="catalogSearchReset" hidden>検索を消す</button></div><div class="filter-bar" role="group" aria-label="ゲームの絞り込み"><button class="filter-btn active" aria-pressed="true" data-filter="all">すべて</button><button class="filter-btn" aria-pressed="false" data-filter="solo">1人で遊べる</button><button class="filter-btn" aria-pressed="false" data-filter="two">2人で遊べる</button><button class="filter-btn" aria-pressed="false" data-filter="family">家族向け</button><button class="filter-btn" aria-pressed="false" data-filter="short">30分以内</button><button class="filter-btn" aria-pressed="false" data-filter="beginner">初心者向け</button></div><section class="catalog-compare" id="catalogCompare" hidden aria-labelledby="catalogCompareHeading"><div class="catalog-compare-intro"><div class="eyebrow">COMPARE TWO</div><h2 id="catalogCompareHeading">気になる2作品を、同じ項目で比べる</h2><p>人数・時間・対象年齢・遊び方を比較。人気順や販売価格の比較ではありません。</p></div><div class="catalog-compare-controls"><label for="catalogCompareFirst">1作品目<select id="catalogCompareFirst">{options}</select></label><label for="catalogCompareSecond">2作品目<select id="catalogCompareSecond">{options}</select></label></div><div id="catalogCompareResult" role="status" aria-live="polite"><p class="small">2作品を選ぶと比較できます。</p></div><p class="small catalog-compare-footnote">対象人数・時間・年齢は掲載版の情報、戦略性・協力度は当サイト独自の編集目安です。購入前に商品版の仕様をご確認ください。</p></section><noscript><p class="small">2作品の比較にはJavaScriptが必要です。作品一覧はそのままご覧いただけます。</p></noscript><p class="small filter-count" id="filterCount" aria-live="polite">{len(GAMES)}本のゲーム</p><p id="catalogEmpty" class="small" hidden>条件に合う作品が見つかりません。検索語や分類を変更してください。</p><div class="games-catalog" id="gamesGrid">{"".join(rows)}</div></section><script defer src="{asset("catalog-search.js")}"></script><script defer src="{asset("catalog-compare.js")}"></script>'''
    return shell("ゲーム一覧",f"きょうボド掲載{len(GAMES)}ゲーム。2人、家族、30分以内、初心者向けなどから絞って探せます。",body,"games/")


def game_page(g):
    r,img,label=load_rakuten(g)
    tracking_attr, link_rel = outgoing_tracking(g)
    similar=sorted([x for x in GAMES if x["game_id"]!=g["game_id"]],key=lambda x:(0 if x["cooperative"]==g["cooperative"] else 10)+abs(x["strategy"]-g["strategy"])+abs(x["excitement"]-g["excitement"])+abs(x["players_min"]-g["players_min"]))[:3]
    axes=[("難しさ","difficulty"),("戦略性","strategy"),("運要素","luck"),("会話量","conversation"),("盛り上がり","excitement"),("協力度","cooperation"),("初心者向け","beginner")]
    axis="".join(f'<div class="axis"><span>{n}</span><span class="dots" aria-label="5段階中{g[k]}">{"●"*g[k]}{"○"*(5-g[k])}</span></div>' for n,k in axes)
    hero_art=f'<img src="{e(img)}" alt="{e(g["title"])}の商品画像" decoding="async">' if img else PLACEHOLDER
    verified_offer = bool(RAKUTEN.get(g["game_id"], {}).get("url"))
    availability = (
        "楽天の商品ページに予約表示があります。受付状況・発送予定・キャンセル条件は販売店でご確認ください。"
        if verified_offer and RAKUTEN[g["game_id"]].get("preorder") else
        "楽天の商品ページを取得済み。販売店で最新の在庫・価格をご確認ください。"
        if verified_offer else
        "掲載作品と一致する販売商品を確認できていません。楽天市場の通常検索へ移動します。"
    )
    purchase_notice = (
        "PR：購入前に販売ページで版・対象年齢・在庫を確認してください。"
        if verified_offer else
        "検索結果には別作品・拡張版・中古品が含まれる場合があります。"
        "作品名・版・商品の状態・対象年齢を確認してください。"
    )
    scenes=' ／ '.join(f'<a href="{u("scenes/"+z["scene_id"]+"/")}">{e(z["title"])}</a>' for z in SCENES if scene_score(g,z)>=80)
    source_note = (f'<p class="small">人数・所要時間・対象年齢の確認元：'
                   f'<a href="{e(g["specs_source"])}" target="_blank" rel="noopener noreferrer">'
                   f'取扱元の商品情報</a></p>') if g.get("specs_source") else ""
    body=f'''<section class="game-detail-hero"><div class="game-hero-card"><div class="game-hero-copy"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("games/")}">ゲーム</a> / {e(g["title"])}</div><div class="eyebrow">LET'S PLAY</div><h1>{e(g["title"])}</h1><p>{e(g["appeal"])}</p>{edition_note(g)}<div class="game-fast-facts"><span><small>人数</small>{e(player_label(g))}</span><span><small>時間</small>{format_play_time(g)}</span><span><small>対象年齢</small>{g["age"]}歳〜</span></div>{source_note}</div><div class="game-hero-art">{hero_art}</div></div></section><section class="section"><div class="detail-layout"><div class="detail-story"><div class="eyebrow">AT THE TABLE</div><h2>どんな時間になる？</h2><p>{e(g["description"])}</p><div class="detail-summary"><div class="decision-box"><h3>こんな日に合う</h3><p>{e(fit_copy(g))}</p></div><div class="decision-box"><h3>今日は別候補でも</h3><p>{e(caution_copy(g))}</p></div></div><div class="eyebrow">ONE-MINUTE RULES</div><h2>1分で分かる遊び方</h2><ol class="howto">{"".join("<li>"+e(z)+"</li>" for z in g["how_to_play"])}</ol><h2>こんな場面で</h2><p class="recommended-scenes">{scenes}</p><details class="game-profile"><summary>ゲームの特徴を詳しく</summary><p class="small">5段階の特徴はゲーム選びのための編集評価です。公式の難易度・評価ではありません。</p>{axis}<p class="small">タイプ：{"協力寄り" if g["cooperation"]>=4 else "対戦・競争寄り"}</p></details></div><aside><div class="product-panel"><div class="eyebrow">BRING IT TO YOUR TABLE</div><h2>このゲームを見てみる</h2><p class="small">版や対象年齢、在庫を確認して、今日のメンバーに合う1本を。</p><a class="btn rakuten large" {tracking_attr} data-game-id="{e(g["game_id"])}" data-source="game_detail" target="_blank" rel="{link_rel}" href="{e(r)}">{label} <span aria-hidden="true">↗</span></a><div class="product-availability">{availability}</div><p class="small">{purchase_notice}</p><a class="btn secondary" href="{u("diagnosis/?src=game_detail")}">診断で他の候補も見る</a></div></aside></div></section><section class="section related-section"><div class="section-lead"><div><div class="eyebrow">YOU MIGHT ALSO LIKE</div><h2>これと迷うなら</h2></div></div><div class="grid">{"".join(card(x,"similar",i+1) for i,x in enumerate(similar))}</div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("game_detail_view",{{game_id:{json.dumps(g["game_id"])},page_path:location.pathname}})}})</script>'''
    game_url=canon("games/"+g["game_id"]+"/")
    schema=json.dumps({"@context":"https://schema.org","@graph":[
        {"@type":"WebPage","name":g["title"]+"｜きょうボド","description":g["description"],"url":game_url,"isPartOf":{"@type":"WebSite","name":"きょうボド","url":SITE_URL}},
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"きょうボド","item":SITE_URL},
            {"@type":"ListItem","position":2,"name":"ゲーム一覧","item":canon("games/")},
            {"@type":"ListItem","position":3,"name":g["title"],"item":game_url}
        ]}
    ]},ensure_ascii=False)
    seo_title = g["title"] + "｜遊び方・人数・時間を1分で確認"
    seo_desc = g["title"] + "の遊び方を1分で確認。プレイ人数・時間・対象年齢、どんな日に合うか、似ているゲームまで分かります。" 
    return shell(seo_title,seo_desc,body,"games/"+g["game_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')


def scenes_index():
    selected={sid for sid,_,_,_ in MAIN_SCENES}
    more="".join(f'<a class="scene-directory-card" href="{u("scenes/"+x["scene_id"]+"/")}"><span><h3>{e(x["title"])}</h3><p>{e(x["intro"].split("。")[0])}。</p></span><span class="scene-arrow" aria-hidden="true">→</span></a>' for x in SCENES if x["scene_id"] not in selected)
    body=f'''<section class="page-hero"><div class="breadcrumb"><a href="{u()}">ホーム</a> / シーン</div><div class="eyebrow">PLAY TOGETHER</div><h1>今日は、どんな集まり？</h1><p>一緒に遊ぶ人から。今日の気分から。ぴったりの入口を選ぼう。</p></section><section class="section">{scene_navigation()}<div class="scene-more-list">{more}</div></section><section class="section"><div class="eyebrow">CAN'T DECIDE?</div><h2>どれも気になるなら、診断で。</h2><p class="small">人数・気分・時間から、今日に合う候補を選びます。</p><a class="btn primary" href="{u("diagnosis/?src=scenes_index")}">今のメンバーで診断する <span aria-hidden="true">→</span></a></section>'''
    return shell("シーンから探す","2人、夫婦、家族、小学生、大人数、初心者、短時間、盛り上がる、協力などシーン別に探せます。",body,"scenes/")


def scene_selection_guide(s, ranked):
    """Explain why real catalog titles were shortlisted, linking only existing pages."""
    tips = {
        'two-player': '2人対応のゲームでも所要時間や会話量は異なります。短時間で遊ぶか、じっくり考えるかを先に決めると選びやすくなります。',
        'family': '一番小さい参加者の対象年齢と、実際の参加人数を先に確認しましょう。慣れていない人がいる日は遊び方の説明も比較してください。',
        'children': '対象年齢の表記は商品版の目安です。読み書きの量や待ち時間なども確認し、大人と子どもが一緒に参加しやすい1本を探しましょう。',
        'short': 'プレイ時間には説明や準備の時間が含まれないことがあります。予定の時間に余裕を持たせて選びましょう。',
        'large-group': '最大人数に入るだけでなく、全員が同時に参加しやすいか、順番待ちが長くならないかを確認しましょう。',
        'solo': '1人に対応する作品でも、ソロ用のルールや遊ぶ手順が通常と異なる場合があります。購入する版で1人用ルールと所要時間を確認してください。',
        'cooperative': '協力ゲームでも相談の多さや難しさは違います。全員が意思決定に参加できる内容かを確認しましょう。',
    }
    tip = tips.get(s['scene_id'], '参加する人数、対象年齢、所要時間と遊び方を先に比較してください。好みが分かれる場合は診断でも候補を見直せます。')
    picks = ''.join(
        f'<li><a href="{u("games/" + g["game_id"] + "/")}">{e(g["title"])}</a>'
        f' — {e(player_label(g))}／{format_play_time(g)}／対象{g["age"]}歳〜。'
        f' {e(g["appeal"])}</li>'
        for g in ranked[:3]
    )
    choices = f'<h3>掲載データから見比べる3本</h3><ol>{picks}</ol>'
    if s['scene_id'] == 'two-player':
        # Use the full catalog, not the first 12 cards. These are factual
        # conditions, not popularity or editorial quality rankings.
        eligible = [g for g in GAMES if supports_players(g, 2)]
        groups = (
            ('人数表記が2人のゲーム', [g for g in eligible
              if g['players_min'] == g['players_max'] == 2]),
            ('2人対応・15分以内で遊べるゲーム', [g for g in eligible
              if g['play_time_max'] <= 15]),
            ('2人対応・20分以内で協力するゲーム', [g for g in eligible
              if g['cooperative'] and g['play_time_max'] <= 20]),
        )
        sections = []
        for label, games in groups:
            items = ''.join(
                f'<li data-choice-game="{e(g["game_id"])}"><a data-track="game_detail_click" '
                f'data-game-id="{e(g["game_id"])}" data-source="two_player_choices" '
                f'href="{u("games/" + g["game_id"] + "/")}">{e(g["title"])}</a>'
                f' — {e(player_label(g))}／{format_play_time(g)}'
                f'／対象{g["age"]}歳〜／{"協力" if g["cooperative"] else "対戦"}。'
                f' {e(g["appeal"])}'
                '<details class="choice-rules"><summary>遊び方の手順を読む</summary><ol>'
                + ''.join(f'<li>{e(step)}</li>' for step in g['how_to_play'])
                + '</ol></details></li>' for g in games
            )
            sections.append(f'<details class="two-player-choices"><summary>{label}（{len(games)}本）</summary>'
                            f'<ul>{items}</ul></details>')
        choices = ('<div id="two-player-choices"><h3>人数と遊び方から候補を選ぶ</h3>'
                   '<p>下の12本以外も含め、掲載カタログ全体から条件に合うゲームを探せます。'
                   '15分以内の候補もカタログの所要時間上限から選べます。'
                   '見出しを開くと、時間・対象年齢・遊び方と詳しい説明へのリンクが表示されます。</p>'
                   '<p>初めて遊ぶときは「遊び方の手順」を開いて、何をするゲームか比べてください。'
                   '掲載時間とは別に、説明・準備の時間も見込んでください。</p>'
                   + ''.join(sections) +
                   '<p class="small">各条件内はカタログ掲載順で、人気順・優劣の順位ではありません。'
                   '複数条件に同じゲームが入ることがあります。人数表記が2人でも、'
                   '2人以上に対応するゲームより優れているという意味ではありません。</p></div>')
    related = {
        'two-player': ('couple', 'short'),
        'solo': ('think', 'short'),
        'family': ('children', 'cooperative'),
        'children': ('family', 'beginner'),
        'short': ('two-player', 'beginner'),
        'large-group': ('friends', 'first-meeting'),
        'cooperative': ('family', 'children'),
    }.get(s['scene_id'], ('two-player', 'family'))
    related_links = ''.join(
        f'<a class="text-link" href="{u("scenes/" + x["scene_id"] + "/")}">{e(x["title"])}から探す →</a> '
        for x in SCENES if x['scene_id'] in related and x['scene_id'] != s['scene_id']
    )
    return f'''<section class="section scene-selection-guide">
<div class="eyebrow">HOW TO CHOOSE</div>
<h2>{e(s['title'])}ときの選び方</h2>
<p>{e(tip)}</p>
{choices}
<p class="small">人数・時間・対象年齢は掲載ゲームデータの参考値です。実際の版・ルールは販売店やメーカーで確認してください。</p>
<nav aria-label="別の遊び方から探す">{related_links}</nav>
</section>'''


def scene_comparison_table(s, ranked):
    # Only the two pilot entry pages; retain their existing ranking and catalog.
    if s['scene_id'] not in ('two-player', 'short', 'solo'):
        return ''
    rows = []
    for game in ranked:
        mode = 'ソロ対応（版のルールを要確認）' if s['scene_id'] == 'solo' else ('協力' if game['cooperative'] else '対戦')
        players = e(player_label(game))
        if game.get('players_source'):
            players += f'<br><a href="{e(game["players_source"])}" target="_blank" rel="noopener">人数の公式情報</a>'
        format_cell = ('<td>2人専用の人数表記</td>' if game['players_min'] == game['players_max'] == 2
                       else '<td>2人を含む複数人数対応</td>') if s['scene_id'] == 'two-player' else ''
        mechanic_cell = (f'<td>{e(game["how_to_play"][1])}</td>'
                         if s['scene_id'] == 'two-player' else '')
        rows.append(f'<tr><th scope="row"><a href="{u("games/" + game["game_id"] + "/")}">{e(game["title"])}</a>{edition_note(game)}</th>{mechanic_cell}<td>{players}</td>{format_cell}<td>{format_play_time(game)}</td><td>{game["age"]}歳〜</td><td>{mode}</td></tr>')
    note = ('掲載人数が2人だけのゲームと、2人を含む複数人数に対応するゲームを、同じ表で比較できます。2人専用の人数表記は「2人のときに必ず優れている」という意味ではありません。時間・対象年齢・協力／対戦も一緒に確認してください。'
            if s['scene_id'] == 'two-player' else ('1人対応の登録情報をもとにした作品一覧です。ソロ用ルールは通常の複数人用ルールと異なる場合があります。版のメーカー情報をご確認ください。' if s['scene_id'] == 'solo' else 'このページは掲載データの上限が20分以内のゲームに絞っています。説明・準備・片付けの時間は別に見込んでください。'))
    compare_id = ' id="two-player-comparison"' if s['scene_id'] == 'two-player' else ''
    format_heading = '<th scope="col">2人専用／複数人数対応</th>' if s['scene_id'] == 'two-player' else ''
    mode_heading = '1人対応の確認' if s['scene_id'] == 'solo' else '協力／対戦'
    mechanic_heading = '<th scope="col">何をする？</th>' if s['scene_id'] == 'two-player' else ''
    return f'''<section class="section scene-quick-comparison"{compare_id}><div class="eyebrow">COMPARE AT A GLANCE</div><h2>人数・時間・遊び方を早見表で比較</h2><p>{note}</p>
<p class="small">表は横にスクロールできます。</p><div class="scene-table-scroll" role="region" aria-label="ゲーム比較表。横にスクロールできます" tabindex="0"><table class="scene-data-table"><caption>このページの候補{len(ranked)}本。掲載順は下の商品カードと同じです。</caption><thead><tr><th scope="col">ゲーム・遊び方</th>{mechanic_heading}<th scope="col">人数</th>{format_heading}<th scope="col">時間目安</th><th scope="col">対象年齢</th><th scope="col">{mode_heading}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="small">人数・時間・対象年齢は掲載データの参考値です。購入前に販売されている版のメーカー表示を確認してください。</p><a class="text-link" href="{u("diagnosis/?src=scene_comparison")}">時間・気分も合わせて診断する →</a></section>'''


def two_player_rule_contrasts():
    """Short, source-backed differences in what two people actually do."""
    pairs = (
        ("対戦：短い時間でも、考え方が違う", ("gobblet-gobblers", "quarto")),
        ("協力：言葉で伝えるか、相談せず動くか", ("codenames-duet", "sky-team")),
    )
    cards = []
    for heading, ids in pairs:
        games = [BY_ID[gid] for gid in ids]
        if not all(supports_players(g, 2) for g in games):
            raise ValueError("2-player contrast includes an unsupported player count")
        if games[0]["cooperative"] != games[1]["cooperative"]:
            raise ValueError("2-player contrast mixes cooperative and versus games")
        entries = []
        for g in games:
            fmt = ("2人だけの人数表記" if g["players_min"] == g["players_max"] == 2
                   else "2人を含む複数人数対応")
            entries.append(
                f'<li><a href="{u("games/" + g["game_id"] + "/")}">'
                f'<strong>{e(g["title"])}</strong></a>'
                f'<span>{format_play_time(g)}・対象{g["age"]}歳〜・{fmt}</span>'
                f'<p>すること：{e(g["how_to_play"][1])}</p></li>'
            )
        cards.append('<article class="two-player-contrast-card"><h3>'
                     + e(heading) + '</h3><ul>' + ''.join(entries) + '</ul></article>')
    return ('''<section class="section two-player-contrast" aria-labelledby="two-player-contrast-title">
<div class="eyebrow">HOW THEY PLAY</div>
<h2 id="two-player-contrast-title">2人で遊べても、することはこんなに違う</h2>
<p>時間や協力・対戦が似ていても、遊びの動きは異なります。4作品をルールの一手で比較します。</p>
<div class="two-player-contrast-grid">''' + ''.join(cards) + '''</div>
<p class="small">掲載ゲームのルール・人数・時間・対象年齢を使った比較例で、人気・優劣の順位ではありません。
販売版の表示も確認してください。<a href="#two-player-comparison">12本の比較表へ</a></p>
</section>''')


def two_player_format_guide():
    """Help visitors choose using only the published player-count fields."""
    eligible = [g for g in GAMES if supports_players(g, 2)]
    only_two = [g for g in eligible if g['players_min'] == g['players_max'] == 2]
    other_sizes = [g for g in eligible if g not in only_two]

    def group(title, explanation, games, marker):
        # Catalog order is deliberately retained; these are not ranked picks.
        previews = ''.join(
            f'<li><a data-two-player-sample href="{u("games/" + g["game_id"] + "/")}">'
            f'{e(g["title"])}</a><span>{format_play_time(g)}・'
            f'{"協力" if g["cooperative"] else "対戦"}</span></li>'
            for g in games[:3]
        )
        return (f'<article class="two-player-format-card" data-format-group="{marker}">'
                f'<h3>{title} <small>{len(games)}本</small></h3>'
                f'<p>{explanation}</p><ul>{previews}</ul></article>')

    return ('''<section class="section two-player-format" data-two-player-format
aria-labelledby="two-player-format-title">
<div class="eyebrow">CHOOSE BY PLAYER COUNT</div>
<h2 id="two-player-format-title">2人だけ対応？ 2人でも遊べる？</h2>
<p>「2人用」には、掲載人数が2人だけの作品と、ほかの人数でも遊べる作品があります。
どちらも2人で遊べますが、人数表記だけで「2人で最も面白い」とは判断していません。</p>
<div class="two-player-format-grid">'''
            + group('掲載人数が2人だけ',
                    '2人で遊ぶ前提の人数表記です。プレイ時間や対戦・協力も確認しましょう。',
                    only_two, 'two-only')
            + group('2人を含む複数人数に対応',
                    '2人でも遊べ、別の人数で使える場合もあります。人数の上限は各商品で確認しましょう。',
                    other_sizes, 'multi')
            + '''</div>
<p class="small">各欄は掲載カタログ内の人数・時間・遊び方に基づく一部の例です。
人気ランキングではありません。詳細で対象年齢やルールを確認し、販売版のメーカー表記も確認してください。</p>
<p><a class="text-link" href="#two-player-comparison">2人対応の候補を表で比べる →</a>
<a class="text-link" href="#two-player-choices">条件別の候補をすべて見る →</a></p>
</section>''')


def scene_representatives(s, limit=12):
    """Factual two-player comparison examples, not a best-of ranking.

    A pure catalog-order prefix previously exposed zero strict two-person
    entries despite the page promising to compare those with multi-player
    games. Preserve catalog order *within each format*, and do not change
    which games are eligible for the full quick filter or diagnosis.
    """
    ranked = sorted(GAMES, key=lambda g: scene_score(g, s), reverse=True)
    eligible = [g for g in ranked if scene_score(g, s) >= 50]
    if s['scene_id'] == 'solo':
        # Show every one-player-compatible title, not an arbitrary 12-card prefix.
        return eligible
    if s['scene_id'] != 'two-player' or limit < 2:
        return eligible[:limit]
    only_two = [g for g in eligible if g['players_min'] == g['players_max'] == 2]
    multi = [g for g in eligible if g not in only_two]
    if not only_two or not multi:
        return eligible[:limit]

    # Representative balance: at most three strictly two-person examples,
    # alongside multi-player examples. This is not a quality or popularity
    # score; game entries retain their original per-format catalog order.
    chosen_two = only_two[:min(3, len(only_two), max(1, limit // 4))]
    chosen_multi = multi[:max(0, limit - len(chosen_two))]
    selected = []
    for index, game in enumerate(chosen_two):
        selected.append(game)
        selected.extend(chosen_multi[index * 3:(index + 1) * 3])
    selected.extend(chosen_multi[len(chosen_two) * 3:])
    if len(selected) < limit:
        existing_ids = {g['game_id'] for g in selected}
        selected.extend(g for g in eligible if g['game_id'] not in existing_ids)
    return selected[:limit]


def children_age_filter():
    """Compare factual age, participant count and maximum playtime without popularity claims.

    All catalog items for children-age filters are available as ordinary links,
    not just the 12 editorial scene cards. Initial results work without JS.
    """
    eligible = [g for g in GAMES if g["age"] <= 12
                and any(supports_players(g, n) for n in range(2, 7))]
    def initially_visible(g):
        return g["age"] <= 6 and supports_players(g, 2) and g["play_time_max"] <= 20
    initial_count = sum(1 for g in eligible if initially_visible(g))
    rows = []
    for g in eligible:
        players = " ".join(str(n) for n in range(2, 7) if supports_players(g, n))
        hidden = "" if initially_visible(g) else " hidden"
        rows.append(
            f'<li class="children-choice-item" data-child-game="{e(g["game_id"])}" '
            f'data-child-age="{g["age"]}" data-child-players="{players}" '
            f'data-child-minutes="{g["play_time_max"]}"{hidden}>'
            f'<a href="{u("games/" + g["game_id"] + "/")}" data-track="game_detail_click" '
            f'data-game-id="{e(g["game_id"])}" data-source="children_age_filter">'
            f'<strong>{e(g["title"])}</strong>'
            f'<span>{e(player_label(g))}／{format_play_time(g)}／対象{g["age"]}歳〜</span>'
            f'<small>すること：{e(g["how_to_play"][1])}</small>'
            '</a></li>'
        )
    nine_year_olds = [g for g in eligible if g["age"] == 9]
    nine_examples = "、".join(
        f'<a href="{u("games/" + g["game_id"] + "/")}">{e(g["title"])}</a>'
        for g in nine_year_olds
    )
    ages = "".join(
        f'<option value="{n}"' + (' selected' if n == 6 else '') + f'>{n}歳</option>'
        for n in range(6, 13)
    )
    players = "".join(
        f'<option value="{n}"' + (' selected' if n == 2 else '') + f'>{n}人</option>'
        for n in (2, 3, 4, 5, 6)
    )
    times = "".join(
        f'<option value="{n}"' + (' selected' if n == "20" else '') + f'>{label}</option>'
        for n, label in (("20", "20分以内"), ("30", "30分以内"), ("60", "60分以内"), ("any", "時間は指定しない"))
    )
    return f'''<section class="section children-choice" id="children-age-compare" aria-labelledby="children-choice-heading">
<div class="eyebrow">CHOOSE WITH CONFIDENCE</div>
<h2 id="children-choice-heading">6〜12歳の子どもの年齢・人数・時間から候補を絞る</h2>
<p>最年少の子どもの年齢を6〜12歳の1歳刻みで選べます。9歳なら「9歳」を指定すると、対象年齢が9歳以下の掲載作品を探せます。
参加する人数と遊べる時間も指定できます。表示するのは<strong>掲載データの対象年齢以下・人数対応・所要時間上限以内</strong>をすべて満たす作品です。
人気順や実際に遊んだ評価ではありません。</p>
<p class="small">たとえば「9歳から」の作品には{nine_examples}があります。両作品を含め、
実際に一緒に遊ぶ人数や制限時間で候補が変わります。表示しているのは製品の対象年齢で、
小学校の学年や9歳の子に必ず合うという保証ではありません。</p>
<form id="children-choice-form" aria-label="親子向けボードゲームの絞り込み" hidden>
<label for="children-age">最年少の子どもの年齢<select id="children-age" name="age">{ages}</select></label>
<label for="children-players">実際に遊ぶ人数（大人も含む）<select id="children-players" name="players">{players}</select></label>
<label for="children-time">遊べる時間の上限<select id="children-time" name="minutes">{times}</select></label>
<button id="children-choice-reset" type="button">6歳・2人・20分に戻す</button>
</form>
<p class="children-choice-count" role="status" aria-live="polite" aria-atomic="true">
条件に合う <strong id="children-choice-count">{initial_count}本</strong> ／ カタログ掲載順</p>
<ul class="children-choice-results" id="children-choice-results">{''.join(rows)}</ul>
<p class="children-choice-empty" id="children-choice-empty" hidden>この条件に合う掲載作品はありません。年齢はそのままに人数や時間を変えてみてください。</p>
<p class="small">対象年齢は「その年齢から遊べる目安」で、学年・理解度や一緒に遊ぶ大人の人数を保証するものではありません。
掲載の時間にはルール説明・準備・片付けが含まれない場合があります。
購入前に販売版の対象年齢・人数・ソロ用ルール・在庫を確認してください。</p>
<noscript><p class="small">条件変更にはJavaScriptが必要です。現在は6歳・2人・20分以内の候補を表示しています。
<a href="{u("games/")}">全作品から探す</a>こともできます。</p></noscript>
<script defer src="{asset("children-filter.js")}"></script>
</section>'''



def short_time_finder():
    """All catalogued games with a maximum stated playtime of 20 minutes.

    The scene's 12 example cards remain editorial examples; this independent
    list is a complete factual selection. No prices, popularity or live
    availability are inferred.
    """
    eligible = [g for g in GAMES if g["play_time_max"] <= 20]
    if not eligible:
        raise ValueError("Short-time finder has no eligible games")
    player_options = (1, 2, 3, 4, 5, 6, 8)
    rows = []
    for g in eligible:
        supported = " ".join(str(n) for n in player_options if supports_players(g, n))
        rows.append(
            f'<li data-short-game="{e(g["game_id"])}" '
            f'data-short-players="{supported}" '
            f'data-short-minutes="{g["play_time_max"]}" data-short-age="{g["age"]}">'
            f'<a data-track="game_detail_click" data-source="short_time_finder" '
            f'data-game-id="{e(g["game_id"])}" href="{u("games/" + g["game_id"] + "/")}">'
            f'<strong>{e(g["title"])}</strong>'
            f'<span>{e(player_label(g))}／{format_play_time(g)}／対象{g["age"]}歳〜'
            f'／{"協力" if g["cooperative"] else "対戦"}</span>'
            f'<small>すること：{e(g["how_to_play"][1])}</small>'
            '</a></li>'
        )
    minutes = "".join(f'<option value="{n}"' + (' selected' if n == 20 else '')
                      + f'>{n}分以内</option>' for n in (10, 15, 20))
    players = '<option value="any" selected>人数は指定しない</option>' + "".join(
        f'<option value="{n}">{n}人</option>' for n in player_options)
    ages = '<option value="any" selected>年齢は指定しない</option>' + "".join(
        f'<option value="{n}">{n}歳から</option>' for n in (6, 8, 10, 12, 14))
    return f'''<section class="section children-choice short-time-choice" id="short-time-finder"
aria-labelledby="short-time-finder-title">
<div class="eyebrow">CHOOSE BY TIME & GROUP</div>
<h2 id="short-time-finder-title">20分以内の掲載{len(eligible)}本から、人数と年齢でも選ぶ</h2>
<p>代表12本だけでなく、カタログ全{len(GAMES)}作品のうち
<strong>登録されている所要時間の上限が20分以内の全{len(eligible)}本</strong>を表示します。
実際に遊ぶ人数、最年少の参加者の年齢、10・15・20分の上限で絞れます。</p>
<form id="short-time-form" aria-label="短時間ボードゲームを人数・時間・対象年齢から絞り込む" hidden>
<label for="short-time-minutes">プレイ時間の上限<select id="short-time-minutes" name="minutes">{minutes}</select></label>
<label for="short-time-players">実際に遊ぶ人数<select id="short-time-players" name="players">{players}</select></label>
<label for="short-time-age">最年少の参加者の年齢<select id="short-time-age" name="age">{ages}</select></label>
<button type="button" id="short-time-reset">すべての20分以内の候補に戻す</button>
</form>
<p class="children-choice-count" role="status" aria-live="polite" aria-atomic="true">
条件に合う <strong id="short-time-count">{len(eligible)}本</strong> ／ カタログ掲載順</p>
<ul class="children-choice-results" id="short-time-results">{''.join(rows)}</ul>
<p class="children-choice-empty" id="short-time-empty" hidden>条件に合う掲載作品がありません。人数・年齢・時間の条件を変えてください。</p>
<p class="small">これは掲載仕様に基づく候補検索で、人気順・実際の試遊評価ではありません。
所要時間にはルール説明・準備・片付けが含まれない場合があります。
対象年齢や参加人数・製品版を販売元で最終確認してください。
年齢などの選択値は保存・送信しません。</p>
<noscript><p class="small">JavaScriptが無効な場合は、20分以内の全候補を表示します。
<a href="{u("games/")}">全作品の一覧</a>も利用できます。</p></noscript>
<script defer src="{asset("short-filter.js")}"></script>
</section>'''




def couple_choice_guide():
    """Offer three non-ranked couple-specific choices using published game facts."""
    paths = (
        ("まずは会話を楽しむ", "ito",
         "お題に合わせて数字の感覚を言葉で伝えるゲーム。相手の考えを知りたい日に。"),
        ("2人で協力して進める", "codenames-duet",
         "一言のヒントを手がかりに、2人で正解を探すゲーム。"),
        ("静かに考えて対戦する", "patchwork",
         "交互に布タイルを選び、空きスペースを埋めていくゲーム。"),
    )
    cards = []
    for title, gid, explanation in paths:
        game = BY_ID[gid]
        if not supports_players(game, 2):
            raise ValueError("Couple guide must contain only two-player compatible titles")
        cards.append(
            '<article class="couple-choice-card">'
            f'<h3>{e(title)}</h3>'
            f'<p>{e(explanation)}</p>'
            '<p class="couple-choice-facts">'
            f'{e(player_label(game))} ／ {format_play_time(game)} ／ 対象{game["age"]}歳〜</p>'
            f'<p class="small">遊び方の一手：{e(game["how_to_play"][1])}</p>'
            f'<a class="btn secondary" data-track="game_detail_click" '
            f'data-game-id="{e(gid)}" data-source="couple_choice" '
            f'href="{u("games/" + gid + "/")}">{e(game["title"])}の詳細を見る →</a>'
            '</article>'
        )
    return (
        '<section class="section couple-choice" id="couple-choose" '
        'aria-labelledby="couple-choose-title">'
        '<div class="eyebrow">CHOOSE YOUR TWO-PLAYER MOMENT</div>'
        '<h2 id="couple-choose-title">カップル・夫婦で、今日はどう遊ぶ？</h2>'
        '<p>2人で遊べる作品でも、会話・協力・対戦では過ごし方が違います。'
        'まず遊び方を1つ選び、人数・時間・対象年齢・ルールを確かめてください。</p>'
        '<div class="couple-choice-grid">' + ''.join(cards) + '</div>'
        '<p class="small">3作品は掲載データに基づく比較例で、人気順・実際の試遊評価ではありません。'
        '説明・準備の時間は別に見込み、購入する版の情報を確認してください。</p>'
        f'<p><a class="text-link" href="{u("scenes/two-player/")}">'
        '2人対応のほかの候補も比較する →</a> '
        f'<a class="text-link" href="{u("guides/two-player-cooperative/")}">'
        '2人で協力する作品を詳しく比較する →</a></p>'
        '</section>'
    )


def scene_page(s):
    ranked = scene_representatives(s)
    order_note = ('2人だけの人数表記と複数人数対応を組み合わせた比較例。'
                  '各グループ内はカタログ掲載順で、人気順・優劣の順位ではありません。'
                  if s['scene_id'] == 'two-player' else
                  '1人対応の全掲載候補をカタログ掲載順に表示。人気順・優劣の順位ではありません。' if s['scene_id'] == 'solo' else '2人対応の候補をカタログ掲載順に紹介。人気順・優劣の順位ではありません。'
                  if s['rule']['type'] == 'players' else
                  'シーン条件と編集評価による適合度順。同点はカタログ掲載順です。')
    scene_i=SCENE_ART[s["scene_id"]]
    choice_link = '<div><a class="text-link" href="#two-player-choices">2人向け・協力の候補から選ぶ →</a></div>' if s["scene_id"] == "two-player" else ""
    if s["scene_id"] == "two-player":
        choice_link += ('<nav aria-label="2人の条件を引き継いで診断">'
                       f'<a class="text-link" data-track="diagnosis_entry" href="{u("diagnosis/?src=two_player_short&preset=two-short")}">2人・15分以内で診断する →</a><br>'
                       f'<a class="text-link" data-track="diagnosis_entry" href="{u("diagnosis/?src=two_player_coop&preset=two-coop")}">2人で協力するゲームを診断 →</a>'
                       '<p class="small">条件を引き継ぎ、残り4問で候補を選べます。診断中に条件を変更できます。</p></nav>')

    if s["scene_id"] == "two-player":
        choice_link += (f'<p class="small"><a class="text-link" data-track="guide_entry" '
                        f'data-source="two_player_scene" href="{u("guides/two-player-cooperative/")}">'
                        '2人で協力する作品だけを時間・会話から比較 →</a></p>')

    if s["scene_id"] == "two-player":
        choice_link += (f'<p class="small"><a class="text-link" href="{u("scenes/couple/")}">'
                        '夫婦・カップルなら会話・協力・対戦から選ぶ →</a></p>')

    scene_h1 = ("2人用・2人でも遊べる" if s["scene_id"] == "two-player" else s["title"])
    body=f'''<section class="scene-page-hero" style="--scene-sprite:url('{asset("scene-sprite.webp")}')"><div class="scene-hero-card"><div class="scene-hero-copy"><div class="breadcrumb"><a href="{u()}">ホーム</a> / <a href="{u("scenes/")}">シーン</a> / {e(s["title"])}</div><div class="eyebrow">{"PLAY SOLO" if s["scene_id"] == "solo" else "PLAY TOGETHER"}</div><h1>{e(scene_h1)}<br>ボードゲーム</h1><p>{e(s["intro"])}</p><a class="text-link" href="{u("diagnosis/?src=scene_page")}">{"1人用を診断で探す" if s["scene_id"] == "solo" else "このメンバーで診断する"} <span class="arrow" aria-hidden="true">→</span></a>{choice_link}</div><div class="scene-art s{scene_i}" aria-hidden="true"></div></div></section>{render_two_player_quick_filter(GAMES,u,asset,player_label,supports_players) if s["scene_id"] == "two-player" else ""}{two_player_rule_contrasts() if s["scene_id"] == "two-player" else ""}{two_player_format_guide() if s["scene_id"] == "two-player" else ""}{children_age_filter() if s["scene_id"] == "children" else ""}{couple_choice_guide() if s["scene_id"] == "couple" else ""}{scene_comparison_table(s, ranked)}{short_time_finder() if s["scene_id"] == "short" else ""}{scene_selection_guide(s, ranked)}<section class="section"><div class="scene-result-head"><div><div class="eyebrow">FOR THIS MOMENT</div><h2>このシーンに合う{len(ranked)}本</h2></div><span>{order_note}</span></div><div class="grid">{"".join(card(g,"scene_page",i+1) for i,g in enumerate(ranked))}</div></section><script>document.addEventListener("DOMContentLoaded",function(){{kyoTrack("scene_view",{{scene_id:{json.dumps(s["scene_id"])},game_count:{len(ranked)}}})}})</script>'''
    schema=json.dumps({"@context":"https://schema.org","@type":"ItemList","name":s["title"]+"ボードゲーム","itemListElement":[{"@type":"ListItem","position":i+1,"url":canon("games/"+g["game_id"]+"/"),"name":g["title"]} for i,g in enumerate(ranked)]},ensure_ascii=False)
    seo={
        "two-player":("2人用ボードゲームおすすめ比較｜2人専用と2人対応の違い", "2人でできるボードゲームを2人専用と複数人数対応に分けて紹介。カップル・友人・夫婦で、遊べる時間・対戦か協力か・対象年齢を確認。人気順位ではありません。"),
        "couple":("カップル・夫婦で遊べる2人用ボードゲーム｜会話・協力・対戦で選ぶ", "カップル・夫婦で遊ぶボードゲームを会話・協力・対戦の3つの過ごし方から比較。2人対応を確認した作品の人数・時間・対象年齢・遊び方を見比べて選べます。"),
        "family":("家族で遊べるボードゲームおすすめ", "家族で遊べるボードゲームを紹介。小学生を含む家族でも選びやすいよう、人数・対象年齢・プレイ時間を確認できます。"),
        "children":("小学生と遊ぶボードゲーム｜6〜12歳・人数・時間で比較", "小学生と遊ぶボードゲームを、6〜12歳の1歳刻み（9歳を含む）、大人を含む2〜6人、プレイ時間上限から絞れます。対象年齢・遊び方を確認して選べます。"),
        "short":("20分以内・短時間で遊べるボードゲームおすすめ", "掲載時間が20分以内のボードゲームを紹介。平日夜やすきま時間に遊ぶ1本を、人数・対象年齢と一緒に選べます。"),
        "solo":("1人で遊べるボードゲーム比較｜ソロプレイ対応作品", "1人でも遊べる掲載作品を人数の登録情報から選出。短時間・じっくり系の遊び方や対象年齢を比較。ソロ用ルール・版は購入前に確認してください。"),
    }
    title,desc=seo.get(s["scene_id"],(s["title"]+"ボードゲーム",s["intro"]))
    return shell(title,desc,body,"scenes/"+s["scene_id"]+"/",'<script type="application/ld+json">'+schema+'</script>')


def two_player_cooperative_guide():
    """Search-intent-specific, fact-checked comparison of shared-goal games for two.

    Distinct from the broad two-player and cooperative scene lists: it makes
    communication restrictions, game mechanics and complete time buckets clear.
    """
    matching = [g for g in GAMES if supports_players(g, 2) and g["cooperative"]]
    if not matching:
        raise ValueError("No verified 2-player cooperative games found")
    short = [g for g in matching if g["play_time_max"] <= 20]
    medium = [g for g in matching if 20 < g["play_time_max"] <= 30]
    long = [g for g in matching if g["play_time_max"] > 30]
    exactly_two = [g for g in matching if g["players_min"] == g["players_max"] == 2]

    def row(g):
        source = (f'<a href="{e(g["specs_source"])}" target="_blank" '
                  f'rel="noopener noreferrer" aria-label="{e(g["title"])}の人数・時間・年齢の確認元">取扱元・メーカー</a>'
                  if g.get("specs_source") else '<span class="small">詳細ページで版をご確認ください</span>')
        return (
            '<tr data-cooperative-game="' + e(g["game_id"]) + '">'
            '<th scope="row"><a data-track="game_detail_click" '
            'data-source="two_player_cooperative_guide" data-game-id="' + e(g["game_id"]) +
            '" href="' + u("games/" + g["game_id"] + "/") + '">' + e(g["title"]) +
            '</a>' + edition_note(g) + '</th>'
            '<td>' + e(g["how_to_play"][1]) + '</td>'
            '<td>' + e(player_label(g)) + '</td>'
            '<td>' + format_play_time(g) + '</td>'
            '<td>' + str(g["age"]) + '歳〜</td>'
            '<td>' + source + '</td></tr>'
        )

    def group(heading, games, note):
        if not games:
            return ''
        return (
            '<section class="two-coop-time-group"><h3>' + heading + '（' +
            str(len(games)) + '本）</h3><p>' + note + '</p>'
            '<div class="scene-table-scroll" role="region" tabindex="0" '
            'aria-label="' + heading + 'の協力ゲーム比較表。横にスクロールできます">'
            '<table class="scene-data-table"><thead><tr>'
            '<th scope="col">ゲーム</th><th scope="col">一緒にすること</th>'
            '<th scope="col">対応人数</th><th scope="col">時間</th><th scope="col">対象年齢</th><th scope="col">情報の確認元</th>'
            '</tr></thead><tbody>' + ''.join(row(g) for g in games) + '</tbody></table></div></section>'
        )

    # Use real registered mechanics; never infer hands-on play tests or say
    # these games are ranked above the remaining catalog candidates.
    contrasts = (
        ("話し合わずに動く", "sky-team", "機長・副操縦士でダイスを相談せず配置する"),
        ("言葉のヒントを交換する", "codenames-duet", "交互の一言ヒントから正解語を探す"),
        ("タイミングを合わせる", "the-mind", "相談せず数字カードを小さい順に出す"),
        ("通路を閉じる", "bandido", "道カードをつなぎながら脱出口を塞ぐ"),
    )
    examples = []
    for heading, gid, action in contrasts:
        g = BY_ID[gid]
        if g not in matching:
            raise ValueError("Comparison example is not a 2-player cooperative game: " + gid)
        examples.append(
            '<article class="two-coop-method-card"><h3>' + e(heading) + '</h3>'
            '<a data-track="game_detail_click" data-game-id="' + e(gid) +
            '" data-source="two_player_cooperative_examples" href="' +
            u("games/" + gid + "/") + '"><strong>' + e(g["title"]) + '</strong></a>'
            '<p>' + e(action) + '。' + format_play_time(g) +
            '／対象' + str(g["age"]) + '歳〜</p></article>'
        )

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "2人で協力するボードゲームの比較",
        "itemListElement": [
            {"@type": "ListItem", "position": i+1,
             "url": canon("games/" + g["game_id"] + "/"), "name": g["title"]}
            for i, g in enumerate(matching)
        ],
    }, ensure_ascii=False)
    content = f'''<section class="page-hero two-coop-hero"><div class="breadcrumb">
<a href="{u()}">ホーム</a> / <a href="{u("scenes/two-player/")}">2人で遊ぶ</a> / 2人で協力
</div><div class="eyebrow">TEAM UP FOR TWO</div>
<h1>2人で協力するボードゲームを比較</h1>
<p>勝ち負けを競う代わりに、2人で共通の目標を目指すゲームを探している方へ。
「ヒントを伝える」「相談せずタイミングを合わせる」など、
<strong>協力のしかた</strong>と遊べる時間で候補を比較します。</p>
<p class="small">掲載カタログから、2人対応かつ協力型の作品を抽出。
人気順位・実際に遊んだ評価ではありません。2人対応でも2人での遊び心地を保証するものではありません。</p>
<a class="text-link" href="#two-coop-by-time">登録情報で{len(matching)}本を比較する →</a>
</section>
<section class="section two-coop-guide" aria-labelledby="two-coop-method-heading">
<div class="eyebrow">WHAT TO DO TOGETHER</div>
<h2 id="two-coop-method-heading">2人でも、協力のしかたはこんなに違う</h2>
<p>同じ目標を達成するゲームでも、話せる量や実際にすることは異なります。
以下は掲載されているルールからの比較例です。人気や難易度の順位ではありません。</p>
<div class="two-coop-method-grid">{''.join(examples)}</div>
</section>
<section class="section two-coop-guide" id="two-coop-by-time" aria-labelledby="two-coop-by-time-heading">
<div class="eyebrow">COMPARE BY DURATION</div>
<h2 id="two-coop-by-time-heading">2人で遊ぶ時間から{len(matching)}本を比べる</h2>
<p>掲載プレイ時間の<strong>上限</strong>が20分以内の作品と、30分以内・30分を超える作品を分けました。
時間・対象年齢・人数を確認して詳細ページへ進めます。説明や準備の時間は別に見込んでください。</p>
<p class="small">表は横スクロールできます。各表はカタログ掲載順で人気・優劣の順位ではありません。
「情報の確認元」は出典を照合できた作品のみ表示し、未確認の作品について根拠を推測で補っていません。</p>
{group("20分以内",short,"食後の空き時間など、上限20分で選びたい場合の候補です。")}
{group("21〜30分",medium,"相談や推理に少し長く時間を使える場合の候補です。")}
{group("30分を超える",long,"まとまった時間を確保できる場合の候補です。")}
</section>
<section class="section two-coop-guide">
<div class="eyebrow">BEFORE YOU BUY</div><h2>2人専用と、2人でも遊べる作品を区別する</h2>
<p>今回の登録情報では、掲載人数が2人だけの協力ゲームは<strong>{len(exactly_two)}本</strong>です。
残りは2人以外の人数にも対応します。ただし、複数人数に対応する版では
2人用の特別ルールが必要な場合があります。購入する版の説明をご確認ください。</p>
<p>「協力するゲーム」と「会話が多いゲーム」は同義ではありません。
相談に制限のあるゲームもあります。遊び方を確認してから購入先を選んでください。</p>
<p class="small">商品価格・在庫・販売版は変動します。各作品の詳細ページから販売店で再確認してください。
リンク先にはアフィリエイト広告を含む場合があります。</p>
<nav class="two-coop-related" aria-label="関連するボードゲーム比較">
<a class="text-link" href="{u("scenes/two-player/")}">対戦型も含めて2人用を比較する →</a>
<a class="text-link" href="{u("scenes/cooperative/")}">3人以上の協力ゲームも探す →</a>
<a class="text-link" href="{u("diagnosis/?src=two_player_cooperative_guide&preset=two-coop")}">2人・協力の条件で診断する →</a>
</nav>
</section>'''
    return shell(
        "2人で協力するボードゲーム比較｜時間・会話・遊び方から選ぶ",
        "2人で協力するボードゲームを掲載情報から比較。スカイチーム、コードネーム：デュエット、ザ・マインドなど、相談・会話制限や20分以内の作品を人数・対象年齢とともに紹介。",
        content, "guides/two-player-cooperative/",
        '<script type="application/ld+json">' + schema + '</script>'
    )


def write(rel,text):
    p=SITE/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8")

def main():
    if SITE.exists(): shutil.rmtree(SITE)
    (SITE/"assets").mkdir(parents=True);(SITE/"data").mkdir(parents=True)
    shutil.copy2(ROOT/"assets/media.js",SITE/"assets/media.js")
    for verification in ROOT.glob("google*.html"): shutil.copy2(verification,SITE/verification.name)
    write("assets/styles.css",CSS);write("assets/analytics.js",ANALYTICS);write("assets/diagnosis.js",DIAGNOSIS);write("assets/today.js",TODAY)
    shutil.copy2(ROOT/"assets/decision-insights.js", SITE/"assets/decision-insights.js")
    shutil.copy2(ROOT/"assets/two-player-quick-filter.js", SITE/"assets/two-player-quick-filter.js")
    shutil.copy2(ROOT/"assets/children-filter.js", SITE/"assets/children-filter.js")
    shutil.copy2(ROOT/"assets/short-filter.js", SITE/"assets/short-filter.js")
    shutil.copy2(ROOT/"assets/catalog-search.js", SITE/"assets/catalog-search.js")
    shutil.copy2(ROOT/"assets/catalog-compare.js", SITE/"assets/catalog-compare.js")
    if HERO_ASSET.exists(): shutil.copy2(HERO_ASSET,SITE/"assets"/HERO_ASSET.name)
    if SCENE_ASSET.exists(): shutil.copy2(SCENE_ASSET,SITE/"assets"/SCENE_ASSET.name)
    write("data/games.json",json.dumps(GAMES,ensure_ascii=False,separators=(",",":")))
    write("data/rakuten.json",json.dumps(RAKUTEN,ensure_ascii=False,separators=(",",":")))
    write("index.html",home());write("diagnosis/index.html",diagnosis());write("games/index.html",games_index());write("scenes/index.html",scenes_index())
    for g in GAMES: write("games/"+g["game_id"]+"/index.html",game_page(g))
    for s in SCENES: write("scenes/"+s["scene_id"]+"/index.html",scene_page(s))
    write("guides/two-player-cooperative/index.html",two_player_cooperative_guide())
    paths=["", "diagnosis/","games/","scenes/","guides/two-player-cooperative/"]+["games/"+g["game_id"]+"/" for g in GAMES]+["scenes/"+s["scene_id"]+"/" for s in SCENES]
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join("<url><loc>"+e(canon(p))+"</loc></url>" for p in paths)+"</urlset>"
    write("sitemap.xml",xml);write("robots.txt","User-agent: *\nAllow: /\nSitemap: "+canon("sitemap.xml")+"\n")
    write("404.html",shell("ページが見つかりません","ページが見つかりません。",'<section class="page-hero"><h1>ページが見つかりません</h1><a class="btn primary" href="'+u()+'">トップへ</a></section>',extra='<meta name="robots" content="noindex">'))
    print("built",len(paths),"indexable URLs in",SITE)

if __name__=="__main__": main()
