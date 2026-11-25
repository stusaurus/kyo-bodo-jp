/* Real Chromium QA for eleven source-backed game detail pages at mobile and desktop widths. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');

const root = path.resolve('site');
const output = path.resolve('audit-results/catalog-expansion');
const prefix = '/kyo-bodo-jp/';
fs.mkdirSync(output, { recursive: true });
const fixtures = [
  {id:'nana-card-game', title:'ナナカードゲーム',
   source:'https://suppe.sugorokuya.jp/items/220738', players:'2〜5人', time:'15分', age:'6歳〜'},
  {id:'lama', title:'ラマ',
   source:'https://mobiusgames.shop-pro.jp/?pid=145076594', players:'2〜6人', time:'20分', age:'8歳〜'},
  {id:'ark-nova', title:'アーク・ノヴァ 新たなる方舟',
   source:'https://tendaysgames.shop-pro.jp/?pid=166436141', players:'1〜4人', time:'90〜150分', age:'14歳〜'},
  {id:'nana-toridori', title:'ナナトリドリ',
   source:'https://arclightgames.jp/product/767toridori/', players:'2〜6人', time:'10〜20分', age:'6歳〜'},
  {id:'incan-gold-rediscovered', title:'インカの黄金 再発掘',
   source:'https://arclightgames.jp/product/298whp/', players:'3〜8人', time:'20〜40分', age:'8歳〜'},
  {id:'ciao-ciao', title:'チャオチャオ',
   source:'https://mobiusgames.shop-pro.jp/?pid=144935571', players:'2〜4人', time:'20〜25分', age:'8歳〜'},
  {id:'nmbr9', title:'ナンバーナイン',
   source:'https://mobiusgames.shop-pro.jp/?pid=145075144', players:'1〜4人', time:'20分', age:'8歳〜'},
  {id:'houseki-ippai', title:'宝石がいっぱい！',
   source:'https://arclightgames.jp/product/576houseki/', players:'2〜6人', time:'5分', age:'4歳〜'},
  {id:'animal-old-maid', title:'どうぶつババ抜き',
   source:'https://arclightgames.jp/product/%E3%81%A9%E3%81%86%E3%81%B6%E3%81%A4%E3%83%90%E3%83%90%E6%8A%9C%E3%81%8D/', players:'2〜6人', time:'15分', age:'6歳〜'},
  {id:'ding', title:'ディング！', source:'https://arclightgames.jp/product/517nds/', players:'2〜7人', time:'10分', age:'8歳〜'},
  {id:'eggsposed', title:'ばれたま', source:'https://oinkgames.com/ja/games/analog/eggsposed/', players:'3〜8人', time:'20分', age:'9歳〜'}
];

const catalog = JSON.parse(fs.readFileSync(path.join(root,'data/games.json'),'utf8'));
assert.equal(catalog.length,91,'generated catalog must include exactly 91 games');
for (const game of fixtures) {
  assert(catalog.some(row=>row.game_id===game.id),'generated catalog missing '+game.id);
}

function serve(port) {
  return new Promise(resolve => {
    const app = http.createServer((req,res)=>{
      const requested = new URL(req.url,'http://localhost').pathname;
      if (!requested.startsWith(prefix)) { res.writeHead(404).end(); return; }
      let relative;
      try { relative = decodeURIComponent(requested.slice(prefix.length)); }
      catch { res.writeHead(400).end(); return; }
      let file = path.resolve(root,relative);
      if (file!==root && !file.startsWith(root+path.sep)) { res.writeHead(403).end(); return; }
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file=path.join(file,'index.html');
      if (!fs.existsSync(file)) { res.writeHead(404).end(); return; }
      const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript',
                   '.json':'application/json','.webp':'image/webp'};
      res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
      fs.createReadStream(file).pipe(res);
    });
    app.listen(port,'127.0.0.1',()=>resolve(app));
  });
}

(async()=>{
  const app=await serve(8791);
  const browser=await chromium.launch();
  try {
    for(const width of [320,390,1440]) {
      const ctx=await browser.newContext({viewport:{width,height:850},isMobile:width<500,hasTouch:width<500});
      await ctx.route(/google-analytics\.com|googletagmanager\.com|analytics\.google\.com/,route=>route.abort());
      const page=await ctx.newPage();
      const jsErrors=[];
      page.on('pageerror',error=>jsErrors.push(error.message));
      for (const game of fixtures) {
        const relative=prefix+'games/'+game.id+'/';
        const res=await page.goto('http://127.0.0.1:8791'+relative,{waitUntil:'domcontentloaded'});
        assert.equal(res.status(),200,game.id+' HTTP status');
        await page.locator('.game-hero-card').waitFor();
        assert.equal((await page.locator('.game-detail-hero h1').innerText()).trim(),game.title);
        assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),
                     'https://stusaurus.github.io'+relative);
        const meta=await page.locator('.game-fast-facts').innerText();
        for(const value of [game.players,game.time,game.age]) {
          assert(meta.includes(value),game.id+' missing '+value+' in facts: '+meta);
        }
        const source=page.locator('.game-hero-copy a[href="'+game.source+'"]');
        assert.equal(await source.count(),1,game.id+' source link');
        assert.equal(await source.getAttribute('rel'),'noopener noreferrer');
        const detail=page.locator('.detail-story');
        assert.equal(await detail.locator('ol.howto > li').count(),3);
        const product=page.locator('.product-panel a.btn.rakuten');
        assert.equal(await product.count(),1);
        const affiliate=await product.getAttribute('data-affiliate');
        const search=await product.getAttribute('data-track');
        assert((affiliate==='rakuten' && search===null) ||
               (affiliate===null && search==='rakuten_search_click'),
               game.id+' must separate verified affiliate from search-only');
        const href=await product.getAttribute('href');
        assert(href.startsWith('https://'),game.id+' unsafe outgoing URL');
        assert(!/検索でご確認/.test(await product.getAttribute('href')));
        const layout=await page.evaluate(()=>({
          width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
          h1Height:document.querySelector('.game-detail-hero h1').getBoundingClientRect().height
        }));
        assert(layout.scrollWidth<=width+3,
               game.id+' horizontal overflow at '+width+': '+layout.scrollWidth);
        assert(layout.h1Height>0,game.id+' invisible headline');
        assert.equal(jsErrors.length,0,game.id+' JS errors: '+jsErrors.join('; '));
        await page.screenshot({path:path.join(output,game.id+'-'+width+'.png'),
                              fullPage:true,animations:'disabled'});
        console.log(JSON.stringify({game:game.id,width,status:200,source:'verified',purchase:affiliate?'affiliate':'search-only',overflow:0,jsErrors:0}));
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
    await new Promise(resolve=>app.close(resolve));
  }
})().catch(err=>{console.error(err);process.exitCode=1});
