'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'game','shangye_diguo_v2_19_1.html'),'utf8');
const script=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const KEY='tycoon_text_empire_rebuild_v1';
let now=Date.parse('2026-11-01T12:00:00Z');
class FakeDate extends Date{constructor(...a){super(...(a.length?a:[now]))}static now(){return now}static parse(v){return Date.parse(v)}static UTC(...a){return Date.UTC(...a)}}
class El{constructor(id=''){this.id=id;this.innerHTML='';this.textContent='';this.className='';this.style={setProperty(){},removeProperty(){}};this.classList={add(){},remove(){},toggle(){},contains(){return false}};this.children=[];this.value='';this.files=[];this.scrollLeft=0;this.clientWidth=1280;this.clientHeight=800}addEventListener(){}removeEventListener(){}appendChild(x){this.children.push(x);return x}remove(){}click(){}focus(){}setAttribute(){}getAttribute(){return null}querySelector(){return new El()}querySelectorAll(){return []}closest(){return new El()}getBoundingClientRect(){return {width:1280,height:800,left:0,top:0,right:1280,bottom:800}}getContext(){return null}}
const els={};const get=id=>els[id]||(els[id]=new El(id));
const document={body:get('body'),visibilityState:'visible',getElementById:get,querySelector(){return new El()},querySelectorAll(){return []},addEventListener(){},removeEventListener(){},createElement(tag){const e=new El(tag);e.tagName=tag.toUpperCase();return e}};
const storage={};const localStorage={getItem(k){return Object.hasOwn(storage,k)?storage[k]:null},setItem(k,v){storage[k]=String(v)},removeItem(k){delete storage[k]},key(i){return Object.keys(storage)[i]||null},get length(){return Object.keys(storage).length}};
function boot(){const math=Object.create(Math),win={addEventListener(){},scrollTo(){},innerWidth:1280,innerHeight:800};const c={console:{...console,warn(){},error(){}},document,localStorage,window:win,navigator:{},location:{protocol:'file:',hostname:''},Date:FakeDate,Math:math,JSON,Number,String,Object,Array,Set,Map,Promise,Blob:function(){},URL:{createObjectURL(){return ''},revokeObjectURL(){}},FileReader:function(){},setInterval(){return 1},clearInterval(){},setTimeout(){return 1},clearTimeout(){},requestAnimationFrame(fn){fn()},cancelAnimationFrame(){}};win.document=document;win.localStorage=localStorage;win.Math=math;vm.createContext(c);vm.runInContext(script,c,{timeout:30000});return c}
function getSave(){return JSON.parse(localStorage.getItem(KEY))}
let c=boot(),G=c.window.Game,s=getSave();
// Team migration and max-six lineup
s.managers=['c1','c2','r1','r2','e1','e2','l1','l2','m1','m2'].map(id=>({id,level:50,star:2,exp:0,breakthroughs:4}));s.team=['c1','c2','r1','r2','e1','e2'];s.assignments={};localStorage.setItem(KEY,JSON.stringify(s));c=boot();G=c.window.Game;
G.toggleManagerTeam('l1');s=getSave();assert.equal(s.team.length,6,'cannot add a seventh manager');
G.toggleManagerTeam('e2');s=getSave();assert.equal(s.team.length,5);G.toggleManagerTeam('l1');s=getSave();assert.equal(s.team.length,6);assert(s.team.includes('l1'));
// Monthly rollover preserves earned but unclaimed rewards.
s.taskMonthly={monthKey:'2026-10',progress:{earnGold:100000,upgrades:0,collects:0},claimed:[],pending:[]};localStorage.setItem(KEY,JSON.stringify(s));now=Date.parse('2026-11-01T12:00:00Z');c=boot();G=c.window.Game;s=getSave();assert(s.taskMonthly.pending.some(p=>p.id==='monthGold1'&&p.monthKey==='2026-10'));
const advBefore=s.inventory.expBookAdvanced;G.claimMonthlyMilestone('monthGold1','2026-10');s=getSave();assert.equal(s.inventory.expBookAdvanced,advBefore+1);assert(!s.taskMonthly.pending.some(p=>p.id==='monthGold1'));
// Offline ad failure preserves amount; success doubles once; repeat is blocked.
s.offlinePending={id:'offline-test',amount:1000,seconds:3600,createdAt:now,adDoubled:false,settled:false};s.adDaily.validCount=0;s.adDaily.dayKey='2026-11-01';localStorage.setItem(KEY,JSON.stringify(s));c=boot();G=c.window.Game;
G.openAd('offlineDouble','');G.completeAd(false,'offlineDouble','');s=getSave();assert.equal(s.offlinePending.amount,1000);assert.equal(s.offlinePending.adDoubled,false);assert.equal(s.adDaily.validCount,0);
G.openAd('offlineDouble','');G.completeAd(true,'offlineDouble','');s=getSave();assert.equal(s.offlinePending.amount,2000);assert.equal(s.offlinePending.adDoubled,true);assert.equal(s.adDaily.validCount,1);
G.openAd('offlineDouble','');s=getSave();assert.equal(s.offlinePending.amount,2000);assert.equal(s.adDaily.validCount,1);
const goldBefore=s.gold;G.claimOffline('normal');s=getSave();assert.equal(s.gold,goldBefore+2000);assert.equal(s.offlinePending,null);
console.log('PASS team/offline/monthly tests: six-slot cap, monthly pending claim, offline ad fail/success/one-time double and payout');
