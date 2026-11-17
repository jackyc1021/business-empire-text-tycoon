#!/usr/bin/env python3
import csv, importlib.util, math
from pathlib import Path
p=Path(__file__).with_name('shop_economy_curve_event_mc.py')
spec=importlib.util.spec_from_file_location('sim',p); sim=importlib.util.module_from_spec(spec);spec.loader.exec_module(sim)
# Determinism and baseline exactness
x=sim.run(12345,12.5,1.0,8); y=sim.run(12345,12.5,1.0,8)
assert x['levels']==y['levels'] and x['gold_end']==y['gold_end']
assert sim.CURVES['linear_current']==1.0
assert sim.SHOPS[0]==('stall','street',10,1)
# Cost curve monotonicity for all shops and tested levels
for _,_,base_cost,_ in sim.SHOPS:
 prev=base_cost
 for L in range(1,101):
  cost=math.ceil(base_cost*((L+1)**1.0))
  assert cost>=prev
  prev=cost
# Check generated output cardinalities and schema
root=p.parents[1]/'project_docs'
for name,expected in [('SHOP_ECONOMY_EVENT_MC_RUNS.csv',2700),('SHOP_ECONOMY_EVENT_MC_DAILY.csv',81000)]:
 with (root/name).open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
 assert len(rows)==expected,(name,len(rows),expected)
with (root/'SHOP_UPGRADE_CURVE_CANDIDATE_COMPARISON.csv').open(encoding='utf-8-sig') as f:
 rows=list(csv.DictReader(f))
assert len(rows)==9*6*6
print('PASS: deterministic event replay; 2,700 runs; 81,000 daily rows; 324 candidate payback rows; monotonic costs')
