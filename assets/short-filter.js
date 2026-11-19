/* Time, group size and minimum-participant-age filtering for all <=20-min
 * catalogued games. All eligible links are static and visible without JS.
 * We never persist/filter-log age or individual selections.
 */
(function(){
  'use strict';
  var root=document.getElementById('short-time-finder');
  if(!root) return;
  var form=root.querySelector('#short-time-form');
  var minutes=root.querySelector('#short-time-minutes');
  var players=root.querySelector('#short-time-players');
  var age=root.querySelector('#short-time-age');
  var reset=root.querySelector('#short-time-reset');
  var count=root.querySelector('#short-time-count');
  var empty=root.querySelector('#short-time-empty');
  var rows=Array.prototype.slice.call(root.querySelectorAll('li[data-short-game]'));
  if(!form||!minutes||!players||!age||!reset||!count||!empty||!rows.length)return;

  function matches(row){
    var supported=(row.dataset.shortPlayers||'').split(' ');
    return Number(row.dataset.shortMinutes)<=Number(minutes.value) &&
      (players.value==='any'||supported.indexOf(players.value)!==-1) &&
      (age.value==='any'||Number(row.dataset.shortAge)<=Number(age.value));
  }
  function render(){
    var visible=0;
    rows.forEach(function(row){
      row.hidden=!matches(row);
      if(!row.hidden)visible++;
    });
    count.textContent=visible+'本';
    empty.hidden=visible!==0;
    return visible;
  }
  function track(dimension,visible){
    if(typeof window.kyoTrack==='function'){
      window.kyoTrack('short_filter_change',{
        filter_dimension:dimension,
        result_count:visible,
        conversion_source:'short_time_finder'
      });
    }
  }
  form.hidden=false;
  render();
  form.addEventListener('submit',function(event){event.preventDefault()});
  [minutes,players,age].forEach(function(input){
    input.addEventListener('change',function(){track(input.name,render())});
  });
  reset.addEventListener('click',function(){
    minutes.value='20';
    players.value='any';
    age.value='any';
    track('reset',render());
    minutes.focus();
  });
})();
