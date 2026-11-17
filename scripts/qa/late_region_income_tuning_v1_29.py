#!/usr/bin/env python3
"""Search late-region shop income multipliers to prevent ROI stagnation."""
import importlib.util,time
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'project_docs'
spec=importlib.util.spec_from_file_location('sim',Path(__file__).with_name('full_economy_iterative_sim_v1_29.py'));sim=importlib.util.module_from_spec(spec);spec.loader.exec_module(sim)
g=sim.GATES[0];rows=[];t=time.time()
for mult in [1.0,1.5,2.0,2.5,3.0]:
 for h in ['none','average','zero_mythic']:
  for a in [12.5,30,75]:
   for off in [0,8]:
    for seed0 in range(2):
     seed=20400101+seed0*7919+int(a*10)+int(off*100)
     rows.append(sim.run(seed,a,off,'roi',h,'balanced3',1.10,.85,g,days=180,late_income_mult=mult))
r=pd.DataFrame(rows);r.to_csv(DOC/'LATE_REGION_INCOME_TUNING_RUNS_v1_29.csv',index=False)
grp=r.groupby(['late_income_mult','active_min','offline_h']).agg(n=('seed','count'),intl_rate=('international_open','mean'),intl_day_p50=('international_day','median'),future_rate=('future_open','mean'),future_day_p50=('future_day','median'),shops_p50=('shops90','median'),gold_p50=('gold90','median'),cum_p50=('cum90','median')).reset_index()
grp.to_csv(DOC/'LATE_REGION_INCOME_TUNING_SUMMARY_v1_29.csv',index=False)
print('runs',len(r),'elapsed',round(time.time()-t,1));print(grp.to_string(index=False));print('\nAggregate by multiplier\n',grp.groupby('late_income_mult')[['future_rate','intl_rate','shops_p50']].mean().to_string())
