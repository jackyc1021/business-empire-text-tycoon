#!/usr/bin/env python3
"""Unified six-manager team + 30-shop economy Monte Carlo (candidate research only)."""
from __future__ import annotations
import math, random, statistics, json
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; DOC=ROOT/'project_docs'
shops=pd.read_csv(DOC/'SHOP_ECONOMY_30_CANDIDATE.csv')
ability=pd.read_csv(DOC/'MANAGER_ABILITY_PARAMETER_REGISTER.csv')
rarity_en={'普通':'common','稀有':'rare','史诗':'epic','传说':'legendary','神话':'mythic'}
rarity_rank={'普通':0,'稀有':1,'史诗':2,'传说':3,'神话':4}
rarity_offline_cap={'普通':0.0,'稀有':0.0,'史诗':.10,'传说':.15,'神话':.25}
weights={}; slot_rarity={}; slot_names={}
for slot,g in ability.groupby('slot'):
    weights[slot]={r:int(g.loc[g.ability==r,'weight_candidate'].iloc[0]) for r in ['经营收益','升级折扣','离线经营','客流增益']}
    slot_rarity[slot]=g.rarity.iloc[0]; slot_names[slot]=g.character_or_placeholder.iloc[0]
rarity_slots=defaultdict(list)
for slot,r in slot_rarity.items(): rarity_slots[r].append(slot)

NORMAL={'普通':48,'稀有':40,'史诗':10.8,'传说':1.2,'神话':0}
ADV={'普通':45,'稀有':40,'史诗':12,'传说':2.4,'神话':.6}
RARITIES=list(NORMAL)

def ability_ranks(slot,level=100,star=1):
    rarity=slot_rarity[slot]; budget={'普通':12,'稀有':15,'史诗':18,'传说':21,'神话':24}[rarity]+math.floor(.24*(level-1))+2*(star-1)+math.floor((level-1)/10)
    w=weights[slot]; total=sum(w.values()); raw={k:budget*v/total for k,v in w.items()}; ranks={k:max(1,math.floor(v)) for k,v in raw.items()}
    while sum(ranks.values())>budget:
        k=max((k for k in ranks if ranks[k]>1),key=lambda k:ranks[k]-raw[k]); ranks[k]-=1
    while sum(ranks.values())<budget:
        k=max(raw,key=lambda k:(raw[k]-math.floor(raw[k]),w[k])); ranks[k]+=1; raw[k]=math.floor(raw[k])
    return ranks

def sat(x,k): return x/(x+k) if x>0 else 0.0

def draw_normal(rng, misses):
    if misses>=49:
        return '传说',0
    r=draw(rng,NORMAL)
    return r,(0 if r=='传说' else misses+1)

def sample_team(seed):
    rng=random.Random(seed+88031); owned=set(); pity=0
    # Eight weeks of 3 normal tickets + 1 advanced ticket, a partial week sign-in,
    # and two 11th free normal results from two ten-pulls.
    sequence=['normal']*6+['advanced']
    sequence=sequence*8+['normal']
    sequence.insert(0,'normal')
    normal_paid=0
    for mode in sequence:
        if mode=='normal':
            normal_paid+=1; r=draw(rng,NORMAL)
        else:
            n=pity+1; w=dict(ADV)
            if n>=80: r='神话'; pity=0
            else:
                if n>70:
                    p=min(100,.6+(n-70)*10); scale=(100-p)/(99.4)
                    for k in w: w[k]=p if k=='神话' else w[k]*scale
                r=draw(rng,w); pity=0 if r=='神话' else n
        if r=='神话' and mode=='normal': continue
        pool=rarity_slots[r]; owned.add(rng.choice(pool))
        if mode=='normal' and normal_paid%10==0:
            rr=draw(rng,NORMAL); owned.add(rng.choice(rarity_slots[rr]))
    ranked=sorted(owned,key=lambda s:rarity_rank[slot_rarity[s]],reverse=True)
    # If the player has more than six, choose highest rarity; ties remain random acquisition order.
    team=ranked[:6]
    while len(team)<6:
        pool=[s for s in ability if False]
        candidates=[s for s in slot_rarity if s not in owned]
        if not candidates: break
        pick=rng.choice(candidates);owned.add(pick);team.append(pick)
    return team

