#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),{spawnSync}=require('child_process');
const root=path.resolve(__dirname,'../..'),game=path.join(root,'game');
const html=fs.readFileSync(path.join(game,'shangye_diguo_v2_19_1.html'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(game,'manifest.webmanifest'),'utf8'));
const sw=fs.readFileSync(path.join(game,'service-worker.js'),'utf8');
assert.equal(manifest.orientation,'landscape');assert.equal(manifest.display,'standalone');
assert(manifest.icons.some(x=>x.sizes==='192x192')&&manifest.icons.some(x=>x.sizes==='512x512'));
for(const x of manifest.icons)assert(fs.existsSync(path.join(game,x.src.replace('./',''))),`missing icon ${x.src}`);
assert(html.includes("navigator.serviceWorker.register('./service-worker.js'"));
const precacheMatch=sw.match(/const PRECACHE_URLS=(\[[\s\S]*?\]);/);assert(precacheMatch,'precache manifest missing');const allRefs=JSON.parse(precacheMatch[1]);assert.equal(new Set(allRefs).size,allRefs.length,'precache manifest contains duplicate entries');const refs=allRefs.filter(p=>p.startsWith('./assets/')).map(p=>p.slice(2));
for(const p of refs)assert(fs.existsSync(path.join(game,p)),`service-worker precache missing ${p}`);
const tmp=path.join(require('os').tmpdir(),`be-sw-${process.pid}.js`);fs.writeFileSync(tmp,sw);
const check=spawnSync(process.execPath,['--check',tmp],{encoding:'utf8'});try{fs.unlinkSync(tmp)}catch{}
assert.equal(check.status,0,check.stderr||'service worker syntax error');
for(const p of ['platform/ad-provider-contract.js','platform/cloud-save-provider-contract.js','platform/PLATFORM_CAPABILITIES.json'])assert(fs.existsSync(path.join(game,p)));
for(const p of ['platform/ad-provider-contract.js','platform/cloud-save-provider-contract.js']){const tmpm=path.join(require('os').tmpdir(),`be-esm-${process.pid}-${path.basename(p)}.mjs`);fs.writeFileSync(tmpm,fs.readFileSync(path.join(game,p),'utf8'));const parsed=spawnSync(process.execPath,['--check',tmpm],{encoding:'utf8'});try{fs.unlinkSync(tmpm)}catch{}assert.equal(parsed.status,0,parsed.stderr||`module syntax error: ${p}`)}
console.log(`PASS PWA/offline static checks; ${refs.length} unique local image assets in precache.`);
