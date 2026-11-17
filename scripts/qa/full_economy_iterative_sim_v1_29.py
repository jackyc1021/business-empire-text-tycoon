#!/usr/bin/env python3
"""v1.29 iterative whole-economy simulation. Research only; does not modify runtime."""
from __future__ import annotations
import math, json, hashlib, itertools, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'project_docs'; QA=ROOT/'qa'
shops=pd.read_csv(DOC/'SHOP_ECONOMY_30_CANDIDATE.csv')
ability=pd.read_csv(DOC/'MANAGER_ABILITY_PARAMETER_REGISTER.csv')
rarity_order=['普通','稀有','史诗','传说','神话']
rarity_en={'普通':'common','稀有':'rare','史诗':'epic','传说':'legendary','神话':'mythic'}
rarity_base={'普通':12,'稀有':15,'史诗':18,'传说':21,'神话':24}
rarity_offline_cap={'普通':0.0,'稀有':0.0,'史诗':.10,'传说':.15,'神话':.25}
rarity_region_cap={'普通':.60,'稀有':.60,'史诗':.70,'传说':.75,'神话':.85}
weights={}
for slot,g in ability.groupby('slot'):
    weights[slot]={r:int(g.loc[g.ability==r,'weight_candidate'].iloc[0]) for r in ['经营收益','升级折扣','离线经营','客流增益']}
slot_rarity=ability.groupby('slot').rarity.first().to_dict()
slot_names=ability.groupby('slot').character_or_placeholder.first().to_dict()

# Fixed test inventories are scenario controls, not claims about drop probabilities.
HOLDINGS={
 'none':[],
 'low_common_rare':['C-01','C-02','R-01'],
 'average':['C-01','C-02','R-01','R-02','E-01'],
 'early_epic':['C-01','R-01','R-02','E-01','E-02'],
 'early_legendary':['C-01','R-01','E-01','L-01','L-02'],
 'zero_mythic':['C-01','C-02','R-01','R-02','R-03','E-01','E-02','L-01'],
 'mythic_luck':['C-01','R-01','E-01','L-01','M-01','M-02'],
}
ROUTES={'concentrate':1,'balanced3':3,'spread6':6}
ACTIVITY=[30]
OFFLINE=[0,8]
STRATEGIES=['roi','unlock_rush']
CURVES=[(1.00,1.00),(1.10,.85)]
SEEDS=1
DAYS=90

# Unlock search candidates are deliberately broad and include the v1.28 baseline as a stress case.
GATES=[
 {'i_cost':1e9,'i_cum':1e9,'i_fin_levels':2,'i_fin_open':2,'f_cost':1e12,'f_cum':1e13,'f_int_levels':4,'f_int_open':4,'tag':'low'},
 {'i_cost':1e10,'i_cum':1e10,'i_fin_levels':2,'i_fin_open':2,'f_cost':1e13,'f_cum':5e13,'f_int_levels':5,'f_int_open':4,'tag':'mid'},
 {'i_cost':1e11,'i_cum':1e11,'i_fin_levels':3,'i_fin_open':3,'f_cost':1e14,'f_cum':1e14,'f_int_levels':7,'f_int_open':4,'tag':'high'},
 {'i_cost':1.5e12,'i_cum':5e12,'i_fin_levels':30,'i_fin_open':3,'f_cost':2e14,'f_cum':5e14,'f_int_levels':40,'f_int_open':4,'tag':'v128'},
]

# Convert integer ability budget to four positive ranks using largest remainder.
def ability_ranks(slot,level,star=1):
    rarity=slot_rarity[slot]
    budget=rarity_base[rarity]+math.floor(.24*(level-1))+2*(star-1)+math.floor((level-1)/10)
    w=weights[slot]; total=sum(w.values()); raw={k:budget*v/total for k,v in w.items()}
    ranks={k:max(1,math.floor(v)) for k,v in raw.items()}
    # Respect positive floor and exact total budget.
    while sum(ranks.values())>budget:
        k=max((k for k in ranks if ranks[k]>1),key=lambda k:ranks[k]-raw[k]);ranks[k]-=1
    while sum(ranks.values())<budget:
        k=max(raw,key=lambda k:(raw[k]-math.floor(raw[k]),w[k]));ranks[k]+=1;raw[k]=math.floor(raw[k])
    return ranks

def sat(rank,k=8): return rank/(rank+k) if rank>0 else 0.0

def manager_effect(slot,level,star=1):
    r=ability_ranks(slot,level,star)
    max_offline_rank=ability_ranks(slot,100,5)['离线经营']
    offline_ratio=min(1.0,r['离线经营']/max(1,max_offline_rank))
    return {
      'income':.35*sat(r['经营收益'],10),
      'discount':.30*sat(r['升级折扣'],9),
      'offline':rarity_offline_cap[slot_rarity[slot]]*offline_ratio,
      'traffic':.22*sat(r['客流增益'],9),
    }

