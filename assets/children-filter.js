/* Parent-friendly age × actual group size × published maximum playtime filter.
 * No assumptions about grade, reading level, or winning chances.
 * Default static HTML works with JavaScript disabled. No child data is stored.
 */
(function(){
  'use strict';
  var root=document.getElementById('children-age-compare');
  if(!root) return;
  var form=document.getElementById('children-choice-form');
  var count=document.getElementById('children-choice-count');
  var empty=document.getElementById('children-choice-empty');
  var reset=document.getElementById('children-choice-reset');
  var ages=document.getElementById('children-age');
  var players=document.getElementById('children-players');
  var times=document.getElementById('children-time');
  var rows=Array.prototype.slice.call(root.querySelectorAll('li[data-child-game]'));
  if(!form||!count||!empty||!reset||!ages||!players||!times||!rows.length) return;

  function matches(row){
    var age=Number(ages.value),size=String(players.value);
    var minutes=times.value;
    var supported=(row.dataset.childPlayers||'').split(' ');
    return Number(row.dataset.childAge)<=age &&
      supported.indexOf(size)!==-1 &&
      (minutes==='any'||Number(row.dataset.childMinutes)<=Number(minutes));
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
    // Deliberately do not send the child's age, identity or individual game histories.
    if(typeof window.kyoTrack==='function'){
      window.kyoTrack('children_filter_change',{
        filter_dimension:dimension,
        result_count:visible,
        conversion_source:'children_age_filter'
      });
    }
  }
  form.hidden=false;
  render();
  form.addEventListener('submit',function(event){event.preventDefault()});
  [ages,players,times].forEach(function(input){
    input.addEventListener('change',function(){
      track(input.name,render());
    });
  });
  reset.addEventListener('click',function(){
    ages.value='6';
    players.value='2';
    times.value='20';
    track('reset',render());
    ages.focus();
  });
})();
