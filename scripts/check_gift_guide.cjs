/* Chromium QA of a real pre-purchase gift guide, without GA4 test traffic. */
const { chromium } = require('playwright');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const assert = require('node:assert/strict');
const root = path.resolve('site'), base = '/kyo-bodo-jp/', port = 8793;
const out = path.resolve('audit-results/gift-guide');
fs.mkdirSync(out, { recursive: true });
const games = JSON.parse(fs.readFileSync(path.join(root, 'data/games.json'), 'utf8'));
const groups = [
  {age:6,ids:['dobble','nine-tiles','bandido']},
  {age:8,ids:['zombie-kidz','kingdomino','the-game']},
  {age:10,ids:['harmonies','splendor-duel','the-crew-deep-sea']}
];
const allIds = groups.flatMap(g=>g.ids);
function server(){
  return new Promise(resolve=>{
    const httpServer=http.createServer((req,res)=>{
      const url=new URL(req.url,'http://127.0.0.1');
      if(!url.pathname.startsWith(base)){res.writeHead(404).end();return;}
      let rel;try{rel=decodeURIComponent(url.pathname.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    httpServer.listen(port,'127.0.0.1',()=>resolve(httpServer));
  });
}
(async()=>{
  const serve=await server(),browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:900},isMobile:width<500,hasTouch:width<500,locale:'ja-JP'});
      await ctx.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/i,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const guidePath=base+'guides/gift-board-games/';
      const res=await page.goto('http://127.0.0.1:'+port+guidePath,{waitUntil:'domcontentloaded'});
      assert.equal(res.status(),200);
      assert((await page.title()).includes('ボードゲームのプレゼント'));
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),'https://stusaurus.github.io'+guidePath);
      assert.equal(await page.locator('h1').count(),1);
      assert.equal(await page.locator('.gift-checklist-grid li').count(),3);
      assert.equal(await page.locator('.gift-age').count(),3);
      assert.equal(await page.locator('.gift-age .game-card').count(),9);
      assert.equal(await page.locator('a[data-gift-detail]').count(),9);
      const links=await page.locator('.gift-age .gift-cards a[data-track="game_detail_click"][data-source="gift_guide"]').evaluateAll(xs=>
        xs.map(x=>({id:x.dataset.gameId,href:x.getAttribute('href')})));
      assert.deepEqual(links.map(x=>x.id),allIds);
      const tableLinks=await page.locator('.gift-age .gift-table a[data-gift-detail][data-track="game_detail_click"][data-source="gift_guide"]').evaluateAll(xs=>
        xs.map(x=>({id:x.dataset.gameId,href:x.getAttribute('href')})));
      assert.deepEqual(tableLinks,links,'table links must mirror the nine card links');
      for(const group of groups){
        const section=page.locator('#age-'+group.age);
        const ids=await section.locator('.gift-cards a[data-track="game_detail_click"][data-source="gift_guide"]').evaluateAll(xs=>xs.map(x=>x.dataset.gameId));
        assert.deepEqual(ids,group.ids);
        const text=await section.innerText();
        for(const id of group.ids){
          const game=games.find(g=>g.game_id===id);
          assert(game&&game.age<=group.age,'wrong age for '+id);
          assert(game.players_min<=2 && (game.players_max>=2 || (game.players_open_ended && game.players_source)));
          assert(text.includes(game.title),'missing title '+id);
          assert(text.includes(String(game.age)+'歳〜'),'missing age '+id);
        }
      }
      for(const link of links){
        assert.equal(link.href,base+'games/'+link.id+'/');
        const response=await page.request.get('http://127.0.0.1:'+port+link.href);
        assert.equal(response.status(),200,'missing detail '+link.id);
      }
      const nav=page.locator('.gift-jumps a');
      assert.equal(await nav.count(),3);
      await nav.first().click();
      assert.equal(new URL(page.url()).hash,'#age-6');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'overflow '+width);
      assert.deepEqual(errors,[],errors.join('; '));
      await page.locator('.gift-age').first().screenshot({path:path.join(out,'age-six-'+width+'.png'),animations:'disabled'});
      for(const entry of ['', 'scenes/children/', 'scenes/family/']){
        await page.goto('http://127.0.0.1:'+port+base+entry,{waitUntil:'domcontentloaded'});
        assert(await page.locator('a[href="'+guidePath+'"]').count()>0,'no discovery link: '+entry);
      }
      assert.deepEqual(errors,[],errors.join('; '));
      console.log(JSON.stringify({width,guide200:true,groups:3,qualifiedGames:9,detailLinks200:9,discoveredFrom:3,ga4Blocked:true,jsErrors:0,overflow:0}));
      await ctx.close();
    }
  }finally{await browser.close();await new Promise(resolve=>serve.close(resolve));}
})().catch(e=>{fs.writeFileSync(path.join(out,'failure.txt'),String(e.stack));console.error(e);process.exitCode=1;});
