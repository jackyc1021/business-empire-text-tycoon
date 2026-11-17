#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname, '../..');
const gameRoot = path.join(root, 'game');
const htmlPath = path.join(gameRoot, 'shangye_diguo_v2_19_1.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const checks = [];
function check(label, fn) { fn(); checks.push(label); }
check('current source is v2.19.1', () => {
  assert(html.includes('v2.19.1'));
  assert(fs.existsSync(htmlPath));
});
check('洛神 keeps legacy mythic ID m1 and 星璃 remains m2', () => {
  assert.strictEqual((html.match(/id:'m1',name:'洛神'/g) || []).length, 1);
  assert(html.includes("id:'m2',name:'星璃'"));
});
check('v6 save schema and 10+1 recruitment bonus remain unchanged', () => {
  assert(/SAVE_VERSION\s*=\s*6/.test(html));
  assert(html.includes('actualPulls=pulls===10?11:1'));
  assert(html.includes('赠送1抽'));
});
check('洛神 half/full/expression/shard image wiring is retained', () => {
  for (const p of [
    'assets/luo_shen_shen_hua/ren_wu/luo_shen__ban_shen_xiao_xiang_.png',
    'assets/luo_shen_shen_hua/ren_wu/luo_shen__quan_shen_li_hui_.png',
    'assets/luo_shen_shen_hua/sui_pian/luo_shen__shen_hua_jiao_se_sui_pian__wan_zheng_zu_he_.png'
  ]) assert(html.includes(p), p);
  for (let i=1;i<=6;i++) assert(html.includes(`assets/luo_shen_shen_hua/biao_qing/luo_shen__biao_qing__${String(i).padStart(2,'0')}.png`));
});
check('all five map shortcuts remain in place', () => {
  for (const f of ['qi_ri_qian_dao_.png','ren_wu_zhong_xin_.png','huo_dong_zhong_xin_.png','cheng_jiu_.png','qu_yu_.png']) assert(html.includes(`assets/ui/buttons/${f}`));
});
check('normal navigation references five cropped button images', () => {
  for (const f of ['dao_hang__jing_ying_.png','dao_hang__dian_chang_.png','dao_hang__zhao_mu_.png','dao_hang__bei_bao_.png','dao_hang__she_zhi_.png']) assert(html.includes(`assets/ui/buttons/dao_hang/${f}`));
});
check('floating guide plate is applied as a pseudo-element background', () => {
  assert(html.includes('beFloatingNavV213'));
  assert(html.includes('background-image:url("assets/ui/nav_guide_background.png")'));
  assert(html.includes('.bottom-nav:not(.recruit-subnav)::before'));
});
check('Recruit is the enlarged centered protruding middle button', () => {
  assert(html.includes('grid-template-columns:repeat(5,minmax(0,1fr))'));
  assert(html.includes('transform:translateY(-8px)!important'));
  assert(html.includes('width:clamp(78px,20vw,108px)!important'));
});
check('standard footer reservation removed while recruit sub-navigation stays', () => {
  assert(html.includes('.app:not(.app-recruit-host):not(.app-map-host){padding-bottom:16px!important}'));
  assert(html.includes('bottom-nav.recruit-subnav'));
  assert(html.includes('recruitPoolScroll'));
});
check('existing cultivation modal remains; no separate upgrade page added', () => {
  for (const f of ['function openManager','function useManagerBook','function breakthroughManager','function starManager']) assert(html.includes(f));
});
check('all referenced local asset URLs exist', () => {
  const refs = [...new Set((html.match(/assets\/[^"'`\s)]+/g) || []).map(x => x.replace(/[;,]+$/, '')))];
  const missing = refs.filter(ref => !fs.existsSync(path.join(gameRoot, ref)));
  assert.deepStrictEqual(missing, [], `Missing paths: ${missing.join(', ')}`);
});
check('all five re-cropped navigation images and guide plate are PNG files', () => {
  const files = [
    'assets/ui/nav_guide_background.png',
    'assets/ui/buttons/dao_hang/dao_hang__jing_ying_.png',
    'assets/ui/buttons/dao_hang/dao_hang__dian_chang_.png',
    'assets/ui/buttons/dao_hang/dao_hang__zhao_mu_.png',
    'assets/ui/buttons/dao_hang/dao_hang__bei_bao_.png',
    'assets/ui/buttons/dao_hang/dao_hang__she_zhi_.png'
  ];
  for (const f of files) {
    const sig = fs.readFileSync(path.join(gameRoot, f)).subarray(0,8).toString('hex');
    assert.strictEqual(sig, '89504e470d0a1a0a', `${f} is not PNG`);
  }
});
check('map canvas covers the complete viewport under the floating dock', () => {
  assert(html.includes('id="beFullBleedMapV214"'));
  assert(html.includes('body.map-body-mode .map-world-screen'));
  assert(html.includes('inset:0!important'));
  assert(html.includes('width:100vw!important'));
  assert(html.includes('height:100dvh!important'));
  assert(html.includes('body.map-body-mode .bottom-nav:not(.recruit-subnav){z-index:40!important;}'));
  assert(html.includes('body.map-body-mode .map-zoom-hint'));
});
console.log(`PASS ${checks.length}/${checks.length} full-bleed map + floating navigation checks`);
for (const item of checks) console.log(`✓ ${item}`);
