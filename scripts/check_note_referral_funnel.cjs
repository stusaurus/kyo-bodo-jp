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

      // Second, specifically authorized campaign: a seasonal note article
      // about the existing gift guide. It must not inherit the old campaign.
      const giftCampaign='gift_guide_20261119';
      const giftPath=base+'guides/gift-board-games/';
      const giftQuery='utm_source=note&utm_medium=referral&utm_campaign='+giftCampaign+'&utm_content=gift_guide';
      const giftCtx=await context(browser,width),gift=await giftCtx.newPage();
      await gift.goto(origin+giftPath+'?'+giftQuery+'&test=1',{waitUntil:'domcontentloaded'});
      await gift.waitForFunction(()=>typeof window.kyoTrack==='function');
      let giftEvents=await events(gift);
      const giftLanding=giftEvents.find(e=>e.name==='note_campaign_landing');
      assert(giftLanding,'gift campaign landing missing');
      assert.equal(giftLanding.data.entry_campaign,giftCampaign);
      assert.equal(giftLanding.data.entry_channel,'note_campaign');
      assert.equal(giftLanding.data.entry_content,'gift_guide');
      assert.equal(giftLanding.data.operator_test,'1');
      assert.equal(giftLanding.data.landing_path,giftPath);
      assert.equal(giftLanding.data.referrer,undefined);
      assert.equal(giftLanding.data.full_url,undefined);
      assert.equal(giftLanding.data.utm_term,undefined);
      const giftTableLink=gift.locator('.gift-age a[data-gift-detail="dobble"]');
      assert.equal(await giftTableLink.getAttribute('data-track'),'game_detail_click');
      await safeClick(gift,giftTableLink);
      let giftTableEvents=await events(gift);
      let giftTableDetail=giftTableEvents.filter(e=>e.name==='game_detail_click');
      assert.equal(giftTableDetail.length,1,'table click must emit exactly one detail event');
      assert.equal(giftTableDetail[0].data.entry_campaign,giftCampaign);
      assert.equal(giftTableDetail[0].data.conversion_source,'gift_guide');
            const giftChoice=gift.locator('.gift-age a[data-track="game_detail_click"][data-source="gift_guide"]').first();
      assert(await giftChoice.count()>0,'gift guide detail links unavailable');
      await safeClick(gift,giftChoice);
      giftEvents=await events(gift);
      assert.equal(giftEvents.filter(e=>e.name==='game_detail_click').length,2,
        'table and card should each emit once');
      const giftDetail=giftEvents.find(e=>e.name==='game_detail_click');
      assert(giftDetail,'gift detail click missing');
      assert.equal(giftDetail.data.entry_campaign,giftCampaign);
      assert.equal(giftDetail.data.entry_content,'gift_guide');
      assert.equal(giftDetail.data.operator_test,'1');
      // On the next same-tab page, distinguish a verified affiliate outbound
      // from an ordinary search; never fabricate a conversion.
      await gift.goto(origin+base+'games/dobble/?test=1',{waitUntil:'domcontentloaded'});
      await gift.waitForFunction(()=>typeof window.kyoTrack==='function');
      const giftOutbound=gift.locator('.product-panel a.btn.rakuten.large');
      assert.equal(await giftOutbound.count(),1);
      const giftAffiliate=await giftOutbound.getAttribute('data-affiliate')==='rakuten';
      await safeClick(gift,giftOutbound);
      giftEvents=await events(gift);
      const giftOutboundName=giftAffiliate?'affiliate_click':'rakuten_search_click';
      const giftOutboundEvent=giftEvents.find(e=>e.name===giftOutboundName);
      assert(giftOutboundEvent,'gift funnel outbound missing');
      assert.equal(giftOutboundEvent.data.entry_campaign,giftCampaign);
      assert.equal(giftOutboundEvent.data.entry_content,'gift_guide');
      assert.equal(giftOutboundEvent.data.operator_test,'1');
      assert.equal(giftEvents.filter(e=>e.name==='affiliate_click').length,giftAffiliate?1:0);
      await gift.goto(origin+giftPath+'?'+giftQuery+'&test=1',{waitUntil:'domcontentloaded'});
      await gift.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(gift)).filter(e=>e.name==='note_campaign_landing').length,0,
        'gift campaign reload duplicated landing');
      await giftCtx.close();

      // Any missing content tag or non-gift destination must be ignored.
      const fakeGiftCtx=await context(browser,width),fakeGift=await fakeGiftCtx.newPage();
      await fakeGift.goto(origin+giftPath+'?utm_source=note&utm_medium=referral&utm_campaign='+giftCampaign+'&test=1',{waitUntil:'domcontentloaded'});
      await fakeGift.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(fakeGift)).filter(e=>e.name==='note_campaign_landing').length,0,
        'missing gift tag must not be counted');
      await fakeGift.goto(origin+base+'scenes/two-player/?'+giftQuery+'&test=1',{waitUntil:'domcontentloaded'});
      await fakeGift.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(fakeGift)).filter(e=>e.name==='note_campaign_landing').length,0,
        'wrong landing destination must not be counted');
      await fakeGiftCtx.close();

      // Distinguish the preschool article from the earlier gift article.
      const preschoolCampaign='preschool_gift_20261127';
      const preschoolQuery='utm_source=note&utm_medium=referral&utm_campaign='+preschoolCampaign+'&utm_content=gift_preschool';
      const preCtx=await context(browser,width),pre=await preCtx.newPage();
      await pre.goto(origin+giftPath+'?'+preschoolQuery+'&test=1#gift-preschool',{waitUntil:'domcontentloaded'});
      const preLanding=(await events(pre)).find(e=>e.name==='note_campaign_landing');
      assert(preLanding);
      assert.equal(preLanding.data.entry_campaign,preschoolCampaign);
      assert.equal(preLanding.data.entry_content,'gift_preschool');
      const preChoice=pre.locator('#gift-preschool a[data-game-id="houseki-ippai"]');
      await preChoice.click();
      await pre.waitForURL('**/games/houseki-ippai/');
      const preOutbound=pre.locator('.product-panel a.btn.rakuten.large');
      const preAffiliate=await preOutbound.getAttribute('data-affiliate')==='rakuten';
      await safeClick(pre,preOutbound);
      const preEvents=await events(pre);
      const preEvent=preEvents.find(e=>e.name===(preAffiliate?'affiliate_click':'rakuten_search_click'));
      assert(preEvent);
      assert.equal(preEvent.data.entry_campaign,preschoolCampaign);
      assert.equal(preEvent.data.entry_content,'gift_preschool');
      assert.equal(preEvents.filter(e=>e.name==='affiliate_click').length,preAffiliate?1:0);
      await pre.goto(origin+giftPath+'?'+preschoolQuery+'&test=1',{waitUntil:'domcontentloaded'});
      assert.equal((await events(pre)).filter(e=>e.name==='note_campaign_landing').length,0);
      await preCtx.close();
      const wrongCtx=await context(browser,width),wrong=await wrongCtx.newPage();
      await wrong.goto(origin+base+'scenes/two-player/?'+preschoolQuery+'&test=1',{waitUntil:'domcontentloaded'});
      assert.equal((await events(wrong)).filter(e=>e.name==='note_campaign_landing').length,0);
      await wrong.goto(origin+giftPath+'?'+preschoolQuery.replace('utm_content=gift_preschool','utm_content=gift_guide')+'&test=1',{waitUntil:'domcontentloaded'});
      assert.equal((await events(wrong)).filter(e=>e.name==='note_campaign_landing').length,0);
      await wrongCtx.close();
      const spoofCtx=await context(browser,width),spoof=await spoofCtx.newPage();
      await spoof.goto(origin+base+'scenes/two-player/?utm_source=note&utm_medium=referral&utm_campaign=anything_else&test=1',
        {waitUntil:'domcontentloaded'});
      await spoof.waitForFunction(()=>typeof window.kyoTrack==='function');
      assert.equal((await events(spoof)).filter(e=>e.name==='note_campaign_landing').length,0,
        'unrecognized campaigns must not be incorrectly counted');
      await spoofCtx.close();
      console.log(JSON.stringify({width,noteLanding:1,internalDetail:true,outbound:isAffiliate?'affiliate':'search-only',
        operatorTest:'1',giftCampaign:true,giftDetail:true,giftOutbound:true,giftSpoof:0,directFalseAttribution:0,reloadDuplicate:0,unrecognizedCampaign:0,errors:0}));
    }
  }finally{
    await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{
  fs.writeFileSync(path.join(output,'failure.txt'),String(e.stack));
  console.error(e);process.exitCode=1;
});
