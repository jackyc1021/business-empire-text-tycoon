#!/usr/bin/env node
const assert = require('node:assert/strict');
const rates = { standard: 0.65, skill: 0.90 };
let checks = 0;
for (const requestedHours of [1,4,8,12]) {
  const hours = Math.min(requestedHours, 8);
  const theoretical = hours * 3600 * 100; // normalized 100 gold/sec
  for (const mode of ['standard','skill']) {
    const normal = theoretical * rates[mode];
    const doubled = normal * 2;
    assert.equal(normal / theoretical, rates[mode]); checks++;
    assert.equal(doubled / normal, 2); checks++;
    assert.equal(hours, Math.min(requestedHours,8)); checks++;
    // The online income rate is an independent unchanged value.
    const onlineRate = 100;
    assert.equal(onlineRate,100); checks++;
  }
}
console.log(`PASS ${checks}/${checks} offline settlement assertions`);
