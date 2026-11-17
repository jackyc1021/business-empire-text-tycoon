#!/usr/bin/env python3
"""60-day six-manager progression and gacha Monte Carlo for the current 10-manager runtime roster."""
from __future__ import annotations
import random, statistics, json
from collections import Counter

SEEDS=10000
RARITIES=['common','rare','epic','legendary','mythic']
ROSTER={'common':2,'rare':2,'epic':2,'legendary':2,'mythic':2}
NORMAL={'common':48.0,'rare':40.0,'epic':10.8,'legendary':1.2,'mythic':0.0}
ADV={'common':45.0,'rare':40.0,'epic':12.0,'legendary':2.4,'mythic':0.6}
COEF={'common':1.0,'rare':1.2,'epic':1.5,'legendary':2.0,'mythic':3.0}
BASE=[2,3,4]
EXP_PER_MANAGER=58410
EXP_SIX=EXP_PER_MANAGER*6

# 60-day calendar: 60 daily clears, 8 complete weekly cycles, 8.57 sign-in cycles,
# 4 biweekly event clears, 2 monthly milestones and 28k one-time onboarding/achievements.
EXP_DAILY=3600*60
EXP_WEEKLY=8000*8
EXP_SIGNIN=3500*(60/7)
EXP_EVENT=8000*4
EXP_MONTHLY=12500*2
EXP_ONETIME=28000
EXP_TOTAL=EXP_DAILY+EXP_WEEKLY+EXP_SIGNIN+EXP_EVENT+EXP_MONTHLY+EXP_ONETIME

MEDALS_DAILY=60
MEDALS_WEEKLY=4*8
MEDALS_SIGNIN=60/7
MEDALS_EVENT=4*4
MEDALS_MONTHLY=8*2
MEDALS_TOTAL=MEDALS_DAILY+MEDALS_WEEKLY+MEDALS_SIGNIN+MEDALS_EVENT+MEDALS_MONTHLY

# Ticket schedule: 4 normal tickets/week from weekly task points + 1 normal sign-in/week
# + 1 normal ticket/week averaged from biweekly events, plus 1 starter ticket; 8 advanced
# tickets from day-7 sign-in. Fifty paid normal tickets produce five 11-pull ten-pulls.
NORMAL_PAID=50
ADV_PAID=8

def draw_rarity(rng, weights):
    x=rng.random()*100
    acc=0
    for r in RARITIES:
        acc+=weights.get(r,0)
        if x<acc:
            return r
    return 'common'

def draw_normal(rng, misses):
    # 50th normal-pool result guarantees legendary; free 11th results also count.
    if misses>=49:
        return 'legendary',0
    r=draw_rarity(rng,NORMAL)
    return r,(0 if r=='legendary' else misses+1)

def pity_advanced(rng, misses):
    n=misses+1
    if n>=80:
        return 'mythic',0
    w=dict(ADV)
    if n>70:
        p=min(100,0.6+(n-70)*10)
        scale=(100-p)/(100-.6)
        for r in w:
            if r=='mythic': w[r]=p
            else: w[r]*=scale
    r=draw_rarity(rng,w)
    return r, (0 if r=='mythic' else misses+1)

def medal_cost(r):
    return [sum(int(__import__('math').ceil(x*COEF[r])) for x in BASE)]*3

def pct(xs,p):
    xs=sorted(xs)
    return xs[min(len(xs)-1,round((len(xs)-1)*p))]

