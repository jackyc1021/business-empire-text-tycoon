const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'game/shangye_diguo_v2_19_1.html'), 'utf8');
const assets = [
  'game/assets/ui/resources/jin_bi_.png',
  'game/assets/ui/resources/gao_ji_zhao_mu_quan_.png',
  'game/assets/ui/resources/di_ji_zhao_mu_quan_.png'
];
for (const a of assets) assert(fs.existsSync(path.join(root, a)), `missing ${a}`);
assert(html.includes('assets/ui/resources/jin_bi_.png'), 'gold image must be wired');
assert(html.includes('assets/ui/resources/gao_ji_zhao_mu_quan_.png'), 'advanced ticket image must be wired');
assert(html.includes('assets/ui/resources/di_ji_zhao_mu_quan_.png'), 'normal ticket image must be wired');
assert(html.includes('resourceValue=normal?state.inventory.ticket:state.inventory.advancedTicket'), 'recruit resource display must follow selected pool');
assert(html.includes("name:'普通招募券',icon:'',image:'assets/ui/resources/di_ji_zhao_mu_quan_.png'"), 'inventory normal ticket art missing');
assert(html.includes("name:'高级招募券',icon:'',image:'assets/ui/resources/gao_ji_zhao_mu_quan_.png'"), 'inventory advanced ticket art missing');
assert(html.includes("<div class=\"wallet-item\"><small><img class=\"resource-inline-icon\" src=\"assets/ui/resources/gao_ji_zhao_mu_quan_.png\""), 'advanced ticket wallet art missing');
assert(html.includes('assets/ui/resources/jin_bi_.png" alt="">金币'), 'map gold resource art missing');
assert(html.includes('赠送1抽，共11抽'), '10+1 draw description must remain');
assert(html.includes('actualPulls=pulls===10?11:1'), '10+1 extra draw logic must remain unchanged');
console.log('Resource icon integration smoke test: 11/11 assertions passed.');
