const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

const source=fs.readFileSync(path.join(__dirname,'../assets/two-player-quick-filter.js'),'utf8');

function build(records) {
  const items=records.map(record=>({dataset:{
    timeMax:String(record.minutes),minAge:String(record.age),
    cooperative:record.coop?'1':'0'
  },hidden:false}));
  const fields={minutes:'0',style:'any',age:'0'};
  const counter={textContent:''};
  const empty={hidden:true};
  let onChange;
  const form={addEventListener:(event,fn)=>{if(event==='change')onChange=fn;}};
  const root={
    querySelectorAll:selector=>selector==='[data-two-game]'?items:[],
    querySelector:selector=>({
      '[data-two-quick-count]':counter,'[data-two-quick-empty]':empty,
      form
    })[selector]
  };
  const document={readyState:'complete',querySelector:selector=>
    selector==='[data-two-player-quick-filter]'?root:null};
  class MockFormData {
    get(name){return fields[name];}
  }
  vm.runInNewContext(source,{document,FormData:MockFormData});
  return {
    items,counter,empty,
    change(next){Object.assign(fields,next);onChange();},
    visible(){return items.map((item,index)=>!item.hidden?index:null).filter(x=>x!==null);}
  };
}

test('default three visible in original catalog order, no invented popularity',()=>{
  const app=build([
    {minutes:15,age:8,coop:true},{minutes:30,age:8,coop:false},
    {minutes:20,age:10,coop:true},{minutes:60,age:12,coop:false}
  ]);
  assert.deepEqual(app.visible(),[0,1,2]);
  assert.match(app.counter.textContent,/4本が条件に一致/);
  assert.match(app.counter.textContent,/優劣・人気順ではありません/);
});

test('progressively refine using proven max play-time, cooperation and age',()=>{
  const app=build([
    {minutes:15,age:8,coop:true},{minutes:30,age:8,coop:false},
    {minutes:20,age:10,coop:true},{minutes:60,age:12,coop:false}
  ]);
  app.change({minutes:'30'});
  assert.deepEqual(app.visible(),[0,1,2]);
  app.change({style:'cooperative'});
  assert.deepEqual(app.visible(),[0,2]);
  app.change({age:'8'});
  assert.deepEqual(app.visible(),[0]);
  app.change({minutes:'0',style:'any',age:'0'});
  assert.deepEqual(app.visible(),[0,1,2]);
});

test('four- and six-year-old choices exclude older-only games without recommendation claims',()=>{
  const app=build([
    {minutes:20,age:4,coop:false},
    {minutes:15,age:5,coop:false},
    {minutes:15,age:6,coop:true},
    {minutes:15,age:8,coop:true}
  ]);
  app.change({age:'4'});
  assert.deepEqual(app.visible(),[0]);
  app.change({age:'6',minutes:'15'});
  assert.deepEqual(app.visible(),[1,2]);
  app.change({style:'cooperative'});
  assert.deepEqual(app.visible(),[2]);
  assert.match(app.counter.textContent,/1本が条件に一致/);
  app.change({age:'0',minutes:'0',style:'any'});
  assert.deepEqual(app.visible(),[0,1,2]);
});

test('catalog-wide records remain filterable beyond the first twelve without ranking',()=>{
  const records=Array.from({length:64},(_,i)=>({
    minutes:i===40?15:50,
    age:i===40?8:12,
    coop:i===40
  }));
  const app=build(records);
  assert.deepEqual(app.visible(),[0,1,2]);
  assert.match(app.counter.textContent,/64本が条件に一致/);
  app.change({minutes:'15',style:'cooperative',age:'8'});
  assert.deepEqual(app.visible(),[40]);
  assert.match(app.counter.textContent,/1本が条件に一致/);
  assert.doesNotMatch(source,/全12本/);
});

test('no matching eligible listing shows calm empty state instead of fake choice',()=>{
  const app=build([{minutes:60,age:12,coop:false}]);
  app.change({minutes:'15',style:'cooperative',age:'8'});
  assert.deepEqual(app.visible(),[]);
  assert.equal(app.empty.hidden,false);
  assert.match(app.counter.textContent,/掲載候補はありません/);
});

test('unverified duration or invalid age never pass filters',()=>{
  const app=build([{minutes:0,age:8,coop:true},{minutes:15,age:-1,coop:true},
    {minutes:15,age:8,coop:true}]);
  assert.deepEqual(app.visible(),[2]);
});

test('filter code never initiates affiliate clicks, tracking or remote fetches',()=>{
  assert.doesNotMatch(source,/fetch\s*\(|XMLHttpRequest|sendBeacon|gtag\s*\(|affiliate_click/);
});
