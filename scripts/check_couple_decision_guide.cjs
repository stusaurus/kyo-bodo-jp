/* Real-browser QA of the newly scoped couple landing page. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve('site'),base='/kyo-bodo-jp/',port=8794;
const out=path.resolve('audit-results/couple-guide');
fs.mkdirSync(out,{recursive:true});
const games=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
const ids=['ito','codenames-duet','patchwork'];
function serve(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://127.0.0.1').pathname;
      if(!pathname.startsWith(base)){res.writeHead(404).end();return;}
      let rel;try{rel=decodeURIComponent(pathname.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(port,'127.0.0.1',()=>resolve(server));
  });
}
(async()=>{
  const server=await serve(),browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:860},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',err=>errors.push(err.message));
      const response=await page.goto('http://127.0.0.1:'+port+base+'scenes/couple/',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      assert((await page.title()).includes('カップル・夫婦で遊べる2人用ボードゲーム'));
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),
        'https://stusaurus.github.io'+base+'scenes/couple/');
      const choices=page.locator('.couple-choice-card');
      assert.equal(await choices.count(),3);
      const discovered=await choices.locator('a[data-source="couple_choice"]').evaluateAll(
        els=>els.map(a=>({href:a.getAttribute('href'),id:a.dataset.gameId})));
      assert.deepEqual(discovered.map(x=>x.id),ids);
      for(let i=0;i<ids.length;i++){
        const g=games.find(x=>x.game_id===ids[i]);
        assert(g,'missing published game '+ids[i]);
        assert(g.players_min<=2 && (g.players_max>=2 || (g.players_open_ended && g.players_source)),'not for two');
        const choice=choices.nth(i),text=await choice.innerText();
        assert(text.includes(g.title));
        assert(text.includes(String(g.age)+'歳〜'));
        assert.equal(discovered[i].href,base+'games/'+ids[i]+'/');
        assert.equal((await page.request.get('http://127.0.0.1:'+port+discovered[i].href)).status(),200);
        const rect=await choice.locator('a[data-source="couple_choice"]').boundingBox();
        assert(rect&&rect.height>=44,'CTA under 44px');
      }
      const grid=await choices.evaluateAll(xs=>xs.map(x=>x.getBoundingClientRect().top));
      if(width<760)assert(grid[0]<grid[1]&&grid[1]<grid[2],'mobile must stack cards');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'couple overflow '+width);
      assert.deepEqual(errors,[],errors.join('; '));
      await page.locator('.couple-choice').screenshot({path:path.join(out,'couple-choice-'+width+'.png'),animations:'disabled'});
      await page.goto('http://127.0.0.1:'+port+base+'scenes/two-player/',{waitUntil:'domcontentloaded'});
      assert(await page.locator('a[href="'+base+'scenes/couple/"]').count()>0,'two-player entry missing');
      assert((await page.locator('main').innerText()).includes('夫婦・カップルなら会話・協力・対戦から選ぶ'));
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+3),false,'two-player overflow '+width);
      assert.deepEqual(errors,[],errors.join('; '));
      console.log(JSON.stringify({width,verifiedLinks:3,source:'published game facts',mobileOverflow:0,jsErrors:0}));
      await ctx.close();
    }
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(err=>{fs.writeFileSync(path.join(out,'failure.txt'),String(err.stack));console.error(err);process.exitCode=1;});
