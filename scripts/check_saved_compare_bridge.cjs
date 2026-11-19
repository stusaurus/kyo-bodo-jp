/* Real browser: home saved picks -> generic URL -> existing comparison with no IDs leaked. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve('site'),base='/kyo-bodo-jp/',port=8799;
const out=path.resolve('audit-results/saved-compare');
fs.mkdirSync(out,{recursive:true});
function serve(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://localhost').pathname;
      if(!pathname.startsWith(base)){res.writeHead(404).end();return}
      let rel;
      try{rel=decodeURIComponent(pathname.slice(base.length))}catch{res.writeHead(400).end();return}
      let target=path.resolve(root,rel);
      if(target!==root&&!target.startsWith(root+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(target)&&fs.statSync(target).isDirectory())target=path.join(target,'index.html');
      if(!fs.existsSync(target)){res.writeHead(404).end();return}
      const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.css':'text/css','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(target)]||'application/octet-stream');
      fs.createReadStream(target).pipe(res);
    });
    server.listen(port,'127.0.0.1',()=>resolve(server));
  });
}
(async()=>{
  const server=await serve(),browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const context=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/,route=>route.abort());
      const page=await context.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const response=await page.goto('http://127.0.0.1:'+port+base,{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('.today-pick [data-today-save]').first().waitFor({timeout:15000});
      assert.equal(await page.locator('#todaySavedGames .today-saved-compare').count(),0,'one pick required at first');
      await page.locator('.today-pick [data-today-save]').first().click();
      assert.equal(await page.locator('#todaySavedGames .today-saved-compare').count(),0,'single saved title must not show comparison CTA');
      await page.locator('.today-pick [data-today-save]').nth(1).click();
      const ids=await page.evaluate(()=>JSON.parse(localStorage.getItem('kyo_bodo_saved_games_v1')||'[]'));
      assert.equal(ids.length,2,'two distinct games should be saved');
      assert.notEqual(ids[0],ids[1]);
      const cta=page.locator('#todaySavedGames .today-saved-compare');
      assert.equal(await cta.count(),1,'CTA should appear for at least two valid saved games');
      assert.equal(await cta.getAttribute('href'),base+'games/#savedCompare');
      assert((await page.locator('.today-saved-compare-actions').innerText()).includes('最後に保存した2本'));
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'home overflow '+width);
      await cta.scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(out,'saved-shelf-'+width+'.png'),animations:'disabled'});
      await cta.click();
      await page.waitForURL('**/games/#savedCompare');
      await page.locator('#catalogCompare:not([hidden])').waitFor({timeout:15000});
      await page.locator('#catalogCompareResult .catalog-compare-card').first().waitFor({timeout:15000});
      assert.equal(await page.locator('#catalogCompareFirst').inputValue(),ids[0]);
      assert.equal(await page.locator('#catalogCompareSecond').inputValue(),ids[1]);
      assert.equal(await page.locator('#catalogCompareResult .catalog-compare-card').count(),2);
      assert((await page.locator('.catalog-compare-loaded').innerText()).includes('最後の2作品'));
      assert.equal(new URL(page.url()).hash,'#savedCompare');
      assert(!page.url().includes(ids[0])&&!page.url().includes(ids[1]),'game IDs should not be sent in URL');
      const persisted=await page.evaluate(()=>JSON.parse(localStorage.getItem('kyo_bodo_saved_games_v1')||'[]'));
      assert.deepEqual(persisted,ids,'comparison must not change existing saved shelf');
      const comparisonEvents=await page.evaluate(()=>(window.dataLayer||[]).filter(x=>x&&x[0]==='event'&&x[1]==='catalog_compare_use').map(x=>x[2]));
      assert.equal(comparisonEvents.length,1);
      assert.deepEqual(Object.keys(comparisonEvents[0]).sort(),['compared_count']);
      assert.equal(comparisonEvents[0].compared_count,2);
      const links=page.locator('#catalogCompareResult a[data-track="game_detail_click"]');
      assert.equal(await links.count(),2);
      for(const link of await links.all()){
        const href=await link.getAttribute('href');
        assert.equal((await page.request.get('http://127.0.0.1:'+port+href)).status(),200);
      }
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'compare overflow '+width);
      assert.deepEqual(errors,[],errors.join('; '));
      await page.screenshot({path:path.join(out,'auto-compared-'+width+'.png'),animations:'disabled'});
      await page.goBack({waitUntil:'domcontentloaded'});
      await page.locator('#todaySavedGames .today-saved-compare').waitFor({timeout:15000});
      await page.locator('#todaySavedGames [data-today-remove]').first().click();
      assert.equal(await page.locator('#todaySavedGames .today-saved-compare').count(),0,'CTA must disappear after dropping below two saved');
      await page.goto('http://127.0.0.1:'+port+base+'games/#savedCompare',{waitUntil:'domcontentloaded'});
      await page.locator('#catalogCompare:not([hidden])').waitFor({timeout:15000});
      assert((await page.locator('#catalogCompareResult').innerText()).includes('保存作品が2本未満'));
      assert.equal(await page.locator('#catalogCompareResult .catalog-compare-card').count(),0);
      assert.deepEqual(errors,[],errors.join('; '));
      console.log(JSON.stringify({width,fromSaved:2,prefill:2,links:2,hash:'IDs omitted',analytics:'count only',oneSaved:'safe fallback',overflow:0,jsErrors:0}));
      await context.close();
    }
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(err=>{console.error(err);process.exitCode=1});
