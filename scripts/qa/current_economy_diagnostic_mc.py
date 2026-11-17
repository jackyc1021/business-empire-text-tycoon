import random, math, statistics, csv
shops=[('stall','street',10,1),('cafe','food',80,5),('fashion','mall',650,24),('tech','mall',5200,115),('hotel','food',42000,560),('mall','mall',360000,2800),('factory','finance',3200000,15000),('tower','finance',28000000,85000),('space','finance',260000000,520000)]
rarity_caps={'none':.60,'epic':.70,'legendary':.75,'mythic':.85}
def run(seed,active_min,luck,offline_style,days=30):
 r=random.Random(seed); levels={x[0]:(1 if x[0]=='stall' else 0) for x in shops}; unlocked={'street'}; gold=120; unlocked_day={}; stuck=0; max_stuck=0; role='none'; role_level=1; role_star=1
 if luck=='good': role=r.choice(['legendary','mythic']); role_level=35; role_star=3
 elif luck=='average': role='epic'; role_level=20; role_star=2
 if offline_style=='offlineheavy': active_min=max(5,active_min*.6)
 elif offline_style=='activeheavy': active_min*=1.25
 def rate():
  if role=='none': return .60
  p=.70*(role_level-1)/99+.30*(role_star-1)/4
  return .60+(rarity_caps[role]-.60)*p
 def income(): return sum(base*levels[sid] for sid,reg,cost,base in shops)
 def total_lv(): return sum(levels.values())
 def avail(s):
  sid=s[0]
  if levels[sid]>0:return True
  return {'stall':True,'cafe':'food' in unlocked and levels['stall']>=1,'hotel':'food' in unlocked and levels['cafe']>=1,'fashion':'mall' in unlocked and levels['hotel']>=1,'tech':'mall' in unlocked and levels['fashion']>=1,'mall':'mall' in unlocked and levels['tech']>=1,'factory':'finance' in unlocked and levels['mall']>=1,'tower':'finance' in unlocked and levels['factory']>=1,'space':'finance' in unlocked and levels['tower']>=1}.get(sid,False)
 for day in range(1,days+1):
  gold += income()*8*3600*rate()+income()*active_min*60
  gold += int(active_min*12)*5*1.04
  for reg,cost,cond in [('food',500,levels['stall']>=2),('mall',5000,levels['hotel']>=1 and total_lv()>=4),('finance',50000,levels['mall']>=1 and total_lv()>=7)]:
   if reg not in unlocked and cond and gold>=cost: gold-=cost;unlocked.add(reg);unlocked_day[reg]=day
  buys=0
  while buys<5:
   opts=[]
   for s in shops:
    sid,reg,basecost,baseinc=s
    if avail(s):
     cost=basecost if levels[sid]==0 else math.ceil(basecost*(levels[sid]+1))
     if cost<=gold:opts.append((baseinc/cost,cost,sid))
   if not opts:break
   _,cost,sid=max(opts);gold-=cost;levels[sid]+=1;buys+=1
  stuck=stuck+1 if buys==0 else 0;max_stuck=max(max_stuck,stuck)
 return {'max_stuck':max_stuck,'unlock_food':unlocked_day.get('food',0),'unlock_mall':unlocked_day.get('mall',0),'unlock_finance':unlocked_day.get('finance',0),'levels':sum(levels.values()),'income':income(),'gold':gold}
if __name__=='__main__':
 rows=[]
 for active in [12,30,75]:
  for luck in ['bad','average','good']:
   for style in ['balanced','offlineheavy','activeheavy']:
    res=[run(20261101+i+active*100000+['bad','average','good'].index(luck)*1000000+['balanced','offlineheavy','activeheavy'].index(style)*10000000,active,luck,style) for i in range(1000)]
    print(active,luck,style,'finance median',statistics.median(x['unlock_finance'] for x in res),'levels median',statistics.median(x['levels'] for x in res),'maxstuck median',statistics.median(x['max_stuck'] for x in res))
    for k in ['unlock_food','unlock_mall','unlock_finance','levels','income','gold','max_stuck']:
     vals=sorted(x[k] for x in res);rows.append({'active_min':active,'luck':luck,'style':style,'metric':k,'mean':statistics.mean(vals),'p10':vals[99],'median':statistics.median(vals),'p90':vals[899],'never_pct':sum(v==0 for v in vals)/len(vals)*100 if k.startswith('unlock_') else ''})
 with open('/tmp/results.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
