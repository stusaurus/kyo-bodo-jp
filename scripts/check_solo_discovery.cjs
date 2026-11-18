/* Chromium regression: one-player scene -> catalog filter -> diagnosis. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve('site'),output=path.resolve('audit-results/solo-discovery');
fs.mkdirSync(output,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
const eligible=data.filter(g=>g.players_min<=1&&(g.players_max===null?g.players_open_ended===true&&!!g.players_source:g.players_max>=1));
assert(eligible.length>=10,'expected substantial solo catalog');
assert(eligible.some(g=>g.game_id==='ark-nova'),'new heavy strategy title must be solo eligible');
const byTitle=new Map(data.map(g=>[g.title,g]));
const base='/kyo-bodo-jp/';
const server=new Promise(resolve=>{
  const app=http.createServer((req,res)=>{
    const pathname=new URL(req.url,'http://127.0.0.1').pathname;
    if(!pathname.startsWith(base)){res.writeHead(404).end();return}
    let rel;
    try{rel=decodeURIComponent(pathname.slice(base.length))}catch(_){res.writeHead(400).end();return}
    let file=path.resolve(root,rel);
    if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return}
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)){res.writeHead(404).end();return}
    const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.json':'application/json','.css':'text/css','.webp':'image/webp'};
    res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
    fs.createReadStream(file).pipe(res);
  });
  app.listen(8792,'127.0.0.1',()=>resolve(app));
});
(async()=>{
  const app=await server;
  const browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:860},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      let response=await page.goto('http://127.0.0.1:8792'+base+'scenes/solo/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      assert((await page.locator('h1').innerText()).includes('1人で遊ぶ'));
      const actual=await page.locator('.game-card h3').allTextContents();
      assert.equal(actual.length,eligible.length,'solo scene must show all eligible games');
      for(const title of actual)assert(eligible.some(g=>g.title===title),'non-solo game '+title);
      assert.equal(await page.locator('.scene-data-table tbody tr').count(),eligible.length);
      assert((await page.locator('.scene-quick-comparison').innerText()).includes('ソロ用ルール'));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),'solo scene overflow '+width);
      await page.screenshot({path:path.join(output,'scene-'+width+'.png'),fullPage:true,animations:'disabled'});
      response=await page.goto('http://127.0.0.1:8792'+base+'games/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('[data-filter="solo"]').click();
      assert.equal(await page.locator('[data-filter="solo"]').getAttribute('aria-pressed'),'true');
      const visible=page.locator('.game-list-card:visible');
      const catalogCount=await visible.count();
      assert.equal(catalogCount,eligible.length);
      assert((await page.locator('#filterCount').innerText()).includes(String(eligible.length)));
      assert((await visible.evaluateAll(xs=>xs.map(x=>x.dataset.solo))).every(x=>x==='1'));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),'catalog overflow '+width);
      await page.screenshot({path:path.join(output,'catalog-'+width+'.png'),fullPage:true,animations:'disabled'});
      response=await page.goto('http://127.0.0.1:8792'+base+'diagnosis/?src=solo_test&test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('.answer[data-v="solo"]').click();
      const persons=page.locator('.answer');
      assert.equal(await persons.count(),1,'solo who choice must not permit 2+ players');
      await page.locator('.answer[data-v="1"]').click();
      const moods=await page.locator('.answer').evaluateAll(xs=>xs.map(x=>x.dataset.v));
      assert.deepEqual(moods,['think','relax','compete']);
      await page.locator('.answer[data-v="think"]').click();
      await page.locator('.answer[data-v="120"]').click();
      await page.locator('.answer[data-v="5"]').click();
      await page.locator('.answer[data-v="skill"]').click();
      await page.locator('.result-card h3').first().waitFor();
      const recommendations=await page.locator('.result-card h3').allTextContents();
      assert(recommendations.length>0);
      for(const title of recommendations){
        const game=byTitle.get(title);
        assert(game&&eligible.some(g=>g.game_id===game.game_id),'recommendation not solo-supported: '+title);
      }
      assert((await page.locator('.diagnosis-heading').innerText()).includes('あなたの'));
      const event=await page.evaluate(()=>window.dataLayer.map(x=>Array.from(x)).find(x=>x[0]==='event'&&x[1]==='diagnosis_complete'));
      assert(event,'missing diagnosis_complete event');
      assert.equal(event[2].players,'1');
      assert.equal(event[2].who,'solo');
      assert.equal(event[2].operator_test,'1');
      assert.equal(errors.length,0,errors.join('\n'));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),'diagnosis overflow '+width);
      await page.screenshot({path:path.join(output,'diagnosis-'+width+'.png'),fullPage:true,animations:'disabled'});
      console.log(JSON.stringify({width,solo:eligible.length,scene:actual.length,catalog:catalogCount,diagnosis:recommendations.length,errors:0,overflow:0}));
      await ctx.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>app.close(resolve));
  }
})().catch(e=>{fs.writeFileSync(path.join(output,'failure.txt'),String(e.stack));console.error(e);process.exitCode=1});