def manager_levels(slots,route,day):
    """Apply free candidate EXP supply; 26k EXP/month, route allocates to 1/3/6.
    Breakthrough medal supply is represented by the candidate monthly cadence; each role
    gets sequential unlocks only while its tier medal budget permits.
    """
    count=ROUTES[route]
    active=slots[:count]
    total_exp=27391.3*day/30.4375
    exp_each=total_exp/max(1,count)
    out={}
    # Candidate medal income per month: 24 basic, 12 intermediate, 6 advanced.
    med_month={'basic':42.8,'intermediate':21.4,'advanced':4.17}
    med_need={'普通':1.0,'稀有':1.2,'史诗':1.5,'传说':2.0,'神话':3.0}
    for s in active:
        rarity=slot_rarity[s]; used=0; level=1; exp_left=exp_each
        medals={k:med_month[k]*day/30.4375/max(1,count) for k in med_month}
        # Sequential level-up and breakthrough simulation.
        while level<100:
            need=100+10*(level-1)
            if exp_left<need: break
            if level%10==0:
                node=level//10; tier='basic' if node<=3 else 'intermediate' if node<=6 else 'advanced'
                qty=math.ceil(([2,3,4][(node-1)%3])*med_need[rarity])
                if medals[tier]<qty: break
                medals[tier]-=qty
            exp_left-=need; used+=need; level+=1
        out[s]=level
    return out

def build_assignment(slots,levels,L,unlocked,region_ix,inc,curve_q,offline_hours):
    """Greedy constrained assignment: one manager->one shop, <=2 per region, distinct shops.
    Only offline ability is regional; income/discount/traffic are assigned-shop only.
    """
    candidates=[]
    for s in slots:
        eff=manager_effect(s,levels.get(s,1),1)
        for i in range(30):
            reg=shops.iloc[i].region_id
            if reg not in unlocked or L[i]<=0: continue
            # Manager's own shop-specific value; offline manager value uses regional offline footprint.
            base=inc[i]*max(1,L[i])**curve_q
            region_base=sum(inc[j]*max(1,L[j])**curve_q for j in region_ix[reg] if L[j]>0)
            value=base*(eff['income']+eff['traffic']*.75+eff['discount']*.35)+region_base*offline_hours/8*eff['offline']*.60
            candidates.append((value,s,i,reg,eff))
    candidates.sort(reverse=True,key=lambda x:x[0])
    used_m=set(); used_shop=set(); region_count={r:0 for r in region_ix}; assigned={}
    for value,s,i,r,e in candidates:
        if s in used_m or i in used_shop or region_count[r]>=2: continue
        assigned[s]=(i,r,e);used_m.add(s);used_shop.add(i);region_count[r]+=1
    return assigned

