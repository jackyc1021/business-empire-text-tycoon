#!/usr/bin/env python3
"""Joint all-shop cost/income/manager surface analysis; candidate-only, no runtime edits."""
import csv, math, itertools, statistics, random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'project_docs'
SHOPS=[('stall','街角小摊',10,1,'street'),('cafe','精品咖啡馆',80,5,'food'),('fashion','潮流服饰店',650,24,'mall'),('tech','数码科技馆',5200,115,'mall'),('hotel','精品酒店',42000,560,'food'),('mall','城市购物中心',360000,2800,'mall'),('factory','智能制造园',3200000,15000,'finance'),('tower','环球金融中心',28000000,85000,'finance'),('space','商业航天集团',260000000,520000,'finance')]
COST_P=[1.0,1.15,1.3,1.5,1.75,2.0]
INCOME_Q=[1.0,1.025,1.05,1.1]
# Exact source-derived manager power at Lv100/5-star; skill effects use source formula.
# Three deployment envelopes: none; source-derived mid-level rare income/discount manager; source-derived max-level five-star rare income and legendary discount manager.
MGR=[('none',1.0,0.0,0.0),('mid_income',3.06,0.2015,0.0),('mid_discount',3.35,0.0,0.141),('max_income',5.51,0.1765,0.0),('max_discount',13.23,0.0,0.1765)]
# Source formulas: managerPower=qualityBase*starMultiplier*(1+.02*(level-1))/100; skillEffect=skillBase*(1+.015*(level-1)+.07*(star-1))
# These are envelope cases, not claims of all managers simultaneously available.
def wr(path, rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rows=[]
for sid,name,bc,bi,region in SHOPS:
 for lv in range(1,101):
  for p,q,(mgr,power,skill,discount) in itertools.product(COST_P,INCOME_Q,MGR):
   cost=math.ceil(bc*((lv+1)**p)*(1-discount))
   old_inc=bi*lv
   new_inc=bi*(lv**q)
   marginal=bi*((lv+1)**q-lv**q)*power*(1+skill)
   payback=cost/marginal if marginal else float('inf')
   rows.append({'shop_id':sid,'shop_name':name,'level_before':lv,'level_after':lv+1,'cost_exponent_p':p,'income_exponent_q':q,'manager_case':mgr,'manager_power':power,'income_skill':skill,'upgrade_discount':discount,'upgrade_cost':cost,'base_income_before_per_sec':old_inc,'candidate_income_after_per_sec':new_inc,'marginal_income_per_sec_with_manager':marginal,'static_payback_seconds':payback,'region':region})
wr(OUT/'JOINT_SHOP_LEVEL_MANAGER_SURFACE.csv',rows)
# Summary by candidate pair and manager envelope across all 9 shops and levels 1..100.
sumrows=[]
from collections import defaultdict
rowgroups=defaultdict(list)
for rr in rows: rowgroups[(rr['cost_exponent_p'],rr['income_exponent_q'],rr['manager_case'])].append(rr)
for p,q,m in itertools.product(COST_P,INCOME_Q,MGR):
 arr=rowgroups[(p,q,m[0])]
 pb=[r['static_payback_seconds'] for r in arr]
 # spread is median ratio of worst/first-level payback, useful to expose late-game inflation
 sumrows.append({'cost_exponent_p':p,'income_exponent_q':q,'manager_case':m[0],'median_payback_sec':statistics.median(pb),'p10_payback_sec':sorted(pb)[int(.1*len(pb))],'p90_payback_sec':sorted(pb)[int(.9*len(pb))],'max_payback_sec':max(pb),'shop_level_cases':len(arr)})
wr(OUT/'JOINT_ECONOMY_CURVE_CASE_SUMMARY.csv',sumrows)
# deterministic Monte Carlo: random portfolio states, upgrades, manager assignment profiles; compare purchase affordability and time-to-next-upgrade pressure.
# Not a player progression sim: a cashflow stress test at common starting levels, with no unapproved reward assumptions.
mc=[]; rng=random.Random(20261101)
for p,q,m in itertools.product(COST_P,INCOME_Q,MGR):
 for run in range(27):
  levels={s[0]:rng.randint(1,30) for s in SHOPS}; gold=0.0; sec=0.0; stuck=0; maxstuck=0
  # 30 day cashflow with 12.5/30/75 active minutes, 0/4/8h offline; 3 active/offline profiles are stratified via deterministic draws.
  activity=[12.5,30,75][(run//3)//3]; off=[0,4,8][(run//3)%3]
  # Portfolio income uses each shop's own current level and manager multiplier. Regional bonus excluded here as a separate sensitivity surface.
  power=m[1]; skill=m[2]
  for day in range(30):
   income=sum(bi*(levels[sid]**q)*power*(1+skill) for sid,name,bc,bi,reg in SHOPS)
   gold += income*(off*3600*.60 + activity*60)
   # Buy best marginal income per coin among all nine industries, with a small noisy preference.
   options=[]
   for sid,name,bc,bi,reg in SHOPS:
    lv=levels[sid]; cost=math.ceil(bc*((lv+1)**p)*(1-m[3])); gain=bi*(((lv+1)**q)-(lv**q))*power*(1+skill)
    if cost<=gold: options.append((gain/cost*math.exp(rng.gauss(0,.25)),sid,cost))
   bought=0
   # operations bounded by active minutes, 1 buy per 2 minutes; high activity materially differs.
   for _ in range(max(1,int(activity/2))):
    if not options: break
    options.sort(reverse=True); _,sid,cost=options.pop(0)
    if cost>gold: continue
    gold-=cost; levels[sid]+=1; bought+=1
    # rebuild options after each purchase
    options=[]
    for sid2,n2,bc2,bi2,reg2 in SHOPS:
     lv2=levels[sid2]; c2=math.ceil(bc2*((lv2+1)**p)*(1-m[3])); g2=bi2*(((lv2+1)**q)-(lv2**q))*power*(1+skill)
     if c2<=gold: options.append((g2/c2*math.exp(rng.gauss(0,.25)),sid2,c2))
   stuck=stuck+1 if bought==0 else 0; maxstuck=max(maxstuck,stuck)
  final_income=sum(bi*(levels[sid]**q)*power*(1+skill) for sid,name,bc,bi,reg in SHOPS)
  mc.append({'cost_exponent_p':p,'income_exponent_q':q,'manager_case':m[0],'run':run,'active_minutes_per_day':activity,'offline_hours_per_day':off,'total_levels_end':sum(levels.values()),'income_per_sec_end':final_income,'gold_end':gold,'max_consecutive_stuck_days':maxstuck})
wr(OUT/'JOINT_ECONOMY_MC_RUNS.csv',mc)
# summarize MC
mcs=[]
mcgroups=defaultdict(list)
for rr in mc: mcgroups[(rr['cost_exponent_p'],rr['income_exponent_q'],rr['manager_case'],rr['active_minutes_per_day'],rr['offline_hours_per_day'])].append(rr)
for p,q,mgr in itertools.product(COST_P,INCOME_Q,[x[0] for x in MGR]):
 for activity,off in itertools.product([12.5,30,75],[0,4,8]):
  a=mcgroups[(p,q,mgr,activity,off)]
  for metric in ['total_levels_end','income_per_sec_end','gold_end','max_consecutive_stuck_days']:
   vals=sorted(r[metric] for r in a)
   mcs.append({'cost_exponent_p':p,'income_exponent_q':q,'manager_case':mgr,'active_minutes':activity,'offline_hours':off,'metric':metric,'p10':vals[0],'median':statistics.median(vals),'p90':vals[2]})
wr(OUT/'JOINT_ECONOMY_MC_SUMMARY.csv',mcs)
print('PASS surface_rows',len(rows),'MC_runs',len(mc),'MC_summary_rows',len(mcs))
