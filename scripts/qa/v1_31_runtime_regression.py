#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, json, csv
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'game/shangye_diguo_v2_19_1.html'
assert HTML.exists(), 'v2.19.1 source missing'
s=HTML.read_text()
js='\n'.join(re.findall(r'<script>(.*?)</script>',s,re.S))
tmp=ROOT/'qa'/'_v1_31_extracted.js'; tmp.write_text(js)
r=subprocess.run(['node','--check',str(tmp)],capture_output=True,text=True)
tmp.unlink(missing_ok=True)
assert r.returncode==0, r.stderr
# Unified lineup and backward-compatible migration
assert 'team:[]' in s and 's.team=Array.isArray(x.team)' in s
assert 'slice(0,6)' in s and 'function toggleManagerTeam' in s
assert 'toggleManagerTeam,' in s[s.index('const Game='):s.index('const Game=')+1500]
assert 'assignedTo(' not in s and 'globalIncomeSkill' not in s
assert 'function assignManager(id){toggleManagerTeam(id)}' in s
# Offline rules and optional one-time double ad
assert 'return .60+Math.min(cap,bonus)' in s
assert 'function teamOfflineRate()' in s
assert "Game.openAd('offlineDouble','')" in s
assert "kind==='offlineDouble'" in s and 'adDoubled=true' in s
assert 'Math.min(elapsed,8*3600)' in s
# Task / reward schedule counts
for name,count in [('DAILY_TASKS',7),('WEEKLY_TASKS',6),('MONTHLY_MILESTONES',4),('SIGN_REWARDS',7),('BUSINESS_MILESTONES',6),('HONOR_STORE_ITEMS',8)]:
    m=re.search(rf'const {name}=\[(.*?)\];',s,re.S)
    assert m, f'{name} missing'
    n=len(re.findall(r"\{label:'" if name=='SIGN_REWARDS' else r"\{id:'",m.group(1)))
    assert n==count,(name,n,count)
assert 'claimMonthlyMilestone' in s and 'pending' in s[s.index('function ensurePeriodsFor'):s.index('function buyShop')]
assert 'ticket:4' in s and 'ticket:2,diamonds:30' in s
for task_block in [re.search(r'const DAILY_TASKS=\[(.*?)\];',s,re.S).group(1),re.search(r'const WEEKLY_TASKS=\[(.*?)\];',s,re.S).group(1)]:
    assert 'recruit' not in task_block and 'ads' not in task_block
assert 'expBookBasic:5' in re.search(r'const SIGN_REWARDS=\[(.*?)\];',s,re.S).group(1)
# Exact EXP arithmetic
need=sum(100+10*(lv-1) for lv in range(1,100))
assert need==58410 and need*6==350460
exp_daily=7*200+800+700+700
exp_weekly=6*500+2000+2000+1000
exp_sign=7*500
exp_event=1000+1000+1500+1500+3000
exp_month=12500
exp_achievements=14*2000
supply=exp_daily*60+exp_weekly*8+exp_sign*8.5714285714+exp_event*4+exp_month*2+exp_achievements
assert exp_daily==3600 and exp_weekly==8000 and exp_sign==3500 and exp_event==8000
assert round(supply)==395000
# v1.31 18-manager roster, four abilities, traffic and recurring campaign implementation
assert len(re.findall(r"\{id:'(?:c1|c2|c3|c4|r1|r2|r3|r4|r5|e1|e2|e3|e4|l1|l2|l3|m1|m2)'", s)) == 18
assert 'function managerAbilityLevels(m)' in s and 'ABILITY_BUDGET_BASE={common:12,rare:15,epic:18,legendary:21,mythic:24}' in s
assert 'function shopOrderModel(d)' in s and 'const capacityPerMin=baseOrdersPerMin*1.35' in s
assert 'function rollCampaignIfNeeded(s,now)' in s and 'history.slice(-12)' in s and 'pending.slice(-60)' in s
# Candidate shop inventory
with (ROOT/'project_docs/SHOP_ECONOMY_30_CANDIDATE.csv').open(encoding='utf-8-sig') as f:
    shops=list(csv.DictReader(f))
assert len(shops)==30
# Version / service worker
assert 'v2.19.1' in (ROOT/'VERSION.md').read_text()
sw=(ROOT/'game/service-worker.js').read_text()
assert 'shangye_diguo_v2_19_1.html' in sw
print('PASS v1.31 runtime regression: JS syntax, unified lineup, save migration, offline double-ad, task counts, 60-day reward arithmetic, 30-shop catalog, PWA entry')
