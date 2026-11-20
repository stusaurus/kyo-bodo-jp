/* Real Chromium checks at 320/390/1440px; never click external Rakuten links. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const root=path.resolve('site'),base='/kyo-bodo-jp/';
const out=path.resolve('audit-results/mobile-purchase');
const port=8789;
fs.mkdirSync(out,{recursive:true});
function server(){
  return new Promise(resolve=>{
    const s=http.createServer((req,res)=>{
      let p;
      try{p=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);}
      catch(_){res.writeHead(400).end();return;}
      if(!p.startsWith(base)){res.writeHead(404).end();return;}
      let file=path.resolve(root,p.slice(base.length));
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const type={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',type[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    s.listen(port,'127.0.0.1',()=>resolve(s));
  });
}
(async()=>{
  const serve=await server();
  const browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:900},isMobile:width<500,hasTouch:width<500,locale:'ja-JP'});
      await ctx.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/i,r=>r.abort());
      for(const id of ['dobble','the-game','splendor-duel']){
        const page=await ctx.newPage(),errors=[];
        page.on('pageerror',e=>errors.push(e.message));
        const rel=base+'games/'+id+'/';
        const response=await page.goto('http://127.0.0.1:'+port+rel,{waitUntil:'domcontentloaded'});
        assert.equal(response.status(),200);
        const hero=page.locator('.game-hero-purchase');
        const heroLink=hero.locator('a.game-hero-purchase-link');
        const panelLink=page.locator('.product-panel a.btn.rakuten.large');
        assert.equal(await heroLink.count(),1);
        assert.equal(await panelLink.count(),1);
        const info=await page.evaluate(()=>{
          const h=document.querySelector('.game-hero-purchase a');
          const p=document.querySelector('.product-panel a.btn.rakuten.large');
          const hero=document.querySelector('.game-hero-purchase');
          return {heroHref:h.getAttribute('href'),panelHref:p.getAttribute('href'),
            heroRel:h.rel,panelRel:p.rel,heroAffiliate:h.dataset.affiliate||'',
            panelAffiliate:p.dataset.affiliate||'',heroTrack:h.dataset.track||'',
            panelTrack:p.dataset.track||'',heroSource:h.dataset.source,
            heroVisible:getComputedStyle(hero).display!=='none',
            docWidth:document.documentElement.scrollWidth,viewport:innerWidth,
            height:h.getBoundingClientRect().height,
            disclosure:hero.innerText};
        });
        assert.equal(info.heroHref,info.panelHref,'same outbound URL');
        assert.equal(info.heroRel,info.panelRel,'same safety policy');
        assert.equal(info.heroAffiliate,info.panelAffiliate,'affiliate must be consistent');
        assert.equal(info.heroTrack,info.panelTrack,'search event must be consistent');
        assert.equal(info.heroSource,'game_detail_hero');
        assert.equal(info.heroVisible,width<=760,'desktop must hide duplicate CTA');
        assert(info.docWidth<=info.viewport+2,'mobile horizontal overflow');
        if(width<=760)assert(info.height>=44,'touch target too short');
        if(info.heroAffiliate==='rakuten'){
          assert(info.heroRel.includes('sponsored'));
          assert(info.disclosure.includes('PR：'));
          assert(info.heroHref.startsWith('https://hb.afl.rakuten.co.jp/'));
        }else{
          assert.equal(info.heroTrack,'rakuten_search_click');
          assert(!info.heroRel.includes('sponsored'));
          assert(info.disclosure.includes('検索結果には別作品'));
          assert(info.heroHref.startsWith('https://search.rakuten.co.jp/'));
        }
        assert.deepEqual(errors,[]);
        if(width<500 && id==='dobble')await page.screenshot({path:path.join(out,'dobble-'+width+'.png'),animations:'disabled'});
        console.log(JSON.stringify({width,id,heroVisible:info.heroVisible,affiliate:!!info.heroAffiliate,
          search:!!info.heroTrack,overflow:false,jsErrors:0}));
        await page.close();
      }
      await ctx.close();
    }
  }finally{await browser.close();await new Promise(resolve=>serve.close(resolve));}
})().catch(e=>{fs.writeFileSync(path.join(out,'failure.txt'),String(e.stack||e));console.error(e);process.exitCode=1;});
