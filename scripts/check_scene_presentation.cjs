const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const out=path.resolve('audit-results/scene-presentation');fs.mkdirSync(out,{recursive:true});
function serve(root,port){return new Promise(resolve=>{
 const server=http.createServer((req,res)=>{
  const rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\/kyo-bodo-jp\//,'');
  let file=path.resolve(root,rel);if(!file.startsWith(path.resolve(root)+path.sep)&&file!==path.resolve(root)){res.writeHead(403).end();return;}
  if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
  if(!fs.existsSync(file)){res.writeHead(404).end();return;}
  const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'};
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
 });server.listen(port,'127.0.0.1',()=>resolve(server));
});}
(async()=>{
 const servers=[await serve('audit-results/baseline/site',8765),await serve('site',8766)];
 const browser=await chromium.launch();const records=[];
 try{
  for(const width of [320,390,1440]){
   const context=await browser.newContext({viewport:{width,height:900},isMobile:width<500,hasTouch:width<500});
   await context.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,r=>r.abort());
   const snapshots=[];
   for(const [index,label] of ['before','after'].entries()){
    const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const response=await page.goto(`http://127.0.0.1:${8765+index}/kyo-bodo-jp/scenes/two-player/?test=1`,{waitUntil:'networkidle'});
    assert.equal(response.status(),200);
    const images=page.locator('.game-card img');const imageCount=await images.count();
    for(let i=0;i<await images.count();i++){await images.nth(i).scrollIntoViewIfNeeded();await images.nth(i).evaluate(img=>img.decode());}
    await page.evaluate(()=>scrollTo(0,0));
    const snapshot=await page.evaluate(()=>({
     title:document.title,description:document.querySelector('meta[name="description"]').content,
     canonical:document.querySelector('link[rel="canonical"]').href,h1:document.querySelector('h1').textContent,
     schema:JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent),
     cards:[...document.querySelectorAll('.game-card')].map(el=>({title:el.querySelector('h3').textContent,
      game:el.querySelector('[data-affiliate]').dataset.gameId,href:el.querySelector('[data-affiliate]').href,
      image:el.querySelector('img')?.getAttribute('src')||null})),
     width:innerWidth,documentWidth:document.documentElement.scrollWidth,
     note:document.querySelector('.scene-result-head span').textContent,
     table:document.querySelector('.scene-table-scroll').scrollWidth>document.querySelector('.scene-table-scroll').clientWidth,
     body:document.body.textContent
    }));
    assert(snapshot.documentWidth<=width+2,'document overflow');assert.equal(errors.length,0,errors.join(','));
    await page.screenshot({path:path.join(out,`${label}-${width}.png`),fullPage:true,animations:'disabled'});
    if(index){assert(snapshot.note.includes('カタログ掲載順'));assert(!snapshot.body.includes('None人'));assert(snapshot.body.includes('2人以上'));}
    if(index){
     const groups=page.locator('details.two-player-choices');assert.equal(await groups.count(),2);
     for(let group=0;group<2;group++){
      const details=groups.nth(group);await details.locator('summary').click();
      const count=Number((await details.locator('summary').textContent()).match(/（(\d+)本）/)[1]);
      assert.equal(await details.locator(':scope > ul > li').count(),count);assert(count>0);
      const rules=details.locator('details.choice-rules').first();
      await rules.locator('summary').click();
      assert(await rules.locator('ol').isVisible());
      assert((await rules.locator('ol > li').count())>0);
      assert(await details.locator('[data-choice-game="sky-team"]').isVisible());
      const links=await details.locator('a').evaluateAll(els=>els.map(a=>a.getAttribute('href')));
      for(const href of links){const response=await page.request.get(`http://127.0.0.1:8766${href}`);assert.equal(response.status(),200);}
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'expanded choices overflow');
     }
     await page.screenshot({path:path.join(out,`choices-${width}.png`),fullPage:true,animations:'disabled'});
     await page.locator('#two-player-choices a[data-game-id="sky-team"]').first().click();
     assert((await page.locator('h1').textContent()).includes('スカイチーム'));
     const purchase=page.locator('.product-panel [data-affiliate]');
     assert.equal(await purchase.getAttribute('rel'),'sponsored noopener');
     assert((await purchase.getAttribute('href')).startsWith('https://'));
     assert.equal(errors.length,0,errors.join(','));
    }
    const {note,table,body,...stable}=snapshot;snapshots.push(stable);
    records.push({label,width,documentWidth:snapshot.documentWidth,images:imageCount,errors,tableScroll:snapshot.table,note:snapshot.note});
    await page.close();
   }
   assert.deepEqual(snapshots[1],snapshots[0],'SEO/order/product links or images changed');
   await context.close();
  }
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',records},null,2));
  // A finite before/after quality check using the same actual offer snapshot.
  const {default:lighthouse}=await import(require.resolve('lighthouse'));
  const launcher=await import(require.resolve('chrome-launcher'));
  const chrome=await launcher.launch({chromePath:chromium.executablePath(),chromeFlags:['--headless','--no-sandbox']});
  try{
   for(const desktop of [false,true])for(const [index,label] of ['before','after'].entries()){
    const result=await lighthouse(`http://127.0.0.1:${8765+index}/kyo-bodo-jp/scenes/two-player/?test=1`,
      {port:chrome.port,output:'json',onlyCategories:['performance','accessibility','best-practices','seo'],
       ...(desktop?{formFactor:'desktop',screenEmulation:{mobile:false,width:1440,height:900,deviceScaleFactor:1,disabled:false},throttlingMethod:'provided'}:{})});
    assert(!result.lhr.runtimeError,JSON.stringify(result.lhr.runtimeError));
    fs.writeFileSync(path.join(out,`lighthouse-${label}-${desktop?'desktop':'mobile'}.json`),result.report);
    console.log('LIGHTHOUSE',label,desktop?'desktop':'mobile',JSON.stringify(Object.fromEntries(Object.entries(result.lhr.categories).map(([k,v])=>[k,v.score]))));
   }
  }finally{await chrome.kill();}
 }finally{await browser.close();servers.forEach(s=>s.close());}
})().catch(error=>{fs.writeFileSync(path.join(out,'failure.txt'),String(error.stack));console.error(error);process.exitCode=1;});
