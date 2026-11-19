/* Progressive title search for the 88-game catalog.
 * Search terms never leave this browser; only category names are tracked.
 */
(function(){
  'use strict';
  var field=document.getElementById('catalogTitleSearch');
  var reset=document.getElementById('catalogSearchReset');
  var count=document.getElementById('filterCount');
  var empty=document.getElementById('catalogEmpty');
  var grid=document.getElementById('gamesGrid');
  if(!field||!reset||!count||!empty||!grid)return;
  var cards=Array.prototype.slice.call(grid.querySelectorAll('.game-list-card'));
  var buttons=Array.prototype.slice.call(document.querySelectorAll('.filter-btn'));
  var active='all';
  function normalize(v){return String(v||'').normalize('NFKC').toLocaleLowerCase('ja').replace(/[\s\u3000・:：!！?？\-ー]/g,'');}
  function eligible(c){
    return active==='all'||(active==='two'&&c.dataset.two==='1')||
      (active==='solo'&&c.dataset.solo==='1')||
      (active==='family'&&c.dataset.family==='1')||
      (active==='short'&&c.dataset.short==='1')||
      (active==='beginner'&&c.dataset.beginner==='1');
  }
  function render(){
    var query=normalize(field.value);
    var matched=0;
    cards.forEach(function(c){
      var show=eligible(c)&&normalize(c.dataset.searchTitle).includes(query);
      c.hidden=!show;
      if(show)matched++;
    });
    count.textContent=matched+'本のゲーム';
    empty.hidden=matched!==0;
    reset.hidden=field.value.length===0;
    return matched;
  }
  field.addEventListener('input',render);
  reset.addEventListener('click',function(){field.value='';render();field.focus()});
  buttons.forEach(function(button){
    button.addEventListener('click',function(){
      active=button.dataset.filter||'all';
      buttons.forEach(function(b){
        b.classList.toggle('active',b===button);
        b.setAttribute('aria-pressed',b===button?'true':'false');
      });
      render();
      if(typeof window.kyoTrack==='function'){
        window.kyoTrack('game_filter_use',{filter:active});
      }
    });
  });
  render();
})();