unique_counts=[]; total_pulls=[]; medal_needs=[[],[],[]]; team_rarity=Counter(); honors=[]; draws_to_six=[]
for seed in range(SEEDS):
    rng=random.Random(seed+301130)
    owned={}; pity=0; honor=0; dupes=0; normal_paid=0; advanced_paid=0; normal_free=0
    # Weekly rhythm: four normal tickets from weekly points, one sign-in ticket and one event ticket, plus one advanced ticket. Ten normal paid
    # tickets grant one additional free result; the free result uses the same pool.
    sequence=[]
    for week in range(8):
        sequence.extend(['normal']*6+['advanced'])
    # Add the partial 4-day week: one normal and no guaranteed advanced ticket.
    sequence.append('normal')
    sequence.insert(0,'normal')  # starter ordinary ticket already in fresh save
    normal_paid_count=0;normal_misses=0
    for mode in sequence:
        if mode=='normal':
            normal_paid_count+=1; normal_paid+=1
            r,normal_misses=draw_normal(rng,normal_misses)
        else:
            advanced_paid+=1; r,pity=pity_advanced(rng,pity)
        cid=rng.choice([f'{r}-{i}' for i in range(ROSTER[r])])
        honor += {'common':1,'rare':2,'epic':5,'legendary':15,'mythic':40}[r]
        if cid in owned: dupes+=1
        else: owned[cid]=r
        # At every tenth paid normal draw, add the 11th free normal result.
        if mode=='normal' and normal_paid_count%10==0:
            rfree,normal_misses=draw_normal(rng,normal_misses); cidfree=rng.choice([f'{rfree}-{i}' for i in range(ROSTER[rfree])])
            honor += {'common':1,'rare':2,'epic':5,'legendary':15,'mythic':40}[rfree]
            if cidfree in owned: dupes+=1
            else: owned[cidfree]=rfree
            normal_free+=1
    # Players may choose any six owned characters; model the strongest available six,
    # which is the conservative medal-demand case for a player chasing higher rarity.
    ordered=sorted(owned.values(),key=lambda r:RARITIES.index(r),reverse=True)
    team=ordered[:6]
    draws_to_six.append(len(sequence)+normal_free if len(owned)>=6 else 999)
    unique_counts.append(len(owned)); total_pulls.append(len(sequence)+normal_free); honors.append(honor)
    costs=[0,0,0]
    for r in team:
        team_rarity[r]+=1
        c=medal_cost(r)
        for j in range(3): costs[j]+=c[j]
    for j in range(3): medal_needs[j].append(costs[j])

result={
 'seeds':SEEDS,
 'experience':{'per_manager':EXP_PER_MANAGER,'six_managers':EXP_SIX,'planned_60day_supply':round(EXP_TOTAL),'surplus':round(EXP_TOTAL-EXP_SIX),'coverage':round(EXP_TOTAL/EXP_SIX,4),'attendance_sensitivity':{str(p):round(EXP_ONETIME+(EXP_TOTAL-EXP_ONETIME)*p) for p in [1.0,.9,.85,.8]}},
 'medals':{'planned_basic_intermediate':round(60+32+8+16+6,1),'planned_advanced':round(60+32+8+16+4,1),'need_p50_each_tier':[pct(x,.5) for x in medal_needs],'need_p90_each_tier':[pct(x,.9) for x in medal_needs],'need_p99_each_tier':[pct(x,.99) for x in medal_needs]},
 'recruitment':{'normal_paid_tickets':NORMAL_PAID,'normal_results_with_tenpull_bonus':int(NORMAL_PAID)+5,'advanced_tickets':ADV_PAID,'normal_plus_advanced_results_before_extra':NORMAL_PAID+5+ADV_PAID,'unique_six_completed_pct':round(sum(x>=6 for x in unique_counts)/SEEDS*100,2),'owned_unique_p50':pct(unique_counts,.5),'owned_unique_p10':pct(unique_counts,.1),'owned_unique_p90':pct(unique_counts,.9),'free_tenpull_bonus_results':5,'extra_draws_to_fill_p50':pct([max(0,x-(int(NORMAL_PAID)+5+8)) for x in total_pulls],.5),'honor_p50':pct(honors,.5),'honor_p90':pct(honors,.9)},
 'roster_model':'current_runtime_10_even_rarity_2_each','team_rarity_share':{r:round(team_rarity[r]/(SEEDS*6),4) for r in RARITIES},
}
print(json.dumps(result,ensure_ascii=False,indent=2))
