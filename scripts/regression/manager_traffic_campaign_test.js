#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),vm=require('vm');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'game','shangye_diguo_v2_19_1.html'),'utf8');
function extractArray(name){const start=html.indexOf(`const ${name}=[`);assert(start>=0,`${name} missing`);let i=html.indexOf('[',start),depth=0,quote=null,esc=false;for(;i<html.length;i++){const c=html[i];if(quote){if(esc)esc=false;else if(c==='\\')esc=true;else if(c===quote)quote=null;continue;}if(c==="'"||c==='"'||c==='`'){quote=c;continue;}if(c==='[')depth++;if(c===']'&&--depth===0)return html.slice(html.indexOf('=',start)+1,i+1);}throw Error('unterminated '+name)}
function extractFunction(name){const start=html.indexOf(`function ${name}(`);assert(start>=0,`${name} missing`);let brace=html.indexOf('{',start),i=brace,depth=0,quote=null,esc=false;for(;i<html.length;i++){const c=html[i];if(quote){if(esc)esc=false;else if(c==='\\')esc=true;else if(c===quote)quote=null;continue;}if(c==="'"||c==='"'||c==='`'){quote=c;continue;}if(c==='{')depth++;if(c==='}'&&--depth===0)return html.slice(start,i+1);}throw Error('unterminated '+name)}
const managerDefs=extractArray('MANAGER_DEFS');
const campaignDefs=extractArray('BUSINESS_CAMPAIGN_DEFS');
const milestoneDefs=extractArray('BUSINESS_MILESTONES');
const eventDefs=extractArray('EVENT_DEFS');
const abilityCode=html.slice(html.indexOf('const ABILITY_KEYS='),html.indexOf('function teamManagers(){'));
const teamCode=['function teamManagers(){return (state.team||[]).map(id=>ownedManager(id)).filter(Boolean)}',extractFunction('teamIncomeBonus'),extractFunction('teamDiscountBonus'),extractFunction('teamTrafficBonus'),extractFunction('teamOfflineRate')].join('\n');
const orderCode=extractFunction('shopOrderModel');
const claimCode=extractFunction('claimBusinessMilestone');
const eventCode=[extractFunction('eventAvailable'),extractFunction('spawnEvent'),extractFunction('updateTimedState')].join('\n');
const campaignCode=['function campaignStartAt(now){const epoch=Date.UTC(2026,10,1);const period=14*86400000;return epoch+Math.floor((now-epoch)/period)*period}',extractFunction('campaignDef'),extractFunction('campaignMilestoneTarget'),extractFunction('makeCampaign'),extractFunction('rollCampaignIfNeeded')].join('\n');
const RealDate=Date;class FixedDate extends RealDate{static now(){return RealDate.UTC(2026,10,1)}};
const context={console,Date:FixedDate,Math,Object,Number,String,Array,JSON,Infinity,NaN,clamp:(n,a,b)=>Math.min(b,Math.max(a,Number.isFinite(Number(n))?Number(n):a)),state:{team:[],managers:[],businessCampaign:null,buffs:{promoUntil:0,discountUntil:0,regionBuffs:{}},eventState:{active:null,nextAt:0,completed:0}},BUSINESS_CAMPAIGN_DEFS:[],BUSINESS_MILESTONES:[],GOLD_REPRESENTATION_LIMIT:1e300};
vm.createContext(context);
vm.runInContext(`const MANAGER_DEFS=${managerDefs}; const BUSINESS_CAMPAIGN_DEFS=${campaignDefs}; const BUSINESS_MILESTONES=${milestoneDefs}; const EVENT_DEFS=${eventDefs}; function managerDef(id){return MANAGER_DEFS.find(d=>d.id===id)} function ownedManager(id){return state.managers.find(m=>m.id===id)} let testGrants=[];let testNotices=[];function ensurePeriods(){}function grantReward(x){testGrants.push(x)}function save(){}function render(){}function toast(x){testNotices.push(x)} function log(){}\n${abilityCode}\n${teamCode}\n${orderCode}\n${campaignCode}\n${claimCode}\n${eventCode}\n`,context);
const result=vm.runInContext(`(()=>{const defs=MANAGER_DEFS;const rarities=['common','rare','epic','legendary','mythic'];const counts=Object.fromEntries(rarities.map(r=>[r,defs.filter(d=>d.rarity===r).length]));const ids=defs.map(d=>d.id);const all=defs.map(d=>{const m={id:d.id,level:1,star:1};const a=managerAbilityLevels(m);return {id:d.id,total:Object.values(a).reduce((x,y)=>x+y,0),levels:a,budget:managerAbilityBudget(m),weights:Object.values(d.abilityWeights||{}).reduce((x,y)=>x+y,0)}});const max=defs.map(d=>managerAbilityBudget({id:d.id,level:100,star:5}));return {counts,idsUnique:new Set(ids).size===ids.length,allPositive:all.every(x=>Object.values(x.levels).every(v=>v>=1)),budgetsMatch:all.every(x=>x.total===x.budget),weightsValid:all.every(x=>x.weights===100),rarityBudgetMonotonic:['common','rare','epic','legendary','mythic'].every((r,i,a)=>i===0||ABILITY_BUDGET_BASE[r]>ABILITY_BUDGET_BASE[a[i-1]]),maxBudgetRange:[Math.min(...max),Math.max(...max)]}})()`,context);
assert.deepStrictEqual(JSON.parse(JSON.stringify(result.counts)),{common:4,rare:5,epic:4,legendary:3,mythic:2});
assert(result.idsUnique&&result.allPositive&&result.budgetsMatch&&result.weightsValid&&result.rarityBudgetMonotonic);
// Verify all 4 attributes are live and all-team stacking respects soft caps.
const teamTest=vm.runInContext(`(()=>{state.managers=MANAGER_DEFS.slice(0,6).map(d=>({id:d.id,level:100,star:5}));state.team=state.managers.map(m=>m.id);return {income:teamIncomeBonus(),discount:teamDiscountBonus(),traffic:teamTrafficBonus(),offline:teamOfflineRate()}})()`,context);
assert(teamTest.income>0&&teamTest.discount>0&&teamTest.traffic>0&&teamTest.offline>.60);
assert(teamTest.income<=.6000001&&teamTest.discount<=.3500001&&teamTest.traffic<=.3500001&&teamTest.offline<=.8500001);
const maxTeam=vm.runInContext(`(()=>{const defs=MANAGER_DEFS;let best={income:0,discount:0,traffic:0,offline:0};for(let a=0;a<defs.length-5;a++)for(let b=a+1;b<defs.length-4;b++)for(let c=b+1;c<defs.length-3;c++)for(let d=c+1;d<defs.length-2;d++)for(let e=d+1;e<defs.length-1;e++)for(let f=e+1;f<defs.length;f++){const picks=[defs[a],defs[b],defs[c],defs[d],defs[e],defs[f]];state.managers=picks.map(x=>({id:x.id,level:100,star:5}));state.team=state.managers.map(x=>x.id);best.income=Math.max(best.income,teamIncomeBonus());best.discount=Math.max(best.discount,teamDiscountBonus());best.traffic=Math.max(best.traffic,teamTrafficBonus());best.offline=Math.max(best.offline,teamOfflineRate())}return best})()`,context);
assert(maxTeam.income<=.6000001&&maxTeam.discount<=.3500001&&maxTeam.traffic<=.3500001&&maxTeam.offline<=.8500001);
// Demand rises with traffic, but realized orders never exceed 135% capacity.
context.shopBaseIncome=()=>1000;context.teamTrafficBonus=()=>.20;
const orderLow=vm.runInContext(`shopOrderModel({id:'test',baseIncome:100})`,context);
context.teamTrafficBonus=()=>.60;
const orderHigh=vm.runInContext(`shopOrderModel({id:'test',baseIncome:100})`,context);
assert(orderLow.demandPerMin>0&&orderLow.servedPerMin===orderLow.demandPerMin);
assert(orderHigh.demandPerMin>orderHigh.capacityPerMin&&orderHigh.servedPerMin===orderHigh.capacityPerMin);
assert(Math.abs(orderHigh.utilization-1)<1e-9);
// Campaigns rotate every 14 days, use template-specific thresholds, and preserve earned rewards/history.
const campaignTest=vm.runInContext(`(()=>{const now=Date.UTC(2026,10,20);const c=makeCampaign(Date.UTC(2026,10,1));const old={...c,endsAt:now-1,progress:{gold:1000000,upgrades:0,recruits:0},claimed:[],pending:[],history:[]};const s={businessCampaign:old};rollCampaignIfNeeded(s,now);return {id:s.businessCampaign.id,endsFuture:s.businessCampaign.endsAt>now,pending:s.businessCampaign.pending.length,history:s.businessCampaign.history.length,historyName:s.businessCampaign.history[0].name,target:campaignMilestoneTarget(BUSINESS_MILESTONES[0],s.businessCampaign.id)}})()`,context);
assert(campaignTest.endsFuture&&campaignTest.pending>=1&&campaignTest.history===1);
assert(['food_festival','city_trade_fair','global_brand_week'].includes(campaignTest.id));
const catchupClaim=vm.runInContext(`(()=>{testGrants.length=0;testNotices.length=0;state.businessCampaign={id:'city_trade_fair',startedAt:10,endsAt:9999999999999,progress:{gold:20000,upgrades:0,recruits:0},claimed:[],pending:[{id:'bizGold1',campaignId:'food_festival',campaignName:'美食街人气节',startedAt:123,reward:{diamonds:1},claimed:false}],history:[]};claimBusinessMilestone('bizGold1','123');const afterOld={grants:testGrants.length,pending:state.businessCampaign.pending.length,activeClaimed:state.businessCampaign.claimed.length};claimBusinessMilestone('bizGold1','123');const afterDuplicate={grants:testGrants.length,pending:state.businessCampaign.pending.length,activeClaimed:state.businessCampaign.claimed.length};claimBusinessMilestone('bizGold1');const afterCurrent={grants:testGrants.length,pending:state.businessCampaign.pending.length,activeClaimed:state.businessCampaign.claimed.length};return {afterOld,afterDuplicate,afterCurrent,notices:testNotices}})()`,context);
assert(catchupClaim.afterOld.grants===1&&catchupClaim.afterOld.pending===0&&catchupClaim.afterOld.activeClaimed===0);
assert(catchupClaim.afterDuplicate.grants===1&&catchupClaim.afterDuplicate.activeClaimed===0);
assert(catchupClaim.afterCurrent.grants===2&&catchupClaim.afterCurrent.activeClaimed===1);
const eventLoop=vm.runInContext(`(()=>{let saves=0,notices=0;save=()=>saves++;toast=()=>notices++;const now=Date.now();state.buffs={promoUntil:0,discountUntil:0,regionBuffs:{}};state.eventState={active:{id:'promotion',startedAt:now-600000,expiresAt:now-1,claimed:false},nextAt:now-1,completed:0};updateTimedState(now);const afterExpire={active:!!state.eventState.active,nextAt:state.eventState.nextAt};updateTimedState(state.eventState.nextAt+1);const afterSpawn={active:!!state.eventState.active,nextAt:state.eventState.nextAt,expiresAt:state.eventState.active?.expiresAt};updateTimedState(Date.now()+1000);const whileActive={active:!!state.eventState.active};return {afterExpire,afterSpawn,whileActive,eventCount:EVENT_DEFS.length}})()`,context);
const eventDurations=vm.runInContext(`EVENT_DEFS.map(e=>e.duration)`,context);
assert(eventDurations.every(ms=>ms>=8*60000&&ms<=10*60000));
assert(eventLoop.eventCount===5&&eventLoop.afterExpire.active===false&&eventLoop.afterSpawn.active===true&&eventLoop.whileActive.active===true);
assert(eventLoop.afterExpire.nextAt>Date.UTC(2026,10,1));
console.log('PASS 18-manager roster, stable IDs, 4 positive abilities, rarity budgets, team caps, order/capacity saturation, 14-day campaign rollover and reward catch-up');
console.log(JSON.stringify({roster:result.counts,teamAtMax:teamTest,teamBestPossible:maxTeam,orderCapacity:{low:orderLow.utilization,high:orderHigh.utilization},campaign:campaignTest,catchupClaim,eventLoop},null,2));
