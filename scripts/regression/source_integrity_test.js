#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');
const assert = require('assert');
const root = path.resolve(__dirname, '../..');
const gameDir = path.join(root, 'game');
const sourceName = 'shangye_diguo_v2_19_1.html';
const sourcePath = path.join(gameDir, sourceName);
const html = fs.readFileSync(sourcePath, 'utf8');
const checks = [];
function check(label, fn) { fn(); checks.push(label); }
check('only one current game HTML is packaged', () => {
  const htmlFiles = fs.readdirSync(gameDir).filter(f => /^shangye_diguo_v.*\.html$/.test(f));
  assert.deepStrictEqual(htmlFiles, [sourceName]);
});
check('all inline JavaScript passes node --check', () => {
  const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m => m[1]).filter(s => s.trim());
  assert(scripts.length > 0, 'No inline scripts found');
  const tmp = path.join(os.tmpdir(), `be-inline-${process.pid}.js`);
  try {
    fs.writeFileSync(tmp, scripts.join('\n;\n'), 'utf8');
    const result = spawnSync(process.execPath, ['--check', tmp], { encoding: 'utf8' });
    assert.strictEqual(result.status, 0, result.stderr || result.stdout || 'node --check failed');
  } finally { try { fs.unlinkSync(tmp); } catch {} }
});
check('every local assets URL used by HTML exists', () => {
  const refs = [...new Set((html.match(/assets\/[^"'`\s)]+/g) || []).map(x => x.replace(/[;,]+$/, '')))];
  const missing = refs.filter(ref => !fs.existsSync(path.join(gameDir, ref)));
  assert.deepStrictEqual(missing, [], `Missing local assets: ${missing.join(', ')}`);
});
check('current source keeps game and save versions', () => {
  assert(html.includes('v2.19.1'));
  assert(html.includes('grantDeveloperResources'));
  assert(html.includes('开发者资源工具'));
  assert(html.includes('devGoldAmount') && html.includes('devDiamondAmount'));
  assert(/RECRUIT_PITY=\{normal:\{hard:50,target:'legendary'\}/.test(html), 'normal pool must not carry a soft-pity increment');
  assert(/normal:\{common:48,rare:40,epic:10\.8,legendary:1\.2\}/.test(html), 'ordinary base probabilities must remain fixed at the user-approved values');
  assert(/advanced:\{soft:70,hard:80,target:'mythic'\}/.test(html), 'advanced pity thresholds must remain unchanged');
  assert(html.includes('manifest.webmanifest') && html.includes('service-worker.js'), 'PWA registration missing');
  assert(/SAVE_VERSION\s*=\s*6/.test(html));
});
check('one current copy of living project records exists', () => {
  for (const f of ['CHANGELOG.md','OPEN_ITEMS.md','DECISIONS.md','HANDOFF.md','PROJECT_MASTER.md','DELIVERY_MANIFEST.md']) {
    assert(fs.existsSync(path.join(root, 'project_docs', f)), `Missing ${f}`);
  }
  for (const f of ['CHANGELOG_v1.4.md','Open_Items_v0.9.md','Decision_Log_v0.9.md','Handoff_Next_Developer_v1.4.md']) {
    assert(!fs.existsSync(path.join(root, 'project_docs', f)), `Old duplicate remains: ${f}`);
  }
});
check('all 24 tracked register entries plus six manager design sections are retained and nine verified items are closed', () => {
  const openItems = fs.readFileSync(path.join(root, 'project_docs', 'OPEN_ITEMS.md'), 'utf8');
  const ids = [...openItems.matchAll(/^### (?:SYS|ADS|TASK|SEC|ART|QA|PLATFORM)-\d+/gm)];
  assert.strictEqual(ids.length, 24, `Expected 24 tracked items, found ${ids.length}`);
  for (const id of ['MGR-001','MGR-002','MGR-003','MGR-004','MGR-005','MGR-006']) assert(openItems.includes(`## ${id}`), `Missing manager design section ${id}`);
  assert.strictEqual((openItems.match(/状态：CLOSED/g) || []).length, 9, 'SYS-007, TASK-001, MGR-001..003/007/008, OPS-001 and LIVEOPS-001 are closed');
  for (const id of ['MGR-001','MGR-002','MGR-003','MGR-007','MGR-008','LIVEOPS-001']) assert(new RegExp('## '+id+'[\\s\\S]*?状态：CLOSED').test(openItems), `${id} must be closed after v1.31 implementation`);
  assert(openItems.includes('OPS-001') && openItems.includes('三主题UTC 14天自动轮换、最近12期历史、达成未领奖励快照与跨期补领'), 'OPS-001 activity calendar closure missing');
  for (const id of ['SYS-007', 'TASK-001']) assert(openItems.includes(`### ${id}`), `Missing closed item ${id}`);
  assert(/### SEC-001[\s\S]*?状态：OPEN/.test(openItems), 'SEC-001 must remain open for production-build gating');
  const version = fs.readFileSync(path.join(root, 'VERSION.md'), 'utf8');
  assert(version.includes('Bundle Version: v1.36') && version.includes('Game Version: v2.19.1'));
  const platform = JSON.parse(fs.readFileSync(path.join(gameDir, 'platform/PLATFORM_CAPABILITIES.json'), 'utf8'));
  assert.strictEqual(platform.bundle_version, '1.34');
  assert.strictEqual(platform.game_version, '2.19.0');
});
console.log(`PASS ${checks.length}/${checks.length} source integrity checks`);
for (const item of checks) console.log(`✓ ${item}`);
