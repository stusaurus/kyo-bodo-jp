/* Explainable, deterministic game-choice insights. No invented product claims.
 * Pure functions: no DOM, analytics, persistence, or affiliate links.
 */
(function(root,factory){
  var api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.KyoDecisionInsights=api;
})(typeof globalThis!=="undefined"?globalThis:null,function(){
  "use strict";
  function numberOrNull(v){
    if(v===null||v===undefined||v==="")return null;
    var n=Number(v);return Number.isFinite(n)?n:null;
  }
  function fit(game,conditions){
    conditions=conditions||{};
    var problems=[],unknown=[];
    var players=numberOrNull(conditions.players);
    var min=numberOrNull(game.players_min),max=numberOrNull(game.players_max);
    if(players!==null){
      if(min===null||max===null){
        if(min!==null&&players<min)problems.push("必要な人数に達していません");
        else if(max===null&&game.players_open_ended===true&&game.players_source&&min!==null){
          // Publisher-supported open-ended player range.
        }else unknown.push("対応人数を確認できません");
      }else if(players<min||players>max)problems.push("対応人数が合いません");
    }
    var minutes=numberOrNull(conditions.minutes);
    if(minutes!==null){
      var duration=numberOrNull(game.play_time_max);
      if(duration===null)unknown.push("プレイ時間の上限が不明です");
      else if(duration>minutes)problems.push("希望時間を超える可能性があります");
    }
    var age=numberOrNull(conditions.youngestAge);
    if(age!==null){
      var minAge=numberOrNull(game.age);
      if(minAge===null)unknown.push("対象年齢を確認できません");
      else if(age<minAge)problems.push("対象年齢を満たしていません");
    }
    return {status:problems.length?"excluded":unknown.length?"unverified":"eligible",problems:problems,unknown:unknown};
  }
  function compare(before,after,previousTop,nextTop){
    var messages=[];
    if(previousTop&&nextTop&&String(previousTop.game_id)!==String(nextTop.game_id)){
      messages.push({type:"rank_change",title:"おすすめが変わりました",detail:"選択条件を変更したため、候補の順番が変わりました。"});
    }
    if(before&&after){
      if(numberOrNull(before.players)!==numberOrNull(after.players))
        messages.push({type:"condition",title:"人数を見直しました",detail:"対応人数を優先して候補を確認します。"});
      if(numberOrNull(before.minutes)!==numberOrNull(after.minutes))
        messages.push({type:"condition",title:"遊べる時間を見直しました",detail:"最大プレイ時間が希望内か確認します。"});
    }
    return messages;
  }
  function explain(game,conditions){
    var result=fit(game,conditions);
    if(result.status==="excluded")return {status:"excluded",title:"この条件ではおすすめしません",reasons:result.problems};
    if(result.status==="unverified")return {status:"unverified",title:"購入前に確認が必要です",reasons:result.unknown};
    return {status:"eligible",title:"指定した必須条件に合っています",reasons:["確認できた人数・時間・年齢の条件に矛盾はありません。好みに合うかは別途比較してください。"]};
  }
  return {fit:fit,explain:explain,compare:compare};
});
