/* Browser QA for targeted two-player cooperative purchase guide. */
const { chromium }=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve('site');
const out=path.resolve('audit-results/two-player-cooperative');
fs.mkdirSync(out,{recursive:true});
const base='/kyo-bodo-jp/';
const games=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
const eligible=games.filter(g=>g.cooperative&&g.players_min<=2&&
  (g.players_max===null ? g.players_open_ended===true&&!!g.players_source : 2<=g.players_max));
assert.equal(eligible.length,15);
const partitions=[
  eligible.filter(g=>g.play_time_max<=20),
  eligible.filter(g=>g.play_time_max>20&&g.play_time_max<=30),
  eligible.filter(g=>g.play_time_max>30)
];
function makeServer(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const request=new URL(req.url,'http://127.0.0.1').pathname;
      if(!request.startsWith(base)){res.writeHead(404).end();return;}
      let rel;try{rel=decodeURIComponent(request.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(8796,'127.0.0.1',()=>resolve(server));
  });
}
(async()=>{
  const server=await makeServer();
  const browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:880},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',err=>errors.push(err.message));
      const target=base+'guides/two-player-cooperative/';
      const response=await page.goto('http://127.0.0.1:8796'+target+'?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      assert((await page.title()).includes('2人で協力するボードゲーム比較'));
      assert((await page.locator('h1').innerText()).includes('2人で協力する'));
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),
        'https://stusaurus.github.io'+target);
      const rowIds=await page.locator('tr[data-cooperative-game]').evaluateAll(
        xs=>xs.map(x=>x.dataset.cooperativeGame));
      const groupedIds=partitions.flat().map(g=>g.game_id);
      assert.deepEqual(rowIds,groupedIds);
      const counts=await page.locator('.two-coop-time-group').evaluateAll(
        xs=>xs.map(x=>x.querySelectorAll('tbody tr').length));
      assert.deepEqual(counts,partitions.map(x=>x.length));
      assert.equal(await page.locator('.two-coop-method-card').count(),4);
      assert.equal(await page.locator('.two-coop-related a').count(),3);
      assert((await page.locator('main').innerText()).includes('相談に制限のあるゲーム'));
      for (const g of eligible) {
        const row=page.locator('tr[data-cooperative-game="'+g.game_id+'"]');
        assert((await row.innerText()).includes(g.title));
        assert((await row.innerText()).includes(String(g.age)+'歳〜'));
        const href=await row.locator('a[data-track="game_detail_click"]').getAttribute('href');
        assert.equal(href,base+'games/'+g.game_id+'/');
      }
      const dimensions=await page.evaluate(()=>({
        viewport:innerWidth,
        document:document.documentElement.scrollWidth,
        scrollContainers:[...document.querySelectorAll('.scene-table-scroll')].map(x=>({
          client:x.clientWidth,scroll:x.scrollWidth
        }))
      }));
      assert(dimensions.document<=width+3,'horizontal page overflow: '+width+
        ' got '+dimensions.document);
      assert.equal(dimensions.scrollContainers.length,3);
      assert(dimensions.scrollContainers.every(x=>x.client>0),'table missing at '+width);
      assert.equal(errors.length,0,errors.join('; '));
      await page.screenshot({path:path.join(out,'guide-'+width+'.png'),
        fullPage:true,animations:'disabled'});
      const detail=await page.request.get('http://127.0.0.1:8796'+base+'games/sky-team/');
      assert.equal(detail.status(),200);
      // Readers can arrive from both the existing broad page and homepage.
      for(const url of ['', 'scenes/two-player/']){
        await page.goto('http://127.0.0.1:8796'+base+url+'?test=1',
          {waitUntil:'domcontentloaded'});
        assert(await page.locator('a[href="'+target+'"]').count()>0,
          'missing discovery link '+url);
      }
      assert.equal(errors.length,0,errors.join('; '));
      console.log(JSON.stringify({width,eligible:eligible.length,partitionSizes:counts,
        guideStatus:200,referencedFrom:'home+two-player',errors:0,overflow:0}));
      await ctx.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(err=>{
  fs.writeFileSync(path.join(out,'failure.txt'),String(err.stack));
  console.error(err);process.exitCode=1;
});
