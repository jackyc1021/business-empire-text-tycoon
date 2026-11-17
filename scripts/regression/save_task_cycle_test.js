#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'game','shangye_diguo_v2_19_1.html'),'utf8');
const script=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const SAVE_KEY='tycoon_text_empire_rebuild_v1';
let fakeNow=Date.parse('2026-11-01T23:59:00Z'),nextImportText=null;
class FakeDate extends Date { constructor(...args){super(...(args.length?args:[fakeNow]))} static now(){return fakeNow} static parse(v){return Date.parse(v)} static UTC(...args){return Date.UTC(...args)} }
class El {constructor(id=''){this.id=id;this.innerHTML='';this.textContent='';this.className='';this.style={setProperty(){},removeProperty(){}};this.classList={add(){},remove(){},toggle(){},contains(){return false}};this.children=[];this.value='';this.files=[];this.scrollLeft=0;this.clientWidth=1280;this.clientHeight=800;}addEventListener(){}removeEventListener(){}appendChild(x){this.children.push(x);return x}remove(){}focus(){}setAttribute(){}getAttribute(){return null}querySelector(){return new El()}querySelectorAll(){return []}closest(){return new El()}getBoundingClientRect(){return {width:1280,height:800,left:0,top:0,right:1280,bottom:800}}getContext(){return null}click(){if(this.type==='file'&&this.onchange&&nextImportText!==null){this.files=[{content:nextImportText}];this.onchange();nextImportText=null}}}
const els={};const get=id=>els[id]||(els[id]=new El(id));
const document={body:get('body'),visibilityState:'visible',getElementById:get,querySelector(){return new El()},querySelectorAll(){return []},addEventListener(){},removeEventListener(){},createElement(tag){const el=new El(tag);el.tagName=tag.toUpperCase();return el}};
const storage={};const localStorage={getItem(k){return Object.hasOwn(storage,k)?storage[k]:null},setItem(k,v){storage[k]=String(v)},removeItem(k){delete storage[k]},key(i){return Object.keys(storage)[i]||null},get length(){return Object.keys(storage).length}};
function boot(){const math=Object.create(Math);const win={addEventListener(){},scrollTo(){},innerWidth:1280,innerHeight:800};class FR{readAsText(file){this.result=file.content;if(this.onload)this.onload()}};const quietConsole={...console,warn(){},error(){}};const c={console:quietConsole,document,localStorage,window:win,navigator:{},location:{protocol:'file:',hostname:''},Date:FakeDate,Math:math,JSON,Number,String,Object,Array,Set,Map,Promise,Blob:function(){},URL:{createObjectURL(){return ''},revokeObjectURL(){}},FileReader:FR,setInterval(){return 1},clearInterval(){},setTimeout(){return 1},clearTimeout(){},requestAnimationFrame(fn){fn()},cancelAnimationFrame(){}};win.document=document;win.localStorage=localStorage;win.Math=math;vm.createContext(c);vm.runInContext(script,c,{timeout:30000});return c}
function getSave(){return JSON.parse(localStorage.getItem(SAVE_KEY))}
function test(label,fn){fn();checks.push(label)}
const checks=[];
// Import compatibility for each supported schema version.
for(let version=1;version<=6;version++){
  fakeNow=Date.parse('2026-11-01T12:00:00Z');
  let c=boot();
  const legacy={version,gold:12345,diamonds:100,level:3,exp:50,prestige:0,totalEarned:5000,clickPower:7,pity:{normal:12,advanced:23},shops:[{id:'stall',level:3}],managers:[{id:'c1',level:5,star:2,exp:20,breakthroughs:0}],shards:{c1:4},assignments:{stall:'c1'},inventory:{ticket:7,advancedTicket:3,boost:1}};
  nextImportText=JSON.stringify(legacy);c.window.Game.importSave();
  const migrated=getSave();
  assert.equal(migrated.version,6,`v${version} migrated schema`);assert.equal(migrated.gold,12345);assert.equal(migrated.shops.find(x=>x.id==='stall').level,3);assert.equal(migrated.managers[0].id,'c1');assert.equal(migrated.team[0],'c1');assert.deepStrictEqual(migrated.assignments,{});assert.equal(migrated.pity.normal,12);assert.equal(migrated.pity.advanced,23);
  if(version<4){assert.equal(migrated.inventory.advancedTicket,0);assert.equal(migrated.diamonds,175)}else{assert.equal(migrated.inventory.advancedTicket,3);assert.equal(migrated.diamonds,100)}
  checks.push(`v${version} import preserves progress and migrates to v6`);
}
// Existing nine-shop progress, region unlocks, manager dispatch and balances survive expansion to 30.
fakeNow=Date.parse('2026-11-01T12:00:00Z');let legacyNine=boot();
const oldNine=['stall','cafe','fashion','tech','hotel','mall','factory','tower','space'];
const expandedFixture={version:6,gold:765432,diamonds:321,shops:oldNine.map((id,i)=>({id,level:i+1})),managers:[{id:'c1',level:12,star:2,exp:30,breakthroughs:1}],assignments:{stall:'c1'},regions:{street:true,food:true,mall:true,finance:true},currentRegion:'finance',inventory:{ticket:9,advancedTicket:4}};
nextImportText=JSON.stringify(expandedFixture);legacyNine.window.Game.importSave();
const expanded=getSave();
assert.equal(expanded.gold,765432);assert.equal(expanded.diamonds,321);assert.equal(expanded.currentRegion,'finance');
for(let i=0;i<oldNine.length;i++)assert.equal(expanded.shops.find(x=>x.id===oldNine[i]).level,i+1,`legacy ${oldNine[i]} level preserved`);
assert.equal(expanded.shops.length,30);assert.equal(expanded.shops.find(x=>x.id==='convenience').level,0);assert.equal(expanded.team[0],'c1');assert.deepStrictEqual(expanded.assignments,{});
for(const id of ['street','food','mall','finance'])assert.equal(expanded.regions[id],true);
for(const id of ['international','future'])assert.equal(expanded.regions[id],false);
checks.push('v6 nine-shop save expands to 30 shops without losing legacy levels, team migration, region unlocks or balances');
// Broken or unsupported import must not overwrite current local save.
fakeNow=Date.parse('2026-11-01T12:00:00Z');let c=boot();let before=getSave();
nextImportText='{broken json';c.window.Game.importSave();assert.deepStrictEqual(getSave(),before);checks.push('malformed JSON import is rejected without damaging current save');
nextImportText=JSON.stringify({version:99,shops:[]});c.window.Game.importSave();assert.deepStrictEqual(getSave(),before);checks.push('unsupported schema import is rejected without damaging current save');
// Task progression and one-time claims around UTC day and Monday boundary.
fakeNow=Date.parse('2026-11-01T23:59:00Z');c=boot();
for(let i=0;i<5;i++)c.window.Game.collect();
let st=getSave();assert.equal(st.taskDaily.progress.collects,5);assert.equal(st.taskWeekly.progress.collects,5);
const books0=st.inventory.expBookBasic;c.window.Game.claimTask('collect5','daily');st=getSave();assert.equal(st.inventory.expBookBasic,books0+2);c.window.Game.claimTask('collect5','daily');assert.equal(getSave().inventory.expBookBasic,books0+2);checks.push('daily task progresses and reward cannot be claimed twice');
// Set incomplete sign-in sequence and complete prior-week ad milestones before UTC Monday.
st.signIn={weekKey:'2026-10-26',lastClaimDate:'2026-11-01',claims:3};st.adDaily={dayKey:'2026-11-01',validCount:20,shopIncomeUses:1,doubleUses:0,claimed:[]};st.adGrowth={weekKey:'2026-10-26',startedAt:Date.parse('2026-10-26T00:00:00Z'),endsAt:Date.parse('2026-11-02T00:00:00Z'),validCount:35,claimed:[],pending:[]};localStorage.setItem(SAVE_KEY,JSON.stringify(st));
fakeNow=Date.parse('2026-11-02T00:00:01Z');c=boot();c.window.Game.openPanel('tasks');st=getSave();
assert.equal(st.taskDaily.dayKey,'2026-11-02');assert.equal(Object.values(st.taskDaily.progress).reduce((a,b)=>a+(Number(b)||0),0),0);
assert.equal(st.taskWeekly.weekKey,'2026-11-02');assert.equal(Object.values(st.taskWeekly.progress).reduce((a,b)=>a+(Number(b)||0),0),0);
assert.equal(st.adDaily.validCount,0);assert.equal(st.signIn.claims,3);assert.equal(st.signIn.lastClaimDate,'2026-11-01');
assert(st.adGrowth.pending.some(x=>x.stageId==='growth35'&&x.weekKey==='2026-10-26'));
c.window.Game.claimSignIn();st=getSave();assert.equal(st.signIn.claims,4);checks.push('UTC daily/weekly resets preserve incomplete sign-in sequence and archive prior ad milestones');
// Prior weekly milestone can be claimed once after rollover.
st=getSave();const p=st.adGrowth.pending.find(x=>x.stageId==='growth35');assert(p);const honorBefore=st.honorTokens;c.window.Game.claimGrowth(p.id);st=getSave();assert(st.adGrowth.pending.find(x=>x.id===p.id).claimed);assert(getSave().diamonds>0);c.window.Game.claimGrowth(p.id);assert.equal(getSave().adGrowth.pending.find(x=>x.id===p.id).claimed,true);checks.push('previous-week ad milestone remains claimable exactly once');
// Daily and weekly counters are independent and update only from actual progress events.
fakeNow=Date.parse('2026-11-02T12:00:00Z');c=boot();for(let i=0;i<20;i++)c.window.Game.collect();st=getSave();assert.equal(st.taskDaily.progress.collects,20);assert.equal(st.taskWeekly.progress.collects,20);const weeklyBookBefore=st.inventory.expBookIntermediate;c.window.Game.claimTask('weekCollect1','weekly');st=getSave();assert.equal(st.inventory.expBookIntermediate,weeklyBookBefore+1);c.window.Game.claimTask('weekCollect1','weekly');assert.equal(getSave().inventory.expBookIntermediate,weeklyBookBefore+1);checks.push('weekly task progress and reward claims are independently protected');
console.log(`PASS ${checks.length}/${checks.length} save migration + UTC task cycle checks`);for(const x of checks)console.log('✓ '+x);
