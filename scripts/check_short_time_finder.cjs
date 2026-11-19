/* Chromium smoke and functional QA for 20-minute complete catalog finder. */
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');

const root=path.resolve('site');
const out=path.resolve('audit-results/short-time-finder');
fs.mkdirSync(out,{recursive:true});
const base='/kyo-bodo-jp/';
const port=8798;
const origin='http://127.0.0.1:'+port;
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
const eligible=catalog.filter(g=>g.play_time_max<=20);
function supports(g,n){
  return g.players_min<=n&&(g.players_max===null?
    g.players_open_ended===true&&!!g.players_source:n<=g.players_max);
}
function expected(minutes,players,age){
  return eligible.filter(g=>g.play_time_max<=minutes&&
    (players==='any'||supports(g,Number(players)))&&
    (age==='any'||g.age<=Number(age))).map(g=>g.game_id);
}
function createServer(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const pathName=new URL(req.url,'http://localhost').pathname;
      if(!pathName.startsWith(base)){res.writeHead(404).end();return;}
      let rel;
      try{rel=decodeURIComponent(pathName.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      res.setHeader('Content-Type',({
        '.html':'text/html; charset=utf-8','.js':'text/javascript',
        '.css':'text/css','.json':'application/json','.webp':'image/webp'
      })[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(port,'127.0.0.1',()=>resolve(server));
  });
}
async function visibleIds(page){
  return page.locator('#short-time-results li:not([hidden])')
    .evaluateAll(rows=>rows.map(x=>x.dataset.shortGame));
}
(async()=>{
  const server=await createServer();
  const browser=await chromium.launch();
  try{
    assert.equal(eligible.length,32,'catalog changed; reevaluate full short-time cohort');
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({
        viewport:{width,height:840},isMobile:width<500,hasTouch:width<500
      });
      await ctx.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com/,
        route=>route.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',err=>errors.push(err.message));
      const response=await page.goto(origin+base+'scenes/short/?test=1',
                                     {waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.locator('#short-time-form').waitFor({state:'visible'});
      assert.equal(await page.locator('#short-time-results li').count(),32);
      assert((await page.title()).includes('20分以内・短時間'));
      assert((await page.locator('h1').textContent()).includes('短時間'));
      const scenarios=[
        {label:'all',minutes:'20',players:'any',age:'any'},
        {label:'ten',minutes:'10',players:'any',age:'any'},
        {label:'fifteen-two',minutes:'15',players:'2',age:'any'},
        {label:'twenty-four-age8',minutes:'20',players:'4',age:'8'},
        {label:'ten-eight-age6',minutes:'10',players:'8',age:'6'}
      ];
      for(const [i,s] of scenarios.entries()){
        if(i){
          await page.locator('#short-time-minutes').selectOption(s.minutes);
          await page.locator('#short-time-players').selectOption(s.players);
          await page.locator('#short-time-age').selectOption(s.age);
        }
        const shown=await visibleIds(page),want=expected(Number(s.minutes),s.players,s.age);
        assert.deepEqual(shown,want,width+' '+s.label+' mismatch');
        assert.equal((await page.locator('#short-time-count').textContent()).trim(),
                     want.length+'本');
        assert.equal(await page.locator('#short-time-empty').isVisible(),want.length===0);
        const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3);
        assert.equal(overflow,false,width+' '+s.label+' horizontal overflow');
        assert.deepEqual(errors,[],width+' '+s.label+' JS errors');
        const labels=await page.locator('#short-time-results li:not([hidden]) a').allTextContents();
        assert(labels.every(t=>t.includes('対象')&&t.includes('すること：')));
        console.log(JSON.stringify({width,scenario:s.label,count:shown.length,overflow:0,errors:0}));
      }
      await page.locator('#short-time-reset').click();
      assert.deepEqual(await visibleIds(page),expected(20,'any','any'));
      assert.equal(await page.locator('#short-time-minutes').inputValue(),'20');
      assert.equal(await page.locator('#short-time-players').inputValue(),'any');
      assert.equal(await page.locator('#short-time-age').inputValue(),'any');
      await page.screenshot({path:path.join(out,'short-all-'+width+'.png'),
                             fullPage:false,animations:'disabled'});
      const first=page.locator('#short-time-results li a').first();
      assert.equal(await first.getAttribute('data-source'),'short_time_finder');
      const href=await first.getAttribute('href');
      assert(href.startsWith(base+'games/'));
      assert.equal((await page.request.get(origin+href)).status(),200);
      const tracked=await page.evaluate(()=>window.dataLayer.map(x=>Array.from(x))
        .filter(x=>x[0]==='event'&&x[1]==='short_filter_change'));
      assert(tracked.length>=1);
      assert(tracked.every(x=>x[2].operator_test==='1'));
      assert(tracked.every(x=>!('age' in x[2])&&!('child_age' in x[2])&&
                              !('players' in x[2])&&!('minutes' in x[2])));
      await ctx.close();

      const noJs=await browser.newContext({viewport:{width,height:840},javaScriptEnabled:false});
      const noJsPage=await noJs.newPage();
      await noJsPage.goto(origin+base+'scenes/short/',{waitUntil:'domcontentloaded'});
      assert.equal(await noJsPage.locator('#short-time-form').isVisible(),false);
      assert.deepEqual(await visibleIds(noJsPage),expected(20,'any','any'));
      await noJs.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{fs.writeFileSync(path.join(out,'failure.txt'),String(e.stack));console.error(e);process.exitCode=1});
