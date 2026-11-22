/* QA: four purchase-intent routes, generated catalog, no external checkout.
 * 2-player / family / gift / diagnosis -> actual game page -> safe outbound CTA.
 * Browser widths 320/390/1440. No Google analytics calls are sent.
 */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const root=path.resolve('site'),out=path.resolve('audit-results/purchase-journeys');
fs.mkdirSync(out,{recursive:true});
const base='/kyo-bodo-jp/',port=8798,origin='http://127.0.0.1:'+port;
const games=JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
const offers=JSON.parse(fs.readFileSync(path.join(root,'data/rakuten.json'),'utf8'));
const byId=new Map(games.map(g=>[g.game_id,g]));
assert.equal(games.length,88);
function serve(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const url=new URL(req.url,origin);
      if(!url.pathname.startsWith(base)){res.writeHead(404).end();return;}
      let rel;
      try{rel=decodeURIComponent(url.pathname.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const types={'.html':'text/html; charset=utf-8','.js':'text/javascript',
        '.json':'application/json','.css':'text/css','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(port,'127.0.0.1',()=>resolve(server));
  });
}
const canPlay=(g,n)=>g.players_min<=n&&(g.players_max===null?
  g.players_open_ended===true&&!!g.players_source:g.players_max>=n);
async function visit(page,rel){
  const response=await page.goto(origin+base+rel,{waitUntil:'domcontentloaded'});
  assert.equal(response.status(),200,'HTTP 200 expected for '+rel);
  assert.equal((await page.locator('main h1').count()),1,'one H1 for '+rel);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),true,'overflow on '+rel);
}
async function inspectOffer(page,gid,width,route){
  const g=byId.get(gid);
  assert(g,'unknown recommended game '+gid);
  assert.equal(new URL(page.url()).pathname,base+'games/'+gid+'/');
  assert((await page.locator('main h1').innerText()).includes(g.title));
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),
    'https://stusaurus.github.io'+base+'games/'+gid+'/');
  const hero=page.locator('.game-hero-purchase a.game-hero-purchase-link');
  const panel=page.locator('.product-panel a.btn.rakuten.large');
  assert.equal(await hero.count(),1);
  assert.equal(await panel.count(),1);
  const attr={};
  for(const k of ['href','rel','data-affiliate','data-track']){
    const h=await hero.getAttribute(k),p=await panel.getAttribute(k);
    assert.equal(h,p,'hero/panel '+k+' mismatch on '+gid);
    attr[k]=p;
  }
  assert.equal(await panel.getAttribute('data-game-id'),gid);
  const matched=offers[gid]&&offers[gid].url;
  if(matched){
    assert.equal(attr.href,matched,'must use verified API offer '+gid);
    assert(attr.href.startsWith('https://hb.afl.rakuten.co.jp/'));
    assert.equal(attr['data-affiliate'],'rakuten');
    assert.equal(attr['data-track'],null);
    assert.equal(attr.rel,'sponsored noopener');
  }else{
    const expected='https://search.rakuten.co.jp/search/mall/'+encodeURIComponent(g.rakuten_query||g.title)+'/';
    assert.equal(attr.href,expected,'plain unverified search for '+gid);
    assert.equal(attr['data-affiliate'],null);
    assert.equal(attr['data-track'],'rakuten_search_click');
    assert.equal(attr.rel,'noopener');
    assert((await page.locator('.product-panel').innerText()).includes('掲載作品と一致する販売商品を確認できていません'));
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),true,'detail overflow '+gid);
  if(width<=390){
    assert(await hero.isVisible(),'mobile hero CTA not visible '+gid);
    const rect=await hero.boundingBox();
    assert(rect&&rect.height>=44,'mobile CTA under 44px '+gid);
  }
  await page.screenshot({path:path.join(out,route+'-'+width+'.png'),animations:'disabled'});
  return {route,width,gid,verified:!!matched,safe:!matched,jsErrors:0,overflow:0};
}
(async()=>{
  const server=await serve(),browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const context=await browser.newContext({viewport:{width,height:900},
        isMobile:width<500,hasTouch:width<500,locale:'ja-JP'});
      await context.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com|stats\.g\.doubleclick\.net/i,r=>r.abort());
      for(const route of ['two-player','family','gift','diagnosis']){
        const page=await context.newPage(),errors=[];
        page.on('pageerror',e=>errors.push(e.message));
        let gid;
        if(route==='two-player'||route==='family'){
          await visit(page,'scenes/'+route+'/?test=1');
          const link=page.locator('a[data-track="game_detail_click"][data-source="scene_page"]').first();
          await link.waitFor({state:'visible'});
          gid=await link.getAttribute('data-game-id');
          assert(canPlay(byId.get(gid),2) || route==='family','two-person recommendation not eligible');
          assert.equal(await link.getAttribute('href'),base+'games/'+gid+'/');
          await link.click();
        }else if(route==='gift'){
          await visit(page,'guides/gift-board-games/?test=1');
          const link=page.locator('.gift-table a[data-gift-detail="dobble"]').first();
          assert.equal(await link.count(),1);
          gid=await link.getAttribute('data-gift-detail');
          assert(byId.get(gid).age<=6);
          await link.click();
        }else{
          await visit(page,'diagnosis/?test=1');
          for(const choice of ['family','8','4','compete','30','1','half']){
            await page.locator('.answer[data-v="'+choice+'"]').click();
          }
          const cards=page.locator('.result-card');
          assert.equal(await cards.count(),5,'must have 5 candidate games');
          for(const card of await cards.all()){
            const link=card.locator('a[data-track="game_detail_click"]');
            const id=await link.getAttribute('data-game-id');
            const g=byId.get(id);
            assert(g&&!g.cooperative&&canPlay(g,4)&&g.play_time_max<=30&&g.age<=8,
              'competitive recommendation invalid '+id);
            const text=await card.innerText();
            assert(text.includes(String(g.age)+'歳〜'),'age missing '+id);
            assert(text.includes(g.play_time_min+'〜'+g.play_time_max+'分'),'time missing '+id);
            const outbound=card.locator('a[data-affiliate], a[data-track="rakuten_search_click"]');
            assert.equal(await outbound.count(),1,'one product outbound '+id);
            assert.equal(await outbound.getAttribute('data-game-id'),id);
            const product=offers[id]&&offers[id].url;
            assert.equal(await outbound.getAttribute('data-affiliate'),product?'rakuten':null);
            assert.equal(await outbound.getAttribute('data-track'),product?null:'rakuten_search_click');
          }
          await page.screenshot({path:path.join(out,'diagnosis-results-'+width+'.png'),fullPage:true,animations:'disabled'});
          const chosen=cards.first().locator('a[data-track="game_detail_click"]');
          gid=await chosen.getAttribute('data-game-id');
          await chosen.click();
        }
        const result=await inspectOffer(page,gid,width,route);
        assert.deepEqual(errors,[],'browser errors '+route);
        console.log(JSON.stringify(result));
        await page.close();
      }
      // Children's journey: age remains a hard gate in results, with no analytics age event.
      const kid=await context.newPage(),kidErrors=[];
      kid.on('pageerror',e=>kidErrors.push(e.message));
      await visit(kid,'diagnosis/?test=1');
      for(const choice of ['children','5','2','compete','30','1','half']){
        await kid.locator('.answer[data-v="'+choice+'"]').click();
      }
      const kidCards=kid.locator('.result-card');
      assert(await kidCards.count()>0,'child age-filtered diagnosis should return games');
      for(const card of await kidCards.all()){
        const id=await card.locator('a[data-track="game_detail_click"]').getAttribute('data-game-id');
        const g=byId.get(id);
        assert(g&&g.age<=5&&canPlay(g,2)&&!g.cooperative,'underage or incompatible recommendation '+id);
        assert((await card.innerText()).includes(g.age+'歳〜'));
      }
      const ageAnswers=await kid.evaluate(()=>window.dataLayer.filter(x=>x[0]==='event'&&x[1]==='diagnosis_answer'));
      assert(ageAnswers.every(x=>x[2].question_id!=='min_age'&&x[2].answer_value!=='5'));
      assert.equal(await kid.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),true);
      assert.deepEqual(kidErrors,[]);
      await kid.screenshot({path:path.join(out,'diagnosis-child-age-'+width+'.png'),fullPage:true,animations:'disabled'});
      console.log(JSON.stringify({route:'children-age',width,ageMax:5,count:await kidCards.count(),privacy:'no age event',jsErrors:0,overflow:0}));
      await kid.close();
      await context.close();
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{
  fs.writeFileSync(path.join(out,'failure.txt'),String(e.stack||e));
  console.error(e);process.exitCode=1;
});
