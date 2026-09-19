#!/usr/bin/env python3
import json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.catalog import GAMES
OUT=ROOT/"data"/"rakuten_cache.json"
APP_ID=os.environ.get("RAKUTEN_APPLICATION_ID","").strip()
ACCESS_KEY=os.environ.get("RAKUTEN_ACCESS_KEY","").strip()
AFFILIATE_ID=os.environ.get("RAKUTEN_AFFILIATE_ID","").strip()
ENDPOINT="https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
def norm(s): return re.sub(r"[\s　・:：!！?？()（）\-ー_]+","",(s or "").lower())
def score(g,x):
    n=norm(x.get("itemName",""));s=30 if norm(g["title"]) in n else 0
    for t in [z for z in re.split(r"[\s　]+",g.get("rakuten_query","")) if len(z)>=2]:
        if norm(t) in n:s+=5
    if "中古" in x.get("itemName",""):s-=80
    if x.get("affiliateUrl"):s+=4
    if x.get("mediumImageUrls"):s+=2
    return s
def one(g):
    p={"applicationId":APP_ID,"keyword":g["rakuten_query"],"hits":10,"availability":1,"imageFlag":1,"format":"json","formatVersion":2,"elements":"itemName,itemCode,itemUrl,affiliateUrl,mediumImageUrls,reviewAverage,reviewCount,shopName"}
    if AFFILIATE_ID:p["affiliateId"]=AFFILIATE_ID
    req=urllib.request.Request(ENDPOINT+"?"+urllib.parse.urlencode(p),headers={"accessKey":ACCESS_KEY,"Origin":"https://stusaurus.github.io","Referer":"https://stusaurus.github.io/kyo-bodo-jp/","User-Agent":"kyo-bodo-jp/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:data=json.loads(r.read().decode())
    items=data.get("Items") or data.get("items") or []
    items=[x.get("Item",x.get("item",x)) if isinstance(x,dict) else {} for x in items]
    if not items:return None
    best=max(items,key=lambda x:score(g,x))
    if score(g,best)<0:return None
    imgs=best.get("mediumImageUrls") or [];im=""
    if imgs:
        z=imgs[0];im=z.get("imageUrl","") if isinstance(z,dict) else str(z)
    return {"item_name":best.get("itemName",""),"item_code":best.get("itemCode",""),"url":best.get("affiliateUrl") or best.get("itemUrl") or "","image_url":im,"shop_name":best.get("shopName","")}
def main():
    if not APP_ID or not ACCESS_KEY:
        print("Rakuten credentials are not configured; using search fallbacks.")
        OUT.write_text("{}\n",encoding="utf-8");return
    out={}
    for i,g in enumerate(GAMES,1):
        try:
            hit=one(g)
            if hit:out[g["game_id"]]=hit
            print("["+str(i)+"/"+str(len(GAMES))+"]",g["title"],"OK" if hit else "no match")
        except Exception as ex:print(g["title"],ex,file=sys.stderr)
        time.sleep(.25)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
