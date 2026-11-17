#!/usr/bin/env python3
"""Candidate-only diminishing marginal income and upgrade-cost surface.
Uses source-derived nine-shop base values and manager power formulas. No runtime edits.
"""
import csv, math, itertools, statistics, random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'project_docs'
SHOPS=[('stall','街角小摊',10,1),('cafe','精品咖啡馆',80,5),('fashion','潮流服饰店',650,24),('tech','数码科技馆',5200,115),('hotel','精品酒店',42000,560),('mall','城市购物中心',360000,2800),('factory','智能制造园',3200000,15000),('tower','环球金融中心',28000000,85000),('space','商业航天集团',260000000,520000)]
P=[1.0,1.10,1.15,1.20,1.30]
Q=[0.70,0.80,0.85,0.90,0.95,1.00]
# Source-derived manager power envelopes from QUALITY_BASE_INDEX, STAR_MULTIPLIERS and level formula.
STAR={'common':[1,1.08,1.16,1.24,1.32],'rare':[1,1.09,1.19,1.30,1.42],'epic':[1,1.12,1.25,1.39,1.55],'legendary':[1,1.13,1.32,1.57,1.85],'mythic':[1,1.15,1.31,1.55,1.82]}
BASE={'common':100,'rare':130,'epic':175,'legendary':240,'mythic':340}
def power(rarity,level,star): return BASE[rarity]*STAR[rarity][star-1]*(1+.02*(level-1))/100
MANAGERS=[('unassigned',1.0,0.0),('rare_L50_3star',power('rare',50,3),0.0),('epic_L75_4star',power('epic',75,4),0.0),('mythic_L100_5star',power('mythic',100,5),0.0)]
def write(path,rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Full level surface: all shops x levels x p x q x manager cases.
surface=[]
for sid,name,bc,bi in SHOPS:
 for lv in range(1,101):
  for p,q,(mn,mp,skill) in itertools.product(P,Q,MANAGERS):
   cost=math.ceil(bc*((lv+1)**p))
   before=bi*(lv**q); after=bi*((lv+1)**q)
   marginal=(after-before)*mp*(1+skill)
   total=after*mp*(1+skill)
   surface.append({'shop_id':sid,'shop_name':name,'level_before':lv,'level_after':lv+1,'cost_p':p,'income_q':q,'manager_case':mn,'manager_power_source_formula':round(mp,6),'upgrade_cost':cost,'income_before_per_sec':round(before*mp*(1+skill),6),'income_after_per_sec':round(total,6),'marginal_income_per_sec':round(marginal,6),'marginal_gain_pct_of_previous_income':round((after-before)/before*100,6),'static_payback_hours':round(cost/marginal/3600,6) if marginal>0 else None})
write(OUT/'DIMINISHING_RETURN_LEVEL_SURFACE.csv',surface)
# summarize cost/income pair unassigned; marginal gain and payback percentiles
summary=[]
for p,q in itertools.product(P,Q):
 a=[r for r in surface if r['cost_p']==p and r['income_q']==q and r['manager_case']=='unassigned']
 pb=sorted(r['static_payback_hours'] for r in a)
 # Representative single-shop curve, normalized to first upgrade; diminishing ratio at L10/50/100
 ratios={}
 for lv in (1,10,50,100):
  x=next(r for r in a if r['shop_id']=='stall' and r['level_before']==lv)
  ratios[f'marginal_L{lv}_vs_L1_pct']=round(x['marginal_income_per_sec']/next(z for z in a if z['shop_id']=='stall' and z['level_before']==1)['marginal_income_per_sec']*100,4)
 summary.append({'cost_p':p,'income_q':q,'median_payback_hours':statistics.median(pb),'p90_payback_hours':pb[int(.9*len(pb))],'max_payback_hours':max(pb),**ratios})
write(OUT/'DIMINISHING_RETURN_CASE_SUMMARY.csv',summary)
# Monte Carlo cashflow stress: all nine shops; fixed seed; bounded active purchase actions.
# This is a relative candidate stress test, not a calibrated player progression prediction.
rng=random.Random(20261101); runs=[]
for p,q in itertools.product(P,Q):
 for activity in (12.5,30,75):
  for offline in (0,4,8):
   for manager_case,mp,skill in MANAGERS:
    for run in range(5):
     levels={s[0]:rng.randint(1,5) for s in SHOPS}; gold=0.0; stuck=0; maxstuck=0; total_buys=0
     for day in range(30):
      rate=sum(bi*(levels[sid]**q)*mp*(1+skill) for sid,n,bc,bi in SHOPS)
      gold += rate*(offline*3600*.60+activity*60)
      buys=0
      for _ in range(max(1,int(activity/2))):
       opts=[]
       for sid,n,bc,bi in SHOPS:
        lv=levels[sid]; cost=math.ceil(bc*((lv+1)**p)); gain=bi*(((lv+1)**q)-(lv**q))*mp*(1+skill)
        if cost<=gold: opts.append((gain/cost,sid,cost))
       if not opts: break
       _,sid,cost=max(opts); gold-=cost; levels[sid]+=1; buys+=1; total_buys+=1
      stuck=stuck+1 if buys==0 else 0; maxstuck=max(maxstuck,stuck)
     final_rate=sum(bi*(levels[sid]**q)*mp*(1+skill) for sid,n,bc,bi in SHOPS)
     runs.append({'cost_p':p,'income_q':q,'active_minutes':activity,'offline_hours':offline,'manager_case':manager_case,'run':run,'total_levels_end':sum(levels.values()),'final_income_per_sec':round(final_rate,4),'gold_end':round(gold,2),'total_upgrades':total_buys,'max_consecutive_no_upgrade_days':maxstuck})
write(OUT/'DIMINISHING_RETURN_MC_RUNS.csv',runs)
# compact grouped summary
from collections import defaultdict
g=defaultdict(list)
for r in runs:g[(r['cost_p'],r['income_q'],r['active_minutes'],r['offline_hours'],r['manager_case'])].append(r)
sm=[]
for k,a in g.items():
 vals=sorted(x['max_consecutive_no_upgrade_days'] for x in a); lev=sorted(x['total_levels_end'] for x in a)
 sm.append({'cost_p':k[0],'income_q':k[1],'active_minutes':k[2],'offline_hours':k[3],'manager_case':k[4],'median_total_levels':statistics.median(lev),'p10_total_levels':lev[int(.1*len(lev))],'p90_total_levels':lev[int(.9*len(lev))],'median_max_no_upgrade_days':statistics.median(vals),'p90_max_no_upgrade_days':vals[int(.9*len(vals))]})
write(OUT/'DIMINISHING_RETURN_MC_SUMMARY.csv',sm)
print(f'PASS surface={len(surface)} MC_runs={len(runs)} summary={len(sm)}')
