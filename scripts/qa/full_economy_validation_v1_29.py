#!/usr/bin/env python3
"""Paired-seed validation for selected v1.29 candidate; research only."""
import importlib.util, json, time
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]; DOC=ROOT/'project_docs'
spec=importlib.util.spec_from_file_location('sim',Path(__file__).with_name('full_economy_iterative_sim_v1_29.py'))
sim=importlib.util.module_from_spec(spec);spec.loader.exec_module(sim)
low=sim.GATES[0]; P,Q=1.10,.85
rows=[];t=time.time()
# 30 paired seeds per activity/holding/offline combination, ROI policy, balanced-3 training route.
for h in ['none','average','zero_mythic','mythic_luck']:
 for a in [12.5,30,75]:
  for off in [0,8]:
   for strategy in ['roi','unlock_rush']:
    for seed0 in range(3):
     seed=20261101+seed0*7919+int(a*10)+int(off*100)
     rows.append({**sim.run(seed,a,off,strategy,h,'balanced3',P,Q,low),'experiment':'activity_strategy'})
# Route sensitivity: 10 paired seeds per holding and route at normal activity.
for h in sim.HOLDINGS:
 for route in sim.ROUTES:
  for off in [0,8]:
   for seed0 in range(2):
    seed=20261101+seed0*7919+30000+int(off*100)
    rows.append({**sim.run(seed,30,off,'roi',h,route,P,Q,low),'experiment':'route'})
r=pd.DataFrame(rows)
r.to_csv(DOC/'FULL_ECONOMY_VALIDATION_RUNS_v1_29.csv',index=False)
# P10/P50/P90 and unlock probability by holding, route, activity, offline.
g=r.groupby(['experiment','holding','route','active_min','offline_h']).agg(
 n=('seed','count'),finance_p10=('finance_day',lambda x:x.quantile(.1)),finance_p50=('finance_day','median'),finance_p90=('finance_day',lambda x:x.quantile(.9)),
 intl_rate=('international_open','mean'),intl_day_p10=('international_day',lambda x:x.dropna().quantile(.1) if x.notna().any() else np.nan),intl_day_p50=('international_day','median'),intl_day_p90=('international_day',lambda x:x.dropna().quantile(.9) if x.notna().any() else np.nan),
 future_rate=('future_open','mean'),future_day_p50=('future_day','median'),shops_p50=('shops90','median'),levels_p50=('levels90','median'),gold_p50=('gold90','median'),cum_p50=('cum90','median'),blocked_p90=('max_no_purchase_days',lambda x:x.quantile(.9))
).reset_index()
g.to_csv(DOC/'FULL_ECONOMY_VALIDATION_SUMMARY_v1_29.csv',index=False)
# Compact rollups for player profiles and activity levels.
for col in ['holding','route','active_min','offline_h']:
 z=r.groupby(['experiment',col]).agg(runs=('seed','count'),intl_rate=('international_open','mean'),future_rate=('future_open','mean'),finance_p50=('finance_day','median'),shops_p50=('shops90','median'),levels_p50=('levels90','median')).reset_index()
 z.to_csv(DOC/f'FULL_ECONOMY_VALIDATION_BY_{col.upper()}_v1_29.csv',index=False)
# Candidate reward arithmetic, using exact cadence-to-month conversion (365.25/12 days).
month_days=365.25/12
reward_rows=[
 ('每日核心任务包',200,30),('每日完成5/7奖励',500,30),('每周任务主线',2000,month_days/7),('七日签到',1000,month_days/7),('双周免费活动',2000,month_days/14),('月度经营里程碑',4000,1)]
rr=[]
for name,exp,events in reward_rows:
 rr.append({'source':name,'exp_each':exp,'events_per_average_month':events,'monthly_exp_at_100pct':exp*events})
rr=pd.DataFrame(rr);rr.to_csv(DOC/'TASK_REWARD_EXP_RECONCILIATION_v1_29.csv',index=False)
med=[('每周任务',6,3,0,month_days/7),('双周活动',4,2,1,month_days/14),('月度里程碑',8,4,2,1)]
mr=[]
for name,b,i,a,n in med:mr.append({'source':name,'basic_per_event':b,'intermediate_per_event':i,'advanced_per_event':a,'events_per_average_month':n,'basic_monthly':b*n,'intermediate_monthly':i*n,'advanced_monthly':a*n})
pd.DataFrame(mr).to_csv(DOC/'TASK_REWARD_MEDAL_RECONCILIATION_v1_29.csv',index=False)
# Assignment-scope invariant test across every inventory and level route.
checks=[]
for h,slots in sim.HOLDINGS.items():
 lv=sim.manager_levels(slots,'balanced3',90)
 L=np.ones(30,dtype=int);unlocked={'street','food','mall','finance','international','future'}
 regix={r:[i for i,x in enumerate(sim.shops.region_id.tolist()) if x==r] for r in ['street','food','mall','finance','international','future']}
 ass=sim.build_assignment(slots,lv,L,unlocked,regix,sim.shops.base_income_per_sec_candidate.to_numpy(float),Q,8)
 regs=[x[1] for x in ass.values()]
 checks.append({'holding':h,'owned':len(slots),'assigned':len(ass),'unique_managers':len(ass)==len(set(ass.keys())),'unique_shops':len({v[0] for v in ass.values()})==len(ass),'max_region_occupancy':max([regs.count(r) for r in set(regs)] or [0]),'constraints_pass':len({v[0] for v in ass.values()})==len(ass) and max([regs.count(r) for r in set(regs)] or [0])<=2})
pd.DataFrame(checks).to_csv(DOC/'MANAGER_ASSIGNMENT_SCOPE_TEST_v1_29.csv',index=False)
print('validation_runs',len(r),'elapsed_s',round(time.time()-t,1))
print('\nBY ACTIVITY\n',pd.read_csv(DOC/'FULL_ECONOMY_VALIDATION_BY_ACTIVE_MIN_v1_29.csv').to_string(index=False))
print('\nBY HOLDING\n',pd.read_csv(DOC/'FULL_ECONOMY_VALIDATION_BY_HOLDING_v1_29.csv').to_string(index=False))
print('\nBY ROUTE\n',pd.read_csv(DOC/'FULL_ECONOMY_VALIDATION_BY_ROUTE_v1_29.csv').to_string(index=False))
print('\nREWARD EXP\n',rr.to_string(index=False))
print('\nASSIGNMENT\n',pd.DataFrame(checks).to_string(index=False))
