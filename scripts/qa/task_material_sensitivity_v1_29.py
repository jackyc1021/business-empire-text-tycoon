#!/usr/bin/env python3
"""Reconcile free task/activity materials and manager growth scenarios."""
from pathlib import Path
import pandas as pd, math
ROOT=Path(__file__).resolve().parents[1]; DOC=ROOT/'project_docs'
month_days=365.25/12; weeks=month_days/7; fortnights=month_days/14
# Baseline assumes daily core pack, weekly mainline, sign-in, free event and monthly milestone all completed.
base=6000+2000*weeks+1000*weeks+2000*fortnights+4000
rows=[]
for daily_core in [0.5,0.75,1.0]:
 for daily_bonus in [0,.5,.7,1.0]:
  for weekly in [.5,.75,1.0]:
   for signin in [.5,.75,1.0]:
    for event in [.5,.75,1.0]:
     for milestone in [.5,.75,1.0]:
      exp=6000*daily_core+15000*daily_bonus+2000*weeks*weekly+1000*weeks*signin+2000*fortnights*event+4000*milestone
      rows.append({'daily_core_completion':daily_core,'daily_5of7_bonus_completion':daily_bonus,'weekly_completion':weekly,'signin_completion':signin,'free_event_completion':event,'monthly_milestone_completion':milestone,'monthly_exp':exp})
df=pd.DataFrame(rows);df.to_csv(DOC/'TASK_MATERIAL_COMPLETION_SENSITIVITY_v1_29.csv',index=False)
# Representative cases and leveling routes, using current candidate level-up EXP formula and medal cadence.
medal_month={'basic':6*weeks+8+4*fortnights,'intermediate':3*weeks+4+2*fortnights,'advanced':2+fortnights}
quality_mult={'普通':1,'稀有':1.2,'史诗':1.5,'传说':2,'神话':3}
base_cases=[('保守低完成',.5,0,.5,.5,.5,.5),('普通稳定',.75,.5,.75,.75,.75,.75),('高完成',1,1,1,1,1,1)]
level_rows=[]
for name,dc,db,w,si,ev,mi in base_cases:
 exp=6000*dc+15000*db+2000*weeks*w+1000*weeks*si+2000*fortnights*ev+4000*mi
 for n in [1,3,6]:
  each=exp/n
  for rarity,mult in quality_mult.items():
   medals={k:v for k,v in medal_month.items()}
   level=1;left=each
   while level<100:
    need=100+10*(level-1)
    if left<need:break
    if level%10==0:
     node=level//10;tier='basic' if node<=3 else 'intermediate' if node<=6 else 'advanced'
     qty=math.ceil([2,3,4][(node-1)%3]*mult)
     if medals[tier]<qty:break
     medals[tier]-=qty
    left-=need;level+=1
   level_rows.append({'completion_profile':name,'route_managers':n,'rarity':rarity,'monthly_exp_total':exp,'exp_per_manager':each,'achievable_level_per_manager':level,'basic_medals_month':medal_month['basic'],'intermediate_medals_month':medal_month['intermediate'],'advanced_medals_month':medal_month['advanced']})
pd.DataFrame(level_rows).to_csv(DOC/'MANAGER_GROWTH_TASK_COMPLETION_SENSITIVITY_v1_29.csv',index=False)
# Candidate shard requirements from the currently proposed fragment progression.
base_frag={'普通':50,'稀有':30,'史诗':20,'传说':15,'神话':10}
sh=[]
for rarity,b in base_frag.items():
 for target in [2,3,4,5]:
  total=b*sum(range(1,target))
  sh.append({'rarity':rarity,'target_star':target,'total_shards_needed':total,'duplicate_recruits_at_10_shards_each':math.ceil(total/10)})
pd.DataFrame(sh).to_csv(DOC/'MANAGER_STAR_FRAGMENT_REQUIREMENT_AUDIT_v1_29.csv',index=False)
print('baseline_exp',base,'with_daily_completion_bonus',base+15000)
print('medal_month',medal_month)
print('\nrepresentative growth\n',pd.DataFrame(level_rows).query("completion_profile in ['保守低完成','普通稳定','高完成'] and rarity=='普通'").to_string(index=False))
print('\nstar shards\n',pd.DataFrame(sh).to_string(index=False))
