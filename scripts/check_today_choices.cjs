/* Real browser regression: intent -> factual cards -> saved shelf -> return visit. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const out=path.resolve('audit-results/today-choice');
fs.mkdirSync(out,{recursive:true});

function server(root,port){
  const base=path.resolve(root);
  return new Promise(resolve=>{
    const app=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://localhost').pathname;
      let rel;
      try{rel=decodeURIComponent(pathname).replace(/^\/kyo-bodo-jp\/?/,'')}catch(_){res.writeHead(400).end();return}
      let file=path.resolve(base,rel);
      if(file!==base&&!file.startsWith(base+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return}
      const ext=path.extname(file);
      const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',types[ext]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    app.listen(port,'127.0.0.1',()=>resolve(app));
  });
}
(async()=>{
  const app=await server('site',8788);
  const browser=await chromium.launch();
  const raw=JSON.parse(fs.readFileSync('site/data/games.json','utf8'));
  const byId=new Map(raw.map(g=>[g.game_id,g]));
  try {
    for(const width of [320,390,1440]){
      const context=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,route=>route.abort());
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const response=await page.goto('http://127.0.0.1:8788/kyo-bodo-jp/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('[data-today-mode="all"]').waitFor({timeout:15000});
      assert.equal(await page.locator('[data-today-mode]').count(),4);
      assert.equal(await page.locator('.today-pick').count(),3);
      await page.locator('[data-today-mode="two"]').click();
      assert.equal(await page.locator('[data-today-mode="two"]').getAttribute('aria-pressed'),'true');
      assert.equal(await page.evaluate(()=>localStorage.getItem('kyo_bodo_today_mode_v1')),null,'filter must not persist without opt-in');
      const twoInsights=page.locator('.today-pick [data-decision-insight]');
      assert.equal(await twoInsights.count(),await page.locator('.today-pick').count());
      for(const verdict of await twoInsights.all())assert.equal(await verdict.getAttribute('data-decision-insight'),'eligible','only publisher-supported 2-player candidates may be recommended');
      const twoIds=await page.locator('.today-pick [data-game-id][data-track]').evaluateAll(els=>els.map(x=>x.dataset.gameId));
      assert(twoIds.length>0&&twoIds.length<=3);
      for(const id of twoIds){
        const g=byId.get(id);assert(g,'unknown game '+id);
        assert(g.players_min<=2 && (g.players_max>=2 || (g.players_max==null&&g.players_open_ended===true&&g.players_source)));
      }
      await page.locator('.today-pick [data-today-save]').first().click();
      assert.equal(await page.locator('#todaySavedGames[hidden]').count(),0);
      assert.equal(await page.locator('#todaySavedGames a').count(),1);
      await page.locator('[data-today-remember]').click();
      assert.equal(await page.locator('[data-today-remember]').getAttribute('aria-pressed'),'true');
      await page.reload({waitUntil:'domcontentloaded'});
      await page.locator('[data-today-mode="two"][aria-pressed="true"]').waitFor({timeout:15000});
      assert.equal(await page.locator('#todaySavedGames a').count(),1);
      await page.locator('#todaySavedGames [data-today-remove]').click();
      assert.equal(await page.locator('#todaySavedGames[hidden]').count(),1);
      await page.locator('[data-today-mode="family"]').click();
      const familyIds=await page.locator('.today-pick [data-game-id][data-track]').evaluateAll(els=>els.map(x=>x.dataset.gameId));
      for(const id of familyIds)assert(Number(byId.get(id).family)>=4);
      await page.locator('[data-today-mode="short"]').click();
      const shortInsights=page.locator('.today-pick [data-decision-insight]');
      assert.equal(await shortInsights.count(),await page.locator('.today-pick').count());
      for(const verdict of await shortInsights.all())assert.equal(await verdict.getAttribute('data-decision-insight'),'eligible','short-play recommendation requires confirmed duration');
      const shortIds=await page.locator('.today-pick [data-game-id][data-track]').evaluateAll(els=>els.map(x=>x.dataset.gameId));
      for(const id of shortIds)assert(Number(byId.get(id).play_time_max)<=30);
      await page.locator('[data-today-remember]').click();
      const remembered=await page.evaluate(()=>localStorage.getItem('kyo_bodo_today_mode_v1'));
      assert.equal(remembered,null);
      const sizes=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
      assert(sizes.scrollWidth<=width+3,'horizontal overflow at '+width+': '+sizes.scrollWidth);
      assert.equal(errors.length,0,errors.join('\n'));
      await page.screenshot({path:path.join(out,'choice-'+width+'.png'),animations:'disabled',fullPage:true});
      console.log(JSON.stringify({width,defaults:3,two:twoIds.length,family:familyIds.length,short:shortIds.length,memory:'explicit+reversible'}));
      await context.close();
    }

    // Real conversion surfaces must use the edition-specific fallback from
    // generated public data, not only the static detail pages.
    const safeSearches={
      qwirkle:'クゥワークル 日本語版',
      cascadia:'カスカディア 日本語版 ケンビル',
      nmbr9:'ナンバーナイン NMBR9 ボードゲーム'
    };
    for(const [gid,phrase] of Object.entries(safeSearches)){
      const g=byId.get(gid);
      assert(g,'catalog game missing: '+gid);
      const expected='https://search.rakuten.co.jp/search/mall/'+encodeURIComponent(phrase)+'/';
      const ctx=await browser.newContext({viewport:{width:390,height:850},isMobile:true,hasTouch:true});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,route=>route.abort());
      await ctx.route('**/data/games.json',route=>route.fulfill({
        status:200,contentType:'application/json',body:JSON.stringify([g])
      }));
      await ctx.route('**/data/rakuten.json',route=>route.fulfill({
        status:200,contentType:'application/json',body:'{}'
      }));
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await page.goto('http://127.0.0.1:8788/kyo-bodo-jp/?test=1',{waitUntil:'domcontentloaded'});
      const todaySearch=page.locator('.today-pick a[data-track="rakuten_search_click"]');
      await todaySearch.waitFor({state:'visible'});
      assert.equal(await todaySearch.count(),1,gid+' should be one search-only card');
      assert.equal(await todaySearch.getAttribute('href'),expected,'today edition mismatch '+gid);
      assert.equal(await todaySearch.getAttribute('data-affiliate'),null);
      assert.equal(await todaySearch.getAttribute('rel'),'noopener');
      await page.goto('http://127.0.0.1:8788/kyo-bodo-jp/diagnosis/?test=1',{waitUntil:'domcontentloaded'});
      for(const answer of ['family','skip','2','think','120','3','skill']){
        await page.locator('.answer[data-v="'+answer+'"]').click();
      }
      const diagnosisSearch=page.locator('.result-card a[data-track="rakuten_search_click"]');
      await diagnosisSearch.waitFor({state:'visible'});
      assert.equal(await diagnosisSearch.count(),1,gid+' should appear in safe diagnosis results');
      assert.equal(await diagnosisSearch.getAttribute('href'),expected,'diagnosis edition mismatch '+gid);
      assert.equal(await diagnosisSearch.getAttribute('data-affiliate'),null);
      assert.equal(await diagnosisSearch.getAttribute('rel'),'noopener');
      assert.equal(errors.length,0,errors.join('; '));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3));
      console.log(JSON.stringify({game:gid,todaySearch:expected,diagnosisSearch:expected,
        directAffiliate:false,errors:0,overflow:0}));
      await ctx.close();
    }
  } finally {
    await browser.close();
    await new Promise(resolve=>app.close(resolve));
  }
})().catch(e=>{console.error(e);process.exitCode=1});
