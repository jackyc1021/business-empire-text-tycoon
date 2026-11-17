#!/usr/bin/env python3
"""Event-budget diagnostic simulator for current 9-shop / 4-region economy.
Activity bands are user-approved design targets, not economic tuning values.
Existing shop and region values are read from source and frozen here for reproducibility.
Unmodeled systems are explicitly excluded in the accompanying report.
"""
import random, math, statistics, csv, json
from pathlib import Path

SHOPS=[
 ('stall','street',10,1),('cafe','food',80,5),('fashion','mall',650,24),
 ('tech','mall',5200,115),('hotel','food',42000,560),('mall','mall',360000,2800),
 ('factory','finance',3200000,15000),('tower','finance',28000000,85000),('space','finance',260000000,520000)]
REGIONS=[('food',500),('mall',5000),('finance',50000)]
BANDS={'light':(10,15),'normal':(20,40),'heavy':(60,90)}
LUCK={'low':('none',1,1),'average':('epic',20,2),'high':('legendary',35,3)}
CAP={'none':.60,'epic':.70,'legendary':.75,'mythic':.85}

def offline_rate(role, level, star):
    # Conservative baseline: no regional dispatch is assumed, so no role bonus applies.
    # Role rarity/level/star are scenario labels only until dispatch is modeled per region.
    return .60

def run(seed, band, luck, days=30):
    rng=random.Random(seed); lo,hi=BANDS[band]; role,rl,rs=LUCK[luck]
    if luck=='high' and rng.random()<.35: role='mythic'
    levels={s[0]:(1 if s[0]=='stall' else 0) for s in SHOPS}
    unlocked={'street'}; gold=120; stuck=0; max_stuck=0; daily=[]
    total_actions=0; total_active=0; days_no_purchase=0
    def income(): return sum(base*levels[sid] for sid,reg,cost,base in SHOPS)
    def total_lv(): return sum(levels.values())
    def can_open(sid):
        prereq={'stall':True,'cafe':'food' in unlocked and levels['stall']>=1,
          'hotel':'food' in unlocked and levels['cafe']>=1,'fashion':'mall' in unlocked and levels['hotel']>=1,
          'tech':'mall' in unlocked and levels['fashion']>=1,'mall':'mall' in unlocked and levels['tech']>=1,
          'factory':'finance' in unlocked and levels['mall']>=1,'tower':'finance' in unlocked and levels['factory']>=1,
          'space':'finance' in unlocked and levels['tower']>=1}
        return prereq[sid]
    for day in range(1,days+1):
        minutes=rng.uniform(lo,hi); total_active+=minutes
        # Existing 8h offline cap at 60%-85%, plus foreground active accrual.
        gold += income()*(8*3600*offline_rate(role,rl,rs)+minutes*60)
        # Actions consume actual playtime. Browsing/management overhead rises with session length.
        # A shop purchase/upgrade takes 0.8-1.8 minutes of modeled attention.
        budget=minutes*rng.uniform(.62,.82); buys=0; spent=0.0
        # Players prioritize affordable upgrades with a modest preference for opening next shop.
        while spent<budget:
            opts=[]
            for sid,reg,basecost,baseinc in SHOPS:
                if not can_open(sid): continue
                cost=basecost if levels[sid]==0 else math.ceil(basecost*(levels[sid]+1))
                if cost<=gold:
                    # Prioritize opening new shops slightly; otherwise use marginal income/cost.
                    score=(baseinc/cost)*(1.18 if levels[sid]==0 else 1.0)
                    opts.append((score,cost,sid))
            if not opts: break
            _,cost,sid=max(opts)
            action_cost=rng.uniform(.8,1.8)
            if spent+action_cost>budget: break
            gold-=cost; levels[sid]+=1; buys+=1; spent+=action_cost
            # Unlock checks happen after each action, as in a player progression loop.
            for reg,cost2,cond in [('food',500,levels['stall']>=2),('mall',5000,levels['hotel']>=1 and total_lv()>=4),('finance',50000,levels['mall']>=1 and total_lv()>=7)]:
                if reg not in unlocked and cond and gold>=cost2:
                    gold-=cost2; unlocked.add(reg)
        total_actions+=buys
        if buys==0: days_no_purchase+=1
        stuck=stuck+1 if buys==0 else 0; max_stuck=max(max_stuck,stuck)
        daily.append({'day':day,'minutes':minutes,'buys':buys,'gold':gold,'income':income(),'levels':total_lv(),'regions':len(unlocked)})
    def first_region(reg):
        for x in daily:
            if x['regions']>= {'street':1,'food':2,'mall':3,'finance':4}[reg]: return x['day']
        return 0
    return {'avg_minutes':total_active/days,'total_active_hours':total_active/60,'actions':total_actions,
      'actions_per_day':total_actions/days,'days_no_purchase':days_no_purchase,'max_stuck':max_stuck,
      'food_day':first_region('food'),'mall_day':first_region('mall'),'finance_day':first_region('finance'),
      'levels':total_lv(),'income':income(),'gold':gold,'regions':len(unlocked)}

def main():
    out=Path(__file__).resolve().parents[1]/'project_docs'
    rows=[]; raw=[]
    for band in BANDS:
      for luck in LUCK:
        results=[run(202611010000+i+list(BANDS).index(band)*1000000+list(LUCK).index(luck)*10000000,band,luck) for i in range(500)]
        for i,r in enumerate(results): raw.append({'activity':band,'luck':luck,'run':i,**r})
        for metric in results[0]:
          vals=sorted(r[metric] for r in results)
          rows.append({'activity':band,'luck':luck,'metric':metric,'mean':statistics.mean(vals),
            'p10':vals[49],'median':statistics.median(vals),'p90':vals[449],
            'zero_pct':sum(v==0 for v in vals)/len(vals)*100})
    with (out/'ACTIVITY_TIME_ECONOMY_MC_SUMMARY.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    with (out/'ACTIVITY_TIME_ECONOMY_MC_SAMPLE.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=raw[0].keys());w.writeheader();w.writerows(raw)
    print('runs',len(raw))
    for band in BANDS:
      for luck in LUCK:
        rs=[x for x in raw if x['activity']==band and x['luck']==luck]
        print(band,luck,'mins',round(statistics.mean(x['avg_minutes'] for x in rs),2),
          'actions/day',round(statistics.mean(x['actions_per_day'] for x in rs),2),
          'levels',round(statistics.median(x['levels'] for x in rs),1),
          'finance_day',round(statistics.median(x['finance_day'] for x in rs),1),
          'stuck',round(statistics.median(x['max_stuck'] for x in rs),1),
          'no-buy-days',round(statistics.mean(x['days_no_purchase'] for x in rs),2))
if __name__=='__main__': main()
