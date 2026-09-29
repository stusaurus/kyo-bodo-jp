#!/usr/bin/env python3
# Quality-first Rakuten refresh for kyo-bodo-jp.
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, urllib.error
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES

OUT=ROOT/"data"/"rakuten_cache.json"
REPORT=ROOT/"data"/"rakuten_audit.json"
APP_ID=os.environ.get("RAKUTEN_APPLICATION_ID","").strip()
ACCESS_KEY=os.environ.get("RAKUTEN_ACCESS_KEY","").strip()
AFFILIATE_ID=os.environ.get("RAKUTEN_AFFILIATE_ID","").strip()
ENDPOINT="https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"

GENERIC_BLOCK_TERMS=[
    "中古","used","ユーズド","拡張","拡張版","拡張セット","エキスパンション","expansion",
    "カードスリーブ","スリーブ","プレイマット","オーガナイザー","収納ケース","収納ボックス",
    "交換用","交換パーツ","スペアパーツ","プロモカード","プロモーションカード","攻略本",
    "ルールブックのみ","説明書のみ","カードケース","専用ケース","アクセサリー","アクセサリ"
]

# Short / generic titles need an extra product-context anchor.
CONTEXT_RULES={
    "ito":["アークライト","ボードゲーム","カードゲーム"],
    "ito-rainbow":["アークライト","ボードゲーム","カードゲーム"],
    "love-letter":["ボードゲーム","カードゲーム","アークライト"],
    "coyote":["ボードゲーム","カードゲーム"],
    "skull":["ボードゲーム","カードゲーム","ホビージャパン"],
    "hanabi":["ボードゲーム","カードゲーム","ホビージャパン"],
    "scout":["オインク","ボードゲーム","カードゲーム"],
    "quarto":["ボードゲーム","ギガミック","gigamic"],
    "patchwork":["ホビージャパン","lookout"],
    "jaipur":["ボードゲーム","カードゲーム","ホビージャパン"],
    "lost-cities":["ボードゲーム","カードゲーム"],
    "azul":["ボードゲーム","ホビージャパン","nextmove"],
    "pandemic":["ボードゲーム","ホビージャパン"],
    "heat":["ボードゲーム","ヒートペダルトゥザメタル","pedaltothemetal"],
    "neu":["カードゲーム","ノイカード","neu"],
    "harmonies":["ボードゲーム","ホビージャパン","libellud"],
    "take-it-easy":["ボードゲーム","カードゲーム","テーブルゲーム","ふるりん本舗"],
    "cat-in-the-box":["ボードゲーム","カードゲーム","ホビージャパン"],
}

# Prevent sibling/base variants from being used for another registered game.
PER_GAME_BLOCK={
    "ito":["レインボー"],
    "codenames":["デュエット","duet","xxl"],
    "quarto":["ミニ","mini"],
    "patchwork":["ドゥードゥル","doodle"],
    "challengers":["ビーチカップ","beachcup"],
    "nine-tiles":["ポケモン","pokemon","ムーミン","サンリオ","パニック","ミッキー","mickey"],
    "machi-koro":["街コロ通","街コロ2","街コロツー"],
    "cat-in-the-box":["じゃらし","アドメイト","add.mate"],
    "sushi-go-party":["中古","スシゴー！ - ピック","sushigo! - the pick"],
}

# Accepted title aliases. Default is the catalog title itself.
ALIASES={
    "6nimmt":["ニムト","6nimmt"],
    "the-mind":["ザマインド","themind"],
    "hanabi":["花火hanabi","hanabi"],
    "sushi-go-party":["スシゴーパーティ","sushigoparty","寿司パーティー"],
    "cat-in-the-box":["キャットインザボックス","catinthebox"],
    "sea-salt-paper":["シーソルト＆ペーパー","シーソルトアンドペーパー","seasaltpaper"],
}

def norm(s):
    s=unicodedata.normalize("NFKC",s or "").lower()
    s=s.replace("＆","and").replace("&","and")
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]+","",s)

def has_term(name,term):
    return norm(term) in norm(name)

def title_aliases(g):
    return ALIASES.get(g["game_id"],[g["title"]])

def is_blocked(g,item_name):
    low=unicodedata.normalize("NFKC",item_name or "").lower()
    for term in GENERIC_BLOCK_TERMS+PER_GAME_BLOCK.get(g["game_id"],[]):
        if term.lower() in low:
            return True,term
    return False,""

