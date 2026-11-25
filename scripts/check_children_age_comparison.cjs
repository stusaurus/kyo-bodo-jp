/* Chromium regression for parent purchase decisions: actual age, party size, time. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');

const root=path.resolve('site');
const out=path.resolve('audit-results/children-age-comparison');
fs.mkdirSync(out,{recursive:true});
const base='/kyo-bodo-jp/';
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
function supports(g,n){
  return g.players_min<=n && (g.players_max===null ?
    g.players_open_ended===true && !!g.players_source : n<=g.players_max);
}
const eligible=catalog.filter(g=>g.age<=12&&[2,3,4,5,6].some(n=>supports(g,n)));
function idsFor(age,players,minutes){
  return eligible.filter(g=>g.age<=age&&supports(g,players)&&
    (minutes==='any'||g.play_time_max<=Number(minutes))).map(g=>g.game_id);
}
function createServer(){
  return new Promise(resolve=>{
    const app=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://localhost').pathname;
      if(!pathname.startsWith(base)){res.writeHead(404).end();return}
      let rel;
      try{rel=decodeURIComponent(pathname.slice(base.length))}catch(_){res.writeHead(400).end();return}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return}
      const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    app.listen(8794,'127.0.0.1',()=>resolve(app));
  });
}
async function visibleIds(page){
  return page.locator('#children-choice-results li:not([hidden])')
    .evaluateAll(rows=>rows.map(x=>x.dataset.childGame));
}
(async()=>{
  const app=await createServer();
  const browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
      const page=await ctx.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const resp=await page.goto('http://127.0.0.1:8794'+base+'scenes/children/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(resp.status(),200);
      const filter=page.locator('#children-choice-form');
      await filter.waitFor({state:'visible'});
      assert.equal(await page.locator('#children-choice-results li').count(),eligible.length);
      assert((await page.locator('h1').innerText()).includes('小学生と遊ぶ'));
      assert((await page.title()).includes('6〜12歳・人数・時間で比較'));
      assert.deepEqual(await page.locator('#children-age option').evaluateAll(nodes=>nodes.map(n=>n.value)),
        ['6','7','8','9','10','11','12']);
      const sets=[
        {age:6,players:2,time:'20',label:'default'},
        {age:8,players:4,time:'20',label:'age8-4p-short'},
        {age:9,players:4,time:'20',label:'age9-4p-short'},
        {age:9,players:2,time:'20',label:'age9-2p-short'},
        {age:10,players:5,time:'30',label:'age10-5p-30'},
        {age:12,players:6,time:'any',label:'age12-6p-any'}
      ];
      for(const [i,config] of sets.entries()){
        if(i){
          await page.locator('#children-age').selectOption(String(config.age));
          await page.locator('#children-players').selectOption(String(config.players));
          await page.locator('#children-time').selectOption(config.time);
        }
        const ids=await visibleIds(page);
        const expected=idsFor(config.age,config.players,config.time);
        assert.deepEqual(ids,expected,config.label+' wrong candidates at '+width);
        if(config.label==='age9-4p-short'){
          assert(ids.includes('scout')&&ids.includes('insider-game')&&ids.includes('eggsposed'), '9y 4p should contain all three age-nine games');
          assert(ids.length===idsFor(8,4,'20').length+2,'9y must add only the two published age-nine games');
        }
        if(config.label==='age9-2p-short'){
          assert(ids.includes('scout')&&!ids.includes('insider-game')&&!ids.includes('eggsposed'), '9y 2p excludes games requiring at least three players');
        }
        assert.equal((await page.locator('#children-choice-count').innerText()).trim(),expected.length+'本');
        assert.equal(await page.locator('#children-choice-empty').isVisible(),expected.length===0);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),
          config.label+' horizontal overflow '+width);
        assert.equal(errors.length,0,errors.join('\n'));
        const labels=await page.locator('#children-choice-results li:not([hidden]) a').allTextContents();
        assert(labels.every(x=>x.includes('対象')&&x.includes('すること：')),'missing comparison metadata');
        if(i===0||config.label==='age9-4p-short'||config.label==='age12-6p-any'){
          await page.screenshot({path:path.join(out,config.label+'-'+width+'.png'),
                                 fullPage:true,animations:'disabled'});
        }
        console.log(JSON.stringify({width,scenario:config.label,matched:ids.length,errors:0,overflow:0}));
      }
      await page.locator('#children-choice-reset').click();
      assert.deepEqual(await visibleIds(page),idsFor(6,2,'20'),'reset must restore default');
      assert.equal(await page.locator('#children-age').inputValue(),'6');
      const source=page.locator('#children-choice-results li:not([hidden]) a').first();
      assert.equal(await source.getAttribute('data-source'),'children_age_filter');
      const href=await source.getAttribute('href');
      assert(href.startsWith(base+'games/'),'link must target existing game details');
      const detail=await page.request.get('http://127.0.0.1:8794'+href);
      assert.equal(detail.status(),200);
      const analytics=await page.evaluate(()=>window.dataLayer.map(x=>Array.from(x))
        .filter(x=>x[0]==='event'&&x[1]==='children_filter_change'));
      assert(analytics.length>=1,'filter change needs aggregate interaction event');
      assert(analytics.every(x=>x[2].operator_test==='1'),'operator traffic must remain test traffic');
      assert(analytics.every(x=>x[2].child_age===undefined &&
                               x[2].age===undefined),'do not transmit child ages');
      await ctx.close();

      const noJs=await browser.newContext({viewport:{width,height:850},javaScriptEnabled:false});
      const staticPage=await noJs.newPage();
      await staticPage.goto('http://127.0.0.1:8794'+base+'scenes/children/',{waitUntil:'domcontentloaded'});
      assert.equal(await staticPage.locator('#children-choice-form').isVisible(),false);
      assert.deepEqual(await visibleIds(staticPage),idsFor(6,2,'20'));
      assert((await staticPage.locator('noscript').textContent()).includes('全作品から探す'));
      await noJs.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>app.close(resolve));
  }
})().catch(err=>{fs.writeFileSync(path.join(out,'failure.txt'),String(err.stack));console.error(err);process.exitCode=1});
