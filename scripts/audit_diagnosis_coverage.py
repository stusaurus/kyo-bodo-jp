#!/usr/bin/env python3
import itertools, json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.catalog import GAMES

WHO = ["couple","family","friends","children","large","first"]
PLAYERS = [str(x) for x in range(2,15)]
MOOD = ["laugh","compete","think","coop","relax","chat"]
TIME = ["15","30","60","120"]
DIFFICULTY = ["1","3","5"]
BALANCE = ["luck","half","skill"]

def score(g, a):
    n=int(a["players"])
    if not (g["players_min"] <= n <= g["players_max"]): return -9999
    if g["play_time_max"] > int(a["time"]): return -9999
    if a["mood"]=="coop" and not g["cooperative"]: return -9999
    s=60
    w=a["who"]
    if w=="couple": s+=g["couple"]*7
    elif w=="family": s+=g["family"]*7
    elif w=="friends": s+=(g["conversation"]+g["party"]+g["excitement"])*3
    elif w=="children": s+=g["children"]*7
    elif w=="large": s+=(g["large_group"]+g["party"])*5
    elif w=="first": s+=(g["beginner"]+g["conversation"]+g["party"])*4
    m=a["mood"]
    if m=="laugh": s+=(g["excitement"]+g["party"]+g["conversation"])*4
    elif m=="compete": s+=(g["strategy"]+g["excitement"])*5
    elif m=="think": s+=g["strategy"]*8
    elif m=="coop": s+=g["cooperation"]*9
    elif m=="relax": s+=g["beginner"]*5+(6-g["difficulty"])*4
    elif m=="chat": s+=g["conversation"]*8
    t=int(a["time"])
    if t<=15: s+=max(0,20-max(0,g["play_time_min"]-15)*2)
    elif t<=30: s+=max(0,18-abs(g["play_time_max"]-30)/3)
    elif t<=60: s+=max(0,16-abs(g["play_time_max"]-60)/5)
    else: s+=18 if g["play_time_max"]>=45 else 5
    d=int(a["difficulty"])
    s+=max(0,18-abs(g["difficulty"]-d)*6)
    if a["balance"]=="luck": s+=g["luck"]*5+(6-g["strategy"])*2
    elif a["balance"]=="skill": s+=g["strategy"]*6+(6-g["luck"])*2
    else: s+=12-abs(g["strategy"]-g["luck"])*3
    return s

def main():
    total=0
    empty=[]
    thin=[]
    top1=Counter()
    top5=Counter()
    pool_hist=Counter()
    unique_result_sets=set()
    for who,players,mood,time,difficulty,balance in itertools.product(WHO,PLAYERS,MOOD,TIME,DIFFICULTY,BALANCE):
        a={"who":who,"players":players,"mood":mood,"time":time,"difficulty":difficulty,"balance":balance}
        ranked=sorted(((g,score(g,a)) for g in GAMES), key=lambda x:x[1], reverse=True)
        eligible=[x for x in ranked if x[1]>-100]
        total+=1
        pool_hist[len(eligible)]+=1
        ids=[g["game_id"] for g,_ in eligible[:5]]
        if not ids:
            empty.append(a)
        elif len(eligible)<5:
            thin.append({**a,"eligible_count":len(eligible),"result_ids":ids})
        if ids:
            top1[ids[0]]+=1
            top5.update(ids)
            unique_result_sets.add(tuple(ids))
    report={
        "catalog_size":len(GAMES),
        "total_combinations":total,
        "empty_combinations":len(empty),
        "thin_combinations_under_5":len(thin),
        "unique_top5_sets":len(unique_result_sets),
        "eligible_pool_histogram":dict(sorted(pool_hist.items())),
        "top1_frequency":top1.most_common(),
        "top5_frequency":top5.most_common(),
        "empty_examples":empty[:100],
        "thin_examples":thin[:100],
        "policy":{
            "catalog_growth":"Do not grow from 50 just for volume. Add games only after actual GA4 diagnosis data and this coverage audit show underserved combinations.",
            "review_signal":"Prioritize combinations with real diagnosis completions and fewer than five strong candidates, repeated top results, or weak affiliate CTR."
        }
    }
    out=ROOT/"data"/"diagnosis_coverage_audit.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"DIAGNOSIS_COVERAGE total={total} empty={len(empty)} thin_lt5={len(thin)} unique_top5_sets={len(unique_result_sets)}")
    print("Top-1 most frequent:", top1.most_common(10))
    if empty: print("Empty examples:", empty[:5])
    if thin: print("Thin examples:", thin[:5])

if __name__=="__main__":
    main()
