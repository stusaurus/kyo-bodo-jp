/* Browser QA: real catalog data, independent two-item comparison and no tracking of selections. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve('site'),base='/kyo-bodo-jp/',port=8798;
const out=path.resolve('audit-results/catalog-compare');
fs.mkdirSync(out,{recursive:true});
function start(){
  return new Promise(resolve=>{
    const app=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://localhost').pathname;
      if(!pathname.startsWith(base)){res.writeHead(404).end();return}
      let rel;try{rel=decodeURIComponent(pathname.slice(base.length))}catch{res.writeHead(400).end();return}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return}
      const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.css':'text/css','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    app.listen(port,'127.0.0.1',()=>resolve(app));
  });
}
(async()=>{
  const server=await start(),browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const context=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/,route=>route.abort());
      const page=await context.newPage(),errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      const response=await page.goto('http://127.0.0.1:'+port+base+'games/',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('#catalogCompare:not([hidden])').waitFor({timeout:15000});
      const first=page.locator('#catalogCompareFirst'),second=page.locator('#catalogCompareSecond'),results=page.locator('#catalogCompareResult');
      assert.equal(await first.locator('option').count(),92,'must offer all 91 catalog titles');
      assert.equal(await second.locator('option').count(),92);
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),91,'catalog remains complete');
      await first.selectOption('nana-toridori');
      assert.equal(await results.locator('.catalog-compare-card').count(),0);
      await second.selectOption('nmbr9');
      assert.equal(await results.locator('.catalog-compare-card').count(),2);
      const cards=results.locator('.catalog-compare-card');
      const text1=await cards.nth(0).innerText(),text2=await cards.nth(1).innerText();
      assert(text1.includes('ナナトリドリ')&&text1.includes('2〜6人')&&text1.includes('10〜20分')&&text1.includes('6歳〜'));
      assert(text2.includes('ナンバーナイン')&&text2.includes('1〜4人')&&text2.includes('20分')&&text2.includes('8歳〜'));
      assert.equal(await cards.nth(0).locator('.catalog-compare-rules li').count(),3);
      assert.equal(await cards.nth(1).locator('.catalog-compare-rules li').count(),3);
      for(const link of await results.locator('a[data-track="game_detail_click"]').all()){
        assert.equal(await link.getAttribute('data-source'),'catalog_compare');
        const href=await link.getAttribute('href');
        assert.equal((await page.request.get('http://127.0.0.1:'+port+href)).status(),200);
        assert(!href.includes('rakuten'),'compare links are only own game details');
      }
      const tracked=await page.evaluate(()=>window.dataLayer.filter(x=>x&&x[0]==='event'&&x[1]==='catalog_compare_use').map(x=>x[2]));
      assert.equal(tracked.length,1);
      assert.equal(tracked[0].compared_count,2);
      for(const field of ['game_id','game_ids','players','age','search_term','query']){
        assert.equal(tracked[0][field],undefined,'do not send comparison content to GA4');
      }
      await page.screenshot({path:path.join(out,'two-games-'+width+'.png'),animations:'disabled'});
      // Capture the complete comparison, not just its heading above the fold.
      await page.locator('#catalogCompare').screenshot({path:path.join(out,'comparison-panel-'+width+'.png'),animations:'disabled'});
      await second.selectOption('nana-toridori');
      assert.equal(await cards.count(),0,'cannot compare a game to itself');
      assert((await results.innerText()).includes('別の作品を選んでください'));
      await second.selectOption('');
      assert.equal(await cards.count(),0,'missing second game should not show stale comparison');
      await second.selectOption('nmbr9');
      assert.equal(await cards.count(),2);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'body overflow '+width);
      assert.deepEqual(errors,[],'JS errors '+width);
      await context.close();
      const noJS=await browser.newContext({viewport:{width,height:850},javaScriptEnabled:false});
      const without=await noJS.newPage();
      await without.goto('http://127.0.0.1:'+port+base+'games/');
      assert.equal(await without.locator('.game-list-card:not([hidden])').count(),91);
      assert.equal(await without.locator('#catalogCompare:not([hidden])').count(),0);
      await noJS.close();
      console.log(JSON.stringify({width,catalog:91,compare:2,duplicate:'blocked',detailLinks:2,noJS:'91 links',overflow:0,jsErrors:0,privateAnalytics:true}));
    }
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(error=>{console.error(error);process.exitCode=1});