def match_item(g,item):
    name=item.get("itemName","") or ""
    if not name:
        return False,"empty_name",0
    blocked,term=is_blocked(g,name)
    if blocked:
        return False,"blocked:"+term,-1000
    alias_hit=next((a for a in title_aliases(g) if has_term(name,a)),None)
    if not alias_hit:
        return False,"title_mismatch",-500
    # Exact product identity rules for titles that Rakuten lists in multiple notations.
    if g["game_id"]=="sushi-go-party":
        jp_exact=has_term(name,"スシゴーパーティ")
        en_exact=has_term(name,"sushigoparty") and has_term(name,"gamewright")
        ja_import=has_term(name,"寿司パーティー") and has_term(name,"gamewright")
        if not (jp_exact or en_exact or ja_import):
            return False,"missing_party_identity",-450
    if g["game_id"]=="take-it-easy":
        exact_jp=has_term(name,"テイクイットイージー") and has_term(name,"日本語版")
        has_context=any(has_term(name,t) for t in CONTEXT_RULES["take-it-easy"])
        if not (exact_jp or has_context):
            return False,"missing_take_it_easy_identity",-450

    required=CONTEXT_RULES.get(g["game_id"])
    if required and g["game_id"] not in ("sushi-go-party","take-it-easy") and not any(has_term(name,t) for t in required):
        return False,"missing_product_context",-400
    # Special-case sibling distinction.
    if g["game_id"]=="ito-rainbow" and not has_term(name,"レインボー"):
        return False,"missing_rainbow",-450
    if g["game_id"]=="codenames-duet" and not (has_term(name,"デュエット") or has_term(name,"duet")):
        return False,"missing_duet",-450
    s=100
    if has_term(name,g["title"]): s+=30
    for t in [z for z in re.split(r"[\s　]+",g.get("rakuten_query","")) if len(norm(z))>=2]:
        if has_term(name,t): s+=3
    if item.get("affiliateUrl"): s+=4
    if item.get("mediumImageUrls"): s+=2
    if item.get("reviewCount") or 0: s+=1
    return True,"ok",s

def request_items(keyword):
    p={
        "applicationId":APP_ID,
        "keyword":keyword,
        "hits":30,
        "availability":1,
        "imageFlag":1,
        "format":"json",
        "formatVersion":2,
        "elements":"itemName,itemCode,itemUrl,affiliateUrl,mediumImageUrls,reviewAverage,reviewCount,shopName",
    }
    if AFFILIATE_ID:
        p["affiliateId"]=AFFILIATE_ID
    req=urllib.request.Request(
        ENDPOINT+"?"+urllib.parse.urlencode(p),
        headers={
            "accessKey":ACCESS_KEY,
            "Origin":"https://stusaurus.github.io",
            "Referer":"https://stusaurus.github.io/kyo-bodo-jp/",
            "User-Agent":"kyo-bodo-jp/0.3",
        },
    )
    with urllib.request.urlopen(req,timeout=30) as r:
        data=json.loads(r.read().decode("utf-8"))
    items=data.get("Items") or data.get("items") or []
    return [x.get("Item",x.get("item",x)) if isinstance(x,dict) else {} for x in items]

def query_variants(g):
    title=g["title"]
    simple=re.sub(r"[：:・!！?？()（）]"," ",title)
    variants=[g.get("rakuten_query") or title,title,simple+" ボードゲーム"]
    if g["game_id"]=="sushi-go-party":
        variants=[
            "Gamewright Sushi Go Party",
            "Gamewright 寿司パーティー カードゲーム",
            "スシゴーパーティ",
            "スシゴー パーティ",
            "Sushi Go Party Gamewright",
            "Sushi Go Party ボードゲーム",
        ]+variants
    if g["game_id"]=="take-it-easy":
        variants=[
            "テイクイットイージー 日本語版",
            "テイク・イット・イージー 日本語版",
            "テイクイットイージー ボードゲーム",
        ]+variants
    out=[]
    for q in variants:
        q=" ".join(q.split()).strip()
        if len(q)>=2 and q not in out:
            out.append(q)
    return out

