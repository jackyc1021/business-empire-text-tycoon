#!/usr/bin/env python3
"""Static 30-shop curve diagnostic for Bundle v1.27.
All new-shop inputs and p/q exponents are candidate assumptions, not runtime values.
"""
import csv, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'project_docs/SHOP_ECONOMY_30_CANDIDATE.csv'
out=ROOT/'project_docs/SHOP_30_CURVE_STATIC_SENSITIVITY_v1_27.csv'
levels=[1,2,5,10,25,50,100]
curves=[(1.00,1.00),(1.00,.85),(1.10,.85),(1.15,.85),(1.10,.90),(1.20,.90)]
rows=[]
with source.open(encoding='utf-8-sig',newline='') as f:
    shops=list(csv.DictReader(f))
for shop in shops:
    cost0=int(shop['base_cost_candidate']); income0=float(shop['base_income_per_sec_candidate'])
    for p,q in curves:
        for L in levels:
            cost=cost0 if L==0 else math.ceil(cost0*((L+1)**p))
            current=income0*(L**q)
            next_income=income0*((L+1)**q)
            delta=next_income-current
            payback=cost/delta/3600 if delta>0 else None
            rows.append({
                'region':shop['region_name'],'shop_id':shop['shop_id'],'shop_name':shop['shop_name'],
                'input_status':shop['status'],'p_cost':p,'q_income':q,'current_level':L,
                'next_level_cost':cost,'income_at_level_per_sec':round(current,6),
                'marginal_income_per_sec':round(delta,6),'static_payback_hours':round(payback,4) if payback is not None else ''
            })
with out.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(f'PASS: {len(shops)} shops, {len(curves)} p/q curves, {len(levels)} level points = {len(rows)} rows')
print(f'Wrote {out}')
