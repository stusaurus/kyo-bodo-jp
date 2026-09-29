#!/usr/bin/env python3
# Robust Rakuten refresh for kyo-bodo-jp.
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES

OUT=ROOT/"data"/"rakuten_cache.json"
APP_ID=os.environ.get("RAKUTEN_APPLICATION_ID","").strip()
ACCESS_KEY=os.environ.get("RAKUTEN_ACCESS_KEY","").strip()
AFFILIATE_ID=os.environ.get("RAKUTEN_AFFILIATE_ID","").strip()
ENDPOINT="https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"

def norm(s):
    return re.sub(r"[\s　・:：!！?？()（）\-ー_]+","",(s or "").lower())

def score(g,x):
    n=norm(x.get("itemName",""))
    if not n: return -999
    s=30 if norm(g["title"]) in n else 0
    for t in [z for z in re.split(r"[\s　]+",g.get("rakuten_query","")) if len(z)>=2]:
        if norm(t) in n: s+=5
    if "中古" in x.get("itemName",""): s-=80
    if x.get("affiliateUrl"): s+=4
    if x.get("mediumImageUrls"): s+=2
    return s

def request_items(keyword):
    p={
        "applicationId":APP_ID,
        "keyword":keyword,
        "hits":10,
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
            "User-Agent":"kyo-bodo-jp/0.2",
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
    for q in query_variants(g):
        items=fetch_with_retry(q)
        if items is None:
            continue
        if not items:
            time.sleep(1.1)
            continue
        best=max(items,key=lambda x:score(g,x))
        if score(g,best)<0:
            time.sleep(1.1)
            continue
        imgs=best.get("mediumImageUrls") or []
        image=""
        if imgs:
            z=imgs[0]
            image=z.get("imageUrl","") if isinstance(z,dict) else str(z)
        return {
            "item_name":best.get("itemName",""),
            "item_code":best.get("itemCode",""),
            "url":best.get("affiliateUrl") or best.get("itemUrl") or "",
            "image_url":image,
            "shop_name":best.get("shopName",""),
        }
    return None

def main():
    if not APP_ID or not ACCESS_KEY:
        print("Rakuten credentials are not configured; using search fallbacks.")
        OUT.write_text("{}\n",encoding="utf-8")
        return
    out={}
    unresolved=[]
    for i,g in enumerate(GAMES,1):
        try:
            hit=one(g)
            if hit:
                out[g["game_id"]]=hit
                print(f"[{i}/{len(GAMES)}] {g['title']} OK")
            else:
                unresolved.append(g["game_id"])
                print(f"[{i}/{len(GAMES)}] {g['title']} no match")
        except Exception as ex:
            unresolved.append(g["game_id"])
            print(f"[{i}/{len(GAMES)}] {g['title']} ERROR: {ex}",file=sys.stderr)
        time.sleep(1.1)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Rakuten refresh complete: {len(out)}/{len(GAMES)} matched")
    if unresolved:
        print("Unresolved:",",".join(unresolved))

if __name__=="__main__":
    main()
