/* Synthetic preorder UI QA: no API credentials, user data, or publication. */
const {chromium}=require('playwright');
const {execFileSync}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const out=path.resolve('audit-results/rakuten-preorder');
fs.mkdirSync(out,{recursive:true});
const fixture=path.join(out,'the-game-reservation-preview.html');
const fallback=path.join(out,'mandala-unverified-search-preview.html');
const url='https://hb.afl.rakuten.co.jp/hgc/qa-synthetic-the-game';
const python=[
  'from pathlib import Path',
  'from scripts import build_site as s',
  'game=s.BY_ID["the-game"]',
  's.RAKUTEN["the-game"]={"url":"'+url+'","image_url":"","preorder":True}',
  'Path("'+fixture.replace(/\\/g,'/')+'").write_text(s.game_page(game),encoding="utf-8")',
  's.RAKUTEN["mandala"]={}',
  'Path("'+fallback.replace(/\\/g,'/')+'").write_text(s.game_page(s.BY_ID["mandala"]),encoding="utf-8")'
].join('; ');
execFileSync('python',['-c',python],{stdio:'inherit'});
const root=path.resolve('site');
const base='/kyo-bodo-jp/';
function serve(){
  return new Promise(resolve=>{
    const app=http.createServer((req,res)=>{
      let rel;try{
        const u=new URL(req.url,'http://127.0.0.1');
        if(!u.pathname.startsWith(base)){res.writeHead(404).end();return}
        rel=decodeURIComponent(u.pathname.slice(base.length));
      }catch(_){res.writeHead(400).end();return}
      if(rel==='games/the-game/'||rel==='games/mandala/'){
        res.setHeader('Content-Type','text/html; charset=utf-8');
        fs.createReadStream(rel==='games/the-game/'?fixture:fallback).pipe(res);
        return;
      }
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return}
      const ext=path.extname(file);
      const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',mime[ext]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    app.listen(8793,'127.0.0.1',()=>resolve(app));
  });
}
(async()=>{
  const app=await serve();
  const browser=await chromium.launch();
  try {
    for(const width of [320,390,1440]){
      const ctx=await browser.newContext({viewport:{width,height:880},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
      const page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const res=await page.goto('http://127.0.0.1:8793'+base+'games/the-game/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(res.status(),200);
      assert.equal((await page.locator('.game-detail-hero h1').innerText()).trim(),'ザ・ゲーム');
      const cta=page.locator('.product-panel a.btn.rakuten.large');
      assert((await cta.innerText()).includes('楽天で予約状況を確認'));
      assert.equal(await cta.getAttribute('data-affiliate'),'rakuten');
      assert.equal(await cta.getAttribute('rel'),'sponsored noopener');
      assert.equal(await cta.getAttribute('href'),url);
      const availability=await page.locator('.product-availability').innerText();
      assert(availability.includes('予約表示があります'));
      assert(availability.includes('発送予定'));
      const dimensions=await page.evaluate(()=>({
        viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
        buttonWidth:document.querySelector('.product-panel a.btn.rakuten.large').getBoundingClientRect().width,
        panelWidth:document.querySelector('.product-panel').getBoundingClientRect().width
      }));
      assert(dimensions.scrollWidth<=width+3,'preorder page horizontal overflow at '+width);
      assert(dimensions.buttonWidth<=dimensions.panelWidth+2,'preorder CTA out of panel at '+width);
      assert.equal(errors.length,0,errors.join('; '));
      await page.screenshot({path:path.join(out,'the-game-'+width+'.png'),fullPage:true,animations:'disabled'});
      const fallbackResponse=await page.goto('http://127.0.0.1:8793'+base+'games/mandala/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(fallbackResponse.status(),200);
      assert.equal((await page.locator('.game-detail-hero h1').innerText()).trim(),'マンダラ');
      const searchPanel=page.locator('.product-panel');
      const searchCTA=searchPanel.locator('a.btn.rakuten.large');
      assert((await searchCTA.innerText()).includes('楽天で探す'));
      assert.equal(await searchCTA.getAttribute('data-affiliate'),null);
      assert.equal(await searchCTA.getAttribute('data-track'),'rakuten_search_click');
      assert.equal(await searchCTA.getAttribute('rel'),'noopener');
      assert((await searchCTA.getAttribute('href')).startsWith('https://search.rakuten.co.jp/search/mall/'));
      const panelText=await searchPanel.innerText();
      assert(panelText.includes('掲載作品と一致する販売商品を確認できていません'));
      assert(panelText.includes('通常検索へ移動します'));
      assert(panelText.includes('別作品・拡張版・中古品'));
      assert(!panelText.includes('PR：'), 'unverified search must not be represented as a sponsored offer');
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),'fallback panel overflow '+width);
      assert.equal(errors.length,0,errors.join('; '));
      await page.screenshot({path:path.join(out,'mandala-unverified-'+width+'.png'),fullPage:true,animations:'disabled'});
      console.log(JSON.stringify({width,title:'the-game + mandala',cta:'preorder + search',outbound:'verified + unverified synthetic',errors:0,overflow:0}));
      await ctx.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>app.close(resolve));
  }
})().catch(e=>{fs.writeFileSync(path.join(out,'failure.txt'),String(e.stack));console.error(e);process.exitCode=1});
