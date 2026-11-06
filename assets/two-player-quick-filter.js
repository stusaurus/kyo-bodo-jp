/* Filter only verified two-player catalog metadata already rendered in HTML.
 * Not a ranking, recommendation score, availability or popularity claim.
 */
(function(){
  'use strict';
  function init(){
    var root=document.querySelector('[data-two-player-quick-filter]');
    if(!root)return;
    var items=Array.from(root.querySelectorAll('[data-two-game]'));
    var counter=root.querySelector('[data-two-quick-count]');
    var empty=root.querySelector('[data-two-quick-empty]');
    var form=root.querySelector('form');
    if(!items.length||!counter||!empty||!form)return;
    function filter(){
      var settings=new FormData(form);
      var max=Number(settings.get('minutes')||0);
      var age=Number(settings.get('age')||0);
      var coop=settings.get('style')==='cooperative';
      var matched=items.filter(function(node){
        var time=Number(node.dataset.timeMax),minAge=Number(node.dataset.minAge);
        return Number.isFinite(time)&&time>0&&Number.isFinite(minAge)&&minAge>=0
          &&(!max||time<=max)&&(!age||minAge<=age)
          &&(!coop||node.dataset.cooperative==='1');
      });
      var chosen=matched.slice(0,3);
      items.forEach(function(node){node.hidden=!chosen.includes(node);});
      empty.hidden=matched.length>0;
      counter.textContent=matched.length
        ?matched.length+'本が条件に一致。うち'+chosen.length+'本を表示（優劣・人気順ではありません）'
        :'この条件に合う掲載候補はありません。条件を広げるか、全12本から探してください。';
    }
    form.addEventListener('change',filter);
    filter();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
