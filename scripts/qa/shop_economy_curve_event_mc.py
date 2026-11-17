#!/usr/bin/env python3
"""Event-level baseline/candidate shop economy simulation.

Candidate exponents are diagnostic scenarios only; none is approved for runtime.
Uses only the nine actual SHOP_DEFS and three existing region costs/conditions.
No managers, tasks, ads, events, click upgrades, or unapproved shop data.
"""
from __future__ import annotations
import csv, math, random, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'project_docs'
SHOPS = [
    ('stall','street',10,1),('cafe','food',80,5),('fashion','mall',650,24),
    ('tech','mall',5200,115),('hotel','food',42000,560),('mall','mall',360000,2800),
    ('factory','finance',3200000,15000),('tower','finance',28000000,85000),('space','finance',260000000,520000),
]
REGIONS = [('food',500),('mall',5000),('finance',50000)]
ACTIVITY = {'light':12.5,'regular':30.0,'high':75.0}
OFFLINE_HOURS = (0,4,8)
CURVES = {'linear_current':1.00,'mild_candidate':1.15,'moderate_candidate':1.30,'strong_candidate':1.50,'very_strong_candidate':1.75,'quadratic_candidate':2.00}
DAYS=30
RUNS=50
SEED=20261101

def region_cond(region, levels):
    total=sum(levels.values())
    if region=='food': return levels['stall']>=2
    if region=='mall': return levels['hotel']>=1 and total>=4
    if region=='finance': return levels['mall']>=1 and total>=7
    return False

def shop_available(sid, unlocked, levels):
    req={'stall':None,'cafe':('food','stall'),'hotel':('food','cafe'),
         'fashion':('mall','hotel'),'tech':('mall','fashion'),'mall':('mall','tech'),
         'factory':('finance','mall'),'tower':('finance','factory'),'space':('finance','tower')}
    if levels[sid]>0: return True
    r= req[sid]
    return r is None or (r[0] in unlocked and levels[r[1]]>=1)

def run(seed, activity_min, exponent, offline_hours, days=DAYS):
    rng=random.Random(seed)
    levels={s[0]:(1 if s[0]=='stall' else 0) for s in SHOPS}
    unlocked={'street'}; gold=120.0
    region_day={}; max_stuck=0; stuck=0; action_count=0
    daily=[]
    def income(): return sum(base*levels[sid] for sid,reg,cost,base in SHOPS)
    def accrue(seconds, offline=False):
        nonlocal gold
        # Current user-confirmed no-qualified-dispatch baseline: 60% per region.
        # All currently open regions have no assigned offline specialist in this scenario.
        total=0.0
        for sid,reg,cost,base in SHOPS:
            lv=levels[sid]
            if lv:
                total += base*lv*(0.60 if offline else 1.0)
        gold += total*seconds
    def unlock_if_possible(day):
        nonlocal gold
        for reg,cost in REGIONS:
            if reg not in unlocked and region_cond(reg,levels) and gold>=cost:
                gold-=cost; unlocked.add(reg); region_day[reg]=day
                return True
        return False
    for day in range(1,days+1):
        start_gold=gold; start_income=income(); day_actions=0
        # One capped 8-hour offline interval per day, followed by the active session.
        accrue(offline_hours*3600,offline=True)
        # Active time is modeled minute by minute; no extra passive income is credited
        # outside the 8h offline cap or the stated active session.
        for minute in range(max(1,round(activity_min))):
            accrue(60,offline=False)
            if unlock_if_possible(day):
                day_actions+=1; action_count+=1; continue
            opts=[]
            for sid,reg,base_cost,base_income in SHOPS:
                if not shop_available(sid,unlocked,levels): continue
                lv=levels[sid]
                raw=base_cost if lv==0 else base_cost*((lv+1)**exponent)
                cost=math.ceil(raw)
                if cost<=gold:
                    # A noisy greedy policy: prioritizes marginal base income per coin,
                    # with modest preference noise to represent different player choices.
                    score=(base_income/cost)*math.exp(rng.gauss(0,0.18))
                    opts.append((score,cost,sid))
            if opts:
                _,cost,sid=max(opts)
                gold-=cost; levels[sid]+=1; day_actions+=1; action_count+=1
        if day_actions==0: stuck+=1
        else: stuck=0
        max_stuck=max(max_stuck,stuck)
        # Record daily state; day-end unlock check catches affordability after final action.
        unlock_if_possible(day)
        daily.append({'day':day,'gold_end':gold,'income_per_sec':income(),'total_levels':sum(levels.values()),
                      'actions':day_actions,'regions':len(unlocked),'stuck_run':stuck})
    return {'seed':seed,'curve':None,'activity':None,'finance_day':region_day.get('finance',0),
            'food_day':region_day.get('food',0),'mall_day':region_day.get('mall',0),
            'total_levels':sum(levels.values()),'income_per_sec':income(),'gold_end':gold,
            'max_consecutive_stuck_days':max_stuck,'actions_total':action_count,'offline_hours':offline_hours,
            'levels':levels,'daily':daily}

