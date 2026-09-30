(function () {
  var icon='<svg class="placeholder-dice" viewBox="0 0 80 80" fill="none" aria-hidden="true"><rect x="15" y="15" width="50" height="50" rx="13" stroke="currentColor" stroke-width="2"/><g fill="currentColor"><circle cx="28" cy="28" r="3"/><circle cx="52" cy="28" r="3"/><circle cx="40" cy="40" r="3"/><circle cx="28" cy="52" r="3"/><circle cx="52" cy="52" r="3"/></g></svg>';
  function fallback(img) {
    if (!(img instanceof HTMLImageElement) || !img.alt.endsWith('の商品画像')) return;
    var stage=document.createElement('div');
    stage.className='game-placeholder';
    stage.setAttribute('role','img');
    stage.setAttribute('aria-label',img.alt.replace('の商品画像','：商品画像を表示できませんでした'));
    stage.innerHTML=icon;
    img.replaceWith(stage);
  }
  document.addEventListener('error',function(event){ fallback(event.target); },true);
  document.querySelectorAll('img').forEach(function(img){ if(img.complete && !img.naturalWidth) fallback(img); });
})();