def draw(rng,weights):
    x=rng.random()*100; acc=0
    for r in RARITIES:
        acc+=weights[r]
        if x<acc:return r
    return '普通'

def team_effect(team):
    totals={'经营收益':0,'升级折扣':0,'离线经营':0,'客流增益':0}; offline_cap=0
    for slot in team:
        r=slot_rarity[slot]; ranks=ability_ranks(slot,100,1)
        for k in totals: totals[k]+=ranks[k]
        offline_cap=max(offline_cap,rarity_offline_cap[r])
    return {
      'income':min(.60,.35*sat(totals['经营收益'],10)),
      'discount':min(.35,.30*sat(totals['升级折扣'],9)),
      'offline':min(offline_cap,.10*sat(totals['离线经营'],8)),
      'traffic':min(.22,.22*sat(totals['客流增益'],9)),
      'rarity_mix':','.join(sorted((slot_rarity[s] for s in team),key=lambda r:rarity_rank[r]))
    }

GATES=[
 {'i_cost':1e9,'i_cum':1e9,'i_fin_levels':2,'i_fin_open':2,'f_cost':1e12,'f_cum':1e13,'f_int_levels':4,'f_int_open':4,'tag':'low'},
 {'i_cost':1e10,'i_cum':1e10,'i_fin_levels':2,'i_fin_open':2,'f_cost':1e13,'f_cum':5e13,'f_int_levels':5,'f_int_open':4,'tag':'mid'},
 {'i_cost':1e11,'i_cum':1e11,'i_fin_levels':3,'i_fin_open':3,'f_cost':1e14,'f_cum':1e14,'f_int_levels':7,'f_int_open':4,'tag':'high'},
 {'i_cost':1e9,'i_cum':1e9,'i_fin_levels':2,'i_fin_open':2,'f_cost':5e12,'f_cum':2e13,'f_int_levels':5,'f_int_open':4,'tag':'recommended'},
]
CURVES=[(1.00,1.00),(1.10,.85)]