def pct(vals,p):
    a=sorted(vals); return a[min(len(a)-1,max(0,math.ceil(p*len(a))-1))]

def main():
    all_rows=[]; daily_rows=[]; summary_rows=[]
    for curve,exp in CURVES.items():
        for activity,minutes in ACTIVITY.items():
          for offline_hours in OFFLINE_HOURS:
            runs=[]
            for i in range(RUNS):
                seed=SEED + i + list(CURVES).index(curve)*100000 + list(ACTIVITY).index(activity)*10000000 + offline_hours*100000000
                x=run(seed,minutes,exp,offline_hours); x['curve']=curve; x['activity']=activity; runs.append(x)
                for d in x['daily']:
                    daily_rows.append({'curve':curve,'exponent':exp,'activity':activity,'offline_hours':offline_hours,'run':i,'seed':seed,**d})
            for metric in ['food_day','mall_day','finance_day','total_levels','income_per_sec','gold_end','max_consecutive_stuck_days','actions_total']:
                vals=[x[metric] for x in runs]
                summary_rows.append({'curve':curve,'exponent':exp,'activity':activity,'offline_hours':offline_hours,'metric':metric,
                    'mean':statistics.mean(vals),'p10':pct(vals,.10),'median':statistics.median(vals),'p90':pct(vals,.90),
                    'never_pct':sum(v==0 for v in vals)/len(vals)*100 if metric.endswith('_day') else ''})
            for x in runs:
                all_rows.append({'curve':curve,'exponent':exp,'activity':activity,'offline_hours':offline_hours,'seed':x['seed'],
                    **{k:x[k] for k in ['food_day','mall_day','finance_day','total_levels','income_per_sec','gold_end','max_consecutive_stuck_days','actions_total']}})
    def write(name,rows):
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    write('SHOP_ECONOMY_EVENT_MC_SUMMARY.csv',summary_rows)
    write('SHOP_ECONOMY_EVENT_MC_RUNS.csv',all_rows)
    write('SHOP_ECONOMY_EVENT_MC_DAILY.csv',daily_rows)
    print(f'PASS: {len(all_rows)} runs, {len(daily_rows)} daily records, {len(summary_rows)} summary rows')
    for curve in CURVES:
        for activity in ACTIVITY:
          for offline_hours in OFFLINE_HOURS:
            x=next(r for r in summary_rows if r['curve']==curve and r['activity']==activity and r['offline_hours']==offline_hours and r['metric']=='finance_day')
            y=next(r for r in summary_rows if r['curve']==curve and r['activity']==activity and r['offline_hours']==offline_hours and r['metric']=='total_levels')
            z=next(r for r in summary_rows if r['curve']==curve and r['activity']==activity and r['offline_hours']==offline_hours and r['metric']=='max_consecutive_stuck_days')
            print(curve,activity,'offline',offline_hours,'finance P50',x['median'],'levels P50',y['median'],'stuck P90',z['p90'])
if __name__=='__main__': main()
