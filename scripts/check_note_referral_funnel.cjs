/* First-party note attribution contract, no live GA4 calls or user traffic.
 * The published UTM campaign is recognized, stored in tab sessionStorage for
 * 30 min, and attached only to internal funnel events. No personal data sent.
 */
const { chromium } = require('playwright');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const assert=require('node:assert/strict');
const root=path.resolve('site'),base='/kyo-bodo-jp/';
const output=path.resolve('audit-results/note-referral-funnel');
fs.mkdirSync(output,{recursive:true});
const campaign='two_player_trial_20261118';
const noteQuery='utm_source=note&utm_medium=referral&utm_campaign='+campaign;
function makeServer(){
  return new Promise(resolve=>{
    const server=http.createServer((req,res)=>{
      const pathname=new URL(req.url,'http://127.0.0.1').pathname;
      if(!pathname.startsWith(base)){res.writeHead(404).end();return;}
      let rel;
      try{rel=decodeURIComponent(pathname.slice(base.length));}
      catch(_){res.writeHead(400).end();return;}
      let file=path.resolve(root,rel);
      if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
      if(!fs.existsSync(file)){res.writeHead(404).end();return;}
      const types={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    server.listen(8797,'127.0.0.1',()=>resolve(server));
  });
}
const origin='http://127.0.0.1:8797';
const events=page=>page.evaluate(()=>window.dataLayer.filter(x=>x[0]==='event').map(x=>({name:x[1],data:x[2]})));
async function safeClick(page,locator){
  await locator.evaluate(a=>a.addEventListener('click',e=>e.preventDefault(),{once:true}));
  await locator.click();
}
async function context(browser,width){
  const ctx=await browser.newContext({viewport:{width,height:880},isMobile:width<500,hasTouch:width<500});
  await ctx.route(/googletagmanager\.com|google-analytics\.com|analytics\.google\.com/,r=>r.abort());
  return ctx;
}
(async()=>{
  const server=await makeServer();
  const browser=await chromium.launch();
  try{
    for(const width of [320,390,1440]){
      const ctx=await context(browser,width),page=await ctx.newPage(),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      const landing=base+'scenes/two-player/?'+noteQuery+'&test=1';
      let response=await page.goto(origin+landing,{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.waitForFunction(()=>typeof window.kyoTrack==='function');
      let emitted=await events(page);
      const landings=emitted.filter(e=>e.name==='note_campaign_landing');
      assert.equal(landings.length,1,'first UTM landing emitted exactly once');
      const landingData=landings[0].data;
      assert.equal(landingData.entry_campaign,campaign);
      assert.equal(landingData.entry_channel,'note_campaign');
      assert.equal(landingData.entry_content,'unspecified');
      assert.equal(landingData.operator_test,'1');
      assert.equal(landingData.landing_path,base+'scenes/two-player/');
      assert.equal(landingData.page_path,base+'scenes/two-player/');
      assert.equal(landingData.referrer,undefined);
      assert.equal(landingData.full_url,undefined);
      assert.equal(landingData.age,undefined);

      const link=page.locator('a[data-track="game_detail_click"]').first();
      assert(await link.count()>0,'no game detail links');
      await safeClick(page,link);
      emitted=await events(page);
      const detailClick=emitted.find(e=>e.name==='game_detail_click');
      assert(detailClick,'game detail click not tracked');
      assert.equal(detailClick.data.entry_channel,'note_campaign');
      assert.equal(detailClick.data.entry_campaign,campaign);
      assert.equal(detailClick.data.operator_test,'1');

      // Same tab, internal game page without UTM: campaign survives only this tab.
      response=await page.goto(origin+base+'games/sky-team/?test=1',{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200);
      await page.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(page)).filter(e=>e.name==='note_campaign_landing').length,0,
        'do not duplicate external campaign landing on internal navigation');
      const outbound=page.locator('.product-panel a.btn.rakuten.large');
      assert.equal(await outbound.count(),1);
      const isAffiliate=await outbound.getAttribute('data-affiliate')==='rakuten';
      await safeClick(page,outbound);
      emitted=await events(page);
      const expectedName=isAffiliate?'affiliate_click':'rakuten_search_click';
      const outboundEvent=emitted.find(e=>e.name===expectedName);
      assert(outboundEvent,'correct outbound category missing: '+expectedName);
      assert.equal(outboundEvent.data.entry_channel,'note_campaign');
      assert.equal(outboundEvent.data.entry_campaign,campaign);
      assert.equal(outboundEvent.data.operator_test,'1');
      assert.equal(emitted.filter(e=>e.name==='affiliate_click').length,isAffiliate?1:0,
        'search-only links must not inflate affiliate clicks');
      assert.equal(errors.length,0,errors.join('; '));

      // A reload of the original campaign URL does not emit a second landing.
      await page.goto(origin+landing,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(page)).filter(e=>e.name==='note_campaign_landing').length,0,
        'reload of UTM link should not multiply landings');
      const state=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('kyo_bodo_note_entry_v1')));
      assert.equal(state.campaign,campaign);
      assert.equal(state.content,'unspecified');
      assert.equal(state.landing_path,base+'scenes/two-player/');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+3),true);
      await ctx.close();

      const independent=await context(browser,width),direct=await independent.newPage();
      await direct.goto(origin+base+'scenes/two-player/?test=1',{waitUntil:'domcontentloaded'});
      await direct.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(direct)).filter(e=>e.name==='note_campaign_landing').length,0);
      const directLink=direct.locator('a[data-track="game_detail_click"]').first();
      await safeClick(direct,directLink);
      const directEvent=(await events(direct)).find(e=>e.name==='game_detail_click');
      assert(directEvent);
      assert.equal(directEvent.data.entry_channel,undefined,
        'direct traffic must not inherit note campaign');
      await independent.close();

      const guideCtx=await context(browser,width),guide=await guideCtx.newPage();
      const guidePath=base+'guides/two-player-cooperative/';
      await guide.goto(origin+guidePath+'?'+noteQuery+'&utm_content=coop_guide&test=1',{waitUntil:'domcontentloaded'});
      await guide.waitForFunction(()=>typeof window.kyoTrack==='function');
      const guideLanding=(await events(guide)).find(e=>e.name==='note_campaign_landing');
      assert(guideLanding);
      assert.equal(guideLanding.data.entry_content,'coop_guide');
      assert.equal(guideLanding.data.landing_path,guidePath);
      await guideCtx.close();

      const spoofCtx=await context(browser,width),spoof=await spoofCtx.newPage();
      await spoof.goto(origin+base+'scenes/two-player/?utm_source=note&utm_medium=referral&utm_campaign=anything_else&test=1',
        {waitUntil:'domcontentloaded'});
      await spoof.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(spoof)).filter(e=>e.name==='note_campaign_landing').length,0,
        'unrecognized campaigns must not be incorrectly counted');
      await spoofCtx.close();
      console.log(JSON.stringify({width,noteLanding:1,internalDetail:true,outbound:isAffiliate?'affiliate':'search-only',
        operatorTest:'1',directFalseAttribution:0,reloadDuplicate:0,unrecognizedCampaign:0,errors:0}));
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{
  fs.writeFileSync(path.join(output,'failure.txt'),String(e.stack));
  console.error(e);process.exitCode=1;
});