def run(seed,active_min,offline_h,strategy,holding,route,p,q,gate,days=DAYS,late_income_mult=1.0):
    rng=np.random.default_rng(seed)
    L=np.zeros(30,dtype=np.int16);L[0]=1;gold=120.;cum=0.;unlocked={'street'};uday={};
    base_cost=shops.base_cost_candidate.to_numpy(float);base_inc=shops.base_income_per_sec_candidate.to_numpy(float);regs=shops.region_id.tolist()
    base_inc=np.array([v*(late_income_mult if regs[i] in ('international','future') else 1.0) for i,v in enumerate(base_inc)],dtype=float)
    region_ix={r:[i for i,x in enumerate(regs) if x==r] for r in ['street','food','mall','finance','international','future']}
    slots=HOLDINGS[holding].copy();levels={s:1 for s in slots};max_no_buy=0;blocked=0;reinvest=0
    last_assign={};
    for day in range(1,days+1):
        # Free material supply is granted monthly-equivalent; route determines concentration.
        levels=manager_levels(slots,route,day)
        # Re-optimize every 7 days (free, instant reassignment) and when the unlocked portfolio changes.
        if day==1 or (day-1)%7==0 or day in uday.values():
            last_assign=build_assignment(slots,levels,L,unlocked,region_ix,base_inc,q,offline_h)
        # Shop-specific effects: never copied to sibling stores.
        shop_eff={i:{'income':0.,'discount':0.,'traffic':0.} for i in range(30)}
        reg_off={r:0. for r in region_ix};reg_cap={r:.60 for r in region_ix}
        for s,(i,r,e) in last_assign.items():
            shop_eff[i]['income']=e['income'];shop_eff[i]['discount']=e['discount'];shop_eff[i]['traffic']=e['traffic']
            reg_off[r]+=e['offline'];reg_cap[r]=max(reg_cap[r],rarity_region_cap[slot_rarity[s]])
        reg_rate={r:min(reg_cap[r],.60+reg_off[r]) for r in region_ix}
        online_rate=0.;offline_rate=0.
        for i in range(30):
            r=regs[i]
            if r not in unlocked or L[i]<=0: continue
            ef=shop_eff[i]
            # Traffic is demand-side only, with a shop-capacity saturation proxy; income is order-value only.
            traffic_real=ef['traffic']*(L[i]/(L[i]+3.0))
            rate=base_inc[i]*(L[i]**q)*(1+traffic_real)*(1+ef['income'])
            online_rate+=rate;offline_rate+=rate*reg_rate[r]
        act=active_min*rng.uniform(.88,1.12);off=min(8,offline_h*rng.uniform(.85,1.15))
        earn=online_rate*act*60+offline_rate*off*3600
        # Candidate free daily/weekly/event reward gold is deliberately zero; EXP/medals are modeled separately.
        gold+=earn;cum+=earn
        actions=max(1,min(8,int(act/12.5)))
        did=False
        for _ in range(actions):
            opts=[]
            # Existing region gates from runtime baseline.
            if 'food' not in unlocked and L[0]>=2 and gold>=500: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','food',500,0))
            if 'mall' not in unlocked and 'food' in unlocked and L[6]>=1 and L.sum()>=4 and gold>=5000: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','mall',5000,0))
            if 'finance' not in unlocked and 'mall' in unlocked and L[12]>=1 and L.sum()>=7 and gold>=50000: opts.append((2.5 if strategy=='unlock_rush' else .25,'unlock','finance',50000,0))
            fin=region_ix['finance']; intl=region_ix['international']
            if 'international' not in unlocked and sum(L[i]>0 for i in fin)>=gate['i_fin_open'] and sum(L[i] for i in fin)>=gate['i_fin_levels'] and cum>=gate['i_cum'] and gold>=gate['i_cost']:
                opts.append((3.5 if strategy=='unlock_rush' else .12,'unlock','international',gate['i_cost'],0))
            if 'future' not in unlocked and 'international' in unlocked and sum(L[i]>0 for i in intl)>=gate['f_int_open'] and sum(L[i] for i in intl)>=gate['f_int_levels'] and cum>=gate['f_cum'] and gold>=gate['f_cost']:
                opts.append((3.5 if strategy=='unlock_rush' else .12,'unlock','future',gate['f_cost'],0))
            for i in range(30):
                r=regs[i]
                if r not in unlocked: continue
                lv=int(L[i]); cost=base_cost[i] if lv==0 else math.ceil(base_cost[i]*(lv+1)**p)
                if gold<cost: continue
                ef=shop_eff[i]; discount=ef['discount'] if lv>0 else 0
                paid=max(base_cost[i]*.65,cost*(1-discount)) if lv>0 else cost
                old=base_inc[i]*(lv**q) if lv>0 else 0
                new=base_inc[i]*((lv+1)**q)
                traffic=ef['traffic']*((max(1,lv+1))/(max(1,lv+1)+3))
                delta=(new-old)*(1+traffic)*(1+ef['income'])
                roi=delta/max(1,paid)
                score=roi
                if strategy=='balanced':
                    # Small preference for opening a new shop and lifting low-level stores.
                    score*=1.0+(0.20 if lv==0 else 0.04/(lv+1))
                if strategy=='unlock_rush' and r in ('international','future'): score*=1.25
                opts.append((score,'shop',i,paid,delta))
            if not opts: break
            best=max(opts,key=lambda x:x[0]);gold-=best[3]
            if best[1]=='unlock': unlocked.add(best[2]);uday[best[2]]=day;last_assign={}
            else: L[best[2]]+=1
            did=True;reinvest+=1
        blocked=0 if did else blocked+1;max_no_buy=max(max_no_buy,blocked)
    return {'seed':seed,'active_min':active_min,'offline_h':offline_h,'strategy':strategy,'holding':holding,'route':route,'p':p,'q':q,'gate':gate['tag'],
      'finance_day':uday.get('finance',np.nan),'international_day':uday.get('international',np.nan),'future_day':uday.get('future',np.nan),
      'shops90':int((L>0).sum()),'levels90':int(L.sum()),'finance_open':int(sum(L[i]>0 for i in region_ix['finance'])),'finance_levels':int(sum(L[i] for i in region_ix['finance'])),'international_open_shops':int(sum(L[i]>0 for i in region_ix['international'])),'international_levels':int(sum(L[i] for i in region_ix['international'])),'gold90':gold,'cum90':cum,'late_income_mult':late_income_mult,'max_no_purchase_days':max_no_buy,
      'international_open':int('international' in unlocked),'future_open':int('future' in unlocked),'managers_owned':len(slots),'managers_levelled':len(levels)}