def fetch_with_retry(keyword):
    last=None
    for attempt in range(4):
        try:
            return request_items(keyword)
        except urllib.error.HTTPError as e:
            last=e
            body=""
            try: body=e.read().decode("utf-8","replace")
            except Exception: pass
            if e.code==429:
                wait=2*(attempt+1)
                print(f"429 for {keyword!r}; retry in {wait}s",file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code==400:
                print(f"400 for {keyword!r}: {body[:240]}",file=sys.stderr)
                return None
            raise
    if last: raise last
    return None

def one(g):
    rejected=[]
    for q in query_variants(g):
        items=fetch_with_retry(q)
        if items is None:
            continue
        candidates=[]
        for item in items:
            ok,reason,s=match_item(g,item)
            if ok:
                candidates.append((s,item,q))
            else:
                rejected.append({"query":q,"item_name":item.get("itemName",""),"reason":reason})
        if candidates:
            candidates.sort(key=lambda z:z[0],reverse=True)
            s,best,q=candidates[0]
            imgs=best.get("mediumImageUrls") or []
            image=""
            if imgs:
                z=imgs[0]
                image=z.get("imageUrl","") if isinstance(z,dict) else str(z)
            hit={
                "item_name":best.get("itemName",""),
                "item_code":best.get("itemCode",""),
                "item_url":best.get("itemUrl") or "",
                "url":best.get("affiliateUrl") or best.get("itemUrl") or "",
                "image_url":image,
                "shop_name":best.get("shopName",""),
                "match_score":s,
                "matched_query":q,
            }
            return hit,rejected
        time.sleep(1.1)
    return None,rejected

def valid_url(url):
    try:
        p=urllib.parse.urlparse(url or "")
        return p.scheme=="https" and bool(p.netloc) and (
            p.netloc.endswith("rakuten.co.jp") or "rakuten" in p.netloc
        )
    except Exception:
        return False

def remove_duplicates(out,audit):
    by_code=defaultdict(list)
    for game_id,hit in out.items():
        if hit.get("item_code"):
            by_code[hit["item_code"]].append(game_id)
    duplicate_groups={code:ids for code,ids in by_code.items() if len(ids)>1}
    for code,ids in duplicate_groups.items():
        for game_id in ids:
            audit[game_id]["status"]="unresolved"
            audit[game_id]["reason"]="duplicate_item_code:"+code
            out.pop(game_id,None)
    return duplicate_groups

def main():
    if not APP_ID or not ACCESS_KEY:
        print("Rakuten credentials are not configured; using search fallbacks.")
        OUT.write_text("{}\n",encoding="utf-8")
        REPORT.write_text(json.dumps({"status":"credentials_missing"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return
    out={}
    audit={}
    for i,g in enumerate(GAMES,1):
        try:
            hit,rejected=one(g)
            if hit and valid_url(hit.get("url")) and valid_url(hit.get("item_url")):
                out[g["game_id"]]=hit
                audit[g["game_id"]]={
                    "title":g["title"],"status":"ok","reason":"api_current_match",
                    "item_name":hit["item_name"],"item_code":hit["item_code"],
                    "item_url":hit["item_url"],"matched_query":hit["matched_query"],
                    "rejected_candidates":len(rejected),
                }
                print(f"[{i}/{len(GAMES)}] {g['title']} OK | {hit['item_code']} | {hit['item_name']}")
            else:
                reason="no_safe_match" if not hit else "invalid_rakuten_url"
                audit[g["game_id"]]={"title":g["title"],"status":"unresolved","reason":reason,"rejected_candidates":len(rejected),"rejected_examples":rejected[:8]}
                print(f"[{i}/{len(GAMES)}] {g['title']} UNRESOLVED | {reason}")
                for row in rejected[:5]:
                    print(f"  REJECTED {row['reason']} | {row['item_name']}")
        except Exception as ex:
            audit[g["game_id"]]={"title":g["title"],"status":"unresolved","reason":"error:"+str(ex)}
            print(f"[{i}/{len(GAMES)}] {g['title']} ERROR: {ex}",file=sys.stderr)
        time.sleep(1.1)

    duplicates=remove_duplicates(out,audit)
    if duplicates:
        print("DUPLICATE ITEM CODES REMOVED:",json.dumps(duplicates,ensure_ascii=False),file=sys.stderr)

    # Final safety pass over every retained item.
    bad=[]
    for g in GAMES:
        hit=out.get(g["game_id"])
        if not hit: continue
        ok,reason,_=match_item(g,{"itemName":hit["item_name"],"affiliateUrl":hit["url"]})
        if not ok or not valid_url(hit["url"]) or not valid_url(hit["item_url"]):
            bad.append((g["game_id"],reason))
    for game_id,reason in bad:
        out.pop(game_id,None)
        audit[game_id]["status"]="unresolved"
        audit[game_id]["reason"]="final_validation:"+reason

    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={
        "total_games":len(GAMES),
        "normal_count":len(out),
        "unresolved_count":len(GAMES)-len(out),
        "duplicate_groups":duplicates,
        "games":audit,
    }
    REPORT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"RAKUTEN_AUDIT_SUMMARY normal={len(out)}/{len(GAMES)} unresolved={len(GAMES)-len(out)} duplicates={len(duplicates)}")
    for game_id,row in audit.items():
        if row["status"]!="ok":
            print(f"UNRESOLVED {game_id}: {row['reason']}")

if __name__=="__main__":
    main()
