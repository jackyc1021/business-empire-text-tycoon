#!/usr/bin/env python3
"""180-day horizon check for shortlisted candidate only."""
import importlib.util,time
from pathlib import Path
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'project_docs'
spec=importlib.util.spec_from_file_location('sim',Path(__file__).with_name('full_economy_iterative_sim_v1_29.py'));sim=importlib.util.module_from_spec(spec);spec.loader.exec_module(sim)
g=sim.GATES[0];rows=[];t=time.time()
for h in ['none','average','zero_mythic','mythic_luck']:
 for a in [12.5,30,75]:
  for off in [0,8]:
   for strategy in ['roi','unlock_rush']:
    for seed0 in range(3):
     seed=20300101+seed0*7919+int(a*10)+int(off*100)
     rows.append({**sim.run(seed,a,off,strategy,h,'balanced3',1.10,.85,g,days=180),'experiment':'long180'})
r=pd.DataFrame(rows);r.to_csv(DOC/'FULL_ECONOMY_LONG_HORIZON_RUNS_v1_29.csv',index=False)
grp=r.groupby(['holding','active_min','offline_h','strategy']).agg(n=('seed','count'),finance_p50=('finance_day','median'),intl_rate=('international_open','mean'),intl_p50=('international_day','median'),future_rate=('future_open','mean'),future_p50=('future_day','median'),shops_p50=('shops90','median'),levels_p50=('levels90','median'),gold_p50=('gold90','median'),cum_p50=('cum90','median')).reset_index()
grp.to_csv(DOC/'FULL_ECONOMY_LONG_HORIZON_SUMMARY_v1_29.csv',index=False)
print('runs',len(r),'elapsed',round(time.time()-t,1));print(grp.groupby('active_min')[['intl_rate','future_rate','finance_p50','shops_p50','levels_p50']].mean().to_string());print('\nBy activity/offline/strategy\n',grp.groupby(['active_min','offline_h','strategy'])[['intl_rate','future_rate','intl_p50','future_p50']].mean().to_string())