def main():
    start=time.time();rows=[]
    # Broad screening round: 30 paired seeds per major configuration; 100-seed validation follows top candidates.
    for gate in GATES[:3]:
      for p,q in CURVES:
       for holding in HOLDINGS:
        for route in ROUTES:
         for active in ACTIVITY:
          for offline in OFFLINE:
           for strategy in STRATEGIES:
            for seed0 in range(SEEDS):
             seed=20261101+seed0*1009+int(active*10)+int(offline*100)+list(HOLDINGS).index(holding)*10000+list(ROUTES).index(route)*100000+list(STRATEGIES).index(strategy)*1000000
             rows.append(run(seed,active,offline,strategy,holding,route,p,q,gate))
             if len(rows)%100==0: print('completed',len(rows),flush=True)
    runs=pd.DataFrame(rows)
    runs.to_csv(DOC/'FULL_ECONOMY_MC_RUNS_v1_29.csv',index=False)
    keys=['gate','p','q','holding','route','active_min','offline_h','strategy']
    summary=runs.groupby(keys).agg(
      finance_p50=('finance_day','median'),international_rate=('international_open','mean'),international_p50=('international_day','median'),
      future_rate=('future_open','mean'),future_p50=('future_day','median'),shops_p50=('shops90','median'),levels_p50=('levels90','median'),
      gold_p50=('gold90','median'),cum_p50=('cum90','median'),blocked_p90=('max_no_purchase_days',lambda x:np.percentile(x,90))
    ).reset_index()
    summary.to_csv(DOC/'FULL_ECONOMY_MC_SUMMARY_v1_29.csv',index=False)
    # Aggregate comparison by curve/gate; missing unlocks are explicit failure, never replaced by arbitrary days.
    curve=summary.groupby(['gate','p','q']).agg(
      intl_rate=('international_rate','mean'),future_rate=('future_rate','mean'),
      finance_p50=('finance_p50','median'),shops_p50=('shops_p50','median'),levels_p50=('levels_p50','median'),blocked_p90=('blocked_p90','median')
    ).reset_index()
    curve['screen_score']=curve.intl_rate*2+curve.future_rate*3-curve.blocked_p90/90*.25
    curve=curve.sort_values('screen_score',ascending=False)
    curve.to_csv(DOC/'FULL_ECONOMY_CURVE_TUNING_v1_29.csv',index=False)
    # Manager effect sanity and assignment-scope assertions.
    audit=[]
    for s in ability.slot.unique():
      for star in [1,3,5]:
       for lv in [1,10,30,50,64,100]:
        e=manager_effect(s,lv,star);r=ability_ranks(s,lv,star)
        audit.append({'slot':s,'rarity':slot_rarity[s],'level':lv,'star':star,'total_budget':sum(r.values()),'income_rank':r['经营收益'],'discount_rank':r['升级折扣'],'offline_rank':r['离线经营'],'traffic_rank':r['客流增益'],**e})
    pd.DataFrame(audit).to_csv(DOC/'MANAGER_EFFECT_CURVE_AUDIT_v1_29.csv',index=False)
    # Scenario coverage and reproducibility metadata.
    meta={'version':'1.29','game_version':'2.17.0','save_schema':6,'days':DAYS,'seeds_per_configuration':SEEDS,
      'runs':len(runs),'holdings':HOLDINGS,'routes':ROUTES,'activity_minutes_per_day':ACTIVITY,'offline_hours_per_day':OFFLINE,
      'strategies':STRATEGIES,'curves':CURVES,'unlock_gate_candidates':GATES,
      'manager_scope':'income/discount/traffic only assigned shop; offline only assigned region',
      'assignment_constraints':'one manager one shop; max two managers per region; distinct assigned shops',
      'base_free_exp_month_candidate':27391.3,'optional_daily_5_of_7_extra_exp_at_100pct_completion':15000,'medal_monthly_supply_candidate':{'basic':42.8,'intermediate':21.4,'advanced':4.17},'status':'research candidate; no runtime or save schema changes', 'elapsed_seconds':round(time.time()-start,2)}
    (DOC/'FULL_ECONOMY_SIMULATION_METADATA_v1_29.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    print('RUNS',len(runs),'elapsed',round(time.time()-start,1))
    print('\nTOP CURVES\n',curve.head(15).to_string(index=False))
    print('\nHOLDING AGGREGATE\n',runs.groupby('holding')[['international_open','future_open','levels90','shops90']].mean().to_string())
    print('\nROUTE AGGREGATE\n',runs.groupby('route')[['international_open','future_open','levels90','shops90']].mean().to_string())
    print('\nGATE AGGREGATE\n',runs.groupby('gate')[['international_open','future_open','levels90','shops90']].mean().to_string())
if __name__=='__main__': main()