def run(seed,active_min,offline_h,strategy,p,q,gate,team):
    rng=random.Random(seed*13+int(active_min*100)+offline_h*71)
    levels=[0]*30; levels[0]=1; gold=120.; cum=0.; unlocked={'street'}; uday={}; max_idle=0; idle=0
    costs=shops.base_cost_candidate.tolist(); incomes=shops.base_income_per_sec_candidate.tolist(); regs=shops.region_id.tolist()
    reg_ids={r:[i for i,x in enumerate(regs) if x==r] for r in ['street','food','mall','finance','international','future']}
    eff=team_effect(team)
    for day in range(1,91):
        act=max(0,active_min*rng.uniform(.88,1.12)); off=min(8,offline_h*rng.uniform(.85,1.15))
        online=0.;
        for i in range(30):
            if regs[i] not in unlocked or levels[i]<=0: continue
            lv=levels[i]
            traffic=eff['traffic']*(lv/(lv+3.0))
            online+=incomes[i]*(lv**q)*(1+eff['income'])*(1+traffic)
        earn=online*act*60+online*(.60+eff['offline'])*off*3600
        gold+=earn;cum+=earn
        actions=max(1,min(8,int(act/12.5)))
        did=False
        for _ in range(actions):
            opts=[]
            if 'food' not in unlocked and levels[0]>=2 and gold>=500: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','food',500))
            if 'mall' not in unlocked and 'food' in unlocked and levels[6]>=1 and sum(levels)>=4 and gold>=5000: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','mall',5000))
            if 'finance' not in unlocked and 'mall' in unlocked and levels[12]>=1 and sum(levels)>=7 and gold>=50000: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','finance',50000))
            if 'international' not in unlocked and sum(levels[i]>0 for i in reg_ids['finance'])>=gate['i_fin_open'] and sum(levels[i] for i in reg_ids['finance'])>=gate['i_fin_levels'] and cum>=gate['i_cum'] and gold>=gate['i_cost']:
                opts.append((3.5 if strategy=='unlock_rush' else .12,'unlock','international',gate['i_cost']))
            if 'future' not in unlocked and 'international' in unlocked and sum(levels[i]>0 for i in reg_ids['international'])>=gate['f_int_open'] and sum(levels[i] for i in reg_ids['international'])>=gate['f_int_levels'] and cum>=gate['f_cum'] and gold>=gate['f_cost']:
                opts.append((3.5 if strategy=='unlock_rush' else .12,'unlock','future',gate['f_cost']))
            for i in range(30):
                if regs[i] not in unlocked: continue
                lv=levels[i]; cost=costs[i] if lv==0 else math.ceil(costs[i]*(lv+1)**p)
                paid=max(costs[i]*.65,cost*(1-eff['discount'])) if lv>0 else cost
                if gold<paid: continue
                old=incomes[i]*(lv**q) if lv>0 else 0
                new=incomes[i]*((lv+1)**q)
                traffic=eff['traffic']*((lv+1)/(lv+4))
                delta=(new-old)*(1+eff['income'])*(1+traffic)
                roi=delta/max(1,paid)
                score=roi
                if strategy=='balanced': score*=1+(0.20 if lv==0 else .04/(lv+1))
                if strategy=='unlock_rush' and regs[i] in ('international','future'): score*=1.25
                opts.append((score,'shop',i,paid))
            if not opts: break
            best=max(opts,key=lambda x:x[0]); gold-=best[3]
            if best[1]=='unlock': unlocked.add(best[2]); uday[best[2]]=day
            else: levels[best[2]]+=1
            did=True
        idle=0 if did else idle+1;max_idle=max(max_idle,idle)
    return {'seed':seed,'active_min':active_min,'offline_h':offline_h,'strategy':strategy,'p':p,'q':q,'gate':gate['tag'],
      'finance_day':uday.get('finance',math.nan),'international_day':uday.get('international',math.nan),'future_day':uday.get('future',math.nan),
      'shops90':sum(x>0 for x in levels),'levels90':sum(levels),'gold90':gold,'cum90':cum,'max_no_purchase_days':max_idle,
      'team_income':eff['income'],'team_discount':eff['discount'],'team_offline':eff['offline'],'team_traffic':eff['traffic'],'team_rarity_mix':eff['rarity_mix']}


def main():
    rows=[]; nseed=50; start=1_300_000
    for gate in GATES:
      for p,q in CURVES:
       for active in [12.5,30,75]:
        for offline in [0,8]:
         for strategy in ['roi','balanced','unlock_rush']:
          for k in range(nseed):
            seed=start+k+int(active*100)+offline*10000+GATES.index(gate)*100000+CURVES.index((p,q))*1000000
            team=sample_team(seed)
            rows.append(run(seed,active,offline,strategy,p,q,gate,team))
    out=pd.DataFrame(rows); out.to_csv(DOC/'UNIFIED_TEAM_ECONOMY_MC_RUNS_v1_30.csv',index=False)
    group=['gate','p','q','active_min','offline_h','strategy']
    agg=out.groupby(group).agg(n=('seed','count'),finance_p50=('finance_day','median'),intl_rate=('international_day',lambda x:x.notna().mean()),intl_p10=('international_day',lambda x:x.quantile(.1)),intl_p50=('international_day','median'),intl_p90=('international_day',lambda x:x.quantile(.9)),future_rate=('future_day',lambda x:x.notna().mean()),future_p10=('future_day',lambda x:x.quantile(.1)),future_p50=('future_day','median'),future_p90=('future_day',lambda x:x.quantile(.9)),shops_p50=('shops90','median'),levels_p50=('levels90','median'),idle_p90=('max_no_purchase_days',lambda x:x.quantile(.9))).reset_index()
    agg.to_csv(DOC/'UNIFIED_TEAM_ECONOMY_MC_SUMMARY_v1_30.csv',index=False)
    print('runs',len(out));print(agg[(agg['p']==1.1)&(agg['q']==.85)&(agg['gate']=='mid')].to_string(index=False))

if __name__=='__main__': main()
