/* Chromium proof: title search and category intersection on all catalog games. */
const {chromium}=require('playwright');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve('site'), base='/kyo-bodo-jp/', port=8797;
const out=path.resolve('audit-results/catalog-search');
fs.mkdirSync(out,{recursive:true});
function server(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const url=new URL(req.url,'http://localhost');
      if(!url.pathname.startsWith(base)){res.writeHead(404).end();return;}
      let decoded;try{decoded=decodeURIComponent(url.pathname.slice(base.length))}catch{res.writeHead(400).end();return}
      let file=path.resolve(root,decoded);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return}
      res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(port,'127.0.0.1',()=>resolve(server));
  });
}
(async()=>{
  const app=await server(), browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const res=await page.goto('http://127.0.0.1:'+port+base+'games/',{waitUntil:'domcontentloaded'});
      assert.equal(res.status(),200);
      const cards=page.locator('.game-list-card'),search=page.locator('#catalogTitleSearch');
      assert.equal(await cards.count(),91);
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),91);
      assert.equal(await page.locator('#filterCount').innerText(),'91本のゲーム');
      await search.fill('ナナトリドリ');
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),1);
      assert.equal(await page.locator('.game-list-card:not([hidden])').getAttribute('data-search-title'),'ナナトリドリ');
      assert.equal(await page.locator('#filterCount').innerText(),'1本のゲーム');
      await search.fill('ナナ　トリドリ'); // Japanese full-width space normalized.
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),1);
      await search.fill('ナナトリドリ');
      await page.locator('[data-filter="solo"]').click();
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),0);
      assert(await page.locator('#catalogEmpty').isVisible());
      await page.locator('[data-filter="two"]').click();
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),1);
      assert(!(await page.locator('#catalogEmpty').isVisible()));
      await search.fill('作品名にない文字列');
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),0);
      await page.locator('#catalogSearchReset').click();
      const twoGames=await page.locator('.game-list-card:not([hidden])').count();
      assert(twoGames>20&&twoGames<91,'category should remain active after resetting query');
      await page.locator('[data-filter="all"]').click();
      assert.equal(await page.locator('.game-list-card:not([hidden])').count(),91);
      assert.equal(await page.locator('#filterCount').innerText(),'91本のゲーム');
      assert.equal(await search.inputValue(),'');
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3);
      assert.equal(overflow,false,'catalog overflows at '+width);
      assert.deepEqual(errors,[],'JS errors at '+width);
      await search.fill('ナナトリドリ');
      await page.screenshot({path:path.join(out,'catalog-search-'+width+'.png'),animations:'disabled'});
      const href=await page.locator('.game-list-card:not([hidden])').getAttribute('href');
      assert.equal((await page.request.get('http://127.0.0.1:'+port+href)).status(),200);
      console.log(JSON.stringify({width,all:91,search:1,categoryTwo:twoGames,zeroState:true,overflow:0,jsErrors:0}));
      await ctx.close();
      const ctxNoJS=await browser.newContext({viewport:{width,height:850},javaScriptEnabled:false});
      const nojs=await ctxNoJS.newPage();
      await nojs.goto('http://127.0.0.1:'+port+base+'games/');
      assert.equal(await nojs.locator('.game-list-card:not([hidden])').count(),91,'all links remain visible without JS');
      await ctxNoJS.close();
    }
  }finally{await browser.close();await new Promise(resolve=>app.close(resolve))}
})().catch(e=>{console.error(e);process.exitCode=1});
