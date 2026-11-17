import pandas as pd,numpy as np, math
from pathlib import Path
D=Path('/mnt/data/work_empire/Business_Empire_Master_Bundle_v1.27/project_docs')
s=pd.read_csv(D/'SHOP_ECONOMY_30_CANDIDATE.csv')
ids=s.shop_id.tolist(); regs=s.region_id.tolist(); costs=s.base_cost_candidate.to_numpy(float); inc=s.base_income_per_sec_candidate.to_numpy(float); ridx={r:[i for i,x in enumerate(regs) if x==r] for r in ['street','food','mall','finance','international','future']}
rcost={'food':500,'mall':5000,'finance':50000,'international':1.5e12,'future':2e14}
profiles={'none':[], 'starter':[('common','income',20,2),('rare','discount',20,2)],'mythic':[('rare','discount',35,3),('epic','income',40,3),('legendary','offline',40,3),('mythic','traffic',45,3)]}
bud={'common':12,'rare':15,'epic':18,'legendary':21,'mythic':24}; capoff={'epic':.70,'legendary':.75,'mythic':.85}
def effs(profile):
 out={}
 for r in ridx:
  sel=profile[:2]; v={'income':0,'discount':0,'offline':0,'traffic':0}
  for rarity,skill,lv,star in sel:
   total=bud[rarity]+int(.24*(lv-1))+2*(star-1)+int((lv-1)//10)
   ranks={'income':max(1,int(total*.17)),'discount':max(1,int(total*.17)),'offline':max(1,int(total*.17)),'traffic':max(1,int(total*.17))}
   ranks[skill]=max(1,int(total*.45))
   for k,x in ranks.items():
    c={'income':.45,'discount':.30,'offline':.25,'traffic':.45}[k]; kval=8
    v[k]+=c*x/(x+kval)
  v['income']=min(.65,v['income']);v['discount']=min(.35,v['discount']);v['traffic']=min(.45,v['traffic'])
  eligible=[x for x in sel if x[0] in capoff]
  v['offline']=min((max([capoff[x[0]] for x in eligible])-.60 if eligible else 0),v['offline']*.55)
  out[r]=v
 return out

def run(seed,a,off,strat,mgr,p,q,days=90):
 rng=np.random.default_rng(seed); L=np.zeros(30,dtype=int); L[0]=1; gold=120.; cum=0.; unlocked={'street'}; uday={}; prof=effs(profiles[mgr]); blocked=0; maxblock=0
 for day in range(1,days+1):
  act=a*rng.uniform(.85,1.15); oh=min(8,off*rng.uniform(.75,1.25)); rate=0
  for r,ix in ridx.items():
   if r not in unlocked:continue
   v=prof[r]; util=min(1,.78*(1+v['traffic']*1.15))
   rr=sum(inc[i]*(L[i]**q)*util*(1+v['income']) for i in ix if L[i]>0)
   rate+=rr
  earn=rate*(act*60+oh*3600*.60) # offline role modifier separately by region omitted here, conservative region mix
  gold+=earn;cum+=earn
  acts=max(1,min(6,int(act*.08)))
  did=False
  for _ in range(acts):
   opts=[]
   # unlocks
   if 'food' not in unlocked and L[0]>=2 and gold>=500: opts.append((3 if strat=='rush' else .1,'u','food',500,0))
   if 'mall' not in unlocked and 'food' in unlocked and L[6]>=1 and L.sum()>=4 and gold>=5000: opts.append((3 if strat=='rush' else .1,'u','mall',5000,0))
   if 'finance' not in unlocked and 'mall' in unlocked and L[12]>=1 and L.sum()>=7 and gold>=50000: opts.append((3 if strat=='rush' else .1,'u','finance',50000,0))
   fi=ridx['finance']; ii=ridx['international']
   if 'international' not in unlocked and sum(L[i]>0 for i in fi)>=3 and sum(L[i] for i in fi)>=30 and cum>=5e12 and gold>=1.5e12:opts.append((4 if strat=='rush' else .1,'u','international',1.5e12,0))
   if 'future' not in unlocked and sum(L[i]>0 for i in ii)>=4 and sum(L[i] for i in ii)>=40 and cum>=5e14 and gold>=2e14:opts.append((4 if strat=='rush' else .1,'u','future',2e14,0))
   for i in range(30):
    if regs[i] not in unlocked:continue
    lv=L[i]; c=costs[i] if lv==0 else math.ceil(costs[i]*(lv+1)**p)
    if gold<c:continue
    v=prof[regs[i]]; discount=v['discount']; realc=max(costs[i]*.65,c*(1-discount)) if lv else c
    old=inc[i]*lv**q; new=inc[i]*max(1,lv+1)**q; delta=(new-old)*min(1,.78*(1+v['traffic']*1.15))*(1+v['income'])
    score=delta/max(1,realc)
    if strat=='rush' and regs[i] in ('international','future'):score*=1.3
    opts.append((score,'s',i,realc,delta))
   if not opts:break
   best=max(opts,key=lambda x:x[0]);gold-=best[3]
   if best[1]=='u':unlocked.add(best[2]);uday[best[2]]=day
   else:L[best[2]]+=1
   did=True
  blocked=0 if did else blocked+1;maxblock=max(maxblock,blocked)
 return {'active':a,'offline':off,'strategy':strat,'manager':mgr,'p':p,'q':q,'intl_day':uday.get('international',np.nan),'future_day':uday.get('future',np.nan),'finance_day':uday.get('finance',np.nan),'shops90':int((L>0).sum()),'levels90':int(L.sum()),'gold90':gold,'cumulative90':cum,'max_no_purchase_days':maxblock}

rows=[]
for p,q in [(1,1),(1.1,.85),(1.15,.85)]:
 for a in [12.5,30,75]:
  for off in [0,4,8]:
   for strat in ['roi','rush']:
    for mgr in ['none','starter','mythic']:
     for seed in range(5):rows.append(run(int(20261101+seed*101+a*10+off),a,off,strat,mgr,p,q))
r=pd.DataFrame(rows);r.to_csv(D/'FULL_ECONOMY_MC_RUNS_v1_28.csv',index=False)
g=r.groupby(['p','q','active','offline','strategy','manager']).agg(intl_p10=('intl_day',lambda x:np.nanpercentile(x.dropna(),10) if x.notna().any() else np.nan),intl_p50=('intl_day','median'),intl_p90=('intl_day',lambda x:np.nanpercentile(x.dropna(),90) if x.notna().any() else np.nan),future_p50=('future_day','median'),levels90_p50=('levels90','median'),shops90_p50=('shops90','median'),gold90_p50=('gold90','median'),blocked_p90=('max_no_purchase_days',lambda x:np.percentile(x,90))).reset_index();g.to_csv(D/'FULL_ECONOMY_MC_SUMMARY_v1_28.csv',index=False)
# curve score across player activity profiles
cr=[]
for (p,q),z in r.groupby(['p','q']):
 score=0; ms=[]
 for a,lo,hi in [(12.5,20,60),(30,12,45),(75,6,30)]:
  x=z[z.active==a].intl_day.dropna(); med=float(x.median()) if len(x) else 120; pct=float(x.between(lo,hi).mean()) if len(x) else 0
  score+=pct*2-abs(med-(lo+hi)/2)/(hi-lo+1);ms.append(med)
 x0=z[z.offline==0].intl_day.dropna();x8=z[z.offline==8].intl_day.dropna(); m0=float(x0.median()) if len(x0) else 120;m8=float(x8.median()) if len(x8) else 120
 score-=max(0,m0/max(1,m8)-3)*.35
 cr.append({'p':p,'q':q,'score':score,'light_intl_p50':ms[0],'normal_intl_p50':ms[1],'high_intl_p50':ms[2],'intl_0h_p50':m0,'intl_8h_p50':m8,'idle_ratio':m0/max(1,m8)})
c=pd.DataFrame(cr).sort_values('score',ascending=False);c.to_csv(D/'FULL_ECONOMY_CURVE_TUNING_v1_28.csv',index=False)
print('n',len(r));print(c.to_string(index=False));print('\nManager:',r.groupby(['manager','active'])[['intl_day','future_day','levels90']].median().to_string());print('\nStrategy:',r.groupby(['strategy','active'])[['intl_day','future_day','levels90']].median().to_string())
