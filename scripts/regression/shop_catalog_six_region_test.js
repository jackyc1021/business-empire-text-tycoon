#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'game','shangye_diguo_v2_19_1.html'),'utf8');
const shopBlock=html.split('const SHOP_DEFS=[')[1]?.split('\n];')[0]||'';
const regionBlock=html.split('const REGION_DEFS=[')[1]?.split('\n];')[0]||'';
const shopIds=[...shopBlock.matchAll(/\{id:'([^']+)'/g)].map(x=>x[1]);
const regions=[...regionBlock.matchAll(/\{id:'([^']+)'[\s\S]*?shopIds:\[([^\]]+)\]/g)].map(m=>({id:m[1],shops:[...m[2].matchAll(/'([^']+)'/g)].map(x=>x[1])}));
const expected={
 street:['stall','convenience','bakery','barber','laundry'],
 food:['cafe','hotel','restaurant','pizza','chinese'],
 mall:['fashion','tech','mall','jewelry','supermarket'],
 finance:['factory','tower','space','bank','automotive'],
 international:['airport','logistics','trade','airline','seaport'],
 future:['ai','energy','biotech','internet','exploration']
};
assert.strictEqual(shopIds.length,30,'runtime must define exactly 30 shops');
assert.strictEqual(new Set(shopIds).size,30,'shop IDs must be unique');
assert.strictEqual(regions.length,6,'runtime must define six regions');
assert.deepStrictEqual(Object.fromEntries(regions.map(r=>[r.id,r.shops])),expected,'each region must contain the approved five shops in order');
for(const r of regions) assert.strictEqual(r.shops.length,5,`${r.id} must contain five shops`);
for(const id of ['stall','cafe','fashion','tech','hotel','mall','factory','tower','space']) assert(shopIds.includes(id),`legacy shop ID ${id} must be preserved`);
for(const id of shopIds.filter(id=>!['stall','cafe','fashion','tech','hotel','mall','factory','tower','space'].includes(id))) {
 const re=new RegExp(`\\{id:'${id}'[^}]*catalogOnly:true`);
 assert(re.test(shopBlock),`${id} must remain catalogue-only until economy values are approved`);
}
assert(html.includes('function shopBaseIncome(d){const s=shopState(d.id);if(d.catalogOnly||!s.level)return 0;'), 'catalog-only shops must never generate income');
assert(html.includes("if(d.catalogOnly){toast('商铺目录已建立；该商铺的经济参数尚未确认，暂不可开业');return}"), 'catalog-only shops must reject opening/upgrades');
assert(html.includes('if(r.unlockable===false){toast(\'该区域已列入规划；解锁条件与成本待确认\');return}'), 'pending regions must reject unlock attempts');
assert(/SAVE_VERSION\s*=\s*6/.test(html),'save schema must remain v6');
assert(/s\.shops=SHOP_DEFS\.map\(d=>\{const old=x\.shops\.find\(z=>z&&z\.id===d\.id\)/.test(html),'save migration must map shop progress by stable ID');
for(const id of ['international','future']) assert(regionBlock.includes(`id:'${id}'`)&&regionBlock.includes('unlockable:false'),'new regions must remain locked pending approved conditions/costs');
console.log('PASS 8/8 six-region / 30-shop catalogue checks');